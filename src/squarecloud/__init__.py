"""Official Python SDK for the Square Cloud API.

Create a client with your API key and call the API through its groups::

    import os
    from squarecloud import SquareCloud

    with SquareCloud(os.environ["SQUARECLOUD_API_KEY"]) as client:
        account = client.account.me()

Use :class:`AsyncSquareCloud` with ``async with`` in asyncio code. Every
failed call raises :class:`SquareCloudAPIError`.
"""

from . import types
from .client import (
    BASE_URL,
    AsyncRealtime,
    AsyncSquareCloud,
    HTTPTransport,
    Realtime,
    Response,
    SquareCloud,
    Transport,
    __version__,
)
from .errors import SquareCloudAPIError

__all__ = [
    'BASE_URL',
    'AsyncRealtime',
    'AsyncSquareCloud',
    'HTTPTransport',
    'Realtime',
    'Response',
    'SquareCloud',
    'SquareCloudAPIError',
    'Transport',
    '__version__',
    'types',
]
