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

from typing import List
import requests
import simplejson

import plenty_api.keyring
import plenty_api.utils as utils


class PlentyApi():
    """
        Provide specified routines to access data from PlentyMarkets
        over the RestAPI.

        Public methods:
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
            **plenty_api_get_vat_id_mappings**
                Get a mapping of VAT configuration IDs to country IDs,
                together with the TaxID for each country.
                [subset]        -   limit the data to the given country IDs

                Reference:
                (developers.plentymarkets.com/rest-doc#/Accounting/get_rest_vat)
            ___
            **plenty_api_get_items**
                Generic interface to item data from Plentymarkets with little
                abstraction.
                [refine]        -   Apply filters to the request
                [additional]    -   Add additional elements to the response.
                [last_update]   -   Date of the last update
                [lang]          -   Provide the text within a specific language
            ___
    """
    def __init__(self, base_url, use_keyring=True, data_format='json',
                 debug=False):
        """
            Initialize the object and directly authenticate to the API to get
            the bearer token.

            Parameter:
                base_url [String]       -   Base URL to the PlentyMarkets API
                                            Endpoint, format:
                                    [https://{name}.plentymarkets-cloud01.com]
                use_keyring [Bool]      -   Save the credentials temporarily or
                                            permanently
                data_format [String]    -   Output format of the response
        """
        self.url = base_url
        self.keyring = plenty_api.keyring.CredentialManager()
        self.debug = debug
        self.data_format = data_format.lower()
        if data_format.lower() not in ['json', 'dataframe']:
            self.data_format = 'json'
        self.creds = {'Authorization': ''}
        self.__authenticate(persistent=use_keyring)

    def __authenticate(self, persistent):
        """
            Get the bearer token from the PlentyMarkets API.

            Parameter:
                persistent [Bool] : Permanent or temporary credential storage
        """

        token = ''
        if persistent:
            creds = self.keyring.get_credentials()
            if not creds:
                creds = utils.new_keyring_creds(kr=self.keyring)
        else:
            creds = utils.get_temp_creds()
        endpoint = self.url + '/rest/login'
        response = requests.post(endpoint, params=creds)
        if response.status_code == 403:
            print("ERROR: Login to API failed, your account is locked")
            print("unlock @ Setup->settings->accounts->{user}->unlock login")
        try:
            token = utils.build_login_token(response_json=response.json())
        except KeyError as err:
            try:
                if response.json()['error'] == 'invalid_credentials':
                    print("Wrong credentials: Please enter valid credentials.")
                    creds = utils.update_keyring_creds(kr=self.keyring)
                    response = requests.post(endpoint, params=creds)
                    token = utils.build_login_token(
                        response_json=response.json())
                else:
                    print(f"ERROR: Login API failed:{err}\nstatus:{response}")
                    return False
            except KeyError as err:
                print(f"ERROR: Login API failed:{err}\nstatus:{response}")
                try:
                    print(f"{response.json()}")
                except Exception as err:
                    print(f"Could not read the response: {err}")
                    return False
        if not token:
            return False

        self.creds['Authorization'] = token
        return True

    def __plenty_api_request(self, method, domain, query=''):
        """
            Make a request to the PlentyMarkets API.

            Parameter:
                method [String]     -   GET/POST
                domain [String]     -   Orders/Items...
            (Optional)
                query [String]      -   Additional options for the request
        """
        route = ''
        endpoint = ''
        raw_response = {}
        response = {}

        route = utils.get_route(domain=domain)
        endpoint = utils.build_endpoint(url=self.url, route=route, query=query)
        if self.debug:
            print(f"DEBUG: Endpoint: {endpoint}")
        if method.lower() == 'get':
            raw_response = requests.get(endpoint, headers=self.creds)
        if method.lower() == 'post':
            raw_response = requests.post(endpoint, headers=self.creds)

        try:
            response = raw_response.json()
        except simplejson.errors.JSONDecodeError:
            print(f"ERROR: No response for request {method} at {endpoint}")
            return None

        return response

    def __repeat_get_request_for_all_records(self,
                                             domain: str,
                                             query: str) -> dict:
        """
            Collect data records from multiple API requests in a single JSON
            data structure.

            Parameter:
                domain [str]        -   Orders/Items/..
                query  [str]        -   Additional options for the request

            Return:
                [dict]              -   API response in as javascript object
                                        notation
        """
        response = self.__plenty_api_request(method='get',
                                             domain=domain,
                                             query=query)
        if not response:
            return None

        entries = response['entries']

        while not response['isLastPage']:
            new_query = query + str(f"&page={response['page'] + 1}")
            response = self.__plenty_api_request(method='get',
                                                 domain=domain,
                                                 query=new_query)
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
                start [String]      -   Start date
                end   [String]      -   End date
                date_type [String]  -   Specify the type of date
                                        {Creation, Change, Payment, Delivery}
                additional [List]   -   Additional arguments for the query
                                        as specified in the manual
                refine [Dict]       -   Apply filters to the request
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

        query_date = utils.build_query_date(date_range=date_range,
                                            date_type=date_type)
        query_attributes = utils.build_query_attributes(domain='orders',
                                                        refine=refine,
                                                        additional=additional)
        query = utils.build_request_query(
            elements=[query_date, query_attributes])

        orders = self.__repeat_get_request_for_all_records(domain='orders',
                                                           query=query)
        if not orders:
            return {}

        if self.data_format == 'json':
            return orders

        if self.data_format == 'dataframe':
            return utils.json_to_dataframe(json=orders)

    def plenty_api_get_vat_id_mappings(self, subset: List[int] = None):
        """
            Get a mapping of all VAT configuration IDs to each country or
            if specified for a subset of countries.
            A VAT configuration is a combination of country, vat rates,
            restrictions and date range.

            Parameter:
                subset [List]   -   restrict the mappings to only the given
                                    IDs (integer)
                You can locate those IDs in your Plenty- Markets system under:
                Setup-> Orders-> Shipping-> Settings-> Countries of delivery

            Return:
                [JSON(Dict) / DataFrame] <= self.data_format
        """
        vat_data = self.__repeat_get_request_for_all_records(domain='vat',
                                                             query='')

        vat_table = utils.create_vat_mapping(data=vat_data, subset=subset)

        if self.data_format == 'json':
            return vat_table

        if self.data_format == 'dateframe':
            return utils.json_to_dataframe(json=vat_table)

    def plenty_api_get_items(self,
                             refine: dict = None,
                             additional: list = None,
                             last_update: str = '',
                             lang: str = ''):
        """
            Get product data from PlentyMarkets.

            Parameter:
                refine [dict]       -   Apply filters to the request
                                        Example:
                                        {'id': '12345', 'flagOne: '5'}
                additional [list]   -   Add additional elements to the
                                        data response.
                                        Example:
                                        ['variations', 'itemImages']
                last_update [str]   -   Date of the last update given as one
                                        of the following formats:
                                            YYYY-MM-DDTHH:MM:SS+UTC-OFFSET
                                            YYYY-MM-DDTHH:MM
                                            YYYY-MM-DD
                lang [str]          -   Provide the text within the data
                                        in one of the following languages:

                developers.plentymarkets.com/rest-doc/gettingstarted#countries

            Return:
                [JSON(Dict) / DataFrame] <= self.data_format
        """
        items = None
        query_attributes = ''
        change_date = ''
        language = ''
        query = ''

        if refine or additional:
            query_attributes = utils.build_query_attributes(
                domain='items', refine=refine, additional=additional)
        if last_update:
            change_date = utils.date_to_timestamp(date=last_update)

        if lang:
            language = utils.get_language(lang=lang)

        query = utils.build_request_query(elements=[query_attributes,
                                                    change_date,
                                                    language])

        items = self.__repeat_get_request_for_all_records(domain='items',
                                                          query=query)

        if self.data_format == 'json':
            return items

        if self.data_format == 'dataframe':
            return utils.json_to_dataframe(json=items)
