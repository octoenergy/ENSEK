import logging
from urllib.parse import urljoin
from http.client import NOT_FOUND, INTERNAL_SERVER_ERROR, BAD_REQUEST
from string import Template

import stringcase
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class EnsekError(Exception):
    def __init__(self, message, response):
        self.response = response
        self.message = message


class Ensek:

    ENDPOINTS = {
        'get_account': Template('/accounts/$account_id'),
        'get_meter_point_readings': Template(
            '/MeterPoints/$meter_point_id/Readings'
        ),
        'get_completed_signups': Template('/SignUps/Completed'),
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
    }

    def __init__(self, *, api_url, api_key):
        self._api_url = api_url.rstrip('/')
        self._api_key = api_key
        self._resource_path = None
        self._headers = {'Authorization': f'Bearer {self._api_key}'}

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

    def _path_to_full_url(self, path):
        return urljoin(self._api_url, path.lstrip('/'))

    def _get(self, path, params=None):
        url = self._path_to_full_url(path)
        try:
            response = requests.get(url, headers=self._headers, params=params)
        except RequestException as exc:
            raise EnsekError(exc, response=None) from exc
        if not response.ok:
            self._handle_bad_response(response)
        return response.json()

    def _post(self, *, path, body):
        url = self._path_to_full_url(path)
        try:
            response = requests.post(url, headers=self._headers, json=body)
        except RequestException as exc:
            raise EnsekError(exc, response=None) from exc
        if not response.ok:
            self._handle_bad_response(response)
        return response.json()

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
