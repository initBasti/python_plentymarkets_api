"""
Python-PlentyMarkets-API-interface.

Interface to the resources from PlentyMarkets(https://www.plentymarkets.eu)

Copyright (C) 2021  Sebastian Fricke, Panasiam

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
import logging

import plenty_api.constants as constants


def create_vat_mapping(data: list, subset: list = None) -> dict:
    """
    Create a mapping of each country ID to (Tax ID and configuration ID),
    restrict the mapping to a subset if given.

    Parameter:
        data            [list]      -   Response JSON data from the request

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
    'linked_variations', which contains every variation ID from @variation,
    where the attributeValueID matches the valueId of the attribute value.

    Parameter:
        variation       [dict]     -   response body entries from:
                                        /rest/items/variations
                                        (with variationAttributeValues)
        attribute       [dict]     -   response body entries from:
                                       /rest/items/attributes (with values)

    Return:
                        [dict]     -   extended response body of the attributes
    """
    value_id_map = {}

    if not attribute:
        return {}

    if not variation:
        return attribute

    for var in variation:
        if 'variationAttributeValues' not in var.keys():
            logging.warning("variations without attribute values"
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
    reduce the API response to a minimum by deleting date information and other
    additional mappings.

    Parameter:
        data            [dict]      -   The response JSON dictionary

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
        domain          [str]       -   type of route for the request
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
    Check if the given language abbreviation is a valid value and return it in
    lower-case letters.

    Parameter:
        lang            [str]       -   Language abbreviation

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
    Build the query dictionary, while checking for invalid arguments and
    removing them.

    Parameter:
        domain          [str]    -   type of route for the request
                                    {item/order/..}
        query           [dict]   -   Dictionary used for the params field for
                                     the requests module.
        refine          [dict]   -   Filters for the request
        additional      [list]   -   additional elements for the response body
        lang            [str]    -   Name of the language for product texts

    Return:
                        [dict]   -   updated query
    """
    if not query:
        query = {}

    if domain not in constants.VALID_DOMAINS:
        logging.error(f"Invalid domain name {domain}")
        return {}

    if refine:
        invalid_keys = set(refine.keys()).difference(
            constants.VALID_REFINE_KEYS[domain])
        if invalid_keys:
            logging.info(f"Invalid refine argument key removed: {invalid_keys}")
            for invalid_key in invalid_keys:
                refine.pop(invalid_key, None)
        if refine:
            query.update(refine)

    if additional:
        invalid_values = set(additional).difference(
            constants.VALID_ADDITIONAL_VALUES[domain])
        if invalid_values:
            logging.info("Invalid additional argument removed: "
                         f"{invalid_values}")
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


def sanity_check_json(route_name: str, json: dict) -> bool:
    """
    Check if the JSON object provided for a POST request contains the minimum
    required fields.

    Parameter:
        route_name      [str]    -   route for the request
        json            [dict]   -   JSON object for the route

    Return:
                        [bool]
    """
    if route_name not in constants.REQUIRED_FIELDS_MAP.keys():
        logging.error(f"unknown route {route_name} in required fields map.")
        return False

    required_keys = [x[0] for x in constants.REQUIRED_FIELDS_MAP[route_name]]
    if not list_contains(search_list=required_keys, target_list=json.keys()):
        logging.error(f"{required_keys} fields required for {route_name} "
                      f"creation. Got: {list(json.keys())}")
        return False

    for key, field_type in constants.REQUIRED_FIELDS_MAP[route_name]:
        if not json_field_filled(json_field=json[key], field_type=field_type):
            logging.error(f"Empty required field within JSON ({key}).")
            return False
    return True


def validate_redistribution_template(template: dict) -> bool:
    """
    Check if the template for redistribution creation is valid

    Make sure that the quantities align, the total quantity should be
    equal to the outgoing quantity, if outgoing quanities are used and
    the optional incoming quantities shall be equal to the outgoing
    quantities.

    Parameter:
        template        [dict]  -   Simplified blueprint JSON for the
                                    redistribution creation
    """
    for variation in template['variations']:
        if 'locations' in variation.keys():
            try:
                individual_quantities = sum(
                    [int(x['quantity']) for x in variation['locations']])
            except ValueError as err:
                logging.error(f"invalid quantity value ({err})")
                return False

            if variation['total_quantity'] != individual_quantities:
                logging.error("Absolute quantity doesn't match the individual "
                              "quantities for variation "
                              f"{variation['variation_id']}")
                return False

            for location in variation['locations']:
                if 'targets' in location.keys():
                    target_quantities = sum(
                        [int(x['quantity']) for x in location['targets']])
                    if location['quantity'] != target_quantities:
                        logging.error("Quantity of location "
                                      f"{location['location_id']} doesn't "
                                      "match the sum of quantities of its "
                                      "target locations for variation "
                                      f"{variation['variation_id']}")
                        return False

    return True


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
        date_range      [dict]  -   Start & End date in W3C date format
                                    (use `build_date_range`)
        date_type       [str]   -   Identifier for the type of date range
                                    {Creation, Payment, Change, Delivery}

    Return:
                        [dict]  -   Date range in python dictionary
    """
    query = {}
    if not date_range or not date_type:
        logging.error("Both date type and date range required")
        return ''
    if date_type.lower() not in constants.ORDER_DATE_ARGUMENTS.keys():
        logging.error(f"Invalid date type for query creation: {date_type}")
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
    and having the correct HTTP encoding for special signs.

    Parameter:
        url             [str]       -   Base url of the plentymarkets API
        route           [str]       -   Route part endpoint (e.g. /rest/items)
        path            [str]       -   Sub route part (e.g. /{item_id}/images)

    Parameter:
                        [str]       -   complete endpoint
    """
    if not re.search(r'https://.*', url):
        logging.error(f"Provided url parameter [{url}] is no valid https url.")
        return ''

    if route not in constants.VALID_ROUTES:
        logging.error(f"Invalid route, [{route}]")
        return ''

    return url + route + path


