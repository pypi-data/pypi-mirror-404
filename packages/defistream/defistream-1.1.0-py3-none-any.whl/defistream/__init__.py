"""
DeFiStream Python Client

Official Python client for the DeFiStream API.

Example:
    >>> from defistream import DeFiStream
    >>> client = DeFiStream(api_key="dsk_...")
    >>>
    >>> # Builder pattern - returns pandas DataFrame
    >>> df = (
    ...     client.erc20.transfers("USDT")
    ...     .network("ETH")
    ...     .block_range(21000000, 21010000)
    ...     .as_df()
    ... )
    >>>
    >>> # Save to file
    >>> query.as_file("transfers.parquet")
"""

from .client import AsyncDeFiStream, DeFiStream
from .exceptions import (
    AuthenticationError,
    DeFiStreamError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .query import AsyncQueryBuilder, QueryBuilder

__version__ = "1.1.0"

__all__ = [
    # Clients
    "DeFiStream",
    "AsyncDeFiStream",
    # Query builders
    "QueryBuilder",
    "AsyncQueryBuilder",
    # Exceptions
    "DeFiStreamError",
    "AuthenticationError",
    "QuotaExceededError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
]
