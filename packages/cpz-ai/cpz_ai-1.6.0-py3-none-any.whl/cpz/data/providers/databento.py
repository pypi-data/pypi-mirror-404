"""Databento Market Data provider.

Supports:
- Stocks: bars, quotes, trades (historical + real-time)
- Futures, Options, Crypto

Docs: https://docs.databento.com/
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, List, Optional

from ..models import Bar, Quote, TimeFrame


class DatabentoProvider:
    """Databento Market Data API provider.
    
    Usage:
        provider = DatabentoProvider(api_key="your_key")
        bars = provider.get_bars("AAPL", TimeFrame.DAY, limit=100)
    """
    
    name = "databento"
    supported_assets = ["stocks", "futures", "options", "crypto"]
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Databento data provider.
        
        Args:
            api_key: Databento API key (defaults to DATABENTO_API_KEY env var or CPZAI platform)
        """
        self._api_key = api_key or ""
        
        # Fetch credentials from CPZAI platform (the ONLY supported method)
        if not self._api_key:
            try:
                from ...common.cpz_ai import CPZAIClient
                cpz_client = CPZAIClient.from_env()
                creds = cpz_client.get_data_credentials(provider="databento")
                if not self._api_key:
                    self._api_key = creds.get("databento_api_key", "") or creds.get("api_key", "")
            except Exception as e:
                print(f"[CPZ SDK] Could not fetch Databento credentials from platform: {e}")
        
        if not self._api_key:
            print("[CPZ SDK] Databento API key not found. Connect Databento in the CPZ platform (Settings > API Connections).")
        
        self._client: Any = None
        self._has_credentials = bool(self._api_key)
    
    def _get_client(self) -> Any:
        """Lazy-load Databento client."""
        if self._client is None:
            try:
                import databento as db
                self._client = db.Historical(key=self._api_key)
            except ImportError:
                raise ImportError(
                    "databento is required for Databento data. Install with: pip install databento"
                )
        return self._client
    
    def _convert_timeframe(self, tf: TimeFrame) -> str:
        """Convert TimeFrame to Databento schema."""
        # Databento uses schemas like "ohlcv-1s", "ohlcv-1m", "ohlcv-1h", "ohlcv-1d"
        mapping = {
            TimeFrame.MINUTE_1: "ohlcv-1m",
            TimeFrame.MINUTE_5: "ohlcv-1m",  # Databento doesn't have 5m, aggregate from 1m
            TimeFrame.MINUTE_15: "ohlcv-1m",
            TimeFrame.MINUTE_30: "ohlcv-1m",
            TimeFrame.HOUR_1: "ohlcv-1h",
            TimeFrame.HOUR_4: "ohlcv-1h",
            TimeFrame.DAY: "ohlcv-1d",
            TimeFrame.WEEK: "ohlcv-1d",
            TimeFrame.MONTH: "ohlcv-1d",
        }
        return mapping.get(tf, "ohlcv-1d")
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
        dataset: str = "XNAS.ITCH",  # Default to NASDAQ
    ) -> List[Bar]:
        """Get historical bars from Databento.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            timeframe: Bar timeframe
            start: Start datetime (defaults to 30 days ago)
            end: End datetime (defaults to now)
            limit: Maximum bars to return
            dataset: Databento dataset (e.g., "XNAS.ITCH", "GLBX.MDP3")
            
        Returns:
            List of Bar objects
        """
        # Check credentials before attempting API call
        if not self._has_credentials:
            print(f"[CPZ SDK] Cannot fetch Databento data - no API key configured")
            return []
        
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        if start is None:
            start = datetime.utcnow() - timedelta(days=30)
        if end is None:
            end = datetime.utcnow()
        
        try:
            client = self._get_client()
            schema = self._convert_timeframe(timeframe)
            
            # Databento query
            data = client.timeseries.get_range(
                dataset=dataset,
                symbols=[symbol],
                schema=schema,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                limit=limit,
            )
            
            bars: List[Bar] = []
            for record in data:
                bars.append(Bar(
                    symbol=symbol,
                    timestamp=record.ts_event,
                    open=float(record.open) / 1e9,  # Databento uses fixed-point
                    high=float(record.high) / 1e9,
                    low=float(record.low) / 1e9,
                    close=float(record.close) / 1e9,
                    volume=float(record.volume),
                ))
            
            return bars
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Databento bars for {symbol}: {e}")
            return []
    
    def get_quotes(self, symbols: List[str], dataset: str = "XNAS.ITCH") -> List[Quote]:
        """Get latest quotes from Databento.
        
        Note: Databento is primarily historical. For real-time quotes,
        use their live feed or consider Alpaca for real-time data.
        
        Args:
            symbols: List of symbols
            dataset: Databento dataset
            
        Returns:
            List of Quote objects (from most recent data)
        """
        quotes: List[Quote] = []
        
        try:
            client = self._get_client()
            
            # Get most recent MBP-1 (market by price) data
            for symbol in symbols:
                try:
                    data = client.timeseries.get_range(
                        dataset=dataset,
                        symbols=[symbol],
                        schema="mbp-1",
                        start=(datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
                        limit=1,
                    )
                    
                    for record in data:
                        quotes.append(Quote(
                            symbol=symbol,
                            timestamp=record.ts_event,
                            bid=float(record.bid_px_00) / 1e9 if hasattr(record, 'bid_px_00') else 0.0,
                            ask=float(record.ask_px_00) / 1e9 if hasattr(record, 'ask_px_00') else 0.0,
                            bid_size=float(record.bid_sz_00) if hasattr(record, 'bid_sz_00') else 0.0,
                            ask_size=float(record.ask_sz_00) if hasattr(record, 'ask_sz_00') else 0.0,
                        ))
                        break  # Only need one
                except Exception as e:
                    print(f"[CPZ SDK] Error fetching Databento quote for {symbol}: {e}")
                    
        except Exception as e:
            print(f"[CPZ SDK] Error with Databento client: {e}")
        
        return quotes
