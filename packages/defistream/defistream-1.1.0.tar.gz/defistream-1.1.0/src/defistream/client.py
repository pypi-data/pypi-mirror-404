"""DeFiStream API client."""

from __future__ import annotations

import os
from typing import Any, Literal

import httpx

from .exceptions import (
    AuthenticationError,
    DeFiStreamError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import ResponseMetadata
from .protocols import (
    AAVEProtocol,
    AsyncAAVEProtocol,
    AsyncERC20Protocol,
    AsyncLidoProtocol,
    AsyncNativeTokenProtocol,
    AsyncStaderProtocol,
    AsyncThresholdProtocol,
    AsyncUniswapProtocol,
    ERC20Protocol,
    LidoProtocol,
    NativeTokenProtocol,
    StaderProtocol,
    ThresholdProtocol,
    UniswapProtocol,
)

DEFAULT_BASE_URL = "https://api.defistream.dev/v1"
DEFAULT_TIMEOUT = 60.0


class BaseClient:
    """Base client with shared functionality."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ):
        # Read API key from argument or environment
        self.api_key = api_key or os.environ.get("DEFISTREAM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Pass api_key or set DEFISTREAM_API_KEY environment variable."
            )

        self.base_url = (base_url or os.environ.get("DEFISTREAM_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.last_response: ResponseMetadata = ResponseMetadata()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "X-API-Key": self.api_key,  # type: ignore
            "Accept": "application/json",
        }

    def _parse_response_metadata(self, headers: httpx.Headers) -> ResponseMetadata:
        """Parse rate limit and quota info from response headers."""
        return ResponseMetadata(
            rate_limit=int(headers.get("X-RateLimit-Limit", 0)) or None,
            quota_remaining=int(headers.get("X-RateLimit-Remaining", 0)) or None,
            request_cost=int(headers.get("X-Request-Cost", 0)) or None,
        )

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses."""
        status_code = response.status_code

        try:
            data = response.json()
            message = data.get("error", data.get("message", response.text))
            error_code = data.get("code", "")
        except Exception:
            message = response.text
            error_code = ""

        if status_code == 401:
            raise AuthenticationError(message, status_code, response)

        if status_code == 403:
            if error_code == "quota_exceeded":
                # Try to extract remaining quota from response
                remaining = 0
                try:
                    remaining = int(data.get("remaining", 0))
                except (ValueError, TypeError):
                    pass
                raise QuotaExceededError(message, remaining=remaining, status_code=status_code, response=response)
            raise AuthenticationError(message, status_code, response)

        if status_code == 404:
            raise NotFoundError(message, status_code, response)

        if status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                retry_after=float(retry_after) if retry_after else None,
                status_code=status_code,
                response=response,
            )

        if status_code == 400:
            raise ValidationError(message, status_code, response)

        if status_code >= 500:
            raise ServerError(message, status_code, response)

        raise DeFiStreamError(message, status_code, response)

    def _process_response(
        self,
        response: httpx.Response,
        as_dataframe: Literal["pandas", "polars"] | None = None,
        output_file: str | None = None,
    ) -> list[dict[str, Any]] | Any:
        """Process response and optionally convert to DataFrame or save to file."""
        self.last_response = self._parse_response_metadata(response.headers)

        if response.status_code >= 400:
            self._handle_error_response(response)

        content_type = response.headers.get("Content-Type", "")

        # Handle file output
        if output_file:
            if output_file.endswith(".parquet"):
                with open(output_file, "wb") as f:
                    f.write(response.content)
            else:
                with open(output_file, "w") as f:
                    f.write(response.text)
            return None

        # Handle CSV response
        if "text/csv" in content_type:
            csv_text = response.text
            if as_dataframe == "pandas":
                import io
                import pandas as pd
                return pd.read_csv(io.StringIO(csv_text))
            elif as_dataframe == "polars":
                import io
                import polars as pl
                return pl.read_csv(io.StringIO(csv_text))
            return csv_text

        # Handle Parquet response
        if "application/octet-stream" in content_type or "application/parquet" in content_type:
            if as_dataframe == "pandas":
                import io
                import pandas as pd
                df = pd.read_parquet(io.BytesIO(response.content))
                if "time" in df.columns:
                    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
                return df
            elif as_dataframe == "polars":
                import io
                import polars as pl
                df = pl.read_parquet(io.BytesIO(response.content))
                if "time" in df.columns:
                    df = df.with_columns(
                        pl.from_epoch("time", time_unit="s").dt.replace_time_zone("UTC")
                    )
                return df
            return response.content

        # Handle JSON response
        data = response.json()

        if data.get("status") == "error":
            raise DeFiStreamError(data.get("error", "Unknown error"))

        events = data.get("events", [])

        if as_dataframe == "pandas":
            import pandas as pd
            df = pd.DataFrame(events)
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
            return df
        elif as_dataframe == "polars":
            import polars as pl
            df = pl.DataFrame(events)
            if "time" in df.columns:
                df = df.with_columns(
                    pl.from_epoch("time", time_unit="s").dt.replace_time_zone("UTC")
                )
            return df

        return events


