# Python PlentyMarkets API interface

## Reference

- [Login](#login)
    + [GPG encrypted password file workflow](#gpg_workflow)
- [GET-Requests](#get-requests)
    + [Order related data](#get-order-section)
        * [get orders by date](#get-orders-by-date)
    + [get referrers](#get-referrers)
    + [Item related data](#get-items-section)
        * [get items](#get-items)
        * [get variations](#get-variations)
        * [get attributes](#get-attributes)
        * [get prices](#get-prices)
        * [get manufacturers](#get-manufacturers)
    + [Tax related data](#get-taxes-section)
        * [get vat id mappings](#get-vat-mappings)
- [POST-Requests](#post-requests)
    + [Item related data](#post-items-section)
        * [post image avaialability](#post-image-availability)
        * [post items](#post-items)
        * [post variations](#post-variations)
        * [post attributes](#post-attributes)
        * [post attribute names](#post-attribute-names)
        * [post attribute values](#post-attribute-values)
        * [post attribute value names](#post-attribute-value-names)

### LOGIN <a name='login'></a>

The login request is sent automatically, as soon as the object is instantiated. There are three methods of providing credentials.

1. Providing them over STDIN [Usually only useful for testing on someone else's machine]
    + Activated by creating the `PlentyApi` object, with the option `use_keyring=False`
2. Enter the credentials once per STDIN and save them into a keyring [Very convenient for commands that are started manually doesn't work for cronjobs]
    + Activated by creating the `PlentyApi` object, with the option `use_keyring=True` (True is the default)
3. Provide the username as an argument and a path to a GPG encrypted file for the password [Works for cronjobs and manual running]
    + Activated by creating the `PlentyApi` object with the arguments, `username={REST-API username}` and `password={path to GPG encrypted file containing the REST-API password}`

#### Example for a GPG encrypted file workflow (on Linux) <a name='gpg_workflow'></a>

The idea behind the GnuPG encrypted file is to simply write the password
of the Plentymarkets REST API user into a `.txt` file and to encrypt that file.
`plenty_api` is then going to decrypt it during authentication and
read the password.
With the username and password, `plenty_api` can then receive an Oauth2
bearer token to be used for authentication.

Here is an example (on Linux):
```
# With a preceding space to skip entering the line into the bash history
  echo "password" > pw.txt
gpg --encrpyt --sign --recipient gpg-key@email.com pw.txt
```

Within python:
```
api = plenty_api.PlentyApi(
        base_url='https://company.plentymarkets-cloud01.com',
        username='api_user',
        password='/home/user/pw.txt.gpg')
```

This will try to access your gpg key through your gpg agent, which manages
access to the key.

In some cases, you might want to increase the time until the passphrase
times out (in which case you would have to enter the password again).
This is how you can modify the time:
```
echo -e "default-cache-ttl 18000\nmax-cache-ttl 86400\nignore-cache-for-signing" >> ~/.gnupg/gpg-agent.conf
chmod 600 ~/.gnupg/gpg-agent.conf
```
This will set the default timeout time for a passphrase to 18000s (5h)
and the maximum timeout time to 86400s (24h) (meaning even if you use
the key multiple times during the 24h, after 24h you will have to enter
the password again).

### GET requests: <a name='get-requests'></a>

#### Orders <a name='get-order-section'></a>

##### plenty_api_get_orders_by_date: <a name='get-orders-by-date'></a>

[*Required parameter*]:

Fetch orders within a specified range of two dates, there are 4 different types of date-types:
- Creation [date and time when the order was created on PlentyMarkets]
- Change   [date and time of the last change, within the order]
- Payment  [date and time when the payment was either automatically received by the order or assigned to the order]
- Delivery [date and time of the removal of products from the stock of the shipping warehouse]

The dates are accepted in the following formats:
- YEAR-MONTH-DAY                                    (2020-09-16)        [ISO 8601 date format]
- YEAR-MONTH-DAYTHOUR:MINUTE                        (2020-09-16T08:00)
- YEAR-MONTH-DAYTHOUR:MINUTE:SECOND+UTC-OFFSET      (2020-09-16T08:00)  [W3C date format]

[*Optional parameter*]:

The **additional** field expects a list of strings, valid values are:  
'addresses', 'relations', 'comments', 'location', 'payments', 'documents', 'contactSender'
'contactReceiver', 'warehouseSender', 'warehouseReceiver', 'orderItems.variation', 'orderItems.giftCardCodes'
'orderItems.transactions', 'orderItems.serialNumbers', 'orderItems.variationBarcodes', 'orderItems.comments',
'originOrderReferences' 'shippingPackages'

The **refine** field can be used to filter the request results by some aspect of the orders.
The field expects a dictionary, where the key has to match one of the following fields:  
orderType, contactId, referrerId, shippingProfileId, shippingServiceProviderId, ownerUserId, warehouseId, isEbayPlus, includedVariation, includedItem, orderIds, countryId, orderItemName, variationNumber, sender.contact, sender.warehouse, receiver.contact, receiver.warehouse, externalOrderId, clientId, paymentStatus, statusFrom, statusTo, hasDocument, hasDocumentNumber, parentOrderId  
For more information about the valid values: [Plenty Developer Documentation](https://developers.plentymarakets.com/rest-doc#/Order/get_rest_orders)

[*Output format*]:

There are currently two supported output formats: 'json' and 'dataframe'.  
The 'json' format simply returns the raw response, without page information and with multiple pages combined into a single data structure.  
The 'dataframe' format transforms that data structure into a pandas DataFrame, which contains subparts in json, that can be split further by the user application.

---

##### plenty_api_get_referrers: <a name='get-referrers'></a>

Fetch all referrers from PlentyMarkets, they contain the following attributes:
'backendName', 'id', 'isEditable', 'isFilterable', 'name', 'orderOwnderId', 'origin'

[*Optional parameter*]:

The **column** parameter limits the response body to the values of a single column. This is actually only useful for 'name', 'id' & 'backendName', but for the sake of completeness the rest is included as well.

[*Output format*]:

There are currently two supported output formats: 'json' and 'dataframe'.  
The 'json' format simply returns the raw response, without page information and with multiple pages combined into a single data structure.  
The 'dataframe' format transforms that data structure into a pandas DataFrame, which contains subparts in json, that can be split further by the user application.

---
---

#### Item data <a name='get-items-section'></a>

##### plenty_api_get_items: <a name='get-items'></a>

[*Optional parameter*]:

The **refine** field can be used to filter the request results by one or more of the attributes of the item:  
id, name, manufacturer, flagOne, flagTwo

Use the **additional** field to add more values to the response, valid values are:  
properties, variations, itemCrossSelling, itemProperties, itemImages, itemShippingProfiles, ebayTitles

With the **last_update** parameter, you can filter the results down to items that were changed at or after the specified date  
The dates are accepted in the following formats:
- YEAR-MONTH-DAY                                    (2020-09-16)        [ISO 8601 date format]
- YEAR-MONTH-DAYTHOUR:MINUTE                        (2020-09-16T08:00)
- YEAR-MONTH-DAYTHOUR:MINUTE:SECOND+UTC-OFFSET      (2020-09-16T08:00)  [W3C date format]

The **lang** field specifies the language of the texts used in the response. Valid values are country abbreviations in ISO-3166-1:  
[List of countries](https://developers.plentymarkets.com/rest-doc/gettingstarted#countries)

[*Output format*]:

There are currently two supported output formats: 'json' and 'dataframe'.  
The 'json' format simply returns the raw response, without page information and with multiple pages combined into a single data structure.  
The 'dataframe' format transforms that data structure into a pandas DataFrame, which contains subparts in json, that can be split further by the user application.

---

##### plenty_api_get_variations: <a name='get-variations'></a>

[*Optional parameter*]:

The **refine** field can be used to filter the request results by one or more of the attributes of the variation:  
id, itemId, flagOne, flagTwo, categoryId, isMain, isActive, barcode, referrerId, sku, date

Use the **additional** field to add more values to the response, valid values are:  
properties, variationProperties, variationBarcodes, variationBundleComponents, variationComponentBundles, variationSalesPrices, marketItemNumbers, variationCategories,
variationClients, variationMarkets, variationDefaultCategory, variationSuppliers, variationWarehouses, images, itemImages, variationAttributeValues, variationSkus,
variationAdditionalSkus, unit, parent, item, stock

The **lang** field specifies the language of the texts used in the response. Valid values are country abbreviations in ISO-3166-1:  
[List of countries](https://developers.plentymarkets.com/rest-doc/gettingstarted#countries)

[*Output format*]:

There are currently two supported output formats: 'json' and 'dataframe'.  
The 'json' format simply returns the raw response, without page information and with multiple pages combined into a single data structure.  
The 'dataframe' format transforms that data structure into a pandas DataFrame, which contains subparts in json, that can be split further by the user application.

---

##### plenty_api_get_attributes: <a name='get-attributes'></a>

List all the attributes from PlentyMarkets (size, color etc.), additionally there is an option to link variations from the PlentyMarkets system to the attribute values.

[*Optional parameter*]:

Use the **additional** field to add more values to the response, valid values are:  
names, values, maps

With the **last_update** parameter, you can filter the results down to items that were changed at or after the specified date  
The dates are accepted in the following formats:
- YEAR-MONTH-DAY                                    (2020-09-16)        [ISO 8601 date format]
- YEAR-MONTH-DAYTHOUR:MINUTE                        (2020-09-16T08:00)
- YEAR-MONTH-DAYTHOUR:MINUTE:SECOND+UTC-OFFSET      (2020-09-16T08:00)  [W3C date format]

Finally, the **variation_map** parameter, performs an additional request to pull all variations in order to link them to the attribute values. Depending on the size of your
PlentyMarkets system, this can take a few seconds and consume some API calls.

[*Output format*]:

There are currently two supported output formats: 'json' and 'dataframe'.  
The 'json' format simply returns the raw response, without page information and with multiple pages combined into a single data structure.  
The 'dataframe' format transforms that data structure into a pandas DataFrame, which contains subparts in json, that can be split further by the user application.

---

##### plenty_api_get_price_configuration: <a name='get-prices'></a>

Fetch price configuration from PlentyMarkets, this can be used among other things to get the ID of a price used by a specific referrer in order to get the price date from variations.

[*Optional parameter*]:

You can reduce the response data to just IDs and names by using the **minimal** parameter (*True/False*).
And you can filter out price configurations, where the last change timestamp is further in the past than the specified date from the **last_change** parameter.
The dates are accepted in the following formats:
- YEAR-MONTH-DAY                                    (2020-09-16)        [ISO 8601 date format]
- YEAR-MONTH-DAYTHOUR:MINUTE                        (2020-09-16T08:00)
- YEAR-MONTH-DAYTHOUR:MINUTE:SECOND+UTC-OFFSET      (2020-09-16T08:00)  [W3C date format]

[*Output format*]:

There are currently two supported output formats: 'json' and 'dataframe'.  
The 'json' format simply returns the raw response, without page information and with multiple pages combined into a single data structure.  
The 'dataframe' format transforms that data structure into a pandas DataFrame, which contains subparts in json, that can be split further by the user application.

---

##### plenty_api_get_manufacturers: <a name='get-manufacturers'></a>

Fetch a list of manufacturers, that were setup on PlentyMarkets.

[*Optional parameter*]:

The **refine** field can be used to reduce the request to only manufacturers with the given name.
example: refine={'name': 'abc_company'}

Use the **additional** field to add more values to the response, valid values are:  
commisions, externals

With the **last_update** parameter, you can filter the results down to items that were changed at or after the specified date  
The dates are accepted in the following formats:
- YEAR-MONTH-DAY                                    (2020-09-16)        [ISO 8601 date format]
- YEAR-MONTH-DAYTHOUR:MINUTE                        (2020-09-16T08:00)
- YEAR-MONTH-DAYTHOUR:MINUTE:SECOND+UTC-OFFSET      (2020-09-16T08:00)  [W3C date format]

[*Output format*]:

There are currently two supported output formats: 'json' and 'dataframe'.  
The 'json' format simply returns the raw response, without page information and with multiple pages combined into a single data structure.  
The 'dataframe' format transforms that data structure into a pandas DataFrame, which contains subparts in json, that can be split further by the user application.

---
---

#### Tax data <a name='get-tax-section'></a>

##### plenty_api_get_vat_id_mappings: <a name='get-vat-mappings'></a>

Create a mapping of all the different VAT configurations, which map to a country ID together with the Tax ID.

[*Optional parameter*]:

**subset**: supply a list of integer country IDs to limit the data to a specific set of countries

[*Output format*]:

Return a dictionary with the country IDs as keys and the corresponding VAT configuration IDs + the TaxID as value.

### POST requests: <a name='post-requests'></a>

#### Items <a name='post-items-section'></a>

##### plenty_api_set_image_availability: <a name='post-image-availability'></a>

[*Required parameter:*]:

The **item_id** field contains the Item ID used in PlentyMarkets.  
With the **image_id** field, the exact image is specified. It is rather hard to obtain, that ID directly from PlentyMarkets. Your best bet is probably to make a `plenty_api_get_items(additional=['itemImages'])` call and use the ID from there.  
In the **target** field you have to specify:  
    * What kind of target to connect
    * The ID of the target
Examples:  
{'marketplace': 1}, {'mandant': 41444}, {'listing': 2}

##### plenty_api_create_items: <a name='post-items'></a>

Create one or more items on Plentymarkets, but do not create the variations for it. This call requires at least a valid category ID and a valid unit type. Additionally, you are able to specify more details for the main variation (virtual doesn't represent a physical product).

[*Required parameter*]:

The **json** field contains either a list of json objects (dictionaries) or a single json object. Please refer to [Plentymarkets Dev documentation: REST API POST items](https://developers.plentymarkets.com/en-gb/plentymarkets-rest-api/index.html#/Item/post_rest_items), for a list of valid attributes.

[*Example*]:
```json
{
    "position": 2,
    "manufacturerId": 1,
    "variations": [
        {
            "name": "test_main_variation",
            "variationCategories": [
                {
                    "categoryId": 400
                }
            ],
            "unit": {
                "unitId": 1,
                "content": 1
            }
        }
    ]
}
```

[*Output format*]:

Return a list of POST request JSON responses, if one of the requests fails return the error message.
When the JSON object doesn't contain the required attributes the method will return: `{'error': 'invalid_json'}`.

#### plenty_api_create_variations <a name='post-variations'></a>

Create a variation for a specific item on Plentymarkets.

[*Required parameter*]:

The **item_id** field contains the ID given to the item by Plentymarkets, the **json** field contains a single JSON object or a list of JSON objects describing a variation.
Please refer to [Plentymarkets Dev documentation: REST API POST items](https://developers.plentymarkets.com/en-gb/plentymarkets-rest-api/index.html#/Item/post_rest_items__itemId__variations), for a list of valid attributes.

[*Example*]:
```json
{
    'isMain': False,
    'isActive': True,
    'availability': 1,
    'number': 'test1234',
    'unit': {'unitId': 1, 'content': 1},
    'variationAttributeValues': [
        {'valueId': 13}, {'valueId': 17}
    ],
    'variationCategories': [{'categoryId': 21}],
    'variationBarcodes': [{'code': '1234567891011', 'barcodeId': 1}],
    "variationClients": [{"plentyId": 54017}]
},
```

[*Output format*]:

Return a list of POST request JSON responses, if one of the requests fails return the error message.
When the JSON object doesn't contain the required attributes the method will return: `{'error': 'invalid_json'}`.
If the **item_id** field is not filled the method will return: `{'error': 'missing_parameter'}`.

#### plenty_api_create_attribute <a name='post-attributes'></a>

Create a new attribute on Plentymarkets.

[*Required parameter*]:

The **json** parameter contains a single JSON object describing an attribute
Please refer to [Plentymarkets Dev documentation: REST API POST attributes](https://developers.plentymarkets.com/en-gb/plentymarkets-rest-api/index.html#/Item/post_rest_items_attributes), for a list of valid attributes.

[*Example*]:
```json
{
    'backendName': 'Material',
    'position': 3,
    'isLinkableToImage': False,
    'amazonAttribute': 'outer_material_type',
    'isGroupable': False
}
```

[*Output format*]:

Return a POST request JSON response, if one of the requests fails return the error message.
When the JSON object doesn't contain the required attributes the method will return: `{'error': 'invalid_json'}`.

#### plenty_api_create_attribute_name

Create an attribute name for a specific attribute on Plentymarkets.

[*Required parameter*]:

The **attribute_id** parameter contains the ID given to the attribute by Plentymarkets, the **lang** parameter contains a two letter abbreviation of the target language (for a list of valid values look here: [Language codes](https://developers.plentymarkets.com/en-gb/developers/main/rest-api-guides/getting-started.html#_language_codes)), and the **name** parameter contains the visible name for the attribute in the given language.
Please refer to [Plentymarkets Dev documentation: REST API POST attribute names](https://developers.plentymarkets.com/en-gb/plentymarkets-rest-api/index.html#/Item/post_rest_items_attributes__attributeId__names), for a list of valid attributes.

[*Output format*]:

Return a POST request JSON response, if one of the requests fails return the error message.
If the **attribute_id** field is not filled the method will return: `{'error': 'missing_parameter'}`.
In case the language within the **lang** parameter is invalid the method will return `{'error': 'invalid_language'}`.

#### plenty_api_create_attribute_values <a name='post-attribute-values'></a>

Create one or more attribute values for a specific attribute on Plentymarkets.

[*Required parameter*]:

The **attribute_id** parameter contains the ID given to the attribute by Plentymarkets, the **json** parameter contains a single JSON object or a list of JSON objects describing an attribute value.
Please refer to [Plentymarkets Dev documentation: REST API POST attribute values](https://developers.plentymarkets.com/en-gb/plentymarkets-rest-api/index.html#/Item/post_rest_items_attributes__attributeId__values), for a list of valid attributes.

[*Example*]:
```json
{
    'backendName': 'Cotton',
    'amazonValue': 'Cotton',
    'position': 2
},
```
Only `backendName` is a required field.

[*Output format*]:

Return a POST request JSON response, if one of the requests fails return the error message.
When the JSON object doesn't contain the required attributes the method will return: `{'error': 'invalid_json'}`.
If the **attribute_id** field is not filled the method will return: `{'error': 'missing_parameter'}`.

#### plenty_api_create_attribute_value_name

Create an attribute value name for a specific attribute value on Plentymarkets.

[*Required parameter*]:

The **value_id** parameter contains the ID given to the attribute value by Plentymarkets, the **lang** parameter contains a two letter abbreviation of the target language (for a list of valid values look here: [Language codes](https://developers.plentymarkets.com/en-gb/developers/main/rest-api-guides/getting-started.html#_language_codes)), and the **name** parameter contains the visible name for the attribute value in the given language.
Please refer to [Plentymarkets Dev documentation: REST API POST attribute value names](https://developers.plentymarkets.com/en-gb/plentymarkets-rest-api/index.html#/Item/post_rest_items_attribute_values__valueId__names), for a list of valid attributes.

[*Output format*]:

Return a POST request JSON response, if one of the requests fails return the error message.
If the **value_id** field is not filled the method will return: `{'error': 'missing_parameter'}`.
In case the language within the `lang` field of the JSON is invalid the method will return `{'error': 'invalid_language'}`.
