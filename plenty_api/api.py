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

import datetime
import time
from typing import List
import requests
import simplejson
import gnupg
import logging
from datetime import datetime, timezone

import plenty_api.keyring
import plenty_api.utils as utils


class PlentyApi():
    """
    Provide specified routines to access data from PlentyMarkets
    over the RestAPI.

    Public methods:
        GET REQUESTS
        **plenty_api_get_orders_by_date**

        **plenty_api_get_attributes**

        **plenty_api_get_vat_id_mappings**

        **plenty_api_get_price_configuration**

        **plenty_api_get_manufacturers**

        **plenty_api_get_referrers**

        **plenty_api_get_items**

        **plenty_api_get_variations**

        **plenty_api_get_stock**

        **plenty_api_get_storagelocations**

        **plenty_api_get_variation_stock_batches**

        **plenty_api_get_variation_warehouses**

        **plenty_api_get_contacts**

        POST REQUESTS
        **plenty_api_set_image_availability**

        **plenty_api_create_items**

        **plenty_api_create_variations**

        **plenty_api_create_attribute**

        **plenty_api_create_attribute_names**

        **plenty_api_create_attribute_values**

        **plenty_api_create_attribute_value_names**

        **plenty_api_create_redistribution**

        **plenty_api_create_transaction**

        **plenty_api_create_booking**

        PUT REQUESTS

        **plenty_api_update_redistribution**

        **plenty_api_book_incoming_items**

        **plenty_api_book_outgoing_items**
    """

    def __init__(self, base_url: str, use_keyring: bool = True,
                 data_format: str = 'json', debug: bool = False,
                 username: str = '', password: str = '', use_gpg: bool = True):
        """
        Initialize the object and directly authenticate to the API to get
        the bearer token.

        Parameter:
            base_url    [str]   -   Base URL to the PlentyMarkets API
                                    Endpoint, format:
                                    [https://{name}.plentymarkets-cloud01.com]
            use_keyring [bool]  -   Save the credentials temporarily or
                                    permanently
            data_format [str]   -   Output format of the response
            debug       [bool]  -   Print out additional information about the
                                    request URL and parameters
            username    [str]   -   skip the keyring and directly enter the
                                    username to the REST-API
            password    [str]   -   password string or path to a gpg-encrypted
                                    file that contains the key
            use_gpg     [bool]  -   Indicates if @password is a password
                                    string(False) or a file path to a
                                    gpg encrypted file containing the password
        """
        self.url = base_url
        self.keyring = plenty_api.keyring.CredentialManager()
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        self.data_format = data_format.lower()
        if data_format.lower() not in ['json', 'dataframe']:
            self.data_format = 'json'
        self.creds = {'Authorization': ''}
        logged_in = self.__authenticate(
            persistent=use_keyring, user=username, pw=password, use_gpg=use_gpg)
        if not logged_in:
            raise RuntimeError('Authentication failed')

    def __authenticate(self, persistent: bool, user: str, pw: str,
                       use_gpg: bool) -> bool:
        """
        Get the bearer token from the PlentyMarkets API.
        There are three possible methods:
            + Enter once and keep the username and the password
                within a keyring
                [persistent TRUE & (user FALSE or pw FALSE)]

            + Enter the username and password directly
                [persistent FALSE & (user FALSE or pw FALSE)]

            + Provide username as an argument and get the password
                from a GnuPG encrypted file at a specified path.
                [user TRUE and pw TRUE and use_gpg TRUE]

            + Provide username and the password as arguments
                [user TRUE and pw TRUE an use_gpg FALSE]

        Parameter:
            persistent  [bool]  -   Permanent or temporary credential storage
            user        [str]   -   skip the keyring and directly enter the
                                    username to the REST-API
            pw          [str]   -   path to a gpg-encrypted file that contains
                                    the key.
            use_gpg     [bool]  -   Indicates if @pw is a password
                                    string(False) or a file path to a
                                    gpg encrypted file containing the password

        Return:
                        [bool]
        """

        token = ''
        decrypt_pw = None

        if persistent and not (user and pw):
            creds = self.keyring.get_credentials()
            if not creds:
                creds = utils.new_keyring_creds(keyring=self.keyring)
        elif not persistent and not (user and pw):
            creds = utils.get_temp_creds()
        elif user and pw:
            if use_gpg:
                gpg = gnupg.GPG()
                try:
                    with open(pw, 'rb') as pw_file:
                        decrypt_pw = gpg.decrypt_file(pw_file)
                except FileNotFoundError as err:
                    logging.error("Login to API failed: Provided gpg file is not "
                                  f"valid\n=> {err}")
                    return False
                if not decrypt_pw:
                    logging.error("Login to API failed: Decryption of password"
                                  " file failed.")
                    return False
                password = decrypt_pw.data.decode('utf-8').strip('\n')
                creds = {'username': user, 'password': password}
            else:
                creds = {'username': user, 'password': pw}

        endpoint = self.url + '/rest/login'
        response = requests.post(endpoint, params=creds)
        if response.status_code == 403:
            logging.error(
                "ERROR: Login to API failed: your account is locked\n"
                "unlock @ Setup->settings->accounts->{user}->unlock login"
            )
        try:
            token = utils.build_login_token(response_json=response.json())
        except KeyError:
            try:
                if response.json()['error'] == 'invalid_credentials' and \
                        persistent:
                    logging.error(
                        "Wrong credentials: Please enter valid credentials."
                    )
                    creds = utils.update_keyring_creds(keyring=self.keyring)
                    response = requests.post(endpoint, params=creds)
                    token = utils.build_login_token(
                        response_json=response.json())
                else:
                    logging.error("Login to API failed: login token retrieval "
                                  f"was unsuccessful.\nstatus:{response}")
                    return False
            except KeyError:
                logging.error("Login to API failed: login token retrieval was "
                              f"unsuccessful.\nstatus:{response}")
                try:
                    logging.debug(f"{response.json()}")
                except Exception as err:
                    logging.error("Login to API failed: Could not read the "
                                  f"response: {err}")
                    return False
        if not token:
            return False

        self.creds['Authorization'] = token
        return True

    def __plenty_api_request(self,
                             method: str,
                             domain: str,
                             query: dict = None,
                             data: dict = None,
                             path: str = '') -> dict:
        """
        Make a request to the PlentyMarkets API.

        Parameter:
            method      [str]   -   GET/POST
            domain      [str]   -   Orders/Items...
        (Optional)
            query       [dict]  -   Additional options for the request
            data        [dict]  -   Data body for post requests
        """
        route = ''
        endpoint = ''
        raw_response = {}
        response = {}

        route = utils.get_route(domain=domain)
        endpoint = utils.build_endpoint(url=self.url, route=route, path=path)
        logging.debug(f"Endpoint: {endpoint}")
        if query:
            logging.debug(f"Params: {query}")
        while True:
            if method.lower() == 'get':
                raw_response = requests.get(endpoint, headers=self.creds,
                                            params=query)

            if method.lower() == 'post':
                raw_response = requests.post(endpoint, headers=self.creds,
                                             params=query, json=data)

            if method.lower() == 'put':
                raw_response = requests.put(endpoint, headers=self.creds,
                                            params=query, json=data)

            if raw_response.status_code != 429:
                break
            logging.warning(
                "API:Request throttled, limit for subscription reached"
            )
            time.sleep(3)

        logging.debug(f"request url: {raw_response.request.url}")
        try:
            response = raw_response.json()
        except simplejson.errors.JSONDecodeError:
            logging.error(f"No response for request {method} at {endpoint}")
            return None

        if isinstance(response, dict) and 'error' in response.keys():
            logging.error(f"Request failed:\n{response['error']['message']}")

        return response

