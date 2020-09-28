"""
    Python-PlentyMarkets-API-interface
    Interface to the resources from PlentyMarkets(https://www.plentymarkets.eu)

    Copyright (C) 2020  Sebastian Fricke, Panasiam

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import getpass
import datetime
import time
import re
import urllib.parse
import dateutil.parser
import pandas

VALID_ROUTES = ['/rest/orders', '/rest/items', '/rest/vat']
VALID_ORDER_REFINE_KEYS = [
    'orderType', 'contactId', 'referrerId', 'shippingProfileId',
    'shippingServiceProviderId', 'ownerUserId', 'warehouseId',
    'isEbayPlus', 'includedVariation', 'includedItem', 'orderIds',
    'countryId', 'orderItemName', 'variationNumber', 'sender.contact',
    'sender.warehouse', 'receiver.contact', 'receiver.warehouse',
    'externalOrderId', 'clientId', 'paymentStatus', 'statusFrom',
    'statusTo', 'hasDocument', 'hasDocumentNumber', 'parentOrderId'
]
VALID_ITEM_REFINE_KEYS = [
    'name', 'manfacturerId', 'id', 'flagOne', 'flagTwo'
]
VALID_COUNTRY_MAP = {
    "DE": 1, "AT": 2, "BE": 3, "CH": 4, "CY": 5, "CZ": 6, "DK": 7, "ES": 8,
    "EE": 9, "FR": 10, "FI": 11, "GB": 12, "GR": 13, "HU": 14, "IT": 15,
    "IE": 16, "LU": 17, "LV": 18, "MT": 19, "NO": 20, "NL": 21, "PT": 22,
    "PL": 23, "SE": 24, "SG": 25, "SK": 26, "SI": 27, "US": 28, "AU": 29,
    "CA": 30, "CN": 31, "JP": 32, "LT": 33, "LI": 34, "MC": 35, "MX": 36,
    "IC": 37, "IN": 38, "BR": 39, "RU": 40, "RO": 41, "EA": 42,
    "BG": 44, "XZ": 45, "KG": 46, "KZ": 47, "BY": 48, "UZ": 49, "MA": 50,
    "AM": 51, "AL": 52, "EG": 53, "HR": 54, "MV": 55, "MY": 56, "HK": 57,
    "YE": 58, "IL": 59, "TW": 60, "GP": 61, "TH": 62, "TR": 63,
    "NZ": 66, "AF": 67, "AX": 68, "DZ": 69, "AS": 70, "AD": 71,
    "AO": 72, "AI": 73, "AQ": 74, "AG": 75, "AR": 76, "AW": 77, "AZ": 78,
    "BS": 79, "BH": 80, "BD": 81, "BB": 82, "BZ": 83, "BJ": 84, "BM": 85,
    "BT": 86, "BO": 87, "BA": 88, "BW": 89, "BV": 90, "IO": 91,
    "BN": 92, "BF": 93, "BI": 94, "KH": 95, "CM": 96, "CV": 97,
    "KY": 98, "CF": 99, "TD": 100, "CL": 101, "CX": 102, "CC": 103,
    "CO": 104, "KM": 105, "CG": 106, "CD": 107, "CK": 108, "CR": 109,
    "CI": 110, "CU": 112, "DJ": 113, "DM": 114, "DO": 115, "EC": 116,
    "SV": 117, "GQ": 118, "ER": 119, "ET": 120, "FK": 121, "FO": 122,
    "FJ": 123, "GF": 124, "PF": 125, "TF": 126, "GA": 127, "GM": 128,
    "GE": 129, "GH": 130, "GI": 131, "GL": 132, "GD": 133, "GU": 134,
    "GT": 135, "GG": 136, "GN": 137, "GW": 138, "GY": 139, "HT": 140,
    "HM": 141, "VA": 142, "HN": 143, "IS": 144, "ID": 145, "IR": 146,
    "IQ": 147, "IM": 148, "JM": 149, "JE": 150, "JO": 151, "KE": 152,
    "KI": 153, "KP": 154, "KR": 155, "KW": 156, "LA": 158, "LB": 159,
    "LS": 160, "LR": 161, "LY": 162, "MO": 163, "MK": 164, "MG": 165,
    "MW": 166, "ML": 168, "MH": 169, "MQ": 170, "MR": 171, "MU": 172,
    "YT": 173, "FM": 174, "MD": 175, "MN": 176, "ME": 177, "MS": 178,
    "MZ": 179, "MM": 180, "NA": 181, "NR": 182, "NP": 183, "AN": 184,
    "NC": 185, "NI": 186, "NE": 187, "NG": 188, "NU": 189, "NF": 190,
    "MP": 191, "OM": 192, "PK": 193, "PW": 194, "PS": 195, "PA": 196,
    "PG": 197, "PY": 198, "PE": 199, "PH": 200, "PN": 201, "PR": 202,
    "QA": 203, "RE": 204, "RW": 205, "SH": 206, "KN": 207, "LC": 208,
    "PM": 209, "VC": 210, "WS": 211, "SM": 212, "ST": 213, "SA": 214,
    "SN": 215, "RS": 216, "SC": 217, "SL": 218, "SB": 219, "SO": 220,
    "ZA": 221, "GS": 222, "LK": 223, "SD": 224, "SR": 225, "SJ": 226,
    "SZ": 227, "SY": 228, "TJ": 229, "TZ": 230, "TL": 231, "TG": 232,
    "TK": 233, "TO": 234, "TT": 235, "TN": 236, "TM": 237, "TC": 238,
    "TV": 239, "UG": 240, "UA": 241, "UM": 242, "UY": 243, "VU": 244,
    "VE": 245, "VN": 246, "VG": 247, "VI": 248, "WF": 249, "EH": 250,
    "ZM": 252, "ZW": 253, "AE": 254, "CUW": 258, "SXM": 259,
    "BES": 260, "BL": 261
}
ORDER_DATE_ARGUMENTS = {
    'creation': 'created',
    'change': 'updated',
    'payment': 'paid',
    'delivery': 'outgoingItemsBooked'
}


def create_vat_mapping(data: list, subset: list = None) -> dict:
    """
        Create a mapping of each country ID to (Tax ID and configuration ID),
        restrict the mapping to a subset if given.

        Parameter:
            data [List]         -   Response JSON data from /rest/vat request

        Return:
            [Dict]
    """
    mapping = {}
    if not data or not isinstance(data[0], dict):
        return {}
    for entry in data:
        country = str(entry['countryId'])
        if country not in mapping.keys():
            mapping[country] = {'config': [str(entry['id'])],
                                'TaxId': entry['taxIdNumber']}
        else:
            mapping[country]['config'].append(str(entry['id']))

    if subset:
        return {x: y for x, y in mapping.items() if int(x) in subset}

    return mapping


def get_route(domain: str) -> str:
    """
        Use fixed mappings to determine the correct route for the endpoint.

        Parameter:
            domain [String]     -   Specifies the type of route for the request
                                    {item/order}

        Return:
            [String]
    """
    if re.match(r'order', domain.lower()):
        return '/rest/orders'
    if re.match(r'item', domain.lower()):
        return '/rest/items'
    if re.match(r'vat', domain.lower()):
        return '/rest/vat'
    return ''


def get_language(lang: str) -> int:
    """
        Use fixed mappings to get the associated PlentyMarkets ID for a
        country abbreviation.

        Parameter:
            lang [str]          -   Country abbreviation

        Return:
            [int]               -   ID from Plentymarkets
    """
    try:
        return VALID_COUNTRY_MAP[lang.upper()]
    except KeyError:
        print(f"ERROR: invalid country abbreviation: {lang}")
        return -1


def build_request_query(elements: list) -> str:
    """
        Combine different query elements and check the query format.

        Parameter:
            elements [list]     -   List of strings containing one or more
                                    query sub-elements

        Return:
            [str]               -   Full query
    """
    query = ''
    query = query.join(elements)

    # Set the first character to '?' and search for invalid occurences
    if re.search(r'\?', query):
        print(f"WARNING: {query} -> found a '?' at position > 0")
    if query:
        query = '?' + query[1:]

    return query


def build_query_date(date_range: dict, date_type: str) -> str:
    """
        Create a query for the API endpoint, with valid values from the
        PlentyMarkets API documentation:
            https://developers.plentymarkets.com/rest-doc#/

        The valid date ranges are:
            Creation : {createdAtFrom & createdAtTo}
            Payment : {paidAtFrom & paidAtTo}
            Change : {updatedAtFrom & updatedAtTo}
            Delivery : {outgoingItemsBookedAtFrom & outgoingItemsBookedAtTo}

        Parameter:
            date_range [Dict]   -   Start & End date in W3C date format
                                    (use `build_date_range`)
            date_type [String]  -   Identifier for the type of date range
                                    {Creation, Payment, Change, Delivery}

        Return:
            [str]               -   Date range in query format
    """
    query = ''
    if not date_range or not date_type:
        print("ERROR: Both date type and date range required")
        return ''
    if date_type.lower() not in ORDER_DATE_ARGUMENTS.keys():
        print(f"ERROR: Invalid date type for query creation: {date_type}")
        return ''
    date_type = ORDER_DATE_ARGUMENTS[date_type.lower()]
    query += str(f"&{date_type}AtFrom={date_range['start']}")
    query += str(f"&{date_type}AtTo={date_range['end']}")
    return urllib.parse.quote(query, safe='?,&,=')


def build_query_attributes(domain: str,
                           refine: dict = None,
                           additional: list = None) -> str:
    """
            refine
            additional [List]   -   List of additional query arguments
                                    used with `&with=`
    """
    query = ''
    if refine is None and additional is None:
        return ''
    for key, item in refine.items():
        if key in VALID_ORDER_REFINE_KEYS and domain.lower() == 'orders':
            query += str(f"&{key}={item}")
        elif key in VALID_ITEM_REFINE_KEYS and domain.lower() == 'items':
            query += str(f"&{key}={item}")
    for argument in additional:
        query += str(f"&with={argument}")

    return urllib.parse.quote(query, safe='?,&,=')


def build_endpoint(url: str, route: str, query: str) -> str:
    """
        Perform basic checks to ensure that a valid endpoint is used for the
        request. Query elements should be obtained by usind the
        `build_request_query` function to ensure using correct arguments
        and having the correcting HTTP encoding for special signs.

        Parameter:
            url [String]        -   Base url of the plentymarkets API
            route [String]      -   Route part endpoint (e.g. /rest/items)
            query [String]      -   Complete query

        Parameter:
            [String]            -   complete endpoint
    """
    if not re.search(r'https://.*.plentymarkets-cloud01.com', url):
        print("ERROR: invalid URL, need: {https://*.plentymarkets-cloud01.com")
        return ''

    if route not in VALID_ROUTES:
        print(f"ERROR: invalid route, [{route}]")
        return ''

    return url + route + query


def json_to_dataframe(json):
    return pandas.json_normalize(json)


def get_utc_offset() -> str:
    """
        Determine the time difference between the current timezone of the user
        and UTC and return a string with the format "02:00"

        Return:
            [String]
    """
    current = datetime.datetime.now(datetime.timezone.utc).astimezone()
    offset = current.tzinfo.utcoffset(None)
    offset_hours = offset.seconds // 3600
    return str("{:0>2d}:00".format(offset_hours))


def check_date_range(date_range: dict) -> bool:
    """
        Check if the user specified date range is a valid range in the past.

        Parameter:
            date_range [Dict]   -   start and end date

        Return:
            [Bool]
    """
    now = datetime.datetime.now().astimezone()
    try:
        start = dateutil.parser.parse(date_range['start'])
        end = dateutil.parser.parse(date_range['end'])
    except dateutil.parser._parser.ParserError as err:
        print(f"ERROR: invalid date {date_range['start']} -> {date_range['end']}\n{err}")
        return False

    if start > end:
        print("Date range check failure: End is before the Start")
        return False

    if start == end:
        print("Date range check failure: Start is equal to end")
        return False

    if start > now or end > now:
        print("Date range validation: Date range is or ends in the future")
        return False

    return True


def parse_date(date: str) -> str:
    """
        Transform the given date into a W3C date format as required by
        the PlentyMarkets API.

        Parameter:
            date [String]   -   user supplied string with the original date.

        Return:
            [String]
    """
    try:
        date = dateutil.parser.parse(date)
    except dateutil.parser._parser.ParserError:
        return ''
    date_str = date.strftime('%Y-%m-%dT%H:%M:%S')
    offset = date.strftime('%z')
    if not offset:
        return date_str + '+' + get_utc_offset()
    return date_str + offset[:3] + ':' + offset[3:]


def build_date_range(start: str, end: str) -> dict:
    """
        Create a range of 2 dates in the W3C dateformat.

        Parameter:
            start [String]  -   user supplied string with the start date
            end [String]    -   user supplied string with the end date

        Return:
            [Dict]/None
    """
    w3c_start = parse_date(date=start)
    w3c_end = parse_date(date=end)
    if not w3c_start or not w3c_end:
        return None
    return {'start': w3c_start, 'end': w3c_end}


def date_to_timestamp(date: str) -> int:
    """
        Parse a date object in to a unix timestamp.

        Parameter:
            date [str]      -   date as function parameter in on of the
                                following formats:
                                    YYYY-MM-DD
                                    YYYY-MM-DDTHH:MM
                                    YYYY-MM-DDTHH:MM:SS+UTC-OFFSET

        Return:
            [int]           -   Unix timestamp since 1970-01-01
    """
    # Check if the date starts with anything else but the year
    first_number = re.search(r'^\d{2,}(?=\D)', date)
    if first_number is not None:
        if int(first_number.group(0)) < 2000:
            return -1
    try:
        date_obj = dateutil.parser.parse(date)
    except dateutil.parser._parser.ParserError:
        return -1
    return int(time.mktime(date_obj.timetuple()))


def get_temp_creds() -> dict:
    """ Get the credentials for the API from the user and don't store
        them permanently """
    username = ''
    password = ''
    while len(username) < 2:
        username = input('Username: ')
    while len(password) < 2:
        password = getpass.getpass()
    return {'username': username, 'password': password}


def new_keyring_creds(kr: object) -> dict:
    """
        Get the credentials for the API from the user and store them into
        a system wide keyring

        Parameter:
            kr [CredentialManager object]
        Return:
            [Dict]  - containing username and password
    """
    kr.set_credentials()
    return kr.get_credentials()


def update_keyring_creds(kr: object) -> dict:
    """
        Delete the current content of the keyring and get new credentials
        for the API from the user, store them into the keyring

        Parameter:
            kr [CredentialManager object]
        Return:
            [Dict]  - containing username and password
    """
    kr.delete_credentials()
    return new_keyring_creds(kr=kr)


def build_login_token(response_json: dict) -> str:
    """ Fetch the bearer token from the API response object """
    token_type = response_json['token_type']
    access_token = response_json['access_token']
    return token_type + ' ' + access_token
