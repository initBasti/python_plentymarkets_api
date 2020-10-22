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


    Set of valid parameter values from the plentymarkets REST API documentation
    https://developers.plentymarkets.com/rest-doc#
"""

VALID_DOMAINS = ['order', 'item', 'variation', 'vat', 'prices', 'manufacturer',
                 'attribute', 'referrer']
VALID_ROUTES = ['/rest/orders', '/rest/items', '/rest/items/variations',
                '/rest/vat', '/rest/items/sales_prices',
                '/rest/items/manufacturers', '/rest/items/attributes',
                '/rest/orders/referrers']
DOMAIN_ROUTE_MAP = {VALID_DOMAINS[i]: VALID_ROUTES[i]
                    for i in range(len(VALID_DOMAINS))}

# Mapping of date_type function parameter value to query parameter
# the date_type function parameter is supposed to be more descriptive
ORDER_DATE_ARGUMENTS = {
    'creation': 'created',
    'change': 'updated',
    'payment': 'paid',
    'delivery': 'outgoingItemsBooked'
}
# Refine argument keys for GET requests to filter the data
VALID_REFINE_KEYS = {
    'order': [
        'orderType', 'contactId', 'referrerId', 'shippingProfileId',
        'shippingServiceProviderId', 'ownerUserId', 'warehouseId',
        'isEbayPlus', 'includedVariation', 'includedItem', 'orderIds',
        'countryId', 'orderItemName', 'variationNumber', 'sender.contact',
        'sender.warehouse', 'receiver.contact', 'receiver.warehouse',
        'externalOrderId', 'clientId', 'paymentStatus', 'statusFrom',
        'statusTo', 'hasDocument', 'hasDocumentNumber', 'parentOrderId'
    ],
    'item': [
        'name', 'manfacturerId', 'id', 'flagOne', 'flagTwo'
    ],
    'variation': [
        'id', 'itemId', 'flagOne', 'flagTwo', 'categoryId', 'isMain',
        'isActive', 'barcode', 'referrerId', 'sku', 'date'
    ],
    'manufacturer': [
        'name'
    ]
}

# Valid additional argument values for GET requests, which are used to
# add optional data to the response body
VALID_ADDITIONAL_VALUES = {
    'order': [
        'addresses', 'relations', 'comments', 'location', 'payments',
        'documents', 'contactSender', 'contactReceiver',
        'warehouseSender', 'warehouseReceiver', 'orderItems.variation',
        'orderItems.giftCardCodes', 'orderItems.transactions',
        'orderItems.serialNumbers', 'orderItems.variationBarcodes',
        'orderItems.comments', 'originOrderReferences',
        'shippingPackages'
    ],
    'item': [
        'itemProperties', 'itemCrossSelling', 'variations', 'itemImages',
        'itemShippingProfiles', 'ebayTitles'
    ],
    'variation': [
        'properties', 'variationProperties', 'variationBarcodes',
        'variationBundleComponents', 'variationComponentBundles',
        'variationSalesPrices', 'marketItemNumbers', 'variationCategories',
        'variationClients', 'variationMarkets', 'variationDefaultCategory',
        'variationSuppliers', 'variationWarehouses', 'images', 'itemImages',
        'variationAttributeValues', 'variationSkus', 'variationAdditionalSkus',
        'unit', 'parent', 'item', 'stock'
    ],
    'manufacturer': [
        'commisions', 'externals'
    ],
    'attribute': [
        'names', 'values', 'maps'
    ]
}

VALID_LANGUAGES = [
    'bg', 'cn', 'cz', 'da', 'de', 'en', 'es', 'fr', 'it', 'nl',
    'nn', 'pl', 'pt', 'ro', 'ru', 'se', 'sk', 'tr', 'vn'
]

VALID_COUNTRY_MAP = {
    "DE": 1, "AT": 2, "BE": 3, "CH": 4, "CY": 5, "CZ": 6, "DK": 7, "ES": 8,
    "EE": 9, "FR": 10, "FI": 11, "GB": 12, "GR": 13, "HU": 14, "IT": 15,
    "IE": 16, "LU": 17, "LV": 18, "MT": 19, "NO": 20, "NL": 21, "PT": 22,
    "PL": 23, "SE": 24, "SG": 25, "SK": 26, "SI": 27, "US": 28, "AU": 29,
    "CA": 30, "CN": 31, "JP": 32, "LT": 33, "LI": 34, "MC": 35, "MX": 36,
    "IC": 37, "IN": 38, "BR": 39, "RU": 40, "RO": 41, "EA": 42,
    "BG": 44, "XZ": 45, "KG": 46, "KZ": 47, "BY": 48, "UZ": 49, "MA": 50,
    "AM": 51, "AL": 52, "EG": 53, "HR": 54, "MV": 55, "MY": 56, "HK": 57,
    "YE": 58, "IL": 59, "TW": 60, "GP": 61, "TH": 62, "TR": 63,
    "NZ": 66, "AF": 67, "AX": 68, "DZ": 69, "AS": 70, "AD": 71,
    "AO": 72, "AI": 73, "AQ": 74, "AG": 75, "AR": 76, "AW": 77, "AZ": 78,
    "BS": 79, "BH": 80, "BD": 81, "BB": 82, "BZ": 83, "BJ": 84, "BM": 85,
    "BT": 86, "BO": 87, "BA": 88, "BW": 89, "BV": 90, "IO": 91,
    "BN": 92, "BF": 93, "BI": 94, "KH": 95, "CM": 96, "CV": 97,
    "KY": 98, "CF": 99, "TD": 100, "CL": 101, "CX": 102, "CC": 103,
    "CO": 104, "KM": 105, "CG": 106, "CD": 107, "CK": 108, "CR": 109,
    "CI": 110, "CU": 112, "DJ": 113, "DM": 114, "DO": 115, "EC": 116,
    "SV": 117, "GQ": 118, "ER": 119, "ET": 120, "FK": 121, "FO": 122,
    "FJ": 123, "GF": 124, "PF": 125, "TF": 126, "GA": 127, "GM": 128,
    "GE": 129, "GH": 130, "GI": 131, "GL": 132, "GD": 133, "GU": 134,
    "GT": 135, "GG": 136, "GN": 137, "GW": 138, "GY": 139, "HT": 140,
    "HM": 141, "VA": 142, "HN": 143, "IS": 144, "ID": 145, "IR": 146,
    "IQ": 147, "IM": 148, "JM": 149, "JE": 150, "JO": 151, "KE": 152,
    "KI": 153, "KP": 154, "KR": 155, "KW": 156, "LA": 158, "LB": 159,
    "LS": 160, "LR": 161, "LY": 162, "MO": 163, "MK": 164, "MG": 165,
    "MW": 166, "ML": 168, "MH": 169, "MQ": 170, "MR": 171, "MU": 172,
    "YT": 173, "FM": 174, "MD": 175, "MN": 176, "ME": 177, "MS": 178,
    "MZ": 179, "MM": 180, "NA": 181, "NR": 182, "NP": 183, "AN": 184,
    "NC": 185, "NI": 186, "NE": 187, "NG": 188, "NU": 189, "NF": 190,
    "MP": 191, "OM": 192, "PK": 193, "PW": 194, "PS": 195, "PA": 196,
    "PG": 197, "PY": 198, "PE": 199, "PH": 200, "PN": 201, "PR": 202,
    "QA": 203, "RE": 204, "RW": 205, "SH": 206, "KN": 207, "LC": 208,
    "PM": 209, "VC": 210, "WS": 211, "SM": 212, "ST": 213, "SA": 214,
    "SN": 215, "RS": 216, "SC": 217, "SL": 218, "SB": 219, "SO": 220,
    "ZA": 221, "GS": 222, "LK": 223, "SD": 224, "SR": 225, "SJ": 226,
    "SZ": 227, "SY": 228, "TJ": 229, "TZ": 230, "TL": 231, "TG": 232,
    "TK": 233, "TO": 234, "TT": 235, "TN": 236, "TM": 237, "TC": 238,
    "TV": 239, "UG": 240, "UA": 241, "UM": 242, "UY": 243, "VU": 244,
    "VE": 245, "VN": 246, "VG": 247, "VI": 248, "WF": 249, "EH": 250,
    "ZM": 252, "ZW": 253, "AE": 254, "CUW": 258, "SXM": 259,
    "BES": 260, "BL": 261
}
