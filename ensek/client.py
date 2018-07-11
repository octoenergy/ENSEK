import logging
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
        'get_completed_signups': Template('/SignUps/Completed'),
        'get_meter_points': Template('/Accounts/$account_id/MeterPoints'),
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

    def _get(self, path, params):
        url = f'{self._api_url}/{path.lstrip("/")}'
        try:
            response = requests.get(url, headers=self._headers, params=params)
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
        try:
            self._resource_path = self.ENDPOINTS[name]
        except KeyError:
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
