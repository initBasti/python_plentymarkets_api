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
import re
import urllib.parse
import dateutil.parser
import pandas

VALID_ROUTES = ['/rest/orders', '/rest/items', '/rest/vat']
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

        Result:
            [String]
    """
    if re.match(r'order', domain.lower()):
        return '/rest/orders'
    if re.match(r'item', domain.lower()):
        return '/rest/items'
    if re.match(r'vat', domain.lower()):
        return '/rest/vat'
    return ''


def build_date_request_query(date_range: dict, date_type: str,
                             **kwargs) -> str:
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
            (Optional)
            additional [List]   -   List of additional query arguments
                                    used with `&with=`
    """
    query = ''
    if not date_range or not date_type:
        print("ERROR: Both date type and date range required")
        return ''
    if date_type.lower() not in ORDER_DATE_ARGUMENTS.keys():
        print(f"ERROR: Invalid date type for query creation: {date_type}")
        return ''
    date_type = ORDER_DATE_ARGUMENTS[date_type.lower()]
    query += str(f"?{date_type}AtFrom={date_range['start']}")
    query += str(f"&{date_type}AtTo={date_range['end']}")
    if 'additional' in kwargs.keys():
        for argument in kwargs['additional']:
            query += str(f"&with[]={argument}")
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
