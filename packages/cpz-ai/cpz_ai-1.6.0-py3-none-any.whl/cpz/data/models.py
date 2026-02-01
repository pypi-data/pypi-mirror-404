"""Data models for the CPZ data layer.

All models use Pydantic for validation and serialization.
Models are designed to be provider-agnostic with consistent field names.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TimeFrame(str, Enum):
    """Standard timeframes for bar data."""
    MINUTE_1 = "1Min"
    MINUTE_5 = "5Min"
    MINUTE_15 = "15Min"
    MINUTE_30 = "30Min"
    HOUR_1 = "1Hour"
    HOUR_4 = "4Hour"
    DAY = "1Day"
    WEEK = "1Week"
    MONTH = "1Month"
    
    @classmethod
    def from_string(cls, value: str) -> "TimeFrame":
        """Parse timeframe from various string formats."""
        mapping = {
            "1m": cls.MINUTE_1, "1min": cls.MINUTE_1, "1minute": cls.MINUTE_1,
            "5m": cls.MINUTE_5, "5min": cls.MINUTE_5, "5minute": cls.MINUTE_5,
            "15m": cls.MINUTE_15, "15min": cls.MINUTE_15, "15minute": cls.MINUTE_15,
            "30m": cls.MINUTE_30, "30min": cls.MINUTE_30, "30minute": cls.MINUTE_30,
            "1h": cls.HOUR_1, "1hour": cls.HOUR_1, "60m": cls.HOUR_1,
            "4h": cls.HOUR_4, "4hour": cls.HOUR_4, "240m": cls.HOUR_4,
            "1d": cls.DAY, "1day": cls.DAY, "d": cls.DAY, "day": cls.DAY, "daily": cls.DAY,
            "1w": cls.WEEK, "1week": cls.WEEK, "w": cls.WEEK, "week": cls.WEEK, "weekly": cls.WEEK,
            "1mo": cls.MONTH, "1month": cls.MONTH, "mo": cls.MONTH, "month": cls.MONTH, "monthly": cls.MONTH,
        }
        normalized = value.lower().replace(" ", "").replace("-", "").replace("_", "")
        if normalized in mapping:
            return mapping[normalized]
        # Try direct enum value match
        for member in cls:
            if member.value.lower() == normalized:
                return member
        raise ValueError(f"Unknown timeframe: {value}")


class Bar(BaseModel):
    """OHLCV bar data for any asset type."""
    symbol: str
    timestamp: datetime = Field(alias="ts")
    open: float = Field(alias="o")
    high: float = Field(alias="h")
    low: float = Field(alias="l")
    close: float = Field(alias="c")
    volume: float = Field(alias="v")
    vwap: Optional[float] = Field(default=None, alias="vw")
    trade_count: Optional[int] = Field(default=None, alias="n")
    
    class Config:
        populate_by_name = True


class Quote(BaseModel):
    """Level 1 quote data."""
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow, alias="ts")
    bid: float
    ask: float
    bid_size: float = Field(default=0, alias="bs")
    ask_size: float = Field(default=0, alias="as_")
    
    class Config:
        populate_by_name = True


class Trade(BaseModel):
    """Individual trade/tick data."""
    symbol: str
    timestamp: datetime = Field(alias="ts")
    price: float = Field(alias="p")
    size: float = Field(alias="s")
    exchange: Optional[str] = Field(default=None, alias="x")
    conditions: Optional[List[str]] = Field(default=None, alias="c")
    
    class Config:
        populate_by_name = True


class News(BaseModel):
    """News article data."""
    id: str
    headline: str
    summary: Optional[str] = None
    author: Optional[str] = None
    source: str
    url: Optional[str] = None
    symbols: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        populate_by_name = True


class OptionQuote(BaseModel):
    """Options quote data."""
    symbol: str  # Option symbol (e.g., AAPL240119C00150000)
    underlying: str  # Underlying symbol (e.g., AAPL)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    bid: float
    ask: float
    bid_size: int = 0
    ask_size: int = 0
    last: Optional[float] = None
    volume: int = 0
    open_interest: int = 0
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    
    class Config:
        populate_by_name = True


class OptionContract(BaseModel):
    """Option contract metadata."""
    symbol: str  # Option symbol
    underlying: str
    expiration: datetime
    strike: float
    option_type: str  # "call" or "put"
    style: str = "american"  # "american" or "european"
    
    class Config:
        populate_by_name = True


class EconomicSeries(BaseModel):
    """Economic data series (FRED, etc.)."""
    series_id: str
    title: str
    observation_date: datetime
    value: Optional[float] = None  # None for missing observations
    units: Optional[str] = None
    frequency: Optional[str] = None
    seasonal_adjustment: Optional[str] = None
    
    class Config:
        populate_by_name = True


class Filing(BaseModel):
    """SEC filing data."""
    accession_number: str
    cik: str
    company_name: str
    form_type: str
    filed_date: datetime
    accepted_date: Optional[datetime] = None
    document_url: Optional[str] = None
    filing_url: Optional[str] = None
    items: Optional[List[str]] = None  # For 8-K item numbers
    
    class Config:
        populate_by_name = True


class SocialPost(BaseModel):
    """Social media post/message data."""
    id: str
    source: str  # "reddit", "stocktwits", etc.
    content: str
    author: Optional[str] = None
    symbols: List[str] = Field(default_factory=list)
    created_at: datetime
    sentiment: Optional[str] = None  # "bullish", "bearish", "neutral"
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    likes: int = 0
    comments: int = 0
    url: Optional[str] = None
    
    class Config:
        populate_by_name = True


class DataRequest(BaseModel):
    """Standard data request parameters."""
    symbols: List[str]
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = 1000
    timeframe: Optional[TimeFrame] = None
    
    class Config:
        populate_by_name = True
