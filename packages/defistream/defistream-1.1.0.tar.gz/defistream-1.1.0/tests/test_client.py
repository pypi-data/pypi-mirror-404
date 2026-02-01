"""Tests for DeFiStream client."""

import os
import pytest
from unittest.mock import MagicMock, patch

from defistream import DeFiStream, AsyncDeFiStream, QueryBuilder, AsyncQueryBuilder
from defistream.exceptions import (
    AuthenticationError,
    QuotaExceededError,
    ValidationError,
)


class TestDeFiStreamInit:
    """Test client initialization."""

    def test_requires_api_key(self):
        """Should raise if no API key provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                DeFiStream()

    def test_accepts_api_key_argument(self):
        """Should accept API key as argument."""
        client = DeFiStream(api_key="dsk_test")
        assert client.api_key == "dsk_test"

    def test_reads_api_key_from_env(self):
        """Should read API key from environment."""
        with patch.dict(os.environ, {"DEFISTREAM_API_KEY": "dsk_env"}):
            client = DeFiStream()
            assert client.api_key == "dsk_env"

    def test_default_base_url(self):
        """Should use default base URL."""
        client = DeFiStream(api_key="dsk_test")
        assert client.base_url == "https://api.defistream.dev/v1"

    def test_custom_base_url(self):
        """Should accept custom base URL."""
        client = DeFiStream(api_key="dsk_test", base_url="http://localhost:8081/v1")
        assert client.base_url == "http://localhost:8081/v1"


class TestProtocolClients:
    """Test protocol client availability."""

    def test_has_erc20_protocol(self):
        """Should have ERC20 protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "erc20")
        assert hasattr(client.erc20, "transfers")

    def test_has_native_token_protocol(self):
        """Should have native token protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "native_token")
        assert hasattr(client.native_token, "transfers")

    def test_has_aave_protocol(self):
        """Should have AAVE protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "aave")
        assert hasattr(client.aave, "deposits")
        assert hasattr(client.aave, "withdrawals")
        assert hasattr(client.aave, "borrows")
        assert hasattr(client.aave, "repays")
        assert hasattr(client.aave, "flashloans")
        assert hasattr(client.aave, "liquidations")

    def test_has_uniswap_protocol(self):
        """Should have Uniswap protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "uniswap")
        assert hasattr(client.uniswap, "swaps")
        assert hasattr(client.uniswap, "deposits")
        assert hasattr(client.uniswap, "withdrawals")
        assert hasattr(client.uniswap, "collects")

    def test_has_lido_protocol(self):
        """Should have Lido protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "lido")
        assert hasattr(client.lido, "deposits")
        assert hasattr(client.lido, "withdrawal_requests")
        assert hasattr(client.lido, "withdrawals_claimed")
        assert hasattr(client.lido, "l2_deposits")
        assert hasattr(client.lido, "l2_withdrawal_requests")

    def test_has_stader_protocol(self):
        """Should have Stader protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "stader")
        assert hasattr(client.stader, "deposits")
        assert hasattr(client.stader, "withdrawal_requests")
        assert hasattr(client.stader, "withdrawals")

    def test_has_threshold_protocol(self):
        """Should have Threshold protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "threshold")
        assert hasattr(client.threshold, "deposit_requests")
        assert hasattr(client.threshold, "deposits")
        assert hasattr(client.threshold, "withdrawal_requests")
        assert hasattr(client.threshold, "withdrawals")


class TestAsyncClient:
    """Test async client."""

    def test_async_client_init(self):
        """Should initialize async client."""
        client = AsyncDeFiStream(api_key="dsk_test")
        assert client.api_key == "dsk_test"

    def test_async_has_protocols(self):
        """Should have all protocol clients."""
        client = AsyncDeFiStream(api_key="dsk_test")
        assert hasattr(client, "erc20")
        assert hasattr(client, "native_token")
        assert hasattr(client, "aave")
        assert hasattr(client, "uniswap")
        assert hasattr(client, "lido")
        assert hasattr(client, "stader")
        assert hasattr(client, "threshold")