def build_date_update_json(date_type: str, date: datetime.datetime) -> dict:
    """
    Create a valid JSON for a redistribution PUT request to update a date.

    Used for the [PUT /rest/redistributions/{orderId}] route

    Parameters:
        date_type       [str]       -   initiate/estimated_delivery/finish
        date            [datetime]  -   specific date to set for the event

    Return:
                        [dict]      -   valid JSON for the request
    """
    if date_type not in constants.REDISTRIBUTION_DATE_TYPES.keys():
        logging.error(f"Invalid date type {date_type} for a redistribution")
        return {}

    date_str = parse_date(date=date.strftime("%Y-%m-%dT%H:%M:%S"))
    if not date_str:
        logging.error(f"Invalid date {str(date)}.")
        return {}

    json = {
        'dates': [
            {
                'typeId': constants.REDISTRIBUTION_DATE_TYPES[date_type],
                'date': date_str
            }
        ]
    }
    return json


def build_redistribution_json(template: dict) -> dict:
    """
    Create a valid JSON for a redistribution POST request.

    Used for the [POST /rest/redistributions route]

    Parameters:
        template            [dict]  -   Required and/or optional elements for
                                        the redistribution creation

    Return:
                            [dict]  -   valid JSON for the request
    """
    variations = [
        {
            'typeId': 1,
            'itemVariationId': x['variation_id'],
            'quantity': x['total_quantity'],
            'orderItemName': x['name']
        }
        for x in template['variations']
    ]

    for index, variation in enumerate(template['variations']):
        if 'amounts' in variation.keys():
            variations[index]['amounts'] = [
                {
                    'isSystemCurrency': True,
                    'priceOriginalGross': variation['amounts']
                }
            ]
        else:
            variations[index]['amounts'] = [
                {
                    'isSystemCurrency': True,
                    'priceOriginalGross': 0
                }
            ]

        if 'referrer' in variation.keys():
            variation[index]['referrerId'] = variation['referrer']

    json = {
        'typeId': 15,
        'plentyId': template['plenty_id'],
        'orderItems': variations,
        'relations': [
            {
                'referenceType': 'warehouse',
                'referenceId': template['sender'],
                'relation': 'sender'
            },
            {
                'referenceType': 'warehouse',
                'referenceId': template['receiver'],
                'relation': 'receiver'
            }
        ]
    }

    return json



def build_transaction(order_item_id: int, location: dict,
                      direction: str = 'out', user_id: int = -1,
                      **kwargs) -> dict:
    """
    Create a valid transaction for the REST API POST route.

    Used for the [POST /rest/orders/items/{orderItemId}/transactions route]

    Parameters:
        order_item_id   [int]   -   ID of the order item the transaction is
                                    connected to
        location        [dict]  -   Combination of location ID and quantity
        direction       [str]   -   OPTIONAL: in/out (default out)
        user_id         [int]   -   OPTIONAL: ID of the user that is
                                    responsible for the booking
        kwargs          [dict]  -   Additional optional keys for handling of
                                    transactions with batches

    Return:
                        [dict]  -   valid JSON for the request
    """
    json = {
        'orderItemId': order_item_id,
        'quantity': location['quantity'],
        'direction': direction,
        'status': 'regular',
        'warehouseLocationId': location['location_id']
    }
    if user_id > 0:
        json['userId'] = user_id

    for extra_key in ['batch', 'bestBeforeDate', 'identification']:
        if extra_key in kwargs.keys():
            json[extra_key] = kwargs[extra_key]

    return json


