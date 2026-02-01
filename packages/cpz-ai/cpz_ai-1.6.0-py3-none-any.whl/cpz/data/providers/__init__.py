"""Data providers for the CPZ data layer.

All providers share a common interface for historical data:
    - get_bars(symbol, timeframe, start, end, limit) -> List[Bar]
    - get_quotes(symbols) -> List[Quote]

Provider credentials are automatically fetched from the CPZAI platform.
"""

from .alpaca import AlpacaDataProvider
from .alphavantage import AlphaVantageProvider
from .databento import DatabentoProvider
from .fred import FREDProvider
from .edgar import EDGARProvider
from .polygon import PolygonProvider
from .twelve import TwelveDataProvider
from .yfinance import YFinanceProvider
from .social import RedditProvider, StocktwitsProvider

__all__ = [
    # Market Data Providers
    "AlpacaDataProvider",
    "AlphaVantageProvider",
    "DatabentoProvider",
    "PolygonProvider",
    "TwelveDataProvider",
    "YFinanceProvider",
    # Economic & Filings
    "FREDProvider",
    "EDGARProvider",
    # Social
    "RedditProvider",
    "StocktwitsProvider",
]
