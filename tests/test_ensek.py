import os
from datetime import datetime, timezone
from pathlib import Path
import itertools
from requests.exceptions import RequestException
from http.client import OK

import pytest
import vcr

from ensek import Ensek, EnsekError

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


def client_factory(*, retries=0, retry_wait=0):
    return Ensek(
            api_url=ENSEK_API_URL, api_key=ENSEK_API_KEY,
            retry_count=retries, retry_wait=retry_wait
        )


def mock_response(*, json, ok, status_code):
    class Response:
        def __init__(self):
            self._json = json
            self.ok = ok
            self.status_code = status_code

        def json(self):
            return self._json

    return Response()


@pytest.fixture
def client():
    return client_factory()


@pytest.mark.parametrize('retries, retry_wait, expect_raise', [
    (5, 0, True),
    (0, 5, True),
    (0, 0, False),
    (5, 6, False)
])
def test_client_init(retries, retry_wait, expect_raise):
    if expect_raise:
        with pytest.raises(ValueError):
            client_factory(retries=retries, retry_wait=retry_wait)
    else:
        client_factory(retries=retries, retry_wait=retry_wait)


@pytest.mark.parametrize('retries', [0, 1, 2, 3])
def test_request_retries_on_ensek_error(mocker, retries):
    side_effect = [EnsekError('', '') for _ in range(retries - 1)]
    expected_result = {'message': 'success'}
    response = mock_response(
        json=expected_result, ok=True, status_code=OK
    )
    side_effect.append(response)
    mocker.patch('requests.get', side_effect=side_effect)
    client = client_factory(retries=3, retry_wait=0.1)

    result = client._request('get', 'fakepath')
    assert result == expected_result


def test_request_raises_after_retries_exceeded(mocker):
    mocker.patch('requests.get', side_effect=[
        EnsekError('', None),
        EnsekError('', None),
        EnsekError('', None),
    ])
    client = client_factory(retries=3, retry_wait=0.1)
    with pytest.raises(EnsekError):
        client._request('get', 'fakepath')


def test_request_raises_when_request_exception(mocker, client):
    mocker.patch('requests.get', side_effect=RequestException)
    with pytest.raises(EnsekError):
        client._request('get', 'fakepath')


@my_vcr.use_cassette()
def test_get_account(client):
    result = client.get_account(account_id=ACCOUNT_ID)

    assert isinstance(result, dict)
    assert set(result.keys()) == {
        'primaryContact', 'id', 'externalReference', 'siteAddress'
    }


@my_vcr.use_cassette()
def test_get_account_settings(client):
    result = client.get_account_settings(account_id=ACCOUNT_ID)

    assert isinstance(result, dict)
    assert result == {
        'AccountID': 1507,
        'BillDayOfMonth': 6,
        'BillFrequencyMonths': 1,
        'TopupWithEstimates': True,
        'SendEmail': True,
        'SendPost': False,
        'NextBillDate': '2018-10-06T00:00:00',
        'NextBillDay': 6,
        'NextBillMonth': 10,
        'NextBillYear': 2018
    }


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
def test_create_and_get_meter_reading(client, mocker):
    meter_points = client.get_meter_points(account_id=ACCOUNT_ID)
    meter_point_id = meter_points[0]['id']
    meter_point = meter_points[0]
    registers = itertools.chain.from_iterable(
        [m['registers'] for m in meter_point['meters']]
    )

    register_id = tuple(registers)[0]['id']

    # Create reading
    result = client.create_meter_reading(
        account_id=ACCOUNT_ID,
        meter_point_id=meter_point_id,
        register_id=register_id,
        value=2.0,
        timestamp=datetime.now(timezone.utc),
        source='SMART',
    )

    assert result == []

    # Check reading added correctly
    result = client.get_meter_point_readings(meter_point_id=meter_point_id)
    assert len(result)
    added_reading = result[-1]
    assert added_reading['meterReadingSource'] == 'SMART'
    assert added_reading['readings'] == [
        {
            'id': mocker.ANY,
            'registerId': register_id,
            'value': 2.0,
        }
    ]


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
        'igtIndicator': False,
        'gasLargeSiteIndicator': False,
        'fuelType': 'Gas',
        'meterDetails': [{
            'meterSerialNumber': '00659516'
        }],
        'meterDesignation': None,
        'meterStatus': None,
        'aq': None,
        'shipper': None,
        'supplier': None,
        'MeterPoint': '3226987202',
        'attributes': {
            'igtIndicator': False,
            'isPrepay': False
        },
        'matchType': 'Confirmed',
        'address': {
            'uprn': None,
            'additionalInformation': None,
            'subBuildingNameNumber': None,
            'buildingNameNumber': '55',
            'dependentThoroughfare': None,
            'thoroughfare': None,
            'doubleDependentLocality': None,
            'dependentLocality': 'Arbour Square',
            'locality': 'London',
            'county': None,
            'postcode': 'E1 0PS',
            'displayName': '55 ,\nArbour Square,\nLondon,\nE1 0PS'
        },
        'includeInRegistration': None,
        'lookupType': 'ByMeterpoint'
    }


