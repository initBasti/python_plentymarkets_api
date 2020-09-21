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

import requests
import simplejson
from typing import List

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
            print("unlock @ Setup->settings->accounts->go to user->unlock login")
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

    def plenty_api_get_orders_by_date(self, start, end, date_type='create',
                                      additional=''):
        """
            Get all orders within a specific date range.

            Parameter:
                start [String]      -   Start date
                end   [String]      -   End date
                date_type [String]  -   Specify the type of date
                                        {Creation, Change, Payment, Delivery}
                additional [List]   -   Additional arguments for the query
                                        as specified in the manual

            Return:
                [JSON(Dict) / DataFrame] <= self.data_format
        """
        date_range = utils.build_date_range(start=start, end=end)
        if not date_range:
            print(f"ERROR: Invalid range {start} -> {end}")

        if not utils.check_date_range(date_range=date_range):
            print(f"ERROR: {date_range['start']} -> {date_range['end']}")
            return None

        query = utils.build_date_request_query(date_range=date_range,
                                               date_type=date_type,
                                               additional=additional)

        response = self.__plenty_api_request(method='get',
                                             domain='orders',
                                             query=query)
        if not response:
            return None

        orders = response['entries']

        while not response['isLastPage']:
            new_query = query + str(f"&page={response['page'] + 1}")
            response = self.__plenty_api_request(method='get',
                                                 domain='orders',
                                                 query=new_query)
            if not response:
                print("ERROR: subsequent API calls failed.")
                return None

            orders += response['entries']

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
        response = self.__plenty_api_request(method='get',
                                             domain='vat',
                                             query='')
        if not response:
            return None

        vat_data = response['entries']

        while not response['isLastPage']:
            new_query = str("?page={response['page'] + 1}")
            response = self.__plenty_api_request(method='get',
                                                 domain='vat',
                                                 query=new_query)
            if not response:
                print("ERROR: subsequent API calls failed.")
                return None

            vat_data += response['entries']

        vat_table = utils.create_vat_mapping(data=vat_data, subset=subset)

        if self.data_format == 'json':
            return vat_table

        if self.data_format == 'dateframe':
            return utils.json_to_dataframe(json=vat_table)
