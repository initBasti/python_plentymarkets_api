# Python PlentyMarkets API interface

## Reference

### GET requests:

#### Orders

##### plenty_api_get_orders_by_date:

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
The 'dataframe' format transforms that data structure into a pandas DataFrame, which contains sub parts in json, that can be split further by the user application.

#### Item data

##### plenty_api_get_items:

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
The 'dataframe' format transforms that data structure into a pandas DataFrame, which contains sub parts in json, that can be split further by the user application.

#### Tax data

##### plenty_api_get_vat_id_mappings:

Create a mapping of all the different VAT configurations, which map to a country ID together with the Tax ID.

[*Optional parameter*]:

**subset**: supply a list of integer country IDs to limit the data to a specific set of countries

[*Output format*]:

Return a dictionary with the country IDs as keys and the corresponding VAT configuration IDs + the TaxID as value.

### POST requests:

#### plenty_api_set_image_availability:

[*Required parameter:*]:

The **item_id** field contains the Item ID used in PlentyMarkets.  
With the **image_id** field, the exact image is specified. It is rather hard to obtain, that ID directly from PlentyMarkets. Your best bet is probably to make a `plenty_api_get_items(additional=['itemImages'])` call and use the ID from there.  
In the **target** field you have to specify:  
    * What kind of target to connect
    * The ID of the target
Examples:  
{'marketplace': 1}, {'mandant': 41444}, {'listing': 2}
