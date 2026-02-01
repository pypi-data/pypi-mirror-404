"""Data provider interfaces and protocols.

All data providers implement the DataProvider protocol for consistency.
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional, Protocol, runtime_checkable

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
    TimeFrame,
)


@runtime_checkable
class DataProvider(Protocol):
    """Protocol for market data providers.
    
    Providers must implement the methods they support.
    Unsupported methods should raise NotImplementedError.
    """
    
    @property
    def name(self) -> str:
        """Provider identifier (e.g., 'alpaca', 'fred')."""
        ...
    
    @property
    def supported_assets(self) -> List[str]:
        """List of supported asset types (e.g., ['stocks', 'crypto', 'options'])."""
        ...
    
    # --- Market Data ---
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Bar]:
        """Get historical bar/candlestick data."""
        ...
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get latest quotes for symbols."""
        ...
    
    def get_trades(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Trade]:
        """Get historical trade data."""
        ...
    
    # --- Streaming ---
    
    async def stream_quotes(self, symbols: List[str]) -> AsyncIterator[Quote]:
        """Stream real-time quotes."""
        ...
    
    async def stream_trades(self, symbols: List[str]) -> AsyncIterator[Trade]:
        """Stream real-time trades."""
        ...
    
    async def stream_bars(
        self, symbols: List[str], timeframe: TimeFrame
    ) -> AsyncIterator[Bar]:
        """Stream real-time bars."""
        ...


@runtime_checkable  
class NewsProvider(Protocol):
    """Protocol for news data providers."""
    
    def get_news(
        self,
        symbols: Optional[List[str]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[News]:
        """Get news articles."""
        ...


@runtime_checkable
class OptionsProvider(Protocol):
    """Protocol for options data providers."""
    
    def get_options_chain(
        self,
        underlying: str,
        expiration: Optional[datetime] = None,
        option_type: Optional[str] = None,  # "call" or "put"
        strike_price_gte: Optional[float] = None,
        strike_price_lte: Optional[float] = None,
    ) -> List[OptionContract]:
        """Get options chain for underlying."""
        ...
    
    def get_option_quotes(self, symbols: List[str]) -> List[OptionQuote]:
        """Get quotes for option symbols."""
        ...


@runtime_checkable
class EconomicDataProvider(Protocol):
    """Protocol for economic data providers (FRED, etc.)."""
    
    def get_series(
        self,
        series_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[EconomicSeries]:
        """Get economic data series."""
        ...
    
    def search_series(self, query: str, limit: int = 50) -> List[Dict[str, str]]:
        """Search for available series."""
        ...


@runtime_checkable
class FilingsProvider(Protocol):
    """Protocol for SEC filings providers."""
    
    def get_filings(
        self,
        symbol: Optional[str] = None,
        cik: Optional[str] = None,
        form_type: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Filing]:
        """Get SEC filings."""
        ...
    
    def get_filing_content(self, accession_number: str) -> str:
        """Get full filing content."""
        ...


@runtime_checkable
class SocialDataProvider(Protocol):
    """Protocol for social sentiment data providers."""
    
    def get_posts(
        self,
        symbols: Optional[List[str]] = None,
        source: Optional[str] = None,  # "reddit", "stocktwits"
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[SocialPost]:
        """Get social media posts."""
        ...
    
    def get_trending(self, source: Optional[str] = None, limit: int = 20) -> List[str]:
        """Get trending symbols."""
        ...
    
    def get_sentiment(
        self, symbol: str, source: Optional[str] = None
    ) -> Dict[str, float]:
        """Get aggregated sentiment for symbol."""
        ...
