"""
    Python-PlentyMarkets-API-interface.

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
import dateutil.parser
import pandas

import plenty_api.constants as constants


def create_vat_mapping(data: list, subset: list = None) -> dict:
    """
        Create a mapping of each country ID to (Tax ID and configuration ID),
        restrict the mapping to a subset if given.

        Parameter:
            data    [list]      -   Response JSON data from /rest/vat request

        Return:
                    [dict]
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


def attribute_variation_mapping(variation: dict, attribute: dict) -> dict:
    """
        Add an additional field to the attribute JSON response body:
        'linked_variations', which contains every variation ID from
        @variation, where the attributeValueID matches the valueId of
        the attribute value.

        Parameter:
            variation[dict]     -   response body entries from:
                                    /rest/items/variations
                                    (with variationAttributeValues)
            attribute[dict]     -   response body entries from:
                                    /rest/items/attributes (with values)

        Return:
                    [dict]      -   extended response body of the attributes
    """
    value_id_map = {}

    if not attribute:
        return {}

    if not variation:
        return attribute

    for var in variation:
        if 'variationAttributeValues' not in var.keys():
            print("WARNING: variations without attribute values"
                  " used for attribute mapping")
            return attribute
        for attr in var['variationAttributeValues']:
            attr_id = str(attr['attributeId'])
            val_id = str(attr['valueId'])
            if attr_id not in value_id_map:
                value_id_map[attr_id] = {val_id: [var['id']]}
                continue
            if val_id not in value_id_map[attr_id]:
                value_id_map[attr_id][val_id] = [var['id']]
                continue
            value_id_map[attr_id][val_id].append(var['id'])

    for entry in attribute:
        attr_id = str(entry['id'])
        if attr_id in value_id_map:
            for value in entry['values']:
                val_id = str(value['id'])
                if val_id in value_id_map[attr_id]:
                    value['linked_variations'] = value_id_map[attr_id][val_id]

    return attribute


def shrink_price_configuration(data: dict) -> dict:
    """
        reduce the API response to a minimum by deleting
        date information and other additional mappings.

        Parameter:
            data    [dict]      -   The response JSON dictionary

        Return:
                    [dict]
    """
    configuration: dict = {
        'id': 0,
        'type': '',
        'position': 0,
        'names': {},
        'referrers': [],
        'accounts': [],
        'clients': [],
        'countries': [],
        'currencies': [],
        'customerClasses': []
    }

    if not data:
        return {}

    key_subkey_map = {
        'clients': 'plentyId',
        'countries': 'countryId',
        'currencies': 'currency',
        'customerClasses': 'customerClassId',
        'referrers': 'referrerId',
        'names': 'nameExternal'
    }

    for key in ['id', 'type', 'position']:
        configuration[key] = data[key]

    for key in key_subkey_map:
        for entity in data[key]:
            subkey = key_subkey_map[key]
            if key == 'names':
                configuration[key].update({entity['lang']: entity[subkey]})
                continue
            configuration[key].append(entity[subkey])

    return configuration


def get_route(domain: str) -> str:
    """
        Use fixed mappings to determine the correct route for the endpoint.

        Parameter:
            domain  [str]       -   Specifies the type of route for the request
                                    {item/order/..}

        Return:
                    [str]
    """
    for valid_domain in constants.VALID_DOMAINS:
        if re.match(valid_domain, domain.lower()):
            return constants.DOMAIN_ROUTE_MAP[valid_domain]
    return ''


def get_language(lang: str) -> str:
    """
        Check if the given language abbreviation is a valid value and
        return it in lower-case letters.

        Parameter:
            lang    [str]       -   Language abbreviation

        Return:
                    [str]       -   Language abbreviation in lower-case
    """
    lang = lang.lower()
    if lang not in constants.VALID_LANGUAGES:
        return 'INVALID_LANGUAGE'
    return lang


def sanity_check_parameter(domain: str,
                           query: dict,
                           refine: dict = None,
                           additional: list = None,
                           lang: str = ''):
    """
        Build the query dictionary, while checking for invalid arguments
        and removing them.

        Parameter:
            domain     [str]    -   specifies the type of route for the request
                                    {item/order/..}
            query      [dict]   -   Dictionary used for the params field
                                    for the requests module.
            refine     [dict]   -   Filters for the request
            additional [list]   -   additional elements for the response body
            lang       [str]    -   Name of the language for product texts

        Return:
                       [dict]   -   updated query
    """
    if domain not in constants.VALID_DOMAINS:
        print(f"ERROR: invalid domain name {domain}")
        return {}

    if refine:
        invalid_keys = set(refine.keys()).difference(
            constants.VALID_REFINE_KEYS[domain])
        if invalid_keys:
            print(f"Invalid refine argument key removed: {invalid_keys}")
            for invalid_key in invalid_keys:
                refine.pop(invalid_key, None)
        if refine:
            query.update(refine)

    if additional:
        invalid_values = set(additional).difference(
            constants.VALID_ADDITIONAL_VALUES[domain])
        if invalid_values:
            print(f"Invalid additional argument removed: {invalid_values}")
            for invalid_value in invalid_values:
                additional.remove(invalid_value)
        if additional:
            if domain == 'order':
                query.update({'with[]': additional})
            else:
                query.update({'with': ','.join(additional)})

    if lang:
        query.update({'lang': get_language(lang=lang)})

    return query