class DeFiStream(BaseClient):
    """
    Synchronous DeFiStream API client with builder pattern.

    Example:
        >>> from defistream import DeFiStream
        >>> client = DeFiStream(api_key="dsk_...")
        >>>
        >>> # Builder pattern
        >>> query = client.erc20.transfers("USDT").network("ETH").start_block(24000000).end_block(24100000)
        >>> df = query.as_pandas()
        >>>
        >>> # Or chain everything
        >>> transfers = client.erc20.transfers("USDT").network("ETH").start_block(24000000).end_block(24100000).as_dict()
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ):
        super().__init__(api_key, base_url, timeout, max_retries)
        self._http_client: httpx.Client | None = None

        # Protocol clients
        self.erc20 = ERC20Protocol(self)
        self.native_token = NativeTokenProtocol(self)
        self.aave = AAVEProtocol(self)
        self.uniswap = UniswapProtocol(self)
        self.lido = LidoProtocol(self)
        self.stader = StaderProtocol(self)
        self.threshold = ThresholdProtocol(self)

    @property
    def _client(self) -> httpx.Client:
        """Lazy-initialize HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
        return self._http_client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> "DeFiStream":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        as_dataframe: Literal["pandas", "polars"] | None = None,
        output_file: str | None = None,
    ) -> list[dict[str, Any]] | Any:
        """Make HTTP request."""
        if params is None:
            params = {}

        if output_file:
            if output_file.endswith(".parquet"):
                params["format"] = "parquet"
            elif output_file.endswith(".csv"):
                params["format"] = "csv"

        response = self._client.request(method, path, params=params)
        return self._process_response(response, as_dataframe, output_file)

    def decoders(self) -> list[str]:
        """Get list of available decoders."""
        response = self._client.get("/decoders")
        if response.status_code >= 400:
            self._handle_error_response(response)
        data = response.json()
        return data.get("decoders", [])


class AsyncDeFiStream(BaseClient):
    """
    Asynchronous DeFiStream API client with builder pattern.

    Example:
        >>> import asyncio
        >>> from defistream import AsyncDeFiStream
        >>>
        >>> async def main():
        ...     async with AsyncDeFiStream(api_key="dsk_...") as client:
        ...         query = client.erc20.transfers("USDT").network("ETH").start_block(24000000).end_block(24100000)
        ...         df = await query.as_pandas()
        ...
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ):
        super().__init__(api_key, base_url, timeout, max_retries)
        self._http_client: httpx.AsyncClient | None = None

        # Protocol clients (async versions)
        self.erc20 = AsyncERC20Protocol(self)
        self.native_token = AsyncNativeTokenProtocol(self)
        self.aave = AsyncAAVEProtocol(self)
        self.uniswap = AsyncUniswapProtocol(self)
        self.lido = AsyncLidoProtocol(self)
        self.stader = AsyncStaderProtocol(self)
        self.threshold = AsyncThresholdProtocol(self)

    @property
    def _client(self) -> httpx.AsyncClient:
        """Lazy-initialize async HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
        return self._http_client

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "AsyncDeFiStream":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        as_dataframe: Literal["pandas", "polars"] | None = None,
        output_file: str | None = None,
    ) -> list[dict[str, Any]] | Any:
        """Make async HTTP request."""
        if params is None:
            params = {}

        if output_file:
            if output_file.endswith(".parquet"):
                params["format"] = "parquet"
            elif output_file.endswith(".csv"):
                params["format"] = "csv"

        response = await self._client.request(method, path, params=params)
        return self._process_response(response, as_dataframe, output_file)

    async def decoders(self) -> list[str]:
        """Get list of available decoders."""
        response = await self._client.get("/decoders")
        if response.status_code >= 400:
            self._handle_error_response(response)
        data = response.json()
        return data.get("decoders", [])