def build_transactions(order: dict, variations: dict,
                       user_id: int = -1) -> list:
    """
    Create transaction JSONs for each order item in the redistribution.

    Parameters:
        order           [dict]  -   Response JSON from the order creation
        variations      [list]  -   Variations with warehouse location to book
                                    stock from
        user_id         [int]   -   OPTIONAL: ID of the user that is
                                    responsible for the booking

    Return:
                        [tuple] -   List of transaction JSONs for outgoing and
                                    incoming transactions
    """
    outgoing = []
    incoming = []
    for item in order['orderItems']:
        template_variation = [
            x for x in variations
            if x['variation_id'] == item['itemVariationId']
        ][0]
        if 'locations' not in template_variation.keys():
            continue
        kwargs = {}
        for extra_key in ['batch', 'bestBeforeDate', 'identification']:
            if not extra_key in template_variation.keys():
                continue
            kwargs[extra_key] = template_variation[extra_key]

        for location in template_variation['locations']:
            outgoing.append(
                build_transaction(order_item_id=item['id'], location=location,
                                  direction='out', user_id=user_id,
                                  **kwargs)
            )
            if 'targets' in location.keys():
                for target in location['targets']:
                    incoming.append(
                        build_transaction(
                            order_item_id=item['id'], location=target,
                            direction='in', user_id=user_id, **kwargs)
                    )
    return (outgoing, incoming)



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
        date_range      [dict]   -   start and end date

    Return:
                        [bool]
    """
    now = datetime.datetime.now().astimezone()
    try:
        start = dateutil.parser.parse(date_range['start'])
        end = dateutil.parser.parse(date_range['end'])
    except dateutil.parser._parser.ParserError as err:
        logging.error(f"invalid date {date_range['start']} -> "
                      f"{date_range['end']}\n{err}")
        return False

    if start > end:
        logging.error("Date range check failure: End is before the Start")
        return False

    if start == end:
        logging.error("Date range check failure: Start is equal to end")
        return False

    if start > now or end > now:
        logging.error("Date range validation: Date range is or ends in the future")
        return False

    return True


def check_order_json(json: dict) -> bool:
    if not json:
        print(f"ERROR: Empty order JSON object.")
        return False
    missing_keys = [x for x in constants.REQUIRED_ORDER_ATTRIBUTES
                    if x not in json.keys()]
    if missing_keys:
        print("ERROR: Missing JSON attributes for an order: "
              f"{missing_keys}.")
        return False

    if len(json['orderItems']) < 1:
        print(f"ERROR: Order must contain at least one item.")
        return False


    for key in json.keys():
        if key in constants.REQUIRED_ATTRIBUTE_MAPPING.keys() and json[key]:
            missing_keys = [x for x in
                            constants.REQUIRED_ATTRIBUTE_MAPPING[key] if
                            x not in json[key][0].keys()]
            if missing_keys:
                print(f"ERROR: Missing JSON attributes for the {key} key "
                      f"within an order: {missing_keys}")
                return False

    if int(json['typeId']) not in range(1,16):
        print(f"ERROR: Invalid order type ID: {json['typeId']}.")
        return False

    return True


def parse_date(date: str) -> str:
    """
    Transform the given date into a W3C date format as required by the
    PlentyMarkets API.

    Parameter:
        date            [str]       -   string with the original date.

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
        start           [str]       -   string with the start date
        end             [str]       -   string with the end date

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
        date            [str]       -   date as function parameter in on of the
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
    """
    Get the credentials for the API from the user and store them temporary.
    """
    username = ''
    password = ''
    while len(username) < 2:
        username = input('Username: ')
    while len(password) < 2:
        password = getpass.getpass()
    return {'username': username, 'password': password}


def new_keyring_creds(keyring: object) -> dict:
    """
    Get the credentials for the API from the user and store them into a
    system-wide keyring.

    Parameter:
        keyring         [CredentialManager object]
    Return:
                        [dict]      - containing username and password
    """
    keyring.set_credentials()
    return keyring.get_credentials()


def update_keyring_creds(keyring: object) -> dict:
    """
    Delete the current content of the keyring and get new credentials for the
    API from the user, store them into the keyring.

    Parameter:
        keyring         [CredentialManager object]
    Return:
                        [dict]      -   containing username and password
    """
    keyring.delete_credentials()
    return new_keyring_creds(keyring=keyring)


def build_login_token(response_json: dict) -> str:
    """ Fetch the bearer token from the API response object """
    token_type = response_json['token_type']
    access_token = response_json['access_token']
    return token_type + ' ' + access_token


def list_contains(search_list: list, target_list: list) -> bool:
    """ Check if all elements of @search_list are found in @target_list """
    return all(elem in target_list for elem in search_list)


def json_field_filled(json_field, field_type: int) -> bool:
    """ Check if the field contains at least one valid element """
    if field_type == constants.JSON_INTEGER:
        if not isinstance(json_field, int):
            return False
    elif field_type == constants.JSON_FLOAT:
        if not isinstance(json_field, float):
            return False
    elif field_type == constants.JSON_STRING:
        if not isinstance(json_field, str):
            return False
    elif field_type == constants.JSON_DICT:
        if not isinstance(json_field, dict) or len(json_field) < 1:
            return False
    elif field_type == constants.JSON_LIST_OF_DICTS:
        if not isinstance(json_field, list) or len(json_field) < 1:
            return False
        if not all([isinstance(x, dict) and len(x) > 0 for x in json_field]):
            return False
    return True
