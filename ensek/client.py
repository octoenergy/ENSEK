import logging
from urllib.parse import urljoin
from http.client import NOT_FOUND, INTERNAL_SERVER_ERROR, BAD_REQUEST
from string import Template

import stringcase
import requests
from requests.exceptions import RequestException
from functools import wraps
from tenacity import (
    retry, before_log, wait_fixed, stop_after_attempt, retry_if_exception_type
)

logger = logging.getLogger(__name__)


class EnsekError(Exception):
    def __init__(self, message, response):
        self.response = response
        self.message = message
        super().__init__(self, message, response)


def _retry_on_ensek_error(func):
    def decorator(*args, **kwargs):
        client = args[0]
        max_retries = client._retry_count
        retry_wait = client._retry_wait
        if max_retries:
            @retry(
                stop=stop_after_attempt(max_retries),
                wait=wait_fixed(retry_wait),
                before=before_log(logging, logging.INFO),
                retry=retry_if_exception_type(EnsekError),
                reraise=True,
            )
            @wraps(func)
            def wrap():
                return func(*args, **kwargs)
            return wrap()
        else:
            return func(*args, **kwargs)
    return decorator


class Ensek:

    ENDPOINTS = {
        'get_account': Template('/accounts/$account_id'),
        'get_account_settings': Template(
            '/accounts/$account_id/AccountSettings'
        ),
        'get_meter_point_readings': Template(
            '/MeterPoints/$meter_point_id/Readings'
        ),
        'get_meter_points': Template('/Accounts/$account_id/MeterPoints'),
        'create_meter_reading': Template('/Accounts/$account_id/Readings'),
        'get_region_id_for_postcode': Template('/Regions/$postcode'),
        'get_gas_utility': Template('/UtilitiesLookups/Gas/$mprn'),
        'get_electricity_utility': (
            Template('/UtilitiesLookups/Elec/$mpan_core_id')
        ),
        'get_account_tariffs': Template('/Accounts/$account_id/Tariffs'),
        'get_account_for_meter_point': Template(
            '/Accounts/Lookups/MeterPoints/$meter_point_id'
        ),
        'get_live_balances': Template('/Accounts/$account_id/LiveBalances'),
        'get_live_balances_detailed': Template(
            '/Accounts/$account_id/LiveBalancesWithDetail'
        ),
        'get_addresses_at_postcode': Template(
            '/PostcodeLookups?postcode=$postcode'
        ),
        'get_account_attributes': Template(
            '/accounts/$account_id/Attributes'
        ),
        'update_account_attributes': Template(
            '/accounts/$account_id/Attributes'
        ),
    }

    def __init__(self, *, api_url, api_key, retry_count=0, retry_wait=0):
        self._api_url = api_url.rstrip('/')
        self._api_key = api_key
        self._resource_path = None
        self._headers = {'Authorization': f'Bearer {self._api_key}'}

        if bool(retry_count) != bool(retry_wait):
            raise ValueError(
                'retry_count and retry_wait must have the same truth value'
            )
        else:
            self._retry_count = retry_count
            self._retry_wait = retry_wait

    def get_all_account_ids(self):

        def _get_completed_signups(after=None):
            if after is not None:
                return self._get(f'/SignUps/Completed?after={after}')
            else:
                return self._get('/SignUps/Completed')

        ids = []
        last_id = None
        while True:
            resp = _get_completed_signups(after=last_id)
            account_ids = tuple(r['accountId'] for r in resp['results'])
            if not account_ids:
                break
            last_id = max(account_ids)
            ids.extend(account_ids)
        return set(ids)

    def create_meter_reading(
        self, *, account_id, meter_point_id, register_id, value, timestamp,
        source=None,
    ):
        path = self.ENDPOINTS['create_meter_reading'].substitute(
            account_id=account_id
        )
        body = [
            {
                'meterPointId': int(meter_point_id),
                'dateTime': timestamp.isoformat(),
                'meterReadingSource': source,
                'readings': [{
                    'registerId': int(register_id),
                    'value': float(value),
                }],
            }
        ]
        return self._post(path=path, body=body)

    def update_account_attribute(self, *, account_id, name, value, type):
        path = self.ENDPOINTS['update_account_attributes'].substitute(
            account_id=account_id
        )
        body = {
            'updatedAttributes': [{
                'accountId': account_id,
                'name': name,
                'value': value,
                'type': type,
            }],
            'deletedAttributes': []
        }
        self._put(path=path, body=body, json_resp=False)

    def _path_to_full_url(self, path):
        return urljoin(self._api_url, path.lstrip('/'))

    def _get(self, path, params=None):
        return self._request(method='get', path=path, params=params)

    def _post(self, *, path, body):
        return self._request(method='post', path=path, body=body)

    def _put(self, *, path, body, json_resp=True):
        return self._request(
            method='put', path=path, body=body, json_resp=json_resp
        )

    @_retry_on_ensek_error
    def _request(self, method, path, body=None, params=None, json_resp=True):
        url = self._path_to_full_url(path)
        try:
            response = getattr(requests, method)(
                url, headers=self._headers, json=body, params=params
            )
        except RequestException as exc:
            raise EnsekError(exc, response=None) from exc
        if not response.ok:
            self._handle_bad_response(response)
        if json_resp:
            return response.json()
        return response.text

    @staticmethod
    def _handle_bad_response(response):
        msg = f'{response.status_code} {response.request.url}'
        if response.status_code == NOT_FOUND:
            raise LookupError(msg)
        elif (
            response.status_code >= BAD_REQUEST and
            response.status_code < INTERNAL_SERVER_ERROR
        ):
            raise ValueError(msg)
        else:
            msg = f'{msg}: {response.text}'
            raise EnsekError(msg, response=response)

    def __getattr__(self, name):
        if name.startswith('get_'):
            try:
                self._resource_path = self.ENDPOINTS[name]
            except KeyError:
                return self.__dict__[name]
        else:
            # If the client method doesn't have `get_` prefix, assume it's
            # defined on the class
            return self.__dict__[name]
        return self

    def __call__(self, **kwargs):
        path = self._resource_path
        self._resource_path = None
        path_kwargs = {}
        params = {}
        for key, val in kwargs.items():
            if f'${key}' in path.template:
                path_kwargs[key] = val
            else:
                # API query params are in camelCase
                key = stringcase.camelcase(key)
                params[key] = val
        path = path.substitute(**kwargs)
        return self._get(path, params=params)
