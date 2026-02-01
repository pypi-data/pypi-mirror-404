<p align="center">
  <a href="https://www.cpz-lab.com/">
    <img src="https://drive.google.com/uc?id=1JY-PoPj9GHmpq3bZLC7WyJLbGuT1L3hN" alt="CPZAI" width="180">
  </a>
</p>

<h1 align="center">CPZAI Python SDK</h1>

<p align="center">
  <strong>Unified Trading, Market Data, and Analytics Platform</strong>
</p>

<p align="center">
  <a href="https://github.com/CPZ-Lab/cpz-py"><img src="https://img.shields.io/badge/version-1.5.0-blue.svg" alt="Version"></a>
  <a href="https://github.com/CPZ-Lab/cpz-py"><img src="https://img.shields.io/badge/coverage-85%25%2B-brightgreen.svg" alt="Coverage"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg" alt="Python"></a>
</p>

---

## Overview

The CPZAI Python SDK provides a unified interface for systematic trading and quantitative research:

| Feature | Description |
|---------|-------------|
| **Trading Execution** | Multi-broker order management with audit trails |
| **Market Data** | Stocks, crypto, options via Alpaca and Twelve Data |
| **Economic Data** | 800,000+ FRED time series |
| **SEC Filings** | 10-K, 10-Q, 8-K, insider transactions via EDGAR |
| **Social Sentiment** | Reddit and Stocktwits analysis |
| **Technical Indicators** | 100+ indicators including SMA, EMA, RSI, MACD |

---

## Installation

```bash
pip install cpz-ai
```

---

## Quick Start

```python
from cpz import CPZClient

client = CPZClient()

# Market Data
bars = client.data.bars("AAPL", timeframe="1D", limit=100)
quotes = client.data.quotes(["AAPL", "MSFT", "GOOGL"])
news = client.data.news("TSLA", limit=5)

# Economic Data
gdp = client.data.economic("GDP")
unemployment = client.data.economic("UNRATE")

# SEC Filings
filings = client.data.filings("AAPL", form="10-K")

# Social Sentiment
sentiment = client.data.sentiment("GME")

# Technical Indicators
rsi = client.data.rsi("AAPL", period=14)
macd = client.data.macd("AAPL")

# Trading Execution
client.execution.use_broker("alpaca", environment="paper")
order = client.execution.order(
    symbol="AAPL",
    qty=10,
    side="buy",
    strategy_id="my-strategy"
)
```

---

## Trading

### Broker Configuration

```python
from cpz import CPZClient

client = CPZClient()

# Single account setup
client.execution.use_broker("alpaca", environment="paper")
client.execution.use_broker("alpaca", environment="live")

# Multi-account: Use account_id to select specific account
client.execution.use_broker("alpaca", account_id="PA3FHUB575J3")
```

When `account_id` is provided, the SDK matches credentials by account ID exclusively, ignoring the environment parameter.

### Order Placement

```python
# Simple order placement
order = client.execution.order(
    symbol="AAPL",
    qty=10,
    side="buy",
    strategy_id="my-strategy"
)
print(f"Order: {order.id} - {order.status}")

# Full control with OrderSubmitRequest
from cpz import OrderSubmitRequest, OrderSide, OrderType, TimeInForce

request = OrderSubmitRequest(
    symbol="AAPL",
    side=OrderSide.BUY,
    qty=10,
    order_type=OrderType.LIMIT,
    time_in_force=TimeInForce.GTC,
    limit_price=150.00,
    strategy_id="my-strategy"
)
order = client.execution.submit_order(request)
```

### Account and Positions

```python
account = client.execution.get_account()
print(f"Buying Power: ${account.buying_power:,.2f}")

positions = client.execution.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.qty} shares @ ${pos.avg_entry_price}")
```

---

## Data API

### Market Data

```python
# Stock bars
bars = client.data.bars("AAPL", timeframe="1D", limit=100)
for bar in bars[-5:]:
    print(f"{bar.timestamp}: O={bar.open} H={bar.high} L={bar.low} C={bar.close}")

# Crypto bars
btc = client.data.bars("BTC/USD", timeframe="1H", limit=50)

# Latest quotes
quotes = client.data.quotes(["AAPL", "MSFT", "GOOGL"])

# News articles
news = client.data.news("TSLA", limit=10)

# Options chain
options = client.data.options("AAPL", option_type="call")
```

### Economic Data (FRED)

```python
# Access 800,000+ economic time series
gdp = client.data.economic("GDP")
unemployment = client.data.economic("UNRATE", limit=12)
cpi = client.data.economic("CPIAUCSL")
fed_rate = client.data.economic("FEDFUNDS")

# Search for series
results = client.data.fred.search("housing prices")
```

### SEC Filings (EDGAR)

```python
# Get filings by type
filings = client.data.filings("AAPL", form="10-K", limit=5)

# Get structured financial data
facts = client.data.edgar.get_facts("AAPL")
revenue = client.data.edgar.get_concept("AAPL", "Revenue")

# Insider transactions
insider = client.data.edgar.insider_transactions("TSLA")
```

### Social Sentiment