def build_query_date(date_range: dict, date_type: str) -> dict:
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
            date_range  [dict]  -   Start & End date in W3C date format
                                    (use `build_date_range`)
            date_type   [str]   -   Identifier for the type of date range
                                    {Creation, Payment, Change, Delivery}

        Return:
                        [dict]  -   Date range in python dictionary
    """
    query = {}
    if not date_range or not date_type:
        print("ERROR: Both date type and date range required")
        return ''
    if date_type.lower() not in constants.ORDER_DATE_ARGUMENTS.keys():
        print(f"ERROR: Invalid date type for query creation: {date_type}")
        return ''
    date_type = constants.ORDER_DATE_ARGUMENTS[date_type.lower()]
    query.update({f"{date_type}AtFrom": date_range['start']})
    query.update({f"{date_type}AtTo": date_range['end']})

    return query


def build_endpoint(url: str, route: str, path: str = '') -> str:
    """
        Perform basic checks to ensure that a valid endpoint is used for the
        request. Query elements should be obtained by usind the
        `build_request_query` function to ensure using correct arguments
        and having the correcting HTTP encoding for special signs.

        Parameter:
            url     [str]       -   Base url of the plentymarkets API
            route   [str]       -   Route part endpoint (e.g. /rest/items)
            path    [str]       -   Sub route part (e.g. /{item_id}/images)

        Parameter:
                    [str]       -   complete endpoint
    """
    if not re.search(r'https://.*.plentymarkets-cloud01.com', url):
        print("ERROR: invalid URL, need: {https://*.plentymarkets-cloud01.com")
        return ''

    if route not in constants.VALID_ROUTES:
        print(f"ERROR: invalid route, [{route}]")
        return ''

    return url + route + path


def json_to_dataframe(json):
    """ simple wrapper for the data conversion from JSON dict to dataframe """
    return pandas.json_normalize(json)


def transform_data_type(data: dict, data_format: str):
    """ simple wrapper around the data conversion before return """
    if not data:
        return {}

    if data_format == 'json':
        return data

    if data_format == 'dataframe':
        data = json_to_dataframe(json=data)
        return data


def get_utc_offset() -> str:
    """
        Determine the time difference between the current timezone of the user
        and UTC and return a string with the format "02:00"

        Return:
                    [str]
    """
    current = datetime.datetime.now(datetime.timezone.utc).astimezone()
    offset = current.tzinfo.utcoffset(None)
    offset_hours = offset.seconds // 3600
    return str("{:0>2d}:00".format(offset_hours))


def check_date_range(date_range: dict) -> bool:
    """
        Check if the user specified date range is a valid range in the past.

        Parameter:
            date_range [dict]   -   start and end date

        Return:
                       [bool]
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
            date    [str]       -   user supplied string with the
                                    original date.

        Return:
                    [str]
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
            start   [str]       -   user supplied string with the start date
            end     [str]       -   user supplied string with the end date

        Return:
                    [dict]/None
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
            date    [str]       -   date as function parameter in on of the
                                    following formats:
                                    YYYY-MM-DD
                                    YYYY-MM-DDTHH:MM
                                    YYYY-MM-DDTHH:MM:SS+UTC-OFFSET

        Return:
                    [int]       -   Unix timestamp since 1970-01-01
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


def new_keyring_creds(keyring: object) -> dict:
    """
        Get the credentials for the API from the user and store them into
        a system wide keyring

        Parameter:
            keyring [CredentialManager object]
        Return:
                    [dict]      - containing username and password
    """
    keyring.set_credentials()
    return keyring.get_credentials()


def update_keyring_creds(keyring: object) -> dict:
    """
        Delete the current content of the keyring and get new credentials
        for the API from the user, store them into the keyring

        Parameter:
            keyring [CredentialManager object]
        Return:
                    [dict]      - containing username and password
    """
    keyring.delete_credentials()
    return new_keyring_creds(keyring=keyring)


def build_login_token(response_json: dict) -> str:
    """ Fetch the bearer token from the API response object """
    token_type = response_json['token_type']
    access_token = response_json['access_token']
    return token_type + ' ' + access_token