@my_vcr.use_cassette()
def test_get_electricity_utility(client):
    result = client.get_electricity_utility(mpan_core_id='1900025225872')

    assert result == {
        'MeterPoint': '1900025225872',
        'address': {
            'additionalInformation': None,
            'buildingNameNumber': '9',
            'county': 'Kent',
            'dependentLocality': 'Weavering',
            'dependentThoroughfare': None,
            'displayName': (
                '9 Speedwell Close,\n'
                'Weavering,\n'
                'Maidstone,\n'
                'Kent,\n'
                'ME14 5SX'
            ),
            'doubleDependentLocality': None,
            'locality': 'Maidstone',
            'postcode': 'ME14 5SX',
            'subBuildingNameNumber': None,
            'thoroughfare': 'Speedwell Close',
            'uprn': None
        },
        'attributes': {
            'greenDealActive': False,
            'isPrepay': False
        },
        'currentSupplier': 'GONG',
        'dataAggregator': 'UDMS',
        'dataAggregatorDate': '2018-04-16T00:00:00',
        'dataCollector': 'UDMS',
        'dataCollectorDate': '2018-04-16T00:00:00',
        'dccServiceFlag': None,
        'dccServiceFlagDate': None,
        'distributor': 'SEEB',
        'energisationStatus': 'Energised',
        'energisationStatusDate': '2017-12-18T00:00:00',
        'fuelType': 'Electricity',
        'greenDealActive': False,
        'greenDealStatus': 'None',
        'gridSupplyPoint': '_J',
        'gridSupplyPointDate': '1997-11-19T00:00:00',
        'ihdInstallStatus': None,
        'ihdInstallStatusDate': None,
        'includeInRegistration': None,
        'lineLossFactorClass': '001',
        'lineLossFactorClassDate': '2018-04-16T00:00:00',
        'lineLossFactorClassIndicator': 'A',
        'lookupType': 'ByMeterpoint',
        'matchType': 'Confirmed',
        'measurementClass': 'F',
        'measurementClassDate': '2018-04-16T00:00:00',
        'meterDetails': [{
            'installingSupplier': 'OVOE',
            'meterInstallationDate': '2016-08-17T00:00:00',
            'meterSerialNumber': '16P0157619',
            'metertype': 'S1'
        }],
        'meterOperator': 'CMSL',
        'meterOperatorDate': '2018-04-16T00:00:00',
        'meterTimeswitchClass': '801',
        'meterTimeswitchClassDate': '2017-12-18T00:00:00',
        'meterTimeswitchClassIsPrePayment': False,
        'meterTimeswitchClassMeterType': 'UN',
        'meterTimeswitchClassPaymentType': 'CR',
        'meterTimeswitchClassRelated': False,
        'meterTimeswitchClassTimePatternRegimeCount': 1,
        'mpanTradingStatus': 'T',
        'profileClass': '00',
        'profileClassDate': '2018-04-16T00:00:00',
        'registrationDate': '2017-12-18T00:00:00',
        'smetsVersion': 'SMETS1',
        'smsoDate': '2016-08-17T00:00:00',
        'smsoMpid': 'SMLU',
        'standardSettlementConfiguration': None,
        'standardSettlementConfigurationDate': None,
        'statusDate': '1997-11-21T00:00:00'
    }


@my_vcr.use_cassette()
def test_get_live_balances(client):
    account_id = 1500
    resp = client.get_live_balances(account_id=account_id)

    expected_resp = {
        'pendingPayments': 0.0, 'lastBill': None, 'unbilledCharges': 0.0,
        'estimatedCharges': 0.0, 'standingCharges': 0.0,
        'discountCharges': 0.0, 'cclCharges': 0.0,
        'total': {
            '$type': (
                'CRMPortalServices.Interface.Account.Statementing.'
                'StatementTotalLine, CRMPortalServices.Interface'
            ),
            'gross': 0.0, 'net': 0.0, 'tax': 0.0, 'taxDetails': []
        },
        'lastUpdated': '0001-01-01T00:00:00',
        'newTransactions': 0.0,
        'currentBalance': 0.0,
        'lastTransactionBalance': None
    }
    assert resp == expected_resp


@my_vcr.use_cassette()
def test_get_live_balances_detailed(client):
    account_id = 1500
    resp = client.get_live_balances_detailed(account_id=account_id)

    expected_resp = {'TotalCharges': 0.0, 'Charges': []}
    assert resp == expected_resp


@my_vcr.use_cassette()
def test_get_all_account_ids(client):
    account_numbers = client.get_all_account_ids()

    assert account_numbers
    assert all(isinstance(num, int) for num in account_numbers)


@my_vcr.use_cassette()
def test_get_addresses_at_postcode(client, mocker):
    results = client.get_addresses_at_postcode(postcode='se14yu')

    assert results
    for result in results:
        assert result == {
            'uprn': mocker.ANY,
            'additionalInformation': mocker.ANY,
            'subBuildingNameNumber': mocker.ANY,
            'buildingNameNumber': mocker.ANY,
            'dependentThoroughfare': mocker.ANY,
            'thoroughfare': mocker.ANY,
            'doubleDependentLocality': mocker.ANY,
            'dependentLocality': mocker.ANY,
            'locality': mocker.ANY,
            'county': mocker.ANY,
            'postcode': 'SE1 4YU',
            'displayName': mocker.ANY,
        }


@my_vcr.use_cassette()
def test_get_account_attributes(client, mocker):
    results = client.get_account_attributes(account_id=ACCOUNT_ID)

    expected_results = [
        {
            'accountId': ACCOUNT_ID,
            'name': 'PaymentType',
            'value': mocker.ANY,
            'type': 'string'
        }
    ]
    assert results == expected_results


@my_vcr.use_cassette()
def test_update_account_attribute(client):
    client.update_account_attribute(
        account_id=ACCOUNT_ID,
        name='PaymentType',
        value='value',
        type='string',
    )

    # Check it was updated
    results = client.get_account_attributes(account_id=ACCOUNT_ID)
    expected_results = [{
        'accountId': ACCOUNT_ID,
        'name': 'PaymentType',
        'value': 'value',
        'type': 'string',
    }]
    assert results == expected_results
