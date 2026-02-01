"""Protocol-specific API clients with builder pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .query import QueryBuilder, AsyncQueryBuilder

if TYPE_CHECKING:
    from .client import BaseClient


class ERC20Protocol:
    """ERC20 token events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def transfers(self, token: str | None = None) -> QueryBuilder:
        """
        Start a query for ERC20 transfer events.

        Args:
            token: Token symbol (USDT, USDC, WETH, etc.) or contract address

        Returns:
            QueryBuilder for chaining filters

        Example:
            df = (
                client.erc20.transfers("USDT")
                .network("ETH")
                .block_range(21000000, 21010000)
                .as_df()
            )
        """
        params = {"token": token} if token else {}
        return QueryBuilder(self._client, "/erc20/events/transfer", params)


class NativeTokenProtocol:
    """Native token (ETH, MATIC, etc.) events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def transfers(self) -> QueryBuilder:
        """
        Start a query for native token transfer events.

        Returns:
            QueryBuilder for chaining filters

        Example:
            df = (
                client.native_token.transfers()
                .network("ETH")
                .block_range(21000000, 21010000)
                .min_amount(1.0)
                .as_df()
            )
        """
        return QueryBuilder(self._client, "/native_token/events/transfer")


class AAVEProtocol:
    """AAVE V3 lending protocol events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> QueryBuilder:
        """Start a query for AAVE deposit/supply events."""
        return QueryBuilder(self._client, "/aave/events/deposit")

    def withdrawals(self) -> QueryBuilder:
        """Start a query for AAVE withdrawal events."""
        return QueryBuilder(self._client, "/aave/events/withdraw")

    def borrows(self) -> QueryBuilder:
        """Start a query for AAVE borrow events."""
        return QueryBuilder(self._client, "/aave/events/borrow")

    def repays(self) -> QueryBuilder:
        """Start a query for AAVE repay events."""
        return QueryBuilder(self._client, "/aave/events/repay")

    def flashloans(self) -> QueryBuilder:
        """Start a query for AAVE flash loan events."""
        return QueryBuilder(self._client, "/aave/events/flashloan")

    def liquidations(self) -> QueryBuilder:
        """Start a query for AAVE liquidation events."""
        return QueryBuilder(self._client, "/aave/events/liquidation")


