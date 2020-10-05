# Overview

Interface for the PlentyMarkets API.

# Setup

## Requirements

* Python 3.7.8+

## Installation

Install it directly into an activated virtual environment:

```text
$ pip install python_plenty_api
```

or add it to your [Poetry](https://poetry.eustace.io/) project:

```text
$ poetry add plenty_api
```

# Usage

After installation, the package can imported:

```text
$ python
>>> import plenty_api
>>> plenty_api.__version__
```
## Examples

```
import plenty_api

def main():
    # Get the bearer token and set the basic attributes for an endpoint
    plenty = plenty_api.PlentyApi(base_url='https://{your-shop}.plentymarkets-cloud01.com',  # available under setup->settings->API->data
                                  use_keyring=True,  # Save the credentials into your system wide Keyring or not
                                  data_format='json',  # Choose the output format (default JSON)
                                  debug=True)  # display the constructed endpoint before making the request

    orders = plenty.plenty_api_get_orders_by_date(start='2020-09-20',
                                                  end='2020-09-24',
                                                  date_type='payment',  # Get orders that were payed in between [start] and [end]
                                                  additional=['documents', 'locations'],  # Include additional attributes to the response
                                                  refine={'orderType': '1', 'referrerId': '1'})  # Only get orders with type 1 and from referrer 1

if __name__ == '__main__':
    main()
```

# Contact

Author: Sebastian Fricke, Company: Panasiam, Email: sebastian.fricke.linux@gmail.com
