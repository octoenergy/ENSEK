import os
from pathlib import Path

import pytest
import vcr

from ensek import Ensek

my_vcr = vcr.VCR(
    serializer='yaml',
    cassette_library_dir='tests/cassettes',
    record_mode='once',
    match_on=['path', 'method'],
    filter_headers=['authorization']
)

ENSEK_API_URL = os.environ['ENSEK_API_URL']
ENSEK_API_KEY = os.environ['ENSEK_API_KEY']
STUBS_DIR = Path(Path().parent, 'fixtures')
# Magic IDs based on data on an environment from which stubs were created
ACCOUNT_ID = 1507
MPAN_CORE_ID = '9910000001507'


@pytest.fixture
def client():
    return Ensek(api_url=ENSEK_API_URL, api_key=ENSEK_API_KEY)


@my_vcr.use_cassette()
def test_get_account(client):
    result = client.get_account(account_id=ACCOUNT_ID)

    assert isinstance(result, dict)
    assert set(result.keys()) == {
        'primaryContact', 'id', 'externalReference', 'siteAddress'
    }


@my_vcr.use_cassette()
def test_get_completed_signups(client):
    result = client.get_completed_signups(after=1500)

    assert isinstance(result, dict)
    assert set(result.keys()) == {'results', 'meta'}


@my_vcr.use_cassette()
def test_get_meter_points(client):
    results = client.get_meter_points(account_id=ACCOUNT_ID)

    assert isinstance(results, list)
    assert set(results[0].keys()) == {
        'associationStartDate', 'associationEndDate', 'supplyStartDate',
        'supplyEndDate', 'isSmart', 'isSmartCommunicating', 'id',
        'meterPointNumber', 'meterPointType', 'meters', 'attributes'
    }


@my_vcr.use_cassette()
def test_get_account_tariffs(client):
    result = client.get_account_tariffs(
        account_id=ACCOUNT_ID, include_history=True
    )

    assert isinstance(result, dict)
    expected_result = {
        'tariffName': 'Standard Variable',
        'startDate': '2017-01-01T00:00:00',
        'endDate': None,
        'Electricity': {
            'unitRates': [
                {
                    'name': 'Any Time',
                    'rate': 10.2,
                    'registers': [1496]
                }, {
                    'name': 'Day Consumption',
                    'rate': 12.2,
                    'registers': []
                }, {
                    'name': 'Night Consumption',
                    'rate': 7.2,
                    'registers': []
                }
            ],
            'standingChargeRates':
            [{
                'name': 'Standing Charge',
                'rate': 20.2,
                'registers': None
            }]
        },
        'Gas': {
            'unitRates':
            [{
                'name': 'Gas Consumption',
                'rate': 2.1,
                'registers': [1497]
            }],
            'standingChargeRates':
            [{
                'name': 'Standing Charge',
                'rate': 20.2,
                'registers': None
            }]
        },
        'discounts': [],
        'tariffType': 'Variable',
        'exitFees': None
    }
    assert result == expected_result


@my_vcr.use_cassette()
def test_raises_lookuperror_if_404_status_code(client):
    account_id_no_tariffs = 1234567890

    with pytest.raises(LookupError) as exc:
        client.get_account_tariffs(account_id=account_id_no_tariffs)

    exc.match(r'404 .+')


@my_vcr.use_cassette()
def test_raises_valuerror_if_400_status_code(client):
    bad_account_id = 'aaa'

    with pytest.raises(ValueError):
        client.get_meter_points(account_id=bad_account_id)


@my_vcr.use_cassette()
def test_get_account_for_meter_point(client):
    result = client.get_account_for_meter_point(meter_point_id=MPAN_CORE_ID)

    assert isinstance(result, dict)
    assert result == {'accountId': ACCOUNT_ID}


@my_vcr.use_cassette()
def test_get_region_id_for_postcode(client):
    result = client.get_region_id_for_postcode(postcode='se14yu')

    assert result == 12


@my_vcr.use_cassette()
def test_get_gas_utility(client):
    result = client.get_gas_utility(mprn='3226987202')

    assert result == {
        'ldz': 'NT',
        'gasTransporter': 'National Grid Gas',
        'igtIndicator': False, 'gasLargeSiteIndicator': False,
        'fuelType': 'Gas', 'meterDetails': [{'meterSerialNumber': '00659516'}],
        'meterDesignation': None, 'meterStatus': None, 'aq': None,
        'shipper': None, 'supplier': None, 'MeterPoint': '3226987202',
        'attributes': {'igtIndicator': False, 'isPrepay': False},
        'matchType': 'Confirmed',
        'address': {
            'uprn': None, 'additionalInformation': None,
            'subBuildingNameNumber': None, 'buildingNameNumber': '55',
            'dependentThoroughfare': None, 'thoroughfare': None,
            'doubleDependentLocality': None,
            'dependentLocality': 'Arbour Square', 'locality': 'London',
            'county': None, 'postcode': 'E1 0PS',
            'displayName': '55 ,\nArbour Square,\nLondon,\nE1 0PS'
        },
        'includeInRegistration': None, 'lookupType': 'ByMeterpoint'
    }