# GET REQUESTS

    def __repeat_get_request_for_all_records(self,
                                             domain: str,
                                             query: dict,
                                             path: str = '') -> dict:
        """
        Collect data records from multiple API requests in a single JSON
        data structure.

        Parameter:
            domain      [str]   -   Orders/Items/..
            query       [dict]  -   Additional options for the request

        Return:
                        [dict]  -   API response in as javascript object
                                    notation
        """
        response = self.__plenty_api_request(method='get',
                                             domain=domain,
                                             path=path,
                                             query=query)
        if not response:
            return None

        if ((isinstance(response, dict) and 'error' in response.keys()) or
                isinstance(response, list)):
            return response

        entries = response['entries']

        while not response['isLastPage']:
            query.update({'page': response['page'] + 1})
            response = self.__plenty_api_request(method='get',
                                                 domain=domain,
                                                 path=path,
                                                 query=query)
            if not response:
                return None

            if isinstance(response, dict) and 'error' in response.keys():
                logging.error(f"subsequent {domain} API requests failed.")
                return response

            entries += response['entries']

        return entries

    def __plenty_api_generic_get(self,
                                 domain: str = '',
                                 path: str = '',
                                 refine: dict = None,
                                 additional: list = None,
                                 query: dict = None,
                                 lang: str = ''):
        """
        Generic wrapper for GET routes that includes basic checks, repeated
        requests and data type conversion.

        Parameters:
            domain      [str]   -   orders/items/...
            path        [str]   -   Addition to the domain for a specific route
            refine      [dict]  -   Apply filters to the request
            additional  [list]  -   Additional arguments for the query
            query       [dict]  -   Extra elements for the query
            lang        [str]   -   Language for the export

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        query = utils.sanity_check_parameter(
            domain=domain, query=query, refine=refine,
            additional=additional,lang=lang)

        data = self.__repeat_get_request_for_all_records(
            domain=domain, path=path, query=query)

        return utils.transform_data_type(
            data=data, data_format=self.data_format)

    def plenty_api_get_orders_by_date(self, start, end, date_type='create',
                                      additional=None, refine=None):
        """
        Get all orders within a specific date range.

        Parameter:
            start       [str]   -   Start date
            end         [str]   -   End date
            date_type   [str]   -   Specify the type of date
                                    {Creation, Change, Payment, Delivery}
            additional  [list]  -   Additional arguments for the query as
                                    specified in the manual
            refine      [dict]  -   Apply filters to the request
                                    Example:
                                    {'orderType': '1,4', referrerId: '1'}
                                    Restrict the request to order types:
                                        1 and 4 (sales orders and refund)
                                    And restrict it to only orders from the
                                    referrer with id '1'

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """

        date_range = utils.build_date_range(start=start, end=end)
        if not date_range:
            logging.error(f"Invalid range {start} -> {end}")
            return None

        if not utils.check_date_range(date_range=date_range):
            logging.error(f"{date_range['start']} -> {date_range['end']}")
            return None

        query = utils.build_query_date(date_range=date_range,
                                       date_type=date_type)
        if not query:
            return None

        query = utils.sanity_check_parameter(domain='order',
                                             query=query,
                                             refine=refine,
                                             additional=additional)

        orders = self.__repeat_get_request_for_all_records(domain='orders',
                                                           query=query)
        if isinstance(orders, dict) and 'error' in orders.keys():
            logging.error(f"GET orders by date failed with:\n{orders}")
            return None

        orders = utils.transform_data_type(data=orders,
                                           data_format=self.data_format)

        return orders

    def plenty_api_get_attributes(self,
                                  additional: list = None,
                                  last_update: str = '',
                                  variation_map: bool = False):
        """
        List all attributes from PlentyMarkets, this will fetch the basic
        attribute structures, so if you require an attribute value use:
        additional=['values'].
        The option variation_map performs an additional request to
        /rest/items/variations in order to map variation IDs to attribute
        values.

        Parameter:
            additional  [list]  -   Add additional elements to the response
                                    data
                                    Viable options:
                                    ['values', 'names', 'maps']
            last_update [str]   -   Date of the last update given as one
                                    of the following formats:
                                        YYYY-MM-DDTHH:MM:SS+UTC-OFFSET
                                        attributes-MM-DDTHH:MM
                                        YYYY-MM-DD
            variation_map[bool]-   Fetch all variations and add a list of
                                    variations, where the attribute value
                                    matches to the corresponding attribute
                                    value

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        attributes = None
        query = {}

        query = utils.sanity_check_parameter(domain='attribute',
                                             query=query,
                                             additional=additional)

        if last_update:
            query.update({'updatedAt': last_update})

        # variation_map was given but the required '&with=values' query is
        # missing, we assume the desired request was to be made with values
        if variation_map:
            if not additional:
                query.update({'with': 'values'})
            if additional:
                if 'values' not in additional:
                    query.update({'with': 'values'})

        attributes = self.__repeat_get_request_for_all_records(
            domain='attributes', query=query)
        if isinstance(attributes, dict) and 'error' in attributes.keys():
            logging.error(f"GET attributes failed with:\n{attributes}")
            return None

        if variation_map:
            variation = self.plenty_api_get_variations(
                additional=['variationAttributeValues'])
            attributes = utils.attribute_variation_mapping(
                variation=variation, attribute=attributes)

        attributes = utils.transform_data_type(data=attributes,
                                               data_format=self.data_format)

        return attributes

    def plenty_api_get_vat_id_mappings(self, subset: List[int] = None):
        """
        Get a mapping of all VAT configuration IDs to each country or
        if specified for a subset of countries.
        A VAT configuration is a combination of country, vat rates,
        restrictions and date range.

        Parameter:
            subset      [list]  -   restrict the mappings to only the given
                                    IDs (integer)
            You can locate these IDs in your Plenty- Markets system under:
            Setup-> Orders-> Shipping-> Settings-> Countries of delivery

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        vat_data = self.__repeat_get_request_for_all_records(domain='vat',
                                                             query={})
        if isinstance(vat_data, dict) and 'error' in vat_data.keys():
            logging.error(f"GET VAT-configuration failed with:\n{vat_data}")
            return None

        vat_table = utils.create_vat_mapping(data=vat_data, subset=subset)

        vat_table = utils.transform_data_type(data=vat_table,
                                              data_format=self.data_format)
        return vat_table

    def plenty_api_get_price_configuration(self,
                                           minimal: bool = False,
                                           last_update: str = ''):
        """
        Fetch the price configuration from PlentyMarkets.

        Parameter:
            minimal     [bool]  -   reduce the response data to necessary IDs.
            last_update [str]   -   Date of the last update given as one of the
                                    following formats:
                                        YYYY-MM-DDTHH:MM:SS+UTC-OFFSET
                                        YYYY-MM-DDTHH:MM
                                        YYYY-MM-DD

        Result:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        prices = None
        minimal_prices: list = []
        query = {}

        if last_update:
            # The documentation refers to Unix timestamps being a valid
            # format, but that is not the case within my tests.
            query.update({'updatedAt': last_update})

        prices = self.__repeat_get_request_for_all_records(
            domain='prices', query=query)
        if isinstance(prices, dict) and 'error' in prices.keys():
            logging.error(f"GET price-configuration failed with:\n{prices}")
            return None

        if not prices:
            return None

        if minimal:
            for price in prices:
                minimal_prices.append(
                    utils.shrink_price_configuration(data=price))
            prices = minimal_prices

        prices = utils.transform_data_type(data=prices,
                                           data_format=self.data_format)
        return prices

    def plenty_api_get_manufacturers(self,
                                     refine: dict = None,
                                     additional: list = None,
                                     last_update: str = ''):
        """
        Get a list of manufacturers (brands), which are setup on
        PlentyMarkets.

        Parameter:
            refine      [dict]  -   Apply a filter to the request
                                    The only viable option currently is:
                                    'name'
            additional  [list]  -   Add additional elements to the response
                                    data.
                                    Viable options currently:
                                    ['commisions', 'externals']
            last_update [str]   -   Date of the last update given as one of the
                                    following formats:
                                        YYYY-MM-DDTHH:MM:SS+UTC-OFFSET
                                        YYYY-MM-DDTHH:MM
                                        YYYY-MM-DD

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        query = {}
        if last_update:
            query.update({'updatedAt': last_update})
        return self.__plenty_api_generic_get(domain='manufacturer',
                                             query=query,
                                             refine=refine,
                                             additional=additional)

    def plenty_api_get_referrers(self,
                                 column: str = ''):
        """
        Get a list of order referrers from PlentyMarkets.

        The description within the PlentyMarkets API documentation is just
        wrong, the parameter doesn't expect an integer nor a list of integers,
        it actually cannot query multiple columns.
        All the parameter can query is a "single" column, which is why I
        renamed the parameter in this method.

        Parameter:
            column      [str]   -   Name of the field from the referrer to be
                                    exported.

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        # TODO actually only backendName, id and name are actually useful
        # because all other attributes are useless without identification
        valid_columns = ['backendName', 'id', 'isEditable', 'isFilterable',
                         'name', 'orderOwnderId', 'origin']
        referrers = None
        query = {}
        if column in valid_columns:
            query = {'columns': column}
        else:
            logging.warning(f"Invalid column argument removed: {column}")

        # This request doesn't export in form of pages
        referrers = self.__plenty_api_request(method='get',
                                              domain='referrer',
                                              query=query)
        if 'error' in referrers.keys():
            logging.error(f"GET referrers failed with:\n{referrers}")
            return None

        referrers = utils.transform_data_type(data=referrers,
                                              data_format=self.data_format)

        return referrers

    def plenty_api_get_items(self,
                             refine: dict = None,
                             additional: list = None,
                             last_update: str = '',
                             lang: str = ''):
        """
        Get product data from PlentyMarkets.

        Parameter:
            refine      [dict]  -   Apply filters to the request
                                    Example:
                                    {'id': '12345', 'flagOne: '5'}
            additional  [list]  -   Add additional elements to the response
                                    data.
                                    Example:
                                    ['variations', 'itemImages']
            last_update [str]   -   Date of the last update given as one of the
                                    following formats:
                                        YYYY-MM-DDTHH:MM:SS+UTC-OFFSET
                                        YYYY-MM-DDTHH:MM
                                        YYYY-MM-DD
            lang        [str]   -   Provide the text within the data in one of
                                    the following languages:

            (plenty documentation: https://rb.gy/r6koft)

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        query = {}
        if last_update:
            query.update({'updatedBetween': utils.date_to_timestamp(
                         date=last_update)})

        return self.__plenty_api_generic_get(domain='item',
                                             query=query,
                                             refine=refine,
                                             additional=additional,
                                             lang=lang)

    def plenty_api_get_variations(self,
                                  refine: dict = None,
                                  additional: list = None,
                                  lang: str = ''):
        """
        Get product data from PlentyMarkets.

        Parameter:
            refine      [dict]  -   Apply filters to the request
                                    Example:
                                    {'id': '2345', 'flagOne: '5'}
            additional  [list]  -   Add additional elements to the response
                                    data.
                                    Example:
                                    ['stock', 'images']
            lang        [str]   -   Provide the text within the data in one
                                    of the following languages:
                                    Example: 'de', 'en', etc.

            (plenty documentation: https://rb.gy/r6koft)

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        query = {}

        return self.__plenty_api_generic_get(domain='variation',
                                             refine=refine,
                                             additional=additional,
                                             query=query,
                                             lang=lang)

    def plenty_api_get_stock(self, refine: dict = None):
        """
        Get stock data from PlentyMarkets.

        Parameter:
            refine      [dict]  -   Apply filters to the request
                                    Example:
                                    {'variationId': 2345}

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        return self.__plenty_api_generic_get(domain='stockmanagement',
                                             refine=refine)

    def plenty_api_get_storagelocations(self,
                                        warehouse_id: int,
                                        refine: dict = None,
                                        additional: list = None):
        """
        Get storage location data from PlentyMarkets.

        Parameter:
            warehouse_id[int]   -   Plentymarkets ID of the target warehouse
            refine      [dict]  -   Apply filters to the request
                                    Example:
                                    {'variationId': 2345}
            additional  [list]  -   Add additional elements to the response
                                    data.
                                    Example:
                                    ['storageLocation']

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        return self.__plenty_api_generic_get(
            domain='warehouses',
            path=f'/{warehouse_id}/stock/storageLocations',
            refine=refine,
            additional=additional)

    def plenty_api_get_variation_stock_batches(self, variation_id: int):
        """
        Get all storage locations from all available warehouses for the given
        variation.

        Parameter:
            variation_id[int]   -   Plentymarkets ID of the target variation

        Return:
                        [list]  -   list of storage locations ordered by the
                                    `bestBeforeDate`
        """
        # get all warehouses for this item
        refine = {'variationId': variation_id}

        # returns only locations with positive stock
        stock = self.plenty_api_get_stock(refine=refine)
        warehouses = [s['warehouseId'] for s in stock]

        # get storage data from everywhere
        storage_data = [location
                        for warehouse_id in warehouses
                        for location in self.plenty_api_get_storagelocations(
                        warehouse_id, refine=refine)]

        # return ordered by best before date (oldest first)
        return sorted(storage_data, key=lambda s: s['bestBeforeDate'])

    def plenty_api_get_variation_warehouses(self,
                                            item_id: int,
                                            variation_id: int) -> list:
        """
        Get all a list of warehouses, where the given variation is stored.

        Parameters:
            item_id     [int]   -   Plentymarkets ID of the item
                                    (variation container)
            variation_id[int]   -   Plentymarkets ID of the specific variation

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        return self.__plenty_api_generic_get(
            domain='item',
            path=f'/{item_id}/variations/{variation_id}/variation_warehouses')

    def plenty_api_get_contacts(self,
                                refine: dict = None,
                                additional: list = None):
        """
        List all contacts on the Plentymarkets system.

        Parameter:
            refine      [dict]  -   Apply filters to the request
                                    Example:
                                    {'email': 'a@posteo.net', 'name': 'Thomas'}
            additional  [list]  -   Add additional elements to the response
                                    data.
                                    Example:
                                    ['addresses']

        Return:
                        [JSON(Dict) / DataFrame] <= self.data_format
        """
        return self.__plenty_api_generic_get(
            domain='contact',
            refine=refine,
            additional=additional)

# POST REQUESTS

    def plenty_api_set_image_availability(self,
                                          item_id: str,
                                          image_id: str,
                                          target: dict) -> dict:
        """
        Create a marketplace availability for a specific item/image
        combiniation.

        Parameter:
            item_id     [str]   -   Item ID from PlentyMarkets
            image_id    [str]   -   Image ID from PlentyMarkets
            target      [dict]  -   ID of the specific:
                                        * marketplace
                                        * mandant (client)
                                        * listing
                                    together with a specifier



        Marketplace IDs: (@setup->orders->order origins)
        Mandant IDs: (@setup->client->{client}->settings[Plenty ID])

        Return:
                        [dict]
        """
        if not item_id or not image_id or not target:
            return {'error': 'missing_parameter'}

        target_name = ''
        target_id = ''
        for element in target:
            if element in ['marketplace', 'mandant', 'listing']:
                if target[element]:
                    target_name = element
                    target_id = target[element]
            else:
                logging.warning(f"{element} is not a valid target for the "
                                "image availability POST request.")

        if not target_name or not target_id:
            logging.error("Invalid target for availability configuration. "
                          f"Got: [{target}]")
            return {'error': 'invalid_target'}

        data = {
            "imageId": image_id,
            "type": target_name,
            "value": str(target_id)
        }
        path = str(f"/{item_id}/images/{image_id}/availabilities")

        response = self.__plenty_api_request(method="post",
                                             domain="items",
                                             path=path,
                                             data=data)

        return response

    def plenty_api_create_items(self, json: list) -> list:
        """
        Create one or more items at Plentymarkets.

        Parameter:
            json        [list]   -   Either a list of JSON objects or a single
                                     JSON, describing the items.

        Return:
                        [list]   -   Response objects if one or more should
                                     fail, the entry contains the error message
        """
        if isinstance(json, dict):
            json = [json]

        response = []
        for item in json:
            if not utils.sanity_check_json(route_name='items',
                                           json=item):
                response.append({'error': 'invalid_json'})
                continue
            response.append(self.__plenty_api_request(
                method="post", domain="items", data=item))
        return response

    def plenty_api_create_variations(self, item_id: int, json: list) -> list:
        """
        Create a variation for a specific item on Plentymarkets.

        Parameter:
            item_id     [int]    -   Add the variations to this item
            json        [list]   -   Either a list of JSON objects or a single
                                     JSON object describing a variation for an
                                     item.

        Return:
                        [list]   -   Response objects if one or more should
                                     fail, the entry contains the error
                                     message.
        """
        if not item_id:
            return [{'error': 'missing_parameter'}]

        if isinstance(json, dict):
            json = [json]

        path = str(f'/{item_id}/variations')

        response = []
        for variation in json:
            if not utils.sanity_check_json(route_name='variations',
                                        json=variation):
                response.append({'error': 'invalid_json'})
                continue
            response.append(self.__plenty_api_request(
                method="post", domain="items", path=path, data=variation))

        return response

    def plenty_api_create_attribute(self, json: dict) -> dict:
        """
        Create a new attribute on Plentymarkets.

        Parameter:
            json        [dict]  -   A single JSON object describing an
                                    attribute

        Return:
                        [dict]  -  Response object if the request should
                                   fail, the entry contains the error
                                   message.
        """
        if not utils.sanity_check_json(route_name='attributes',
                                    json=json):
            return {'error': 'invalid_json'}

        return self.__plenty_api_request(method="post", domain="attributes",
                                         data=json)

    def plenty_api_create_attribute_name(self, attribute_id: int,
                                         lang: str, name: str) -> dict:
        """
        Create an attribute name for a specific attribute.

        Parameter:
            attribute_id[str]   -   Attribute ID from PlentyMarkets
            lang        [str]   -   two letter abbreviation of a language
            name        [str]   -   The visible name of the attribute in
                                    the given language

        Return:
                        [dict]
        """
        if not attribute_id or not lang or not name:
            return [{'error': 'missing_parameter'}]

        path = str(f"/{attribute_id}/names")

        if utils.get_language(lang=lang) == 'INVALID_LANGUAGE':
            return {'error': 'invalid_language'}

        data = {
            'attributeId': attribute_id,
            'lang': lang,
            'name': name
        }

        return self.__plenty_api_request(method="post", domain="attributes",
                                         path=path, data=data)

    def plenty_api_create_attribute_values(self, attribute_id: int,
                                           json: list) -> dict:
        """
        Create one or more attribute values for a specific attribute.

        Parameter:
            attribute_id[str]   -   Attribute ID from PlentyMarkets
            json        [list]  -   Either a list of JSON objects or a
                                    single JSON object describing an
                                    attribute value for an attribute

        Return:
                        [list]
        """
        if not attribute_id:
            return [{'error': 'missing_parameter'}]

        if isinstance(json, dict):
            json = [json]

        path = str(f"/{attribute_id}/values")

        response = []
        for name in json:
            if not utils.sanity_check_json(route_name='attribute_values',
                                           json=name):
                response.append({'error': 'invalid_json'})
                continue

            response.append(self.__plenty_api_request(
                method="post", domain="attributes", path=path, data=name))

        return response

    def plenty_api_create_attribute_value_name(self, value_id: int,
                                               lang: str, name: str) -> dict:
        """
        Create an attribute value name for a specific attribute.

        Parameter:
            value_id    [str]   -   Attribute value ID from PlentyMarkets
            lang        [str]   -   two letter abbreviation of a language
            name        [str]   -   The visible name of the attribute in the
                                    given language

        Return:
                        [dict]
        """
        if not value_id or not lang or not name:
            return [{'error': 'missing_parameter'}]

        path = str(f"/attribute_values/{value_id}/names")

        if utils.get_language(lang=lang) == 'INVALID_LANGUAGE':
            return {'error': 'invalid_language'}

        data = {
            'valueId': value_id,
            'lang': lang,
            'name': name
        }

        return self.__plenty_api_request(method="post", domain="items",
                                         path=path, data=data)

    def plenty_api_create_redistribution(self, template: dict,
                                         book_out: bool = False) -> dict:
        """
        Create a new redistribution on Plentymarkets.

        The creation of a redistribution is split into multiple steps with the
        REST API, first the order has to be created, then the outgoing
        transaction have to be created and booked, before incoming transactions
        are created and booked.

        As soon as the order was initiated it cannot be changed/deleted anymore

        Parameter:
            template    [dict]  -   Describes the transactions between two
                                    warehouses
            book_out    [bool]  -   Book outgoing transaction directly

        Return:
                        [dict]
        """
        if not utils.validate_redistribution_template(template=template):
            return {'error': 'invalid_template'}

        redistribution_json = utils.build_redistribution_json(
            template=template)
        response = self.__plenty_api_request(method="post",
                                             domain="redistribution",
                                             data=redistribution_json)

        (outgoing, incoming) = utils.build_transactions(
            order=response, variations=template['variations'])

        if outgoing:
            for transaction in outgoing:
                transaction_response = self.plenty_api_create_transaction(
                    order_item_id=transaction['orderItemId'], json=transaction)
                if 'error' in transaction_response.keys():
                    logging.warning("transaction creation failed "
                                    f"({transaction_response})")

        if book_out:
            initiate_order_date = utils.build_date_update_json(
                date_type='initiate', date=datetime.datetime.now())
            self.plenty_api_update_redistribution(order_id=response['id'],
                                                  json=initiate_order_date)
            self.plenty_api_create_booking(order_id=response['id'])

        if incoming:
            for transaction in incoming:
                transaction_response = self.plenty_api_create_transaction(
                    order_item_id=transaction['orderItemId'], json=transaction)
            if book_out:
                self.plenty_api_create_booking(order_id=response['id'])
                finish_order_date = utils.build_date_update_json(
                    date_type='finish', date=datetime.datetime.now())
                self.plenty_api_update_redistribution(order_id=response['id'],
                                                    json=finish_order_date)

        return response

    def plenty_api_create_transaction(self, order_item_id: int,
                                      json: dict) -> dict:
        """
        Create an outgoing or incoming transaction for an order.

        Parameter:
            order_item_id [int] -   ID of a single item (variation) within an
                                    order
            json        [dict]  -   single JSON object describing the
                                    transaction

        Return:
                        [dict]  -  Response object if the request should fail,
                                   the entry contains the error message.
        """
        if not order_item_id:
            return {'error': 'missing_parameter'}

        if not utils.sanity_check_json(route_name='transaction', json=json):
            return {'error': 'invalid_json'}

        path = str(f"/items/{order_item_id}/transactions")
        response = self.__plenty_api_request(method="post",
                                             domain="order",
                                             path=path,
                                             data=json)
        return response

    def plenty_api_create_booking(self, order_id: int,
                                  delivery_note: str = '') -> dict:
        """
        Execute all pending transactions within an order.

        This route handles outgoing and incoming transactions within an
        order (sales/redistribution/reorder/etc..). Which means it books
        out and books in.

        Parameter:
            order_id    [int]   -   ID of the order on Plentymarkets
            delivery_note [str] -   Identifier of the delivery note document,
                                    connected to the order

        Return:
                        [dict]  -  Response object if the request should
                                   fail, the entry contains the error message.
        """
        data = {}
        path = str(f"/{order_id}/booking")
        if delivery_note:
            data = {
                'deliveryNoteNumber': delivery_note
            }
        response = self.__plenty_api_request(method="post",
                                             domain="order",
                                             path=path,
                                             data=data)
        return response

# PUT REQUESTS

    def plenty_api_update_redistribution(self, order_id: int,
                                         json: dict) -> dict:
        """
        Change certain attributes of a redistribution.

        Commonly used for changing certain event dates like:
            initiation, estimated delivery date and finish

        Parameter:
            order_id    [int]   -   ID of the order on Plentymarkets
            json        [dict]  -   single JSON object describing the update

        Return:
                        [dict]  -  Response object if the request should
                                   fail, the entry contains the error
                                   message.
        """
        if not order_id:
            return {'error': 'missing_parameter'}

        path = str(f"/{order_id}")
        response = self.__plenty_api_request(method="put",
                                             domain="redistribution",
                                             path=path,
                                             data=json)

        return response

    def plenty_api_book_incoming_items(self,
                                       item_id: int,
                                       variation_id: int,
                                       quantity: float,
                                       warehouse_id: int,
                                       location_id: int = 0,
                                       batch: str = None,
                                       best_before_date: str = None) -> dict:
        """
        Book a certain amount of stock of a specific variation into a location.

        If no stock location is given, this will book the stock into the
        standard location.
        The difference to the `plenty_api_create_booking` method is that the
        `plenty_api_create_booking` route needs existing transactions, while
        this method performs the booking directly.

        Parameters:
            item_id     [int]   -   Plentymarkets ID of the item
                                    (variation container)
            variation_id[int]   -   Plentymarkets ID of the specific variation
            quantity    [float] -   Amount to be booked into the location
            warehouse_id[int]   -   Plentymarkets ID of the target warehouse
            location_id [int]   -   Assigned ID for the storage location by
                                    default 0 (standard location)
            batch       [str]   -   Batch number that describes a specific
                                    group of products that are created within a
                                    limited time window
            best_before_date[str] -   Date at which a product loses guarantees
                                    for certain properties to be effective

        Return:
                        [dict]
        """
        data = {
            "warehouseId": warehouse_id,
            "storageLocationId": location_id,
            "deliveredAt": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            "currency": "EUR",
            "quantity": quantity,
            "reasonId": 181,
        }

        if batch:
            data.update(batch=batch)
        if best_before_date:
            w3c_date = utils.parse_date(best_before_date)
            if w3c_date:
                data.update(best_before_date=w3c_date)

        path = str(f"/{item_id}/variations/{variation_id}/stock/"
                   "bookIncomingItems")

        response = self.__plenty_api_request(method="put",
                                             domain="items",
                                             path=path,
                                             data=data)

        # TODO Error handling and introduce proper logging
        logging.debug(response)

        return response

    def plenty_api_book_outgoing_items(self,
                                       item_id: int,
                                       variation_id: int,
                                       quantity: float,
                                       warehouse_id: int,
                                       location_id: int = 0,
                                       batch: str = None,
                                       best_before_date: str = None):
        """
        Book a certain amount of stock of a specific variation from a location.

        If no stock location is given, this will book the stock from the
        standard location.
        The difference to the `plenty_api_create_booking` method is that the
        `plenty_api_create_booking` route needs existing transactions, while
        this method performs the booking directly.

        Parameters:
            item_id     [int]   -   Plentymarkets ID of the item
                                    (variation container)
            variation_id[int]   -   Plentymarkets ID of the specific variation
            quantity    [float] -   Amount to be booked into the location
            warehouse_id[int]   -   Plentymarkets ID of the target warehouse
            location_id [int]   -   Assigned ID for the storage location by
                                    default 0 (standard location)
            batch       [str]   -   Batch number that describes a specific
                                    group of products that are created within a
                                    limited time window
            best_before_date[str] -   Date at which a product loses guarantees
                                    for certain properties to be effective

        Return:
                        [dict]
        """
        data = {
            "warehouseId": warehouse_id,
            "storageLocationId": location_id,
            "deliveredAt": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            "currency": "EUR",
            "quantity": quantity,
            "reasonId": 201,
        }

        if batch:
            data.update(batch=batch)
        if best_before_date:
            w3c_date = utils.parse_date(best_before_date)
            if w3c_date:
                data.update(best_before_date=w3c_date)

        path = str(f"/{item_id}/variations/{variation_id}/stock/"
                   "bookOutgoingItems")

        response = self.__plenty_api_request(method="put",
                                             domain="items",
                                             path=path,
                                             data=data)
        # TODO Error handling and introduce proper logging
        logging.debug(response)

        return response
