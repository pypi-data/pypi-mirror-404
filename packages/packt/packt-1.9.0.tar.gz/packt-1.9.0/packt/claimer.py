import logging
import re

from .api import (
    PACKT_API_FREE_LEARNING_CLAIM_URL,
    PACKT_API_PRODUCTS_URL,
    PACKT_PRODUCT_SUMMARY_URL
)
from .constants import PACKT_FREE_LEARNING_URL

logger = logging.getLogger("packt")


def fetch_all_books(api_client):
    limit = 250

    def fetch_all_books_with_acc(acc, offset):
        response = api_client.get(
            PACKT_API_PRODUCTS_URL,
            params={'sort': 'createdAt:desc', 'limit': limit, 'offset': offset}
        ).json()

        total = response.get('count')
        data = acc + response.get('data')

        if offset + limit > total:
            return data

        return fetch_all_books_with_acc(data, offset + limit)

    return fetch_all_books_with_acc([], 0)


def get_all_books_data(api_client):
    """Fetch all user's ebooks data."""
    logger.info("Getting your books data...")
    try:
        all_books = fetch_all_books(api_client)

        ids, my_books_data = (set(), [])
        for book in all_books:
            if book['id'] not in ids:
                ids.add(book['id'])
                my_books_data.append({'id': book['productId'], 'title': book['productName']})

        logger.info('Books data has been successfully fetched.')
        return my_books_data
    except (AttributeError, TypeError):
        logger.error('Couldn\'t fetch user\'s books data.')


def claim_product(api_client, recaptcha_solution):
    """Grab Packt Free Learning ebook."""
    logger.info("Start grabbing ebook...")

    free_learning_html = api_client.get(PACKT_FREE_LEARNING_URL).text
    offer_id_match = re.search(re.compile("offerId=\"(.*?)\""), free_learning_html)
    offer_id = offer_id_match.group(1) if offer_id_match else None

    # Handle case when there is no Free Learning offer
    if not offer_id:
        logger.info("There is no Free Learning offer right now")
        raise Exception("There is no Free Learning offer right now")

    product_id_match = re.search(re.compile("const metaProductId = \'(.*?)\';"), free_learning_html)
    product_id = product_id_match.group(1)

    product_response = api_client.get(PACKT_PRODUCT_SUMMARY_URL.format(product_id=product_id))
    product_data = {'id': product_id, 'title': product_response.json().get('data')['title']}\
        if product_response.status_code == 200 else None

    if any(product_id == book['id'] for book in get_all_books_data(api_client)):
        logger.info('You have already claimed Packt Free Learning "{}" offer.'.format(product_data['title']))
        return product_data

    claim_response = api_client.post(
        PACKT_API_FREE_LEARNING_CLAIM_URL.format(offer_id=offer_id),
        json={'recaptcha': recaptcha_solution}
    )

    if claim_response.status_code == 200:
        logger.info('A new Packt Free Learning ebook "{}" has been grabbed!'.format(product_data['title']))
    else:
        logger.error('Claiming Packt Free Learning book has failed.')

    return product_data
