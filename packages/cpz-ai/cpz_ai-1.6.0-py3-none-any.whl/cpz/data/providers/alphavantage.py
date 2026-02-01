"""Alpha Vantage data provider.

Premium market data with extensive historical coverage.
Free tier: 25 requests/day. Premium tiers available.

Docs: https://www.alphavantage.co/documentation/
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from ..models import Bar, Quote, TimeFrame


class AlphaVantageProvider:
    """Alpha Vantage data provider.
    
    Supports stocks, forex, crypto, and economic indicators.
    
    Usage:
        provider = AlphaVantageProvider(api_key="your_key")
        bars = provider.get_bars("AAPL", start=datetime(2023, 1, 1))
    """
    
    name = "alphavantage"
    supported_assets = ["stocks", "forex", "crypto", "commodities"]
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Alpha Vantage provider.
        
        Args:
            api_key: Alpha Vantage API key. Get free key at alphavantage.co
        """
        self._api_key = api_key or ""
        
        # Try to get from CPZAI platform if not provided
        if not self._api_key:
            try:
                from ...common.cpz_ai import CPZAIClient
                cpz_client = CPZAIClient.from_env()
                creds = cpz_client.get_data_credentials(provider="alphavantage")
                self._api_key = creds.get("alphavantage_api_key", "")
            except Exception:
                pass
        
        if not self._api_key:
            print("[CPZ SDK] Alpha Vantage API key not found. Get a free key at alphavantage.co")
    
    def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request."""
        params["apikey"] = self._api_key
        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def _convert_timeframe(self, tf: TimeFrame) -> tuple[str, str]:
        """Convert TimeFrame to Alpha Vantage function and interval."""
        if tf in (TimeFrame.MINUTE_1, TimeFrame.MINUTE_5, TimeFrame.MINUTE_15, TimeFrame.MINUTE_30, TimeFrame.HOUR_1):
            interval_map = {
                TimeFrame.MINUTE_1: "1min",
                TimeFrame.MINUTE_5: "5min",
                TimeFrame.MINUTE_15: "15min",
                TimeFrame.MINUTE_30: "30min",
                TimeFrame.HOUR_1: "60min",
            }
            return "TIME_SERIES_INTRADAY", interval_map.get(tf, "60min")
        elif tf == TimeFrame.WEEK:
            return "TIME_SERIES_WEEKLY_ADJUSTED", ""
        elif tf == TimeFrame.MONTH:
            return "TIME_SERIES_MONTHLY_ADJUSTED", ""
        else:
            return "TIME_SERIES_DAILY_ADJUSTED", ""
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        outputsize: str = "full",  # "compact" (100 points) or "full" (20+ years)
    ) -> List[Bar]:
        """Get historical bars from Alpha Vantage.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum bars
            outputsize: "compact" for last 100 points, "full" for full history
            
        Returns:
            List of Bar objects
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        function, interval = self._convert_timeframe(timeframe)
        
        params: Dict[str, Any] = {
            "function": function,
            "symbol": symbol,
            "outputsize": outputsize,
        }
        
        if interval:
            params["interval"] = interval
        
        try:
            data = self._request(params)
            
            # Find the time series key (varies by endpoint)
            ts_key = None
            for key in data.keys():
                if "Time Series" in key or "Weekly" in key or "Monthly" in key:
                    ts_key = key
                    break
            
            if not ts_key or ts_key not in data:
                print(f"[CPZ SDK] No data in Alpha Vantage response for {symbol}")
                return []
            
            bars: List[Bar] = []
            for date_str, values in data[ts_key].items():
                try:
                    timestamp = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                    
                    # Filter by date range
                    if start and timestamp < start:
                        continue
                    if end and timestamp > end:
                        continue
                    
                    # Alpha Vantage uses various key formats
                    open_val = float(values.get("1. open", 0))
                    high_val = float(values.get("2. high", 0))
                    low_val = float(values.get("3. low", 0))
                    close_val = float(values.get("4. close", 0) or values.get("5. adjusted close", 0))
                    volume_val = float(values.get("5. volume", 0) or values.get("6. volume", 0))
                    
                    bars.append(Bar(
                        symbol=symbol,
                        timestamp=timestamp,
                        open=open_val,
                        high=high_val,
                        low=low_val,
                        close=close_val,
                        volume=volume_val,
                        vwap=None,
                    ))
                except (ValueError, KeyError) as e:
                    continue
            
            # Sort by timestamp (oldest first)
            bars.sort(key=lambda x: x.timestamp)
            
            # Apply limit
            if limit and len(bars) > limit:
                bars = bars[-limit:]
            
            return bars
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Alpha Vantage data for {symbol}: {e}")
            return []
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get latest quote from Alpha Vantage."""
        try:
            data = self._request({
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
            })
            
            quote_data = data.get("Global Quote", {})
            if not quote_data:
                return None
            
            price = float(quote_data.get("05. price", 0))
            
            return Quote(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                bid=price,
                ask=price,
                bid_size=0,
                ask_size=0,
            )
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Alpha Vantage quote for {symbol}: {e}")
            return None
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get quotes for multiple symbols."""
        quotes: List[Quote] = []
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes.append(quote)
        return quotes
    
    def get_forex(
        self,
        from_currency: str,
        to_currency: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Bar]:
        """Get forex data.
        
        Args:
            from_currency: Base currency (e.g., "EUR")
            to_currency: Quote currency (e.g., "USD")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            
        Returns:
            List of Bar objects
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        if timeframe == TimeFrame.DAY:
            function = "FX_DAILY"
        elif timeframe == TimeFrame.WEEK:
            function = "FX_WEEKLY"
        elif timeframe == TimeFrame.MONTH:
            function = "FX_MONTHLY"
        else:
            function = "FX_INTRADAY"
        
        params: Dict[str, Any] = {
            "function": function,
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "outputsize": "full",
        }
        
        try:
            data = self._request(params)
            
            # Find time series key
            ts_key = None
            for key in data.keys():
                if "Time Series" in key:
                    ts_key = key
                    break
            
            if not ts_key:
                return []
            
            symbol = f"{from_currency}/{to_currency}"
            bars: List[Bar] = []
            
            for date_str, values in data[ts_key].items():
                try:
                    timestamp = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                    
                    if start and timestamp < start:
                        continue
                    if end and timestamp > end:
                        continue
                    
                    bars.append(Bar(
                        symbol=symbol,
                        timestamp=timestamp,
                        open=float(values.get("1. open", 0)),
                        high=float(values.get("2. high", 0)),
                        low=float(values.get("3. low", 0)),
                        close=float(values.get("4. close", 0)),
                        volume=0,
                        vwap=None,
                    ))
                except (ValueError, KeyError):
                    continue
            
            bars.sort(key=lambda x: x.timestamp)
            return bars
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Alpha Vantage forex data: {e}")
            return []
    
    def get_crypto(
        self,
        symbol: str,
        market: str = "USD",
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Bar]:
        """Get cryptocurrency data.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC")
            market: Market currency (e.g., "USD")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            
        Returns:
            List of Bar objects
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        if timeframe == TimeFrame.DAY:
            function = "DIGITAL_CURRENCY_DAILY"
        elif timeframe == TimeFrame.WEEK:
            function = "DIGITAL_CURRENCY_WEEKLY"
        elif timeframe == TimeFrame.MONTH:
            function = "DIGITAL_CURRENCY_MONTHLY"
        else:
            function = "DIGITAL_CURRENCY_DAILY"
        
        try:
            data = self._request({
                "function": function,
                "symbol": symbol,
                "market": market,
            })
            
            # Find time series key
            ts_key = None
            for key in data.keys():
                if "Time Series" in key:
                    ts_key = key
                    break
            
            if not ts_key:
                return []
            
            full_symbol = f"{symbol}/{market}"
            bars: List[Bar] = []
            
            for date_str, values in data[ts_key].items():
                try:
                    timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if start and timestamp < start:
                        continue
                    if end and timestamp > end:
                        continue
                    
                    # Alpha Vantage crypto has different keys
                    bars.append(Bar(
                        symbol=full_symbol,
                        timestamp=timestamp,
                        open=float(values.get(f"1a. open ({market})", 0)),
                        high=float(values.get(f"2a. high ({market})", 0)),
                        low=float(values.get(f"3a. low ({market})", 0)),
                        close=float(values.get(f"4a. close ({market})", 0)),
                        volume=float(values.get("5. volume", 0)),
                        vwap=None,
                    ))
                except (ValueError, KeyError):
                    continue
            
            bars.sort(key=lambda x: x.timestamp)
            return bars
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Alpha Vantage crypto data: {e}")
            return []
