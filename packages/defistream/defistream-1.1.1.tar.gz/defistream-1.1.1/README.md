# DeFiStream Python Client

Official Python client for the [DeFiStream API](https://defistream.dev).

## Getting an API Key

To use the DeFiStream API, you need to sign up for an account at [defistream.dev](https://defistream.dev) to obtain your API key.

## Installation

```bash
pip install defistream
```

This includes pandas and pyarrow by default for DataFrame support.

With polars support (in addition to pandas):
```bash
pip install defistream[polars]
```

## Quick Start

```python
from defistream import DeFiStream

# Initialize client (reads DEFISTREAM_API_KEY from environment if not provided)
client = DeFiStream()

# Or with explicit API key
client = DeFiStream(api_key="dsk_your_api_key")

# Query ERC20 transfers using builder pattern
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_df()
)

print(df.head())
```

## Features

- **Builder pattern**: Fluent query API with chainable methods
- **Type-safe**: Full type hints and Pydantic models
- **Multiple formats**: DataFrame (pandas/polars), CSV, Parquet, JSON
- **Async support**: Native async/await with `AsyncDeFiStream`
- **All protocols**: ERC20, AAVE, Uniswap, Lido, Stader, Threshold, Native tokens

## Supported Protocols

| Protocol | Events |
|----------|--------|
| ERC20 | `transfers` |
| Native Token | `transfers` |
| AAVE V3 | `deposits`, `withdrawals`, `borrows`, `repays`, `flashloans`, `liquidations` |
| Uniswap V3 | `swaps`, `deposits`, `withdrawals`, `collects` |
| Lido | `deposits`, `withdrawal_requests`, `withdrawals_claimed`, `l2_deposits`, `l2_withdrawal_requests` |
| Stader | `deposits`, `withdrawal_requests`, `withdrawals` |
| Threshold | `deposit_requests`, `deposits`, `withdrawal_requests`, `withdrawals` |

## Usage Examples

### Builder Pattern

The client uses a fluent builder pattern. The query is only executed when you call a terminal method like `as_df()`, `as_file()`, or `as_dict()`.

```python
from defistream import DeFiStream

client = DeFiStream()

# Build query step by step
query = client.erc20.transfers("USDT")
query = query.network("ETH")
query = query.block_range(21000000, 21010000)
query = query.min_amount(1000)

# Execute and get DataFrame
df = query.as_df()

# Or chain everything
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .min_amount(1000)
    .as_df()
)
```

### ERC20 Transfers

```python
# Get USDT transfers over 10,000 USDT
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .min_amount(10000)
    .as_df()
)

# Filter by sender
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .sender("0x28c6c06298d514db089934071355e5743bf21d60")
    .as_df()
)
```

### AAVE Events

```python
# Get deposits
df = (
    client.aave.deposits()
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_df()
)

# Use a specific market type on ETH (Core, Prime, or EtherFi)
df = (
    client.aave.deposits()
    .network("ETH")
    .block_range(21000000, 21010000)
    .eth_market_type("Prime")
    .as_df()
)
```

### Uniswap Swaps

```python
# Get swaps for WETH/USDC pool with 0.05% fee tier
df = (
    client.uniswap.swaps("WETH", "USDC", 500)
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_df()
)

# Or build with chain methods
df = (
    client.uniswap.swaps()
    .symbol0("WETH")
    .symbol1("USDC")
    .fee(500)
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_df()
)
```

### Native Token Transfers

```python
# Get ETH transfers >= 1 ETH
df = (
    client.native_token.transfers()
    .network("ETH")
    .block_range(21000000, 21010000)
    .min_amount(1.0)
    .as_df()
)
```

### Label & Category Filters

```python
# Get USDT transfers involving Binance wallets
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .involving_label("Binance")
    .as_df()
)

# Get USDT transfers FROM exchanges TO DeFi protocols
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .sender_category("exchange")
    .receiver_category("defi")
    .as_df()
)

# Get AAVE deposits involving exchange addresses
df = (
    client.aave.deposits()
    .network("ETH")
    .block_range(21000000, 21010000)
    .involving_category("exchange")
    .as_df()
)

# Get native ETH transfers FROM Binance or Coinbase (multi-value)
df = (
    client.native_token.transfers()
    .network("ETH")
    .block_range(21000000, 21010000)
    .sender_label("Binance,Coinbase")
    .as_df()
)
```

### Verbose Mode

By default, responses omit metadata fields to reduce payload size. Use `.verbose()` to include all fields:

```python
# Default: compact response (no tx_hash, tx_id, log_index, network, name)
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_df()
)

# Verbose: includes all metadata fields
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .verbose()
    .as_df()
)
```

### Return as DataFrame

```python
# As pandas DataFrame (default)
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_df()
)

# As polars DataFrame
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_df("polars")
)
```

### Save to File

Format is automatically determined by file extension:

```python
# Save as Parquet (recommended for large datasets)
(
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21100000)
    .as_file("transfers.parquet")
)

# Save as CSV
(
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21100000)
    .as_file("transfers.csv")
)

# Save as JSON
(
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_file("transfers.json")
)
```

### Return as Dictionary (JSON)

For small queries, you can get results as a list of dictionaries:

```python
transfers = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_dict()
)

for transfer in transfers:
    print(f"{transfer['sender']} -> {transfer['receiver']}: {transfer['amount']}")
```

> **Note:** `as_dict()` and `as_file("*.json")` use JSON format which has a **10,000 block limit**. For larger block ranges, use `as_df()` or `as_file()` with `.parquet` or `.csv` extensions, which support up to 1,000,000 blocks.

### Context Manager

Both sync and async clients support context managers to automatically close connections:

```python
# Sync
with DeFiStream() as client:
    df = (
        client.erc20.transfers("USDT")
        .network("ETH")
        .block_range(21000000, 21010000)
        .as_df()
    )
```

### Async Usage

```python
import asyncio
from defistream import AsyncDeFiStream

async def main():
    async with AsyncDeFiStream() as client:
        df = await (
            client.erc20.transfers("USDT")
            .network("ETH")
            .block_range(21000000, 21010000)
            .as_df()
        )
        print(f"Found {len(df)} transfers")

asyncio.run(main())
```

### List Available Decoders

```python
client = DeFiStream()
decoders = client.decoders()
print(decoders)  # ['native_token', 'erc20', 'aave', 'uniswap', 'lido', 'stader', 'threshold']
```

## Configuration

### Environment Variables

```bash
export DEFISTREAM_API_KEY=dsk_your_api_key
export DEFISTREAM_BASE_URL=https://api.defistream.dev/v1  # optional
```

```python
from defistream import DeFiStream

# API key from environment
client = DeFiStream()

# Or explicit
client = DeFiStream(api_key="dsk_...", base_url="https://api.defistream.dev/v1")
```

### Timeout and Retries

```python
client = DeFiStream(
    api_key="dsk_...",
    timeout=60.0,  # seconds
    max_retries=3
)
```

## Error Handling

```python
from defistream import DeFiStream
from defistream.exceptions import (
    DeFiStreamError,
    AuthenticationError,
    QuotaExceededError,
    RateLimitError,
    ValidationError
)

client = DeFiStream()

try:
    df = (
        client.erc20.transfers("USDT")
        .network("ETH")
        .block_range(21000000, 21010000)
        .as_df()
    )
except AuthenticationError:
    print("Invalid API key")
except QuotaExceededError as e:
    print(f"Quota exceeded. Remaining: {e.remaining}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
except ValidationError as e:
    print(f"Invalid request: {e.message}")
except DeFiStreamError as e:
    print(f"API error: {e}")
```

## Response Headers

Access rate limit and quota information:

```python
df = (
    client.erc20.transfers("USDT")
    .network("ETH")
    .block_range(21000000, 21010000)
    .as_df()
)

# Access response metadata
print(f"Rate limit: {client.last_response.rate_limit}")
print(f"Remaining quota: {client.last_response.quota_remaining}")
print(f"Request cost: {client.last_response.request_cost}")
```

## Builder Methods Reference

### Common Methods (all protocols)

| Method | Description |
|--------|-------------|
| `.network(net)` | Set network (ETH, ARB, BASE, OP, POLYGON, etc.) |
| `.start_block(n)` | Set starting block number |
| `.end_block(n)` | Set ending block number |
| `.block_range(start, end)` | Set both start and end blocks |
| `.start_time(ts)` | Set starting time (ISO format or Unix timestamp) |
| `.end_time(ts)` | Set ending time (ISO format or Unix timestamp) |
| `.time_range(start, end)` | Set both start and end times |
| `.verbose()` | Include all metadata fields |

### Protocol-Specific Parameters

| Method | Protocols | Description |
|--------|-----------|-------------|
| `.token(symbol)` | ERC20 | Token symbol (USDT, USDC) or contract address (required) |
| `.sender(*addrs)` | ERC20, Native | Filter by sender address (multi-value) |
| `.receiver(*addrs)` | ERC20, Native | Filter by receiver address (multi-value) |
| `.involving(*addrs)` | All | Filter by any involved address (multi-value) |
| `.from_address(*addrs)` | ERC20, Native | Alias for `.sender()` |
| `.to_address(*addrs)` | ERC20, Native | Alias for `.receiver()` |
| `.min_amount(amt)` | ERC20, Native | Minimum transfer amount |
| `.max_amount(amt)` | ERC20, Native | Maximum transfer amount |
| `.eth_market_type(type)` | AAVE | Market type for ETH: 'Core', 'Prime', 'EtherFi' |
| `.symbol0(sym)` | Uniswap | First token symbol (required) |
| `.symbol1(sym)` | Uniswap | Second token symbol (required) |
| `.fee(tier)` | Uniswap | Fee tier: 100, 500, 3000, 10000 (required) |

### Address Label & Category Filters

Filter events by entity names or categories using the labels database. Available on all protocols.

| Method | Protocols | Description |
|--------|-----------|-------------|
| `.involving_label(label)` | All | Filter where any involved address matches a label substring (e.g., "Binance") |
| `.involving_category(cat)` | All | Filter where any involved address matches a category (e.g., "exchange") |
| `.sender_label(label)` | ERC20, Native | Filter sender by label substring |
| `.sender_category(cat)` | ERC20, Native | Filter sender by category |
| `.receiver_label(label)` | ERC20, Native | Filter receiver by label substring |
| `.receiver_category(cat)` | ERC20, Native | Filter receiver by category |

**Multi-value support:** Pass multiple values as separate arguments (e.g., `.sender_label("Binance", "Coinbase")`) or as a comma-separated string (e.g., `.sender_label("Binance,Coinbase")`). Both forms are equivalent.

**Mutual exclusivity:** Within each slot (involving/sender/receiver), only one of address/label/category can be set. `involving*` filters cannot be combined with `sender*`/`receiver*` filters.

### Terminal Methods

| Method | Description |
|--------|-------------|
| `.as_df()` | Execute and return pandas DataFrame |
| `.as_df("polars")` | Execute and return polars DataFrame |
| `.as_file(path)` | Execute and save to file (format from extension) |
| `.as_file(path, format="csv")` | Execute and save with explicit format |
| `.as_dict()` | Execute and return list of dicts (JSON, 10K block limit) |

## License

MIT License
