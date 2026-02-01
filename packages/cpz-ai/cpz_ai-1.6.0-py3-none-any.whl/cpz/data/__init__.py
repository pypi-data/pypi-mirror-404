"""CPZ Data Layer - Unified market data access across multiple providers.

Usage:
    from cpz import CPZClient
    
    client = CPZClient()
    
    # Simple unified interface
    bars = client.data.bars("AAPL", timeframe="1D", limit=100)
    quotes = client.data.quotes(["AAPL", "MSFT"])
    news = client.data.news("AAPL")
    
    # Economic data
    gdp = client.data.economic("GDP")
    
    # SEC filings
    filings = client.data.filings("AAPL", form="10-K")
    
    # Social sentiment
    posts = client.data.social("AAPL", source="reddit")
    
    # Direct provider access for power users
    options = client.data.alpaca.options_chain("AAPL")
    series = client.data.fred.series("UNRATE")
"""

from .models import (
    Bar,
    Quote,
    Trade,
    News,
    OptionQuote,
    OptionContract,
    EconomicSeries,
    Filing,
    SocialPost,
    DataRequest,
    TimeFrame,
)
from .interfaces import DataProvider
from .client import DataClient

__all__ = [
    # Models
    "Bar",
    "Quote", 
    "Trade",
    "News",
    "OptionQuote",
    "OptionContract",
    "EconomicSeries",
    "Filing",
    "SocialPost",
    "DataRequest",
    "TimeFrame",
    # Interfaces
    "DataProvider",
    # Client
    "DataClient",
]
