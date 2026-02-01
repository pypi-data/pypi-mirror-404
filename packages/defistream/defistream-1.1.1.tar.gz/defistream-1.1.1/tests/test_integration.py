"""
Integration tests for DeFiStream Python client against the live API server.

These tests require:
1. A reachable API server (default: https://api.defistream.dev/v1)
2. TEST_API_KEY set in .env

Run with:
    python -m pytest tests/test_integration.py -v
    python -m pytest tests/test_integration.py -v --local
"""

import os

import pandas as pd
import pytest

from defistream import AsyncDeFiStream, DeFiStream
from defistream.exceptions import ValidationError

# Constants are defined here rather than imported from conftest because pytest
# conftest modules cannot be imported directly as regular Python modules.
# The conftest.py provides fixtures (client, async_client) and the --local flag.
TEST_ADDRESS = "0x28c6c06298d514db089934071355e5743bf21d60"   # Binance Hot Wallet
TEST_ADDRESS_2 = "0xdfd5293d8e347dfe59e90efd55b2956a1343963d"  # Binance 14
ETH_BLOCK_START = 21000000
ETH_BLOCK_END = 21010000


# ===========================================================================
# Decoders endpoint (matches api/test_common.py)
# ===========================================================================


class TestDecoders:
    """Test the decoders() discovery endpoint."""

    def test_decoders_returns_list(self, client):
        """decoders() should return a non-empty list of decoder names."""
        decoders = client.decoders()
        assert isinstance(decoders, list)
        assert len(decoders) > 0

    def test_decoders_contains_known_decoders(self, client):
        """decoders() result should include all known protocol decoders."""
        decoders = client.decoders()
        for expected in ("erc20", "native_token", "aave", "uniswap", "lido", "stader", "threshold"):
            assert expected in decoders, f"Missing decoder: {expected}"


# ===========================================================================
# ERC20 integration tests (matches api/test_erc20.py + test_involving.py)
# ===========================================================================


