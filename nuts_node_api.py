"""A simple python client for the nuts.nl nuts-node API"""
import json
import requests

from base64 import b64decode
from functools import lru_cache
from hashlib import sha256


# This should be defined by the user before calling functions in this module
base_url = None


def _url(path: str):
    return f'{base_url}{path}'


@lru_cache
def ref(index: int) -> str:
    """Return the ref (digest) for a given transaction index"""
    return refs()[index]


@lru_cache
def refs() -> list[str]:
    """Return all known transaction refs (digests) in order"""
    url = _url('/internal/network/v1/transaction')

    # TODO: A more efficient way to get transaction refs should be found
    # and it should likely include pagination
    transactions = requests.get(url).json()

    # Build a list of refs by iterating over the known transactions in order
    refs = []
    for transaction in transactions:
        # Calculate the ref (digest) for this transaction
        #
        # TODO: Currently the ref must be calculated client side as it is
        # not returned by the server
        ref = sha256(transaction.encode('utf-8')).hexdigest()

        # Append this ref to the list of known refs, making this function an
        # iterator
        refs.append(ref)

    # Return the transaction refs
    return refs


@lru_cache
def transaction(ref) -> dict:
    """Return the data about the specified transaction"""
    # Build the URL for the API call
    url = _url(f'/internal/network/v1/transaction/{ref}')

    # Fetch and parse the specified transaction
    response = requests.get(url)

    # The data we are after is the first component of the transaction.
    # This is base64 encoded JSON, which needs to be parsed.
    details = json.loads(b64decode(response.text.split('.')[0] + '=='))

    # Add the ref value if not already present in the transaction data
    if 'ref' not in details:
        details['ref'] = ref

    # Return the transaction data fields
    return details


@lru_cache
def transaction_count():
    # The server diagnostics endpoint of the nuts-node software contains
    # the total number of transactions known on the network
    url = _url('/status/diagnostics')
    response = requests.get(url, headers={'accept': 'application/json'})
    return response.json()['network']['state']['transaction_count']


def cache_clear():
    """Clear the cache used by API functions"""
    ref.cache_clear()
    refs.cache_clear()
    transaction.cache_clear()
    transaction_count.cache_clear()
