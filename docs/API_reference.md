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
