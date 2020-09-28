import pytest

from plenty_api.utils import (
    get_route, build_endpoint, check_date_range, parse_date, build_date_range,
    get_utc_offset, build_query_date, create_vat_mapping, date_to_timestamp,
    get_language
)


@pytest.fixture
def sample_date_ranges() -> list:
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
def sample_input_date() -> list:
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
def expected_date() -> list:
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
def sample_date_range_input() -> list:
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
def expected_date_range() -> list:
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
def sample_query_data() -> list:
    samples = [
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Creation'},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Payment'},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Change'},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Delivery'},
        {'date_range': {},
         'date_type': 'Creation'},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': ''},
        {'date_range': {'start': '2020-09-14T08:00:00+02:00',
                        'end': '2020-09-14T10:00:30+02:00'},
         'date_type': 'Creation'}
    ]
    return samples


@pytest.fixture
def sample_vat_data() -> list:
    samples = [
        [
            {
                'id': 1,
                'countryId': 1,
                'taxIdNumber': 'DE12345678910',
                'locationId': 1
            },
            {
                'id': 2,
                'countryId': 2,
                'taxIdNumber': 'GB12345678910',
                'locationId': 2
            },
            {
                'id': 3,
                'countryId': 2,
                'taxIdNumber': 'GB12345678910',
                'locationId': 2
            },
            {
                'id': 4,
                'countryId': 3,
                'taxIdNumber': 'FR12345678910',
                'locationId': 3
            },
            {
                'id': 5,
                'countryId': 1,
                'taxIdNumber': 'DE12345678910',
                'locationId': 1
            }
        ],
        [
            ''
        ]
    ]

    return samples


@pytest.fixture
def expected_date_query() -> list:
    expected = [
        '&createdAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&createdAtTo=2020-09-14T10%3A00%3A30%2B02%3A00',
        '&paidAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&paidAtTo=2020-09-14T10%3A00%3A30%2B02%3A00',
        '&updatedAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&updatedAtTo=2020-09-14T10%3A00%3A30%2B02%3A00',
        '&outgoingItemsBookedAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&outgoingItemsBookedAtTo=2020-09-14T10%3A00%3A30%2B02%3A00',
        '',
        '',
        '&createdAtFrom=2020-09-14T08%3A00%3A00%2B02%3A00' +
        '&createdAtTo=2020-09-14T10%3A00%3A30%2B02%3A00'
    ]
    return expected


@pytest.fixture
def expected_query_attributes() -> list:
    expected = [
        '&with%5B%5D=documents',
        '&with%5B%5D=documents&with%5B%5D=comments&orderType=1,4&referrerId=1',
        '&with%5B%5D=shippingPackages&countryId=1',
        '&with%5B%5D=documents'
    ]
    return expected


def test_get_route() -> None:
    sample_data = ['order', 'item', 'ITEMS', 'oRdErS', 'wrong', '']
    result = []
    expected = ['/rest/orders', '/rest/items', '/rest/items', '/rest/orders',
                '', '']

    for domain in sample_data:
        result.append(get_route(domain=domain))

    assert expected == result


def test_build_endpoint() -> None:
    sample_data = [
        {'url': 'https://test.plentymarkets-cloud01.com',
         'route': '/rest/orders',
         'query': "?orderType=1&with%5B%5D=documents"},
        {'url': 'https://test.plentymarkets-cloud01.com',
         'route': '/rest/orders',
         'query': ""},
        {'url': 'https://invalid.com',
         'route': '/rest/orders',
         'query': "?orderType=1&with%5B%5D=documents"},
        {'url': 'https://test.plentymarkets-cloud01.com',
         'route': '/rest/invalid',
         'query': "?orderType=1&with%5B%5D=documents"},
        {'url': '',
         'route': '/rest/orders',
         'query': "?orderType=1&with%5B%5D=documents"},
        {'url': 'https://test.plentymarkets-cloud01.com',
         'route': '',
         'query': "?orderType=1&with%5B%5D=documents"}
    ]

    expected = ['https://test.plentymarkets-cloud01.com/rest/orders' +
                '?orderType=1&with%5B%5D=documents',
                'https://test.plentymarkets-cloud01.com/rest/orders', '', '',
                '', '']
    result = []

    for sample in sample_data:
        result.append(build_endpoint(url=sample['url'],
                                     route=sample['route'],
                                     query=sample['query']))

    assert expected == result


def test_check_date_range(sample_date_ranges: list) -> None:
    expected = [True, False, True, False]
    result = []

    for sample in sample_date_ranges:
        result.append(check_date_range(date_range=sample))

    assert expected == result


def test_parse_date(sample_input_date: list,
                    expected_date: list) -> None:
    result = []

    for sample in sample_input_date:
        result.append(parse_date(date=sample))

    assert expected_date == result


def test_build_date_range(sample_date_range_input: list,
                          expected_date_range: list) -> None:
    result = []
    for sample in sample_date_range_input:
        result.append(build_date_range(start=sample['start'],
                                       end=sample['end']))

    assert expected_date_range == result


def test_build_query_date(sample_query_data: list,
                          expected_date_query: list) -> None:
    result = []

    for sample in sample_query_data:
        result.append(build_query_date(date_range=sample['date_range'],
                                       date_type=sample['date_type']))

    assert expected_date_query == result


def test_create_vat_mapping(sample_vat_data: list) -> None:
    subset = [[], [1, 2]]
    expected = [
        {
            '1': {'config': ['1', '5'], 'TaxId': 'DE12345678910'},
            '2': {'config': ['2', '3'], 'TaxId': 'GB12345678910'},
            '3': {'config': ['4'], 'TaxId': 'FR12345678910'}
        },
        {
            '1': {'config': ['1', '5'], 'TaxId': 'DE12345678910'},
            '2': {'config': ['2', '3'], 'TaxId': 'GB12345678910'}
        },
        {},
        {}
    ]
    result = []

    for sample in sample_vat_data:
        for sub in subset:
            result.append(create_vat_mapping(data=sample, subset=sub))

    assert expected == result


def test_date_to_timestamp() -> None:
    samples = ['2020-08-01', '2020-08-01T15:00', '2020-08-01T15:00:00+02:00',
               '01-08-2020', '2020.08.01', 'abc', '']
    loc = int(get_utc_offset()[0:3].strip(':'))*3600
    expected = [1596232800, 1596286800, 1596290400,
                -1, 1596232800, -1, -1]
    result = []

    for sample in samples:
        result.append(date_to_timestamp(date=sample))

    assert expected == result


def test_get_language() -> None:
    samples = ['de', 'GB', 'fR', 'Greece', '12', '']
    expected = [1, 12, 10, -1, -1, -1]
    result = []

    for sample in samples:
        result.append(get_language(lang=sample))

    assert expected == result