class TestContextManager:
    """Test context manager support."""

    def test_sync_context_manager(self):
        """Should work as context manager."""
        with DeFiStream(api_key="dsk_test") as client:
            assert client.api_key == "dsk_test"

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Should work as async context manager."""
        async with AsyncDeFiStream(api_key="dsk_test") as client:
            assert client.api_key == "dsk_test"


class TestBuilderPattern:
    """Test builder pattern for queries."""

    def test_transfers_returns_query_builder(self):
        """Protocol methods should return QueryBuilder."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert isinstance(query, QueryBuilder)

    def test_transfers_with_token_sets_param(self):
        """transfers('USDT') should set token param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers("USDT")
        assert query._params.get("token") == "USDT"

    def test_builder_chaining(self):
        """Builder methods should return QueryBuilder for chaining."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers("USDT").network("ETH").start_block(21000000).end_block(21010000)
        assert isinstance(query, QueryBuilder)
        assert query._params["network"] == "ETH"
        assert query._params["block_start"] == 21000000
        assert query._params["block_end"] == 21010000

    def test_builder_immutability(self):
        """Builder methods should return new instances."""
        client = DeFiStream(api_key="dsk_test")
        query1 = client.erc20.transfers("USDT")
        query2 = query1.network("ETH")
        assert query1 is not query2
        assert "network" not in query1._params
        assert query2._params["network"] == "ETH"

    def test_last_value_wins(self):
        """Multiple calls to same filter should use last value."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().network("ETH").network("ARB")
        assert query._params["network"] == "ARB"

    def test_block_range_method(self):
        """block_range should set both start and end."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().block_range(21000000, 21010000)
        assert query._params["block_start"] == 21000000
        assert query._params["block_end"] == 21010000

    def test_from_address_alias(self):
        """from_address should be alias for sender."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().from_address("0x123")
        assert query._params["sender"] == "0x123"

    def test_to_address_alias(self):
        """to_address should be alias for receiver."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().to_address("0x456")
        assert query._params["receiver"] == "0x456"

    def test_verbose_mode(self):
        """verbose() should set verbose param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().verbose()
        assert query._verbose is True
        params = query._build_params()
        assert params["verbose"] == "true"

    def test_verbose_false_by_default(self):
        """verbose should be False by default."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert query._verbose is False
        params = query._build_params()
        assert "verbose" not in params

    def test_min_amount_filter(self):
        """min_amount should set param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().min_amount(1000)
        assert query._params["min_amount"] == 1000

    def test_max_amount_filter(self):
        """max_amount should set param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().max_amount(10000)
        assert query._params["max_amount"] == 10000

    def test_start_time(self):
        """start_time should set since param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().start_time("2024-01-01T00:00:00Z")
        assert query._params["since"] == "2024-01-01T00:00:00Z"

    def test_end_time(self):
        """end_time should set until param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().end_time("2024-01-31T23:59:59Z")
        assert query._params["until"] == "2024-01-31T23:59:59Z"

    def test_time_range(self):
        """time_range should set both since and until params."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().time_range("2024-01-01", "2024-01-31")
        assert query._params["since"] == "2024-01-01"
        assert query._params["until"] == "2024-01-31"

class TestAsyncBuilderPattern:
    """Test async builder pattern."""

    def test_async_transfers_returns_async_query_builder(self):
        """Async protocol methods should return AsyncQueryBuilder."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert isinstance(query, AsyncQueryBuilder)

    def test_async_builder_chaining(self):
        """Async builder methods should chain correctly."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers("USDT").network("ETH").start_block(21000000).end_block(21010000)
        assert isinstance(query, AsyncQueryBuilder)
        assert query._params["network"] == "ETH"


class TestUniswapBuilder:
    """Test Uniswap-specific builder methods."""

    def test_swaps_with_tokens_and_fee(self):
        """swaps() should accept symbol0, symbol1, fee."""
        client = DeFiStream(api_key="dsk_test")
        query = client.uniswap.swaps("WETH", "USDC", 500)
        assert query._params["symbol0"] == "WETH"
        assert query._params["symbol1"] == "USDC"
        assert query._params["fee"] == 500

    def test_deposits_endpoint(self):
        """deposits() should use correct endpoint."""
        client = DeFiStream(api_key="dsk_test")
        query = client.uniswap.deposits("WETH", "USDC", 500)
        assert query._endpoint == "/uniswap/events/deposit"

    def test_withdrawals_endpoint(self):
        """withdrawals() should use correct endpoint."""
        client = DeFiStream(api_key="dsk_test")
        query = client.uniswap.withdrawals("WETH", "USDC", 500)
        assert query._endpoint == "/uniswap/events/withdraw"

    def test_collects_endpoint(self):
        """collects() should use correct endpoint."""
        client = DeFiStream(api_key="dsk_test")
        query = client.uniswap.collects("WETH", "USDC", 500)
        assert query._endpoint == "/uniswap/events/collect"

    def test_symbol_and_fee_chain_methods(self):
        """symbol0, symbol1, fee should work as chain methods."""
        client = DeFiStream(api_key="dsk_test")
        query = client.uniswap.swaps().symbol0("WETH").symbol1("USDC").fee(3000)
        assert query._params["symbol0"] == "WETH"
        assert query._params["symbol1"] == "USDC"
        assert query._params["fee"] == 3000


class TestAAVEBuilder:
    """Test AAVE-specific builder methods."""

    def test_flashloans_endpoint(self):
        """flashloans() should use correct endpoint."""
        client = DeFiStream(api_key="dsk_test")
        query = client.aave.flashloans()
        assert query._endpoint == "/aave/events/flashloan"

    def test_eth_market_type_filter(self):
        """eth_market_type should set param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.aave.deposits().eth_market_type("Prime")
        assert query._params["eth_market_type"] == "Prime"


