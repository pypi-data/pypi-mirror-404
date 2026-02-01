# jyapystock

A Python library to fetch live and historical prices for Indian and American stocks.

## Status Badges

[![CI](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci.yml/badge.svg)](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci.yml)

[![yfinance tests](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-yfinance.yml/badge.svg)](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-yfinance.yml)
[![Alpha Vantage tests](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-alphavantage.yml/badge.svg)](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-alphavantage.yml)
[![NASDAQ tests](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-nasdaq.yml/badge.svg)](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-nasdaq.yml)
[![NYSE tests](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-nyse.yml/badge.svg)](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-nyse.yml)
[![NSE tests](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-nse.yml/badge.svg)](https://github.com/JustYetAnother/jyapystock/actions/workflows/ci-nse.yml)

## Features

- Live price and historical price support with timestamp and % change data
- Indian (NSE) and American (NYSE/NASDAQ) stocks
- Multiple data sources: yfinance, NASDAQ, NSE (for India), Alpha Vantage (optional API key)
- Auto-fallback: tries available sources in order based on country and API key availability
- Country support: `India` and `USA` with automatic symbol variant detection (e.g., `.NS`, `.BO` for Indian stocks)

## Installation

```bash
pip install jyapystock
```

## Installation for Development

To install locally for development:

```bash
# Install editable for development
pip install -e .

# Or install for local use
pip install .
```

For development and CI reproducibility, install pinned dev dependencies:

```bash
pip install -r requirements-dev.txt
```

## Usage

### Basic Usage - USA Stocks

```python
from jyapystock import StockPriceProvider

# Using yfinance (default)
provider = StockPriceProvider(country="USA")
result = provider.get_live_price("AAPL")
# Returns: {'timestamp': '2025-12-24T00:00:00-05:00', 'price': 273.81, 'change_percent': 0.53}
```

### Indian Stocks with NSE

```python
from jyapystock import StockPriceProvider

# Using NSE (National Stock Exchange)
provider = StockPriceProvider(country="India", source="nse")
result = provider.get_live_price("SBIN")
# Returns: {'timestamp': '24-Dec-2025 16:00:00', 'price': 968.85, 'change_percent': -0.31}

# Using yfinance for India (auto-tries .NS and .BO variants)
provider = StockPriceProvider(country="India")
result = provider.get_live_price("RELIANCE")
```

### Historical Data

```python
# Get historical prices
hist = provider.get_historical_price("AAPL", "2023-01-01", "2023-01-31")
# Returns list of records with date/open/high/low/close/volume
```

### Using NASDAQ Provider

```python
provider = StockPriceProvider(country="USA", source="nasdaq")
result = provider.get_live_price("AAPL")
```

### Using Alpha Vantage (requires API key)

```python
provider = StockPriceProvider(
    country="USA", 
    source="alphavantage", 
    alpha_vantage_api_key="YOUR_API_KEY"
)
result = provider.get_live_price("AAPL")
```

## Supported Sources

- **yfinance**: Free, supports most global stocks (USA & India)
- **NASDAQ**: Free, USA stocks only
- **NSE**: Free, Indian stocks only (via National Stock Exchange)
- **Alpha Vantage**: Free tier with limits, requires API key, supports global stocks
- **NYSE**: Free, USA stocks only

## Testing
Install library in editable mode
```bash
pip install -e .
```
Run tests
```bash
python -m unittest discover tests

# Run provider-specific tests
PROVIDER=yfinance python -m unittest discover tests
PROVIDER=nse python -m unittest discover tests
PROVIDER=nasdaq python -m unittest discover tests
PROVIDER=alphavantage python -m unittest discover tests
```

## License

MIT
