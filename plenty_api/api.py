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

import time
from typing import List
import requests
import simplejson
import gnupg

import plenty_api.keyring
import plenty_api.utils as utils


class PlentyApi():
    """
        Provide specified routines to access data from PlentyMarkets
        over the RestAPI.

        Public methods:
            GET REQUESTS
            **plenty_api_get_orders_by_date**
                Get all orders of all types within a specified range of two
                dates.
                [start]         -   start date
                [end]           -   end date
                [date_type]     -   {Creation, Change, Payment, Delivery}
                [additional]    -   List of additional arguments **
                [refine]        -   Dictionary of filter query names and values

                Accepted date formats:
                    {Y-m-d | Y-m-dTH:M | Y-m-dTH:M:S+UTC-OFFSET}
                    Examples:
                        2020-09-16              (get your local timezone)
                        2020-09-16T08:00        (get your local timezone)
                        2020-09-16T08:00Z       (UTC timezone)
                        2020-09-16T08:00+02:00  (CEST timezone)

                ** Reference of query arguments
                (developers.plentymarkets.com/rest-doc#/Order/get_rest_orders)
            ___
            **plenty_api_get_attributes**
                List all the attributes from PlentyMarkets, optionally link
                variation IDs to the response, that are connected to the
                attribute value
                [additional]    -   Add additional elements to the response.
                [last_change]   -   filter out attributes were the last
                                    change is older than the specified date
                [variation_map] -   Add a list of connected variations

                Reference:
                (https://developers.plentymarkets.com/rest-doc#/Item/get_rest_items_attributes)
            ___
            **plenty_api_get_vat_id_mappings**
                Get a mapping of VAT configuration IDs to country IDs,
                together with the TaxID for each country.
                [subset]        -   limit the data to the given country IDs

                Reference:
                (developers.plentymarkets.com/rest-doc#/Accounting/get_rest_vat)
            ___
            **plenty_api_get_price_configuration**
                Fetch the set of price configuration, that were setup on
                PlentyMarkets.
                [minimal]       -   reduce the response body to necessary info
                [last_change]   -   filter out configuration were the last
                                    change is older than the specified date

                Reference:
                (https://developers.plentymarkets.com/rest-doc#/Item/get_rest_items_sales_prices)
            ___
            **plenty_api_get_manufacturers**
                Fetch a list of manufacturer (brands) in PlentyMarkets.
                [refine]        -   Apply filters to the request
                [additional]    -   Add additional elements to the response.
                [last_update]   -   Date of the last update

                Reference:
                (https://developers.plentymarkets.com/rest-doc#/Item/get_rest_items_manufacturers)
            ---
            **plenty_api_get_referrers**
                Fetch a list of referrers from PlentyMarkets.

                [column]        -   Get only a specific column

                Reference:
                (https://developers.plentymarkets.com/rest-doc#/Order/get_rest_orders_referrers)
                * WARNING the parameter description is just wrong, the columns
                 attribute actually only takes a single 'string', instead of
                 an integer and if you pass a list it only uses the last index*
            ___
            **plenty_api_get_items**
                Generic interface to item data from Plentymarkets with little
                abstraction.
                [refine]        -   Apply filters to the request
                [additional]    -   Add additional elements to the response.
                [last_update]   -   Date of the last update
                [lang]          -   Provide the text within a specific language

                Reference:
                (https://developers.plentymarkets.com/rest-doc#/Item/get_rest_items)

            ___
            **plenty_api_get_variations**
                Generic interface to variation data from PlentyMarkets
                [refine]        -   Apply filters to the request
                [additional]    -   Add additional elements to the response.
                [lang]          -   Provide the text within a specific language

                Reference:
                (https://developers.plentymarkets.com/rest-doc#/Item/get_rest_items_variations)

            POST REQUESTS
            **plenty_api_set_image_availability**
                Update the availability of an image for a marketplace, client
                or listing on PlentyMarkets.
                [item_id]       -   item ID, where the image is found
                [image_id]      -   ID of the specific image
                [target]        -   ID of the target
                                    Example:
                                        {'marketplace': 102}

                Reference:
                (https://developers.plentymarkets.com/rest-doc#/Item/post_rest_items__id__images__imageId__availabilities)
            ___
    """
    def __init__(self, base_url: str, use_keyring: bool = True,
                 data_format: str = 'json', debug: bool = False,
                 username: str = '', password: str = ''):
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
                debug       [bool]  -   Print out additional information
                                        about the request URL and parameters
                username    [str]   -   skip the keyring and directly enter
                                        the username to the REST-API
                password    [str]   -   path to a gpg-encrypted file that
                                        contains the key.

        """
        self.url = base_url
        self.keyring = plenty_api.keyring.CredentialManager()
        self.debug = debug
        self.data_format = data_format.lower()
        if data_format.lower() not in ['json', 'dataframe']:
            self.data_format = 'json'
        self.creds = {'Authorization': ''}
        self.__authenticate(persistent=use_keyring, user=username, pw=password)

    def __authenticate(self, persistent: str, user: str, pw: str):
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
                  [user TRUE and pw TRUE]

            Parameter:
                persistent  [bool]  -   Permanent or temporary credential
                                        storage
                user        [str]   -   skip the keyring and directly enter
                                        the username to the REST-API
                pw          [str]   -   path to a gpg-encrypted file that
                                        contains the key.
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
            gpg = gnupg.GPG()
            try:
                with open(pw, 'rb') as pw_file:
                    decrypt_pw = gpg.decrypt_file(pw_file)
            except FileNotFoundError as err:
                print("ERROR Login to API failed: Provided gpg file is not "
                      f"valid\n=> {err}")
                return False
            if not decrypt_pw:
                print("ERROR Login to API failed: Decryption of password file"
                      " failed.")
                return False
            password = decrypt_pw.data.decode('utf-8').strip('\n')
            creds = {'username': user, 'password': password}

        endpoint = self.url + '/rest/login'
        response = requests.post(endpoint, params=creds)
        if response.status_code == 403:
            print("ERROR: Login to API failed: your account is locked")
            print("unlock @ Setup->settings->accounts->{user}->unlock login")
        try:
            token = utils.build_login_token(response_json=response.json())
        except KeyError:
            try:
                if response.json()['error'] == 'invalid_credentials':
                    print("Wrong credentials: Please enter valid credentials.")
                    creds = utils.update_keyring_creds(keyring=self.keyring)
                    response = requests.post(endpoint, params=creds)
                    token = utils.build_login_token(
                        response_json=response.json())
                else:
                    print("ERROR: Login to API failed: login token retrieval "
                          f"was unsuccessful.\nstatus:{response}")
                    return False
            except KeyError:
                print("ERROR: Login to API failed: login token retrieval was "
                      f"unsuccessful.\nstatus:{response}")
                try:
                    print(f"{response.json()}")
                except Exception as err:
                    print("ERROR: Login to API failed: Could not read the "
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
        if self.debug:
            print(f"DEBUG: Endpoint: {endpoint}")
            print(f"DEBUG: Params: {query}")
        while True:
            if method.lower() == 'get':
                raw_response = requests.get(endpoint, headers=self.creds,
                                            params=query)

            if method.lower() == 'post':
                raw_response = requests.post(endpoint, headers=self.creds,
                                             params=query, json=data)
            if raw_response.status_code != 429:
                break
            print("API:Request throttled, limit for subscription reached")
            time.sleep(3)

        if self.debug:
            print(f"DEBUG: request url: {raw_response.request.url}")
        try:
            response = raw_response.json()
        except simplejson.errors.JSONDecodeError:
            print(f"ERROR: No response for request {method} at {endpoint}")
            return None

        if domain == 'referrer':
            # The referrer request responds with a different format
            return response

        if 'error' in response.keys():
            print(f"ERROR: Request failed:\n{response['error']['message']}")
            return None

        return response

# GET REQUESTS

    def __repeat_get_request_for_all_records(self,
                                             domain: str,
                                             query: dict) -> dict:
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
                                             query=query)
        if not response:
            return None

        entries = response['entries']

        while not response['isLastPage']:
            query.update({'page': response['page'] + 1})
            response = self.__plenty_api_request(method='get',
                                                 domain=domain,
                                                 query=query)
            if not response:
                print(f"ERROR: subsequent {domain} API requests failed.")
                return None

            entries += response['entries']

        return entries

    def plenty_api_get_orders_by_date(self, start, end, date_type='create',
                                      additional=None, refine=None):
        """
            Get all orders within a specific date range.

            Parameter:
                start       [str]   -   Start date
                end         [str]   -   End date
                date_type   [str]   -   Specify the type of date
                                        {Creation, Change, Payment, Delivery}
                additional  [list]  -   Additional arguments for the query
                                        as specified in the manual
                refine      [dict]  -   Apply filters to the request
                                        Example:
                                        {'orderType': '1,4', referrerId: '1'}
                                        Restrict the request to order types:
                                            1 and 4 (sales orders and refund)
                                        And restrict it to only orders from
                                        the referrer with id '1'

            Return:
                [JSON(Dict) / DataFrame] <= self.data_format
        """

        date_range = utils.build_date_range(start=start, end=end)
        if not date_range:
            print(f"ERROR: Invalid range {start} -> {end}")

        if not utils.check_date_range(date_range=date_range):
            print(f"ERROR: {date_range['start']} -> {date_range['end']}")
            return {}

        query = utils.build_query_date(date_range=date_range,
                                       date_type=date_type)

        query = utils.sanity_check_parameter(domain='order',
                                             query=query,
                                             refine=refine,
                                             additional=additional)

        orders = self.__repeat_get_request_for_all_records(domain='orders',
                                                           query=query)

        orders = utils.transform_data_type(data=orders,
                                           data_format=self.data_format)

        return orders

    def plenty_api_get_attributes(self,
                                  additional: list = None,
                                  last_update: str = '',
                                  variation_map: bool = False):
        """
            List all attributes from PlentyMarkets, this will fetch the
            basic attribute structures, so if you require an attribute value
            use: additional=['values'].
            The option variation_map performs an additional request to
            /rest/items/variations in order to map variation IDs to
            attribute values.

            Parameter:
                additional  [list]  -   Add additional elements to the
                                        response data.
                                        Viable options:
                                        ['values', 'names', 'maps']
                last_update [str]   -   Date of the last update given as one
                                        of the following formats:
                                            YYYY-MM-DDTHH:MM:SS+UTC-OFFSET
                                            attributes-MM-DDTHH:MM
                                            YYYY-MM-DD
                variation_map [bool]-   Fetch all variations and add a list
                                        of variations, where the attribute
                                        value matches to the corresponding
                                        attribute value

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
                subset      [list]  -   restrict the mappings to only
                                        the given IDs (integer)
                You can locate those IDs in your Plenty- Markets system under:
                Setup-> Orders-> Shipping-> Settings-> Countries of delivery

            Return:
                [JSON(Dict) / DataFrame] <= self.data_format
        """
        vat_data = self.__repeat_get_request_for_all_records(domain='vat',
                                                             query={})

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
                minimal     [bool]  -   reduce the response data to necessary
                                        IDs.
                last_update [str]   -   Date of the last update given as one
                                        of the following formats:
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
                additional  [list]  -   Add additional elements to the
                                        response data.
                                        Viable options currently:
                                        ['commisions', 'externals']
                last_update [str]   -   Date of the last update given as one
                                        of the following formats:
                                            YYYY-MM-DDTHH:MM:SS+UTC-OFFSET
                                            YYYY-MM-DDTHH:MM
                                            YYYY-MM-DD

            Return:
                [JSON(Dict) / DataFrame] <= self.data_format
        """
        manufacturers = None
        query = {}
        query = utils.sanity_check_parameter(domain='manufacturer',
                                             query=query,
                                             refine=refine,
                                             additional=additional)

        if last_update:
            query.update({'updatedAt': last_update})

        manufacturers = self.__repeat_get_request_for_all_records(
            domain='manufacturer', query=query)

        manufacturers = utils.transform_data_type(data=manufacturers,
                                                  data_format=self.data_format)
        return manufacturers

    def plenty_api_get_referrers(self,
                                 column: str = ''):
        """
            Get a list of order referrers from PlentyMarkets.

            The description within the PlentyMarkets API documentation
            is just wrong, the parameter doesn't expect an integer nor a
            list of integers, it actually cannot query multiple columns.
            All the parameter can query is a "single" column, which
            is why I renamed the parameter in this method.

            Parameter:
                column      [str]   -   Name of the field from the referrer
                                        to be exported.

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
            print(f"Invalid column argument removed: {column}")

        # This request doesn't export in form of pages
        referrers = self.__plenty_api_request(method='get',
                                              domain='referrer',
                                              query=query)

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
                additional  [list]  -   Add additional elements to the
                                        response data.
                                        Example:
                                        ['variations', 'itemImages']
                last_update [str]   -   Date of the last update given as one
                                        of the following formats:
                                            YYYY-MM-DDTHH:MM:SS+UTC-OFFSET
                                            YYYY-MM-DDTHH:MM
                                            YYYY-MM-DD
                lang        [str]   -   Provide the text within the data
                                        in one of the following languages:

                developers.plentymarkets.com/rest-doc/gettingstarted#countries

            Return:
                [JSON(Dict) / DataFrame] <= self.data_format
        """
        items = None
        query = {}

        query = utils.sanity_check_parameter(domain='item',
                                             query=query,
                                             refine=refine,
                                             additional=additional,
                                             lang=lang)

        if last_update:
            query.update({'updatedBetween': utils.date_to_timestamp(
                         date=last_update)})

        items = self.__repeat_get_request_for_all_records(domain='items',
                                                          query=query)

        items = utils.transform_data_type(data=items,
                                          data_format=self.data_format)
        return items

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
                additional  [list]  -   Add additional elements to the
                                        response data.
                                        Example:
                                        ['stock', 'images']
                lang        [str]   -   Provide the text within the data
                                        in one of the following languages:
                                        Example: 'de', 'en', etc.

                developers.plentymarkets.com/rest-doc/gettingstarted#countries

            Return:
                [JSON(Dict) / DataFrame] <= self.data_format
        """
        variations = None
        query = {}

        query = utils.sanity_check_parameter(domain='variation',
                                             query=query,
                                             refine=refine,
                                             additional=additional,
                                             lang=lang)

        variations = self.__repeat_get_request_for_all_records(
            domain='variations', query=query)

        variations = utils.transform_data_type(data=variations,
                                               data_format=self.data_format)
        return variations

# POST REQUESTS

    def plenty_api_set_image_availability(self,
                                          item_id: str,
                                          image_id: str,
                                          target: dict) -> bool:
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
                [bool]
        """
        target_name = ''
        target_id = ''
        for element in target:
            if element in ['marketplace', 'mandant', 'listing']:
                if target[element]:
                    target_name = element
                    target_id = target[element]
            else:
                print(f"WARNING: {element} is not a valid target "
                      "for the image availability POST request.")

        if not target_name or not target_id:
            print("ERROR: target for availability configuration required.")
            return False

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

        if not response:
            return False

        return True