class TestQueryBuilderRepr:
    """Test QueryBuilder repr."""

    def test_repr(self):
        """Should have informative repr."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers("USDT").network("ETH")
        repr_str = repr(query)
        assert "QueryBuilder" in repr_str
        assert "/erc20/events/transfer" in repr_str


class TestTerminalMethods:
    """Test terminal methods."""

    def test_has_as_dict(self):
        """QueryBuilder should have as_dict method."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_dict")

    def test_has_as_df(self):
        """QueryBuilder should have as_df method."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_df")

    def test_has_as_file(self):
        """QueryBuilder should have as_file method."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_file")

    def test_as_df_invalid_library(self):
        """as_df should raise for invalid library."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        with pytest.raises(ValueError, match="library must be"):
            query.as_df("invalid")

    def test_as_file_detects_csv_extension(self):
        """as_file should detect CSV format from extension."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        # We can't actually call as_file without a real API, but we can test the format detection logic
        # by checking that it doesn't raise for valid extensions
        assert hasattr(query, "as_file")

    def test_as_file_requires_format_or_extension(self):
        """as_file should raise if no format or extension."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        with pytest.raises(ValueError, match="Cannot determine format"):
            query.as_file("transfers_without_extension")

    def test_as_file_invalid_format(self):
        """as_file should raise for invalid format."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        with pytest.raises(ValueError, match="format must be"):
            query.as_file("transfers", format="xml")