```python
# Aggregated sentiment
sentiment = client.data.sentiment("GME")
print(f"Score: {sentiment['score']}, Bullish: {sentiment['bullish_pct']:.1%}")

# Trending symbols
trending = client.data.trending()

# Social posts
posts = client.data.social.get_posts(symbols=["AAPL"], source="reddit")
```

### Technical Indicators

> **IMPORTANT**: To use technical indicators, you must have Twelve Data connected
> in the CPZAI platform. Go to the **Data page** and connect your Twelve Data API key.

```python
# Via Twelve Data (100+ indicators available)
# Requires Twelve Data connection on the Data page

# Trend indicators
sma = client.data.sma("AAPL", period=20)
ema = client.data.ema("AAPL", period=20)
bbands = client.data.bbands("AAPL", period=20)
vwap = client.data.vwap("AAPL")
ichimoku = client.data.ichimoku("AAPL")
supertrend = client.data.supertrend("AAPL")

# Momentum indicators
rsi = client.data.rsi("AAPL", period=14)
macd = client.data.macd("AAPL")
stoch = client.data.stoch("AAPL")
adx = client.data.adx("AAPL", period=14)
cci = client.data.cci("AAPL", period=20)
mfi = client.data.mfi("AAPL", period=14)
willr = client.data.willr("AAPL", period=14)

# Volatility indicators
atr = client.data.atr("AAPL", period=14)

# Volume indicators
obv = client.data.obv("AAPL")

# Direct provider access for full control
keltner = client.data.twelve.get_keltner("AAPL", period=20, multiplier=2)
donchian = client.data.twelve.get_donchian("AAPL", period=20)
aroon = client.data.twelve.get_aroon("AAPL", period=14)
force_index = client.data.twelve.get_force_index("AAPL")

# Access ANY TwelveData indicator by name
custom = client.data.indicator("stochrsi", "AAPL", time_period=14)

# Candlestick pattern recognition
patterns = client.data.twelve.get_pattern("cdl_doji", "AAPL")
```

### Direct Provider Access

For advanced use cases, access providers directly:

```python
# Alpaca-specific features
crypto = client.data.alpaca.get_crypto_bars("ETH/USD", "1H")
options = client.data.alpaca.get_options_chain("SPY")

# FRED-specific features
categories = client.data.fred.categories()

# Twelve Data-specific
forex = client.data.twelve.get_forex("EUR/USD")
```

---

## Architecture

```
CPZClient
├── execution          Trading operations
│   ├── use_broker()   Configure broker connection
│   ├── order()        Place orders
│   ├── get_account()  Account information
│   └── get_positions() Current positions
│
├── data               Market and reference data
│   ├── bars()         OHLCV price data
│   ├── quotes()       Real-time quotes
│   ├── news()         News articles
│   ├── options()      Options chains
│   ├── economic()     FRED economic data
│   ├── filings()      SEC EDGAR filings
│   ├── sentiment()    Social sentiment
│   └── [provider]     Direct provider access
│
└── platform           CPZAI platform services
    ├── health()       Platform status
    └── list_tables()  Available data tables
```

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CPZ_AI_API_KEY` | CPZAI API key | Yes |
| `CPZ_AI_SECRET_KEY` | CPZAI API secret | Yes |
| `CPZ_AI_STRATEGY_ID` | Strategy ID for orders | Yes (for trading) |

### Getting Started

1. **Get CPZAI Credentials**: [https://ai.cpz-lab.com/settings?tab=api-keys](https://ai.cpz-lab.com/settings?tab=api-keys)
2. **Configure Trading Accounts**: [https://ai.cpz-lab.com/execution](https://ai.cpz-lab.com/execution)

Alpaca market data uses your trading account credentials automatically.

---

## CLI Reference

```bash
# List available brokers
cpz-ai broker list

# Configure broker connection
cpz-ai broker use alpaca --env paper
cpz-ai broker use alpaca --env live --account-id "YOUR_ACCOUNT_ID"

# Stream quotes
cpz-ai stream quotes AAPL,MSFT,GOOGL --broker alpaca --env paper
```

---

## Error Handling

```python
from cpz.common.errors import CPZBrokerError

try:
    order = client.execution.order(
        symbol="AAPL",
        qty=10,
        side="buy",
        strategy_id="my-strategy"
    )
except CPZBrokerError as e:
    print(f"Order failed: {e}")
```

---

## Testing

```bash
# Run tests
make test

# Run with coverage
pytest --cov=cpz --cov-report=term-missing
```

---

## Python Compatibility

| Version | Status |
|---------|--------|
| Python 3.9 | Supported |
| Python 3.10 | Supported |
| Python 3.11 | Supported |
| Python 3.12 | Supported |

---

## Documentation

- [User Guide](docs/user-guide.md) - Comprehensive usage documentation
- [Contributing](CONTRIBUTING.md) - Contribution guidelines
- [Security](SECURITY.md) - Security policy
- [Changelog](CHANGELOG.md) - Version history

---

## Support

- **Documentation**: [https://ai.cpz-lab.com/](https://ai.cpz-lab.com/)
- **Repository**: [https://github.com/CPZ-Lab/cpz-py](https://github.com/CPZ-Lab/cpz-py)
- **Email**: contact@cpz-lab.com

---

<p align="center">
  <sub>Built by <a href="https://ai.cpz-lab.com/">CPZAI</a></sub>
</p>