class UniswapProtocol:
    """Uniswap V3 DEX events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def swaps(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> QueryBuilder:
        """
        Start a query for Uniswap V3 swap events.

        Args:
            symbol0: First token symbol (e.g., WETH)
            symbol1: Second token symbol (e.g., USDC)
            fee: Fee tier (100, 500, 3000, 10000)

        Returns:
            QueryBuilder for chaining filters

        Example:
            df = (
                client.uniswap.swaps("WETH", "USDC", 500)
                .network("ETH")
                .block_range(21000000, 21010000)
                .as_df()
            )
        """
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return QueryBuilder(self._client, "/uniswap/events/swap", params)

    def deposits(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> QueryBuilder:
        """Start a query for Uniswap V3 deposit (add liquidity) events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return QueryBuilder(self._client, "/uniswap/events/deposit", params)

    def withdrawals(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> QueryBuilder:
        """Start a query for Uniswap V3 withdrawal (remove liquidity) events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return QueryBuilder(self._client, "/uniswap/events/withdraw", params)

    def collects(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> QueryBuilder:
        """Start a query for Uniswap V3 collect (fee collection) events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return QueryBuilder(self._client, "/uniswap/events/collect", params)


class LidoProtocol:
    """Lido liquid staking events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    # L1 ETH events
    def deposits(self) -> QueryBuilder:
        """Start a query for Lido stETH deposit events (ETH L1 only)."""
        return QueryBuilder(self._client, "/lido/events/deposit")

    def withdrawal_requests(self) -> QueryBuilder:
        """Start a query for Lido withdrawal request events (ETH L1 only)."""
        return QueryBuilder(self._client, "/lido/events/withdrawal_request")

    def withdrawals_claimed(self) -> QueryBuilder:
        """Start a query for Lido claimed withdrawal events (ETH L1 only)."""
        return QueryBuilder(self._client, "/lido/events/withdrawal_claimed")

    # L2 events
    def l2_deposits(self) -> QueryBuilder:
        """Start a query for Lido L2 deposit events (L2 networks only)."""
        return QueryBuilder(self._client, "/lido/events/l2_deposit")

    def l2_withdrawal_requests(self) -> QueryBuilder:
        """Start a query for Lido L2 withdrawal request events (L2 networks only)."""
        return QueryBuilder(self._client, "/lido/events/l2_withdrawal_request")


class StaderProtocol:
    """Stader ETHx staking events with builder pattern (ETH only)."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> QueryBuilder:
        """Start a query for Stader deposit events."""
        return QueryBuilder(self._client, "/stader/events/deposit")

    def withdrawal_requests(self) -> QueryBuilder:
        """Start a query for Stader withdrawal request events."""
        return QueryBuilder(self._client, "/stader/events/withdrawal_request")

    def withdrawals(self) -> QueryBuilder:
        """Start a query for Stader withdrawal events."""
        return QueryBuilder(self._client, "/stader/events/withdrawal")


class ThresholdProtocol:
    """Threshold tBTC events with builder pattern (ETH only)."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposit_requests(self) -> QueryBuilder:
        """Start a query for tBTC deposit request (reveal) events."""
        return QueryBuilder(self._client, "/threshold/events/deposit_request")

    def deposits(self) -> QueryBuilder:
        """Start a query for tBTC deposit (mint) events."""
        return QueryBuilder(self._client, "/threshold/events/deposit")

    def withdrawal_requests(self) -> QueryBuilder:
        """Start a query for tBTC withdrawal request events."""
        return QueryBuilder(self._client, "/threshold/events/withdrawal_request")

    def withdrawals(self) -> QueryBuilder:
        """Start a query for tBTC withdrawal (unmint) events."""
        return QueryBuilder(self._client, "/threshold/events/withdrawal")


# Async protocol implementations
class AsyncERC20Protocol:
    """Async ERC20 token events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def transfers(self, token: str | None = None) -> AsyncQueryBuilder:
        """Start a query for ERC20 transfer events."""
        params = {"token": token} if token else {}
        return AsyncQueryBuilder(self._client, "/erc20/events/transfer", params)


class AsyncNativeTokenProtocol:
    """Async native token events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def transfers(self) -> AsyncQueryBuilder:
        """Start a query for native token transfer events."""
        return AsyncQueryBuilder(self._client, "/native_token/events/transfer")


class AsyncAAVEProtocol:
    """Async AAVE V3 events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> AsyncQueryBuilder:
        """Start a query for AAVE deposit/supply events."""
        return AsyncQueryBuilder(self._client, "/aave/events/deposit")

    def withdrawals(self) -> AsyncQueryBuilder:
        """Start a query for AAVE withdrawal events."""
        return AsyncQueryBuilder(self._client, "/aave/events/withdraw")

    def borrows(self) -> AsyncQueryBuilder:
        """Start a query for AAVE borrow events."""
        return AsyncQueryBuilder(self._client, "/aave/events/borrow")

    def repays(self) -> AsyncQueryBuilder:
        """Start a query for AAVE repay events."""
        return AsyncQueryBuilder(self._client, "/aave/events/repay")

    def flashloans(self) -> AsyncQueryBuilder:
        """Start a query for AAVE flash loan events."""
        return AsyncQueryBuilder(self._client, "/aave/events/flashloan")

    def liquidations(self) -> AsyncQueryBuilder:
        """Start a query for AAVE liquidation events."""
        return AsyncQueryBuilder(self._client, "/aave/events/liquidation")


class AsyncUniswapProtocol:
    """Async Uniswap V3 events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def swaps(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> AsyncQueryBuilder:
        """Start a query for Uniswap V3 swap events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return AsyncQueryBuilder(self._client, "/uniswap/events/swap", params)

    def deposits(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> AsyncQueryBuilder:
        """Start a query for Uniswap V3 deposit events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return AsyncQueryBuilder(self._client, "/uniswap/events/deposit", params)

    def withdrawals(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> AsyncQueryBuilder:
        """Start a query for Uniswap V3 withdrawal events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return AsyncQueryBuilder(self._client, "/uniswap/events/withdraw", params)

    def collects(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> AsyncQueryBuilder:
        """Start a query for Uniswap V3 collect events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return AsyncQueryBuilder(self._client, "/uniswap/events/collect", params)


class AsyncLidoProtocol:
    """Async Lido events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> AsyncQueryBuilder:
        """Start a query for Lido deposit events (ETH L1 only)."""
        return AsyncQueryBuilder(self._client, "/lido/events/deposit")

    def withdrawal_requests(self) -> AsyncQueryBuilder:
        """Start a query for Lido withdrawal request events (ETH L1 only)."""
        return AsyncQueryBuilder(self._client, "/lido/events/withdrawal_request")

    def withdrawals_claimed(self) -> AsyncQueryBuilder:
        """Start a query for Lido claimed withdrawal events (ETH L1 only)."""
        return AsyncQueryBuilder(self._client, "/lido/events/withdrawal_claimed")

    def l2_deposits(self) -> AsyncQueryBuilder:
        """Start a query for Lido L2 deposit events."""
        return AsyncQueryBuilder(self._client, "/lido/events/l2_deposit")

    def l2_withdrawal_requests(self) -> AsyncQueryBuilder:
        """Start a query for Lido L2 withdrawal request events."""
        return AsyncQueryBuilder(self._client, "/lido/events/l2_withdrawal_request")


class AsyncStaderProtocol:
    """Async Stader events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> AsyncQueryBuilder:
        """Start a query for Stader deposit events."""
        return AsyncQueryBuilder(self._client, "/stader/events/deposit")

    def withdrawal_requests(self) -> AsyncQueryBuilder:
        """Start a query for Stader withdrawal request events."""
        return AsyncQueryBuilder(self._client, "/stader/events/withdrawal_request")

    def withdrawals(self) -> AsyncQueryBuilder:
        """Start a query for Stader withdrawal events."""
        return AsyncQueryBuilder(self._client, "/stader/events/withdrawal")


class AsyncThresholdProtocol:
    """Async Threshold events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposit_requests(self) -> AsyncQueryBuilder:
        """Start a query for tBTC deposit request events."""
        return AsyncQueryBuilder(self._client, "/threshold/events/deposit_request")

    def deposits(self) -> AsyncQueryBuilder:
        """Start a query for tBTC deposit events."""
        return AsyncQueryBuilder(self._client, "/threshold/events/deposit")

    def withdrawal_requests(self) -> AsyncQueryBuilder:
        """Start a query for tBTC withdrawal request events."""
        return AsyncQueryBuilder(self._client, "/threshold/events/withdrawal_request")

    def withdrawals(self) -> AsyncQueryBuilder:
        """Start a query for tBTC withdrawal events."""
        return AsyncQueryBuilder(self._client, "/threshold/events/withdrawal")