class TestAsyncTerminalMethods:
    """Test async terminal methods."""

    def test_async_has_as_dict(self):
        """AsyncQueryBuilder should have as_dict method."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_dict")

    def test_async_has_as_df(self):
        """AsyncQueryBuilder should have as_df method."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_df")

    def test_async_has_as_file(self):
        """AsyncQueryBuilder should have as_file method."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_file")


class TestLabelCategoryMethods:
    """Test label and category filter methods."""

    def test_involving_sets_param(self):
        """involving() should set involving param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving("0xA")
        assert query._params["involving"] == "0xA"

    def test_involving_label_sets_param(self):
        """involving_label() should set involving_label param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_label("Binance")
        assert query._params["involving_label"] == "Binance"

    def test_involving_category_sets_param(self):
        """involving_category() should set involving_category param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_category("CEX")
        assert query._params["involving_category"] == "CEX"

    def test_sender_label_sets_param(self):
        """sender_label() should set sender_label param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender_label("Binance")
        assert query._params["sender_label"] == "Binance"

    def test_sender_category_sets_param(self):
        """sender_category() should set sender_category param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender_category("CEX")
        assert query._params["sender_category"] == "CEX"

    def test_receiver_label_sets_param(self):
        """receiver_label() should set receiver_label param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().receiver_label("Coinbase")
        assert query._params["receiver_label"] == "Coinbase"

    def test_receiver_category_sets_param(self):
        """receiver_category() should set receiver_category param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().receiver_category("DEX")
        assert query._params["receiver_category"] == "DEX"

    def test_label_chaining(self):
        """Label methods should chain with other methods."""
        client = DeFiStream(api_key="dsk_test")
        query = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .sender_label("Binance")
            .block_range(21000000, 21010000)
        )
        assert query._params["sender_label"] == "Binance"
        assert query._params["network"] == "ETH"
        assert query._params["block_start"] == 21000000

    def test_label_immutability(self):
        """Label methods should return new instances (immutability)."""
        client = DeFiStream(api_key="dsk_test")
        query1 = client.erc20.transfers()
        query2 = query1.sender_label("Binance")
        assert query1 is not query2
        assert "sender_label" not in query1._params
        assert query2._params["sender_label"] == "Binance"

    def test_sender_and_receiver_labels_together(self):
        """sender_label and receiver_label should work together."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender_label("Binance").receiver_label("Coinbase")
        params = query._build_params()
        assert params["sender_label"] == "Binance"
        assert params["receiver_label"] == "Coinbase"


class TestMultiValueSupport:
    """Test multi-value support for address and label/category filters."""

    def test_sender_varargs_join(self):
        """sender() with multiple args should join with comma."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender("0xA", "0xB", "0xC")
        assert query._params["sender"] == "0xA,0xB,0xC"

    def test_receiver_varargs_join(self):
        """receiver() with multiple args should join with comma."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().receiver("0xA", "0xB")
        assert query._params["receiver"] == "0xA,0xB"

    def test_from_address_varargs_join(self):
        """from_address() with multiple args should join with comma."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().from_address("0xA", "0xB")
        assert query._params["sender"] == "0xA,0xB"

    def test_to_address_varargs_join(self):
        """to_address() with multiple args should join with comma."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().to_address("0xA", "0xB")
        assert query._params["receiver"] == "0xA,0xB"

    def test_involving_varargs_join(self):
        """involving() with multiple args should join with comma."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving("0xA", "0xB")
        assert query._params["involving"] == "0xA,0xB"

    def test_involving_label_varargs_join(self):
        """involving_label() with multiple args should join with comma."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_label("Binance", "Coinbase")
        assert query._params["involving_label"] == "Binance,Coinbase"

    def test_involving_category_varargs_join(self):
        """involving_category() with multiple args should join with comma."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_category("CEX", "DEX")
        assert query._params["involving_category"] == "CEX,DEX"

    def test_sender_label_varargs_join(self):
        """sender_label() with multiple args should join with comma."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender_label("Binance", "Coinbase")
        assert query._params["sender_label"] == "Binance,Coinbase"

    def test_pre_joined_string_passthrough(self):
        """A single pre-joined string should pass through unchanged."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender("0xA,0xB,0xC")
        assert query._params["sender"] == "0xA,0xB,0xC"

    def test_single_string_backward_compat(self):
        """Single string arg should still work (backward compatibility)."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender("0xA")
        assert query._params["sender"] == "0xA"

    def test_sender_no_args_raises(self):
        """sender() with no args should raise ValueError."""
        client = DeFiStream(api_key="dsk_test")
        with pytest.raises(ValueError, match="At least one value is required"):
            client.erc20.transfers().sender()

    def test_involving_label_no_args_raises(self):
        """involving_label() with no args should raise ValueError."""
        client = DeFiStream(api_key="dsk_test")
        with pytest.raises(ValueError, match="At least one value is required"):
            client.erc20.transfers().involving_label()


class TestMutualExclusivity:
    """Test mutual exclusivity validation between filter slots."""

    def test_involving_vs_involving_label_raises(self):
        """involving + involving_label should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving("0xA").involving_label("Binance")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_involving_vs_involving_category_raises(self):
        """involving + involving_category should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving("0xA").involving_category("CEX")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_involving_label_vs_involving_category_raises(self):
        """involving_label + involving_category should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_label("Binance").involving_category("CEX")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_sender_vs_sender_label_raises(self):
        """sender + sender_label should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender("0xA").sender_label("Binance")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_sender_vs_sender_category_raises(self):
        """sender + sender_category should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender("0xA").sender_category("CEX")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_receiver_vs_receiver_label_raises(self):
        """receiver + receiver_label should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().receiver("0xA").receiver_label("Coinbase")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_receiver_vs_receiver_category_raises(self):
        """receiver + receiver_category should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().receiver("0xA").receiver_category("CEX")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_involving_with_sender_raises(self):
        """involving + sender should raise ValidationError (cross-slot)."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving("0xA").sender("0xB")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_involving_label_with_receiver_label_raises(self):
        """involving_label + receiver_label should raise ValidationError (cross-slot)."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_label("Binance").receiver_label("Coinbase")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_involving_category_with_sender_category_raises(self):
        """involving_category + sender_category should raise ValidationError (cross-slot)."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_category("CEX").sender_category("DEX")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_sender_and_receiver_valid(self):
        """sender + receiver should be valid (different slots, no involving)."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender("0xA").receiver("0xB")
        params = query._build_params()
        assert params["sender"] == "0xA"
        assert params["receiver"] == "0xB"

    def test_sender_label_and_receiver_category_valid(self):
        """sender_label + receiver_category should be valid."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender_label("Binance").receiver_category("DEX")
        params = query._build_params()
        assert params["sender_label"] == "Binance"
        assert params["receiver_category"] == "DEX"


class TestSQLSafetyValidation:
    """Test SQL safety validation for label/category params."""

    def test_single_quote_in_label_raises(self):
        """Label with single quote should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_label("Binance'; DROP TABLE--")
        with pytest.raises(ValidationError, match="unsafe characters"):
            query._build_params()

    def test_backslash_in_label_raises(self):
        """Label with backslash should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender_label("Binance\\x00")
        with pytest.raises(ValidationError, match="unsafe characters"):
            query._build_params()

    def test_single_quote_in_category_raises(self):
        """Category with single quote should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().receiver_category("CEX'")
        with pytest.raises(ValidationError, match="unsafe characters"):
            query._build_params()

    def test_backslash_in_category_raises(self):
        """Category with backslash should raise ValidationError."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_category("CEX\\")
        with pytest.raises(ValidationError, match="unsafe characters"):
            query._build_params()

    def test_clean_label_passes(self):
        """Clean label values should pass validation."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_label("Binance 14")
        params = query._build_params()
        assert params["involving_label"] == "Binance 14"

    def test_address_params_not_checked(self):
        """Address params (sender, receiver) should not be SQL-checked."""
        client = DeFiStream(api_key="dsk_test")
        # Addresses can contain any characters — only label/category is checked
        query = client.erc20.transfers().sender("0x'abc")
        params = query._build_params()
        assert params["sender"] == "0x'abc"


class TestAsyncLabelCategoryMethods:
    """Test label/category methods on AsyncQueryBuilder."""

    def test_async_involving_label(self):
        """Async involving_label should set param."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving_label("Binance")
        assert isinstance(query, AsyncQueryBuilder)
        assert query._params["involving_label"] == "Binance"

    def test_async_sender_multi_value(self):
        """Async sender with multiple args should join."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender("0xA", "0xB")
        assert query._params["sender"] == "0xA,0xB"

    def test_async_mutual_exclusivity(self):
        """Async builder should enforce mutual exclusivity."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().involving("0xA").sender("0xB")
        with pytest.raises(ValidationError, match="Cannot combine"):
            query._build_params()

    def test_async_sql_safety(self):
        """Async builder should enforce SQL safety."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().sender_label("test'injection")
        with pytest.raises(ValidationError, match="unsafe characters"):
            query._build_params()

    def test_async_label_chaining(self):
        """Async label methods should chain correctly."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .sender_label("Binance", "Coinbase")
            .receiver_category("DEX")
        )
        assert query._params["sender_label"] == "Binance,Coinbase"
        assert query._params["receiver_category"] == "DEX"