class TestERC20Integration:
    """Test ERC20 queries against the live API."""

    # -- basic queries -------------------------------------------------------

    def test_basic_transfer_as_dict(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)
        assert len(results) > 0
        assert "block_number" in results[0]

    def test_basic_transfer_as_df(self, client):
        df = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_df()
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "block_number" in df.columns

    # -- single-value address filters ----------------------------------------

    def test_sender_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)
        for row in results:
            assert row["sender"].lower() == TEST_ADDRESS.lower()

    def test_receiver_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)
        for row in results:
            assert row["receiver"].lower() == TEST_ADDRESS.lower()

    def test_involving_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)
        for row in results:
            involved = (
                row["sender"].lower() == TEST_ADDRESS.lower()
                or row["receiver"].lower() == TEST_ADDRESS.lower()
            )
            assert involved

    # -- label / category filters --------------------------------------------

    def test_involving_label_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_involving_category_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_sender_label_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_receiver_label_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_sender_category_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_receiver_category_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_sender_label_and_receiver_category_combined(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_label("Binance")
            .receiver_category("defi")
            .as_dict()
        )
        assert isinstance(results, list)

    # -- multi-value address filters -----------------------------------------

    def test_multi_value_sender(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_receiver(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_sender_and_receiver(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender(TEST_ADDRESS, TEST_ADDRESS_2)
            .receiver(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    # -- multi-value label / category filters --------------------------------

    def test_multi_value_involving_label(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_receiver_label(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_sender_category(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_receiver_category(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_category(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_sender_label_with_receiver_category(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_label("Binance", "Coinbase")
            .receiver_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)

    # -- verbose & amount filters -------------------------------------------

    def test_verbose_mode(self, client):
        df = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .verbose()
            .as_df()
        )
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            assert "name" in df.columns
            assert "network" in df.columns
            assert "tx_id" in df.columns

    def test_min_amount_filter(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .min_amount(10000)
            .as_dict()
        )
        assert isinstance(results, list)
        for row in results:
            assert float(row["amount"]) >= 10000


# ===========================================================================
# Native Token integration tests (matches api/test_native_token.py)
# ===========================================================================


class TestNativeTokenIntegration:
    """Test native token queries against the live API."""

    # -- basic queries -------------------------------------------------------

    def test_basic_transfer_as_dict(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .min_amount(1)
            .as_dict()
        )
        assert isinstance(results, list)
        assert len(results) > 0

    # -- single-value address filters ----------------------------------------

    def test_sender_filter(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_receiver_filter(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_involving_filter(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)

    # -- label / category filters --------------------------------------------

    def test_involving_label_filter(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_involving_category_filter(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_sender_label_filter(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_receiver_label_filter(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_sender_category_filter(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_receiver_category_filter(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    # -- multi-value address filters -----------------------------------------

    def test_multi_value_sender(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_receiver(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_sender_and_receiver(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender(TEST_ADDRESS, TEST_ADDRESS_2)
            .receiver(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    # -- multi-value label / category filters --------------------------------

    def test_multi_value_involving_label(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_category(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_sender_label(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_receiver_label(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_sender_category(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_receiver_category(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .receiver_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)


# ===========================================================================
# AAVE integration tests (matches api/test_aave.py)
# ===========================================================================


class TestAaveIntegration:
    """Test AAVE queries against the live API."""

    # -- event types ---------------------------------------------------------

    def test_deposits_as_dict(self, client):
        results = (
            client.aave.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_withdrawals_as_dict(self, client):
        results = (
            client.aave.withdrawals()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_borrows_as_dict(self, client):
        results = (
            client.aave.borrows()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_repays_as_dict(self, client):
        results = (
            client.aave.repays()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_flashloans_as_dict(self, client):
        results = (
            client.aave.flashloans()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_liquidations_as_dict(self, client):
        results = (
            client.aave.liquidations()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    # -- involving filters ---------------------------------------------------

    def test_deposits_involving(self, client):
        results = (
            client.aave.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposits_involving_label(self, client):
        results = (
            client.aave.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposits_involving_category(self, client):
        results = (
            client.aave.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_borrows_involving(self, client):
        results = (
            client.aave.borrows()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)

    # -- multi-value involving filters ---------------------------------------

    def test_multi_value_involving(self, client):
        results = (
            client.aave.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_label(self, client):
        results = (
            client.aave.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_category(self, client):
        results = (
            client.aave.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)


# ===========================================================================
# Uniswap integration tests (matches api/test_uniswap.py)
# ===========================================================================


class TestUniswapIntegration:
    """Test Uniswap queries against the live API."""

    # -- event types ---------------------------------------------------------

    def test_swaps_as_dict(self, client):
        results = (
            client.uniswap.swaps("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposits_as_dict(self, client):
        results = (
            client.uniswap.deposits("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_withdrawals_as_dict(self, client):
        results = (
            client.uniswap.withdrawals("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_collects_as_dict(self, client):
        results = (
            client.uniswap.collects("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    # -- involving filters ---------------------------------------------------

    def test_swaps_involving(self, client):
        results = (
            client.uniswap.swaps("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_swaps_involving_label(self, client):
        results = (
            client.uniswap.swaps("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_swaps_involving_category(self, client):
        results = (
            client.uniswap.swaps("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    # -- multi-value involving filters ---------------------------------------

    def test_multi_value_involving(self, client):
        results = (
            client.uniswap.swaps("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_label(self, client):
        results = (
            client.uniswap.swaps("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_category(self, client):
        results = (
            client.uniswap.swaps("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)


# ===========================================================================
# Lido integration tests (matches api/test_lido.py)
# ===========================================================================


class TestLidoIntegration:
    """Test Lido queries against the live API."""

    # -- event types ---------------------------------------------------------

    def test_deposits_as_dict(self, client):
        results = (
            client.lido.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_withdrawal_requests_as_dict(self, client):
        results = (
            client.lido.withdrawal_requests()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_withdrawals_claimed_as_dict(self, client):
        results = (
            client.lido.withdrawals_claimed()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    # -- involving filters ---------------------------------------------------

    def test_deposits_involving(self, client):
        results = (
            client.lido.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposits_involving_label(self, client):
        results = (
            client.lido.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposits_involving_category(self, client):
        results = (
            client.lido.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    # -- multi-value involving filters ---------------------------------------

    def test_multi_value_involving(self, client):
        results = (
            client.lido.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_label(self, client):
        results = (
            client.lido.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_category(self, client):
        results = (
            client.lido.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)


# ===========================================================================
# Stader integration tests (matches api/test_stader.py)
# ===========================================================================


class TestStaderIntegration:
    """Test Stader queries against the live API."""

    # -- event types ---------------------------------------------------------

    def test_deposits_as_dict(self, client):
        results = (
            client.stader.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_withdrawal_requests_as_dict(self, client):
        results = (
            client.stader.withdrawal_requests()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_withdrawals_as_dict(self, client):
        results = (
            client.stader.withdrawals()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    # -- involving filters ---------------------------------------------------

    def test_deposits_involving(self, client):
        results = (
            client.stader.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposits_involving_label(self, client):
        results = (
            client.stader.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposits_involving_category(self, client):
        results = (
            client.stader.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    # -- multi-value involving filters ---------------------------------------

    def test_multi_value_involving(self, client):
        results = (
            client.stader.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_label(self, client):
        results = (
            client.stader.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_category(self, client):
        results = (
            client.stader.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)


# ===========================================================================
# Threshold integration tests (matches api/test_threshold.py)
# ===========================================================================


class TestThresholdIntegration:
    """Test Threshold queries against the live API."""

    # -- event types ---------------------------------------------------------

    def test_deposits_as_dict(self, client):
        results = (
            client.threshold.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposit_requests_as_dict(self, client):
        results = (
            client.threshold.deposit_requests()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_withdrawal_requests_as_dict(self, client):
        results = (
            client.threshold.withdrawal_requests()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_withdrawals_as_dict(self, client):
        results = (
            client.threshold.withdrawals()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    # -- involving filters ---------------------------------------------------

    def test_deposits_involving(self, client):
        results = (
            client.threshold.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposits_involving_label(self, client):
        results = (
            client.threshold.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_deposits_involving_category(self, client):
        results = (
            client.threshold.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    # -- multi-value involving filters ---------------------------------------

    def test_multi_value_involving(self, client):
        results = (
            client.threshold.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_label(self, client):
        results = (
            client.threshold.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_multi_value_involving_category(self, client):
        results = (
            client.threshold.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange", "defi")
            .as_dict()
        )
        assert isinstance(results, list)


# ===========================================================================
# Verbose mode tests (matches api/test_verbose.py)
# ===========================================================================


class TestVerboseMode:
    """Test verbose mode across different protocols."""

    def test_erc20_verbose_includes_metadata(self, client):
        df = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .verbose()
            .as_df()
        )
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            for col in ("name", "network", "tx_id"):
                assert col in df.columns, f"Missing verbose column: {col}"

    def test_erc20_default_drops_verbose_columns(self, client):
        df = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_df()
        )
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            for col in ("name", "network", "tx_id"):
                assert col not in df.columns, f"Verbose column should be dropped: {col}"

    def test_native_token_verbose(self, client):
        df = (
            client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .verbose()
            .as_df()
        )
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            assert "name" in df.columns
            assert "network" in df.columns

    def test_aave_verbose(self, client):
        df = (
            client.aave.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .verbose()
            .as_df()
        )
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            assert "name" in df.columns
            assert "network" in df.columns

    def test_lido_verbose(self, client):
        df = (
            client.lido.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .verbose()
            .as_df()
        )
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            assert "name" in df.columns
            assert "network" in df.columns


# ===========================================================================
# Time-based query tests (matches api/test_time_queries.py)
# ===========================================================================


class TestTimeQueries:
    """Test time-based queries using since/until parameters."""

    def test_unix_timestamp_range(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .time_range("1700000000", "1700100000")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_iso8601_time_range(self, client):
        results = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .time_range("2023-11-14T00:00:00Z", "2023-11-15T00:00:00Z")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_native_token_unix_time_range(self, client):
        results = (
            client.native_token.transfers()
            .network("ETH")
            .time_range("1700000000", "1700100000")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_aave_unix_time_range(self, client):
        results = (
            client.aave.deposits()
            .network("ETH")
            .time_range("1700000000", "1700100000")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_uniswap_unix_time_range(self, client):
        results = (
            client.uniswap.swaps("WETH", "USDC", 3000)
            .network("ETH")
            .time_range("1700000000", "1700100000")
            .as_dict()
        )
        assert isinstance(results, list)

    def test_lido_unix_time_range(self, client):
        results = (
            client.lido.deposits()
            .network("ETH")
            .time_range("1700000000", "1700100000")
            .as_dict()
        )
        assert isinstance(results, list)


# ===========================================================================
# Output format tests (matches api/test_format_comprehensive.py)
# ===========================================================================


class TestOutputFormats:
    """Test different output formats."""

    def test_as_df_pandas(self, client):
        df = (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_df("pandas")
        )
        assert isinstance(df, pd.DataFrame)

    def test_as_file_csv(self, client, tmp_path):
        path = str(tmp_path / "transfers.csv")
        (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_file(path)
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_as_file_parquet(self, client, tmp_path):
        path = str(tmp_path / "transfers.parquet")
        (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_file(path)
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_as_file_json(self, client, tmp_path):
        import json

        path = str(tmp_path / "transfers.json")
        (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_file(path)
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, list)


# ===========================================================================
# Client-side validation tests (matches api/test_involving.py validation)
# ===========================================================================


class TestClientSideValidation:
    """Test that client-side validation catches errors before making API calls."""

    def test_involving_with_sender_raises_before_api_call(self, client):
        with pytest.raises(ValidationError, match="Cannot combine"):
            (
                client.erc20.transfers("USDT")
                .network("ETH")
                .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
                .involving(TEST_ADDRESS)
                .sender(TEST_ADDRESS)
                .as_dict()
            )

    def test_involving_label_with_sender_label_raises(self, client):
        with pytest.raises(ValidationError, match="Cannot combine"):
            (
                client.erc20.transfers("USDT")
                .network("ETH")
                .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
                .involving_label("Binance")
                .sender_label("Coinbase")
                .as_dict()
            )

    def test_sender_with_sender_label_raises(self, client):
        with pytest.raises(ValidationError, match="Cannot combine"):
            (
                client.erc20.transfers("USDT")
                .network("ETH")
                .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
                .sender(TEST_ADDRESS)
                .sender_label("Binance")
                .as_dict()
            )

    def test_sql_injection_in_label_raises(self, client):
        with pytest.raises(ValidationError, match="unsafe characters"):
            (
                client.erc20.transfers("USDT")
                .network("ETH")
                .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
                .involving_label("Binance'; DROP TABLE--")
                .as_dict()
            )

    def test_backslash_in_category_raises(self, client):
        with pytest.raises(ValidationError, match="unsafe characters"):
            (
                client.erc20.transfers("USDT")
                .network("ETH")
                .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
                .involving_category("exchange\\test")
                .as_dict()
            )


# ===========================================================================
# Async integration tests (expanded to match sync coverage)
# ===========================================================================


class TestAsyncIntegration:
    """Test async client against the live API."""

    @pytest.mark.asyncio
    async def test_basic_transfer_as_dict(self, async_client):
        results = await (
            async_client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_involving_label_filter(self, async_client):
        results = await (
            async_client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_sender_label_filter(self, async_client):
        results = await (
            async_client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender_label("Binance")
            .as_dict()
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_as_df(self, async_client):
        df = await (
            async_client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance")
            .as_df()
        )
        assert isinstance(df, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_native_token_involving_category(self, async_client):
        results = await (
            async_client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_category("exchange")
            .as_dict()
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_aave_deposits(self, async_client):
        results = await (
            async_client.aave.deposits()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_uniswap_swaps(self, async_client):
        results = await (
            async_client.uniswap.swaps("WETH", "USDC", 3000)
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .as_dict()
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_native_token_multi_value_sender(self, async_client):
        results = await (
            async_client.native_token.transfers()
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .sender(TEST_ADDRESS, TEST_ADDRESS_2)
            .as_dict()
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_multi_value_involving_label(self, async_client):
        results = await (
            async_client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(ETH_BLOCK_START, ETH_BLOCK_END)
            .involving_label("Binance", "Coinbase")
            .as_dict()
        )
        assert isinstance(results, list)
