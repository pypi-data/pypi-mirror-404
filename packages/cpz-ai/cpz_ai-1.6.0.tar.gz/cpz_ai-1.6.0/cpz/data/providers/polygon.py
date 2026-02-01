"""Polygon.io data provider.

Real-time and historical market data for stocks, options, forex, and crypto.
Free tier: 5 API calls/minute. Premium plans available.

Docs: https://polygon.io/docs
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from ..models import Bar, Quote, Trade, News, TimeFrame


class PolygonProvider:
    """Polygon.io data provider.
    
    Comprehensive market data with excellent historical coverage.
    
    Usage:
        provider = PolygonProvider(api_key="your_key")
        bars = provider.get_bars("AAPL", start=datetime(2023, 1, 1))
    """
    
    name = "polygon"
    supported_assets = ["stocks", "options", "forex", "crypto"]
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Polygon provider.
        
        Args:
            api_key: Polygon.io API key
        """
        self._api_key = api_key or ""
        
        # Try to get from CPZAI platform if not provided
        if not self._api_key:
            try:
                from ...common.cpz_ai import CPZAIClient
                cpz_client = CPZAIClient.from_env()
                creds = cpz_client.get_data_credentials(provider="polygon")
                self._api_key = creds.get("polygon_api_key", "")
            except Exception:
                pass
        
        if not self._api_key:
            print("[CPZ SDK] Polygon API key not found. Get a key at polygon.io")
    
    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make API request."""
        if params is None:
            params = {}
        params["apiKey"] = self._api_key
        
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def _convert_timeframe(self, tf: TimeFrame) -> tuple[str, int]:
        """Convert TimeFrame to Polygon multiplier and timespan."""
        mapping = {
            TimeFrame.MINUTE_1: (1, "minute"),
            TimeFrame.MINUTE_5: (5, "minute"),
            TimeFrame.MINUTE_15: (15, "minute"),
            TimeFrame.MINUTE_30: (30, "minute"),
            TimeFrame.HOUR_1: (1, "hour"),
            TimeFrame.HOUR_4: (4, "hour"),
            TimeFrame.DAY: (1, "day"),
            TimeFrame.WEEK: (1, "week"),
            TimeFrame.MONTH: (1, "month"),
        }
        return mapping.get(tf, (1, "day"))
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50000,
        adjusted: bool = True,
    ) -> List[Bar]:
        """Get historical bars from Polygon.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum bars (up to 50,000)
            adjusted: Adjust for splits/dividends
            
        Returns:
            List of Bar objects
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        multiplier, timespan = self._convert_timeframe(timeframe)
        
        if start is None:
            start = datetime.utcnow() - timedelta(days=365)
        if end is None:
            end = datetime.utcnow()
        
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        
        endpoint = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_str}/{end_str}"
        
        try:
            data = self._request(endpoint, {
                "adjusted": str(adjusted).lower(),
                "sort": "asc",
                "limit": limit,
            })
            
            if data.get("status") != "OK" or "results" not in data:
                print(f"[CPZ SDK] Polygon returned no data for {symbol}")
                return []
            
            bars: List[Bar] = []
            for r in data["results"]:
                bars.append(Bar(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(r["t"] / 1000),
                    open=float(r["o"]),
                    high=float(r["h"]),
                    low=float(r["l"]),
                    close=float(r["c"]),
                    volume=float(r["v"]),
                    vwap=float(r.get("vw")) if r.get("vw") else None,
                    trade_count=r.get("n"),
                ))
            
            return bars
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Polygon data for {symbol}: {e}")
            return []
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get latest quote from Polygon."""
        try:
            data = self._request(f"/v2/last/nbbo/{symbol}")
            
            if "results" not in data:
                return None
            
            r = data["results"]
            return Quote(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(r.get("t", 0) / 1e9) if r.get("t") else datetime.utcnow(),
                bid=float(r.get("p", 0)),
                ask=float(r.get("P", 0)),
                bid_size=float(r.get("s", 0)),
                ask_size=float(r.get("S", 0)),
            )
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Polygon quote for {symbol}: {e}")
            return None
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get quotes for multiple symbols."""
        quotes: List[Quote] = []
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes.append(quote)
        return quotes
    
    def get_trades(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50000,
    ) -> List[Trade]:
        """Get historical trades from Polygon.
        
        Args:
            symbol: Stock symbol
            start: Start datetime
            end: End datetime
            limit: Maximum trades
            
        Returns:
            List of Trade objects
        """
        if start is None:
            start = datetime.utcnow() - timedelta(days=1)
        
        date_str = start.strftime("%Y-%m-%d")
        endpoint = f"/v3/trades/{symbol}"
        
        try:
            data = self._request(endpoint, {
                "timestamp.gte": start.isoformat(),
                "limit": limit,
                "sort": "timestamp",
                "order": "asc",
            })
            
            if "results" not in data:
                return []
            
            trades: List[Trade] = []
            for r in data["results"]:
                trades.append(Trade(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(r.get("sip_timestamp", 0) / 1e9),
                    price=float(r.get("price", 0)),
                    size=float(r.get("size", 0)),
                    exchange=str(r.get("exchange")),
                    conditions=r.get("conditions"),
                ))
            
            return trades
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Polygon trades for {symbol}: {e}")
            return []
    
    def get_news(
        self,
        symbols: Optional[List[str]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[News]:
        """Get news articles from Polygon.
        
        Args:
            symbols: Filter by symbols
            start: Start datetime
            end: End datetime
            limit: Maximum articles
            
        Returns:
            List of News objects
        """
        params: Dict[str, Any] = {"limit": limit, "sort": "published_utc"}
        
        if symbols:
            params["ticker"] = ",".join(symbols)
        if start:
            params["published_utc.gte"] = start.strftime("%Y-%m-%d")
        if end:
            params["published_utc.lte"] = end.strftime("%Y-%m-%d")
        
        try:
            data = self._request("/v2/reference/news", params)
            
            if "results" not in data:
                return []
            
            articles: List[News] = []
            for r in data["results"]:
                articles.append(News(
                    id=r.get("id", ""),
                    headline=r.get("title", ""),
                    summary=r.get("description"),
                    author=r.get("author"),
                    source=r.get("publisher", {}).get("name", "Polygon"),
                    url=r.get("article_url"),
                    symbols=r.get("tickers", []),
                    created_at=datetime.fromisoformat(r["published_utc"].replace("Z", "+00:00")) if r.get("published_utc") else datetime.utcnow(),
                ))
            
            return articles
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Polygon news: {e}")
            return []
    
    def get_crypto_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50000,
    ) -> List[Bar]:
        """Get crypto bars from Polygon.
        
        Args:
            symbol: Crypto symbol (e.g., "X:BTCUSD")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum bars
            
        Returns:
            List of Bar objects
        """
        # Polygon uses X: prefix for crypto
        if not symbol.startswith("X:"):
            # Convert "BTC/USD" to "X:BTCUSD"
            symbol = "X:" + symbol.replace("/", "")
        
        return self.get_bars(symbol, timeframe, start, end, limit)
    
    def get_forex_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50000,
    ) -> List[Bar]:
        """Get forex bars from Polygon.
        
        Args:
            symbol: Forex pair (e.g., "C:EURUSD")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum bars
            
        Returns:
            List of Bar objects
        """
        # Polygon uses C: prefix for forex
        if not symbol.startswith("C:"):
            # Convert "EUR/USD" to "C:EURUSD"
            symbol = "C:" + symbol.replace("/", "")
        
        return self.get_bars(symbol, timeframe, start, end, limit)
    
    def get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """Get ticker details/fundamentals.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Ticker details including market cap, description, etc.
        """
        try:
            data = self._request(f"/v3/reference/tickers/{symbol}")
            return data.get("results", {})
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Polygon ticker details for {symbol}: {e}")
            return {}
    
    def get_financials(
        self,
        symbol: str,
        limit: int = 10,
        timeframe: str = "annual",  # "annual" or "quarterly"
    ) -> List[Dict[str, Any]]:
        """Get company financials.
        
        Args:
            symbol: Stock symbol
            limit: Number of periods
            timeframe: "annual" or "quarterly"
            
        Returns:
            List of financial statements
        """
        try:
            data = self._request("/vX/reference/financials", {
                "ticker": symbol,
                "limit": limit,
                "timeframe": timeframe,
            })
            return data.get("results", [])
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Polygon financials for {symbol}: {e}")
            return []
