"""Module with Packt API client handling API's authentication."""
import logging

import requests

PACKT_API_LOGIN_URL = 'https://www.packtpub.com/api/login'
PACKT_API_PRODUCTS_URL = 'https://www.packtpub.com/api/entitlements/users/me/owned'
PACKT_PRODUCT_SUMMARY_URL = 'https://subscription.packtpub.com/api/products/{product_id}/summary'
PACKT_API_PRODUCT_FILE_TYPES_URL = 'https://services.packtpub.com/products-v1/products/{product_id}/types'
PACKT_API_PRODUCT_FILE_DOWNLOAD_URL =\
    'https://services.packtpub.com/products-v1/products/{product_id}/files/{file_type}'
PACKT_API_FREE_LEARNING_CLAIM_URL = 'https://www.packtpub.com/api/claim-free-learning/offers/{offer_id}'

logger = logging.getLogger("packt")


class PacktAPIClient:
    """Packt API client making API requests on script's behalf."""

    def __init__(self, credentials):
        self.session = requests.Session()
        self.credentials = credentials
        self.fetch_jwt()

    def fetch_jwt(self):
        """Fetch user's JWT to be used when making Packt API requests."""
        try:
            response = self.post(PACKT_API_LOGIN_URL, json=self.credentials)
            jwt = response.json().get('data').get('tokens').get('access')
            self.session.headers.update({'authorization': 'Bearer {}'.format(jwt)})
            logger.info('JWT token has been fetched successfully!')
        except Exception:
            logger.error('Fetching JWT token failed!')

    def request(self, method, url, **kwargs):
        """Make a request to a Packt API."""
        response = self.session.request(method, url, **kwargs)
        if response.status_code == 401:
            # Fetch a new JWT as the old one has expired and update session headers
            self.fetch_jwt()
            return self.session.request(method, url, **kwargs)
        else:
            return response

    def get(self, url, **kwargs):
        """Make a GET request to a Packt API."""
        return self.request('get', url, **kwargs)

    def post(self, url, **kwargs):
        """Make a POST request to a Packt API."""
        return self.request('post', url, **kwargs)

    def put(self, url, **kwargs):
        """Make a PUT request to a Packt API."""
        return self.request('put', url, **kwargs)

    def patch(self, url, **kwargs):
        """Make a PATCH request to a Packt API."""
        return self.request('patch', url, **kwargs)

    def delete(self, url, **kwargs):
        """Make a DELETE request to a Packt API."""
        return self.request('delete', url, **kwargs)
