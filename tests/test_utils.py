import pytest

from plenty_api.utils import (
    get_route, build_endpoint, check_date_range, parse_date, build_date_range,
    get_utc_offset, build_date_request_query
)


@pytest.fixture
def sample_date_ranges():
    samples = [
        {'start': '2020-09-14T08:00:00+02:00',  # Normal date => CORRECT
         'end': '2020-09-15T08:00:00+02:00'},
        {'start': '2020-09-16T08:00:00+02:00',  # End before start => FAIL
         'end': '2020-09-13T08:00:00+02:00'},
        {'start': '2019-09-16T08:00:00+02:00',  # Past date => CORRECT
         'end': '2019-10-13T08:00:00+02:00'},
        {'start': '2021-09-16T08:00:00+02:00',  # Future date => FAIL
         'end': '2021-10-13T08:00:00+02:00'}
    ]
    return samples


@pytest.fixture
def sample_input_date():
    samples = [
        '2020-09-14',
        '14-09-2020',
        '2020-09-14T08:00Z',
        '2020-09-14T08:00',
        '2020-09-14T08:00:00+02:00',
        'abc',
        ''
    ]
    return samples


@pytest.fixture
def expected_date():
    expected = [
        str(f'2020-09-14T00:00:00+{get_utc_offset()}'),
        str(f'2020-09-14T00:00:00+{get_utc_offset()}'),
        '2020-09-14T08:00:00+00:00',
        str(f'2020-09-14T08:00:00+{get_utc_offset()}'),
        '2020-09-14T08:00:00+02:00',
        '',
        ''
    ]
    return expected


@pytest.fixture
def sample_date_range_input():
    samples = [
        {'start': '2020-09-14', 'end': '2020-09-15'},
        {'start': '2020-09-14', 'end': '2020-09-13'},
        {'start': '2020-09-14T08:00Z', 'end': '2020-09-14T09:00Z'},
        {'start': '2020-09-14T08:00:00+02:00',
         'end': '2020-09-14T10:00:30+02:00'},
        {'start': 'abc', 'end': 'def'},
        {'start': '', 'end': ''}
    ]
    return samples


@pytest.fixture
def expected_date_range():
    expected = [
        {'start': str(f'2020-09-14T00:00:00+{get_utc_offset()}'),
         'end': str(f'2020-09-15T00:00:00+{get_utc_offset()}')},
        {'start': str(f'2020-09-14T00:00:00+{get_utc_offset()}'),
         'end': str(f'2020-09-13T00:00:00+{get_utc_offset()}')},
        {'start': '2020-09-14T08:00:00+00:00',
         'end': '2020-09-14T09:00:00+00:00'},
        {'start': '2020-09-14T08:00:00+02:00',
         'end': '2020-09-14T10:00:30+02:00'},
        None,
        None
    ]
    return expected


@pytest.fixture
def sample_query_data():
    samples = [
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Creation',
         'additional': ['documents']},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Payment',
         'additional': ['documents', 'comments']},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Change',
         'additional': ['shippingPackages']},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Delivery',
         'additional': ['documents']},
        {'date_range': {},
         'date_type': 'Creation',
         'additional': ['documents']},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': '',
         'additional': ['documents']},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Creation',
         'additional': ''}
    ]
    return samples


@pytest.fixture
def expected_query():
    expected = [
        '?createdAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&createdAtTo=2020-09-14T10%3A00%3A30%2B02%3A00' +
        '&with=documents',
        '?paidAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&paidAtTo=2020-09-14T10%3A00%3A30%2B02%3A00' +
        '&with=documents&with=comments',
        '?updatedAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&updatedAtTo=2020-09-14T10%3A00%3A30%2B02%3A00' +
        '&with=shippingPackages',
        '?outgoingItemsBookedAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&outgoingItemsBookedAtTo=2020-09-14T10%3A00%3A30%2B02%3A00' +
        '&with=documents',
        '',
        '',
        '?createdAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&createdAtTo=2020-09-14T10%3A00%3A30%2B02%3A00'
    ]
    return expected


def test_get_route():
    sample_data = ['order', 'item', 'ITEMS', 'oRdErS', 'wrong', '']
    result = []
    expected = ['/rest/orders', '/rest/items', '/rest/items', '/rest/orders',
                '', '']

    for domain in sample_data:
        result.append(get_route(domain=domain))

    assert expected == result


def test_build_endpoint():
    sample_data = [
        {'url': 'https://test.plentymarkets-cloud01.com',
         'route': '/rest/orders',
         'query': "?orderType=1&with=documents"},
        {'url': 'https://test.plentymarkets-cloud01.com',
         'route': '/rest/orders',
         'query': ""},
        {'url': 'https://invalid.com',
         'route': '/rest/orders',
         'query': "?orderType=1&with=documents"},
        {'url': 'https://test.plentymarkets-cloud01.com',
         'route': '/rest/invalid',
         'query': "?orderType=1&with=documents"},
        {'url': '',
         'route': '/rest/orders',
         'query': "?orderType=1&with=documents"},
        {'url': 'https://test.plentymarkets-cloud01.com',
         'route': '',
         'query': "?orderType=1&with=documents"}
    ]

    expected = ['https://test.plentymarkets-cloud01.com/rest/orders?orderType=1&with=documents',
                'https://test.plentymarkets-cloud01.com/rest/orders', '', '',
                '', '']
    result = []

    for sample in sample_data:
        result.append(build_endpoint(url=sample['url'],
                                     route=sample['route'],
                                     query=sample['query']))

    assert expected == result


def test_check_date_range(sample_date_ranges):
    expected = [True, False, True, False]
    result = []

    for sample in sample_date_ranges:
        result.append(check_date_range(date_range=sample))

    assert expected == result


def test_parse_date(sample_input_date, expected_date):
    result = []

    for sample in sample_input_date:
        result.append(parse_date(date=sample))

    assert expected_date == result


def test_build_date_range(sample_date_range_input, expected_date_range):
    result = []
    for sample in sample_date_range_input:
        result.append(build_date_range(start=sample['start'],
                                       end=sample['end']))

    assert expected_date_range == result


def test_build_date_request_query(sample_query_data, expected_query):
    result = []

    for sample in sample_query_data:
        result.append(build_date_request_query(date_range=sample['date_range'],
                                               date_type=sample['date_type'],
                                               additonal=sample['additional']))

    assert expected_query == result
