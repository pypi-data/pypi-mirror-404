"""Twelve Data provider for stocks, forex, crypto, and technical indicators.

IMPORTANT: To use technical indicators, you must have Twelve Data connected
in the CPZAI platform. Go to the Data page and connect your Twelve Data API key.

Supports:
- Real-time and historical stock data
- Forex pairs (100+ currency pairs)
- Cryptocurrency data
- ETFs and Indices
- 100+ Technical Indicators (RSI, MACD, Bollinger Bands, Stochastic, ADX, etc.)

Technical Indicator Categories:
- Overlap Studies: SMA, EMA, BBANDS, Ichimoku, VWAP, Supertrend, etc.
- Momentum: RSI, MACD, Stochastic, ADX, CCI, Williams %R, MFI, etc.
- Volatility: ATR, Keltner Channels, Donchian Channels, etc.
- Volume: OBV, AD, CMF, VWMA, Force Index, etc.
- Cycle: Hilbert Transform indicators
- Pattern Recognition: 50+ candlestick patterns (Doji, Hammer, Engulfing, etc.)
- Math Transform: Log, Sqrt, Trig functions

Docs: https://twelvedata.com/docs#technical-indicators
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional

import requests

from ..models import Bar, Quote, TimeFrame


class TwelveDataProvider:
    """Twelve Data market data provider.
    
    Usage:
        provider = TwelveDataProvider()
        bars = provider.get_bars("AAPL", TimeFrame.DAY, limit=100)
        forex = provider.get_forex_quote("EUR/USD")
    """
    
    name = "twelve"
    supported_assets = ["stocks", "forex", "crypto", "etfs", "indices"]
    
    BASE_URL = "https://api.twelvedata.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Twelve Data provider.
        
        Args:
            api_key: Twelve Data API key (fetched from CPZAI platform)
        """
        self._api_key = api_key or ""
        
        # Fetch credentials from CPZAI platform (the ONLY supported method)
        if not self._api_key:
            try:
                from ...common.cpz_ai import CPZAIClient
                cpz_client = CPZAIClient.from_env()
                creds = cpz_client.get_data_credentials(provider="twelve")
                self._api_key = creds.get("twelve_api_key", "")
            except Exception as e:
                print(f"[CPZ SDK] Could not fetch Twelve Data credentials from platform: {e}")
        
        if not self._api_key:
            raise ValueError(
                "Twelve Data API key not found. Connect Twelve Data in the CPZ platform (Settings > API Connections)."
            )
    
    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Twelve Data API."""
        params["apikey"] = self._api_key
        
        response = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if data.get("status") == "error":
            raise ValueError(f"Twelve Data API error: {data.get('message', 'Unknown error')}")
        
        return data
    
    def _convert_timeframe(self, tf: TimeFrame) -> str:
        """Convert TimeFrame to Twelve Data interval string."""
        mapping = {
            TimeFrame.MINUTE_1: "1min",
            TimeFrame.MINUTE_5: "5min",
            TimeFrame.MINUTE_15: "15min",
            TimeFrame.MINUTE_30: "30min",
            TimeFrame.HOUR_1: "1h",
            TimeFrame.HOUR_4: "4h",
            TimeFrame.DAY: "1day",
            TimeFrame.WEEK: "1week",
            TimeFrame.MONTH: "1month",
        }
        return mapping.get(tf, "1day")
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
        exchange: Optional[str] = None,
    ) -> List[Bar]:
        """Get historical bars for stocks, forex, or crypto.
        
        Args:
            symbol: Symbol (e.g., "AAPL", "EUR/USD", "BTC/USD")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum bars to return (max 5000)
            exchange: Exchange code (optional)
            
        Returns:
            List of Bar objects
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        params: Dict[str, Any] = {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "outputsize": min(limit, 5000),
        }
        
        if start:
            params["start_date"] = start.strftime("%Y-%m-%d %H:%M:%S")
        if end:
            params["end_date"] = end.strftime("%Y-%m-%d %H:%M:%S")
        if exchange:
            params["exchange"] = exchange
        
        data = self._request("time_series", params)
        
        bars: List[Bar] = []
        for item in data.get("values", []):
            bars.append(Bar(
                symbol=symbol,
                timestamp=datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S") 
                    if " " in item["datetime"] 
                    else datetime.strptime(item["datetime"], "%Y-%m-%d"),
                open=float(item["open"]),
                high=float(item["high"]),
                low=float(item["low"]),
                close=float(item["close"]),
                volume=float(item.get("volume", 0)),
            ))
        
        # Twelve Data returns newest first, reverse for chronological order
        bars.reverse()
        return bars
    
    def get_quote(self, symbol: str, exchange: Optional[str] = None) -> Quote:
        """Get latest quote for a symbol.
        
        Args:
            symbol: Symbol (e.g., "AAPL", "EUR/USD")
            exchange: Exchange code (optional)
            
        Returns:
            Quote object
        """
        params: Dict[str, Any] = {"symbol": symbol}
        if exchange:
            params["exchange"] = exchange
        
        data = self._request("quote", params)
        
        return Quote(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            bid=float(data.get("close", 0)),  # Twelve Data doesn't have bid/ask in quote
            ask=float(data.get("close", 0)),
            bid_size=float(data.get("volume", 0)),
            ask_size=0.0,
        )
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get latest quotes for multiple symbols.
        
        Args:
            symbols: List of symbols
            
        Returns:
            List of Quote objects
        """
        return [self.get_quote(symbol) for symbol in symbols]
    
    def get_price(self, symbol: str) -> float:
        """Get current price for a symbol.
        
        Args:
            symbol: Symbol (e.g., "AAPL")
            
        Returns:
            Current price
        """
        data = self._request("price", {"symbol": symbol})
        return float(data.get("price", 0))
    
    def get_forex_quote(self, symbol: str) -> Dict[str, Any]:
        """Get forex pair quote with detailed info.
        
        Args:
            symbol: Forex pair (e.g., "EUR/USD")
            
        Returns:
            Detailed forex quote data
        """
        data = self._request("quote", {"symbol": symbol})
        return {
            "symbol": symbol,
            "open": float(data.get("open", 0)),
            "high": float(data.get("high", 0)),
            "low": float(data.get("low", 0)),
            "close": float(data.get("close", 0)),
            "change": float(data.get("change", 0)),
            "percent_change": float(data.get("percent_change", 0)),
            "timestamp": data.get("datetime"),
        }
    
    def get_crypto_quote(self, symbol: str) -> Dict[str, Any]:
        """Get cryptocurrency quote.
        
        Args:
            symbol: Crypto pair (e.g., "BTC/USD")
            
        Returns:
            Crypto quote data
        """
        return self.get_forex_quote(symbol)
    
    # --- Technical Indicators ---
    
    def get_sma(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Simple Moving Average.
        
        Args:
            symbol: Symbol
            timeframe: Bar timeframe
            period: SMA period
            limit: Number of data points
            
        Returns:
            List of SMA values with timestamps
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("sma", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        
        return [
            {"datetime": v["datetime"], "sma": float(v["sma"])}
            for v in data.get("values", [])
        ]
    
    def get_ema(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Exponential Moving Average."""
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("ema", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        
        return [
            {"datetime": v["datetime"], "ema": float(v["ema"])}
            for v in data.get("values", [])
        ]
    
    def get_rsi(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Relative Strength Index."""
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("rsi", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        
        return [
            {"datetime": v["datetime"], "rsi": float(v["rsi"])}
            for v in data.get("values", [])
        ]
    
    def get_macd(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get MACD (Moving Average Convergence Divergence)."""
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("macd", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period,
            "outputsize": limit,
        })
        
        return [
            {
                "datetime": v["datetime"],
                "macd": float(v["macd"]),
                "macd_signal": float(v["macd_signal"]),
                "macd_hist": float(v["macd_hist"]),
            }
            for v in data.get("values", [])
        ]
    
    def get_bbands(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        std_dev: float = 2.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Bollinger Bands."""
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("bbands", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "sd": std_dev,
            "outputsize": limit,
        })
        
        return [
            {
                "datetime": v["datetime"],
                "upper_band": float(v["upper_band"]),
                "middle_band": float(v["middle_band"]),
                "lower_band": float(v["lower_band"]),
            }
            for v in data.get("values", [])
        ]
    
    def get_indicator(
        self,
        indicator: str,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
        **params: Any,
    ) -> List[Dict[str, Any]]:
        """Get any technical indicator.
        
        This is a generic method that can fetch ANY TwelveData indicator.
        For specific indicators with proper typing, use dedicated methods like
        get_rsi(), get_macd(), get_stoch(), etc.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            indicator: Indicator name (e.g., "stoch", "adx", "atr", "ichimoku")
            symbol: Symbol
            timeframe: Bar timeframe
            limit: Number of data points
            **params: Additional indicator parameters (e.g., time_period=14)
            
        Returns:
            List of indicator values with timestamps
            
        Examples:
            >>> provider.get_indicator("stoch", "AAPL", fast_k_period=14)
            >>> provider.get_indicator("adx", "AAPL", time_period=14)
            >>> provider.get_indicator("ichimoku", "AAPL")
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        request_params: Dict[str, Any] = {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "outputsize": limit,
            **params,
        }
        
        data = self._request(indicator.lower(), request_params)
        return data.get("values", [])
    
    # ==========================================================================
    # OVERLAP STUDIES (Trend Indicators)
    # ==========================================================================
    
    def get_wma(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Weighted Moving Average.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("wma", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "wma": float(v["wma"])} for v in data.get("values", [])]
    
    def get_dema(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Double Exponential Moving Average.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("dema", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "dema": float(v["dema"])} for v in data.get("values", [])]
    
    def get_tema(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Triple Exponential Moving Average.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("tema", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "tema": float(v["tema"])} for v in data.get("values", [])]
    
    def get_t3(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 5,
        v_factor: float = 0.7,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Tillson T3 Moving Average.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("t3", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "v_factor": v_factor,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "t3": float(v["t3"])} for v in data.get("values", [])]
    
    def get_kama(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 10,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Kaufman Adaptive Moving Average.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("kama", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "kama": float(v["kama"])} for v in data.get("values", [])]
    
    def get_trima(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Triangular Moving Average.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("trima", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "trima": float(v["trima"])} for v in data.get("values", [])]
    
    def get_vwap(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Volume Weighted Average Price.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("vwap", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "vwap": float(v["vwap"])} for v in data.get("values", [])]
    
    def get_sar(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        acceleration: float = 0.02,
        maximum: float = 0.2,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Parabolic SAR.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("sar", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "acceleration": acceleration,
            "maximum": maximum,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "sar": float(v["sar"])} for v in data.get("values", [])]
    
    def get_supertrend(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 10,
        multiplier: float = 3.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Supertrend indicator.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("supertrend", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "period": period,
            "multiplier": multiplier,
            "outputsize": limit,
        })
        return data.get("values", [])
    
    def get_ichimoku(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        tenkan: int = 9,
        kijun: int = 26,
        senkou: int = 52,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Ichimoku Cloud indicator.
        
        Returns tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("ichimoku", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "tenkan_period": tenkan,
            "kijun_period": kijun,
            "senkou_span_period": senkou,
            "outputsize": limit,
        })
        return data.get("values", [])
    
    def get_keltner(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Keltner Channels.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("keltner", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "atr_time_period": atr_period,
            "multiplier": multiplier,
            "outputsize": limit,
        })
        return data.get("values", [])
    
    def get_donchian(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Donchian Channels.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("donchian", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return data.get("values", [])
    
    # ==========================================================================
    # MOMENTUM INDICATORS
    # ==========================================================================
    
    def get_stoch(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        fast_k_period: int = 14,
        slow_k_period: int = 3,
        slow_d_period: int = 3,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Stochastic Oscillator.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("stoch", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "fast_k_period": fast_k_period,
            "slow_k_period": slow_k_period,
            "slow_d_period": slow_d_period,
            "outputsize": limit,
        })
        return data.get("values", [])
    
    def get_stochrsi(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        fast_k_period: int = 5,
        fast_d_period: int = 3,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Stochastic RSI.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("stochrsi", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "fast_k_period": fast_k_period,
            "fast_d_period": fast_d_period,
            "outputsize": limit,
        })
        return data.get("values", [])
    
    def get_adx(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Average Directional Index.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("adx", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "adx": float(v["adx"])} for v in data.get("values", [])]
    
    def get_cci(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Commodity Channel Index.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("cci", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "cci": float(v["cci"])} for v in data.get("values", [])]
    
    def get_willr(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Williams %R.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("willr", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "willr": float(v["willr"])} for v in data.get("values", [])]
    
    def get_mfi(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Money Flow Index.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("mfi", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "mfi": float(v["mfi"])} for v in data.get("values", [])]
    
    def get_aroon(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Aroon indicator (aroon_up and aroon_down).
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("aroon", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return data.get("values", [])
    
    def get_ppo(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        fast_period: int = 12,
        slow_period: int = 26,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Percentage Price Oscillator.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("ppo", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "fast_period": fast_period,
            "slow_period": slow_period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "ppo": float(v["ppo"])} for v in data.get("values", [])]
    
    def get_mom(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 10,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Momentum.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("mom", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "mom": float(v["mom"])} for v in data.get("values", [])]
    
    def get_roc(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 10,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Rate of Change.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("roc", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "roc": float(v["roc"])} for v in data.get("values", [])]
    
    def get_trix(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 18,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get TRIX (Triple Smoothed EMA ROC).
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("trix", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "trix": float(v["trix"])} for v in data.get("values", [])]
    
    def get_ultosc(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period1: int = 7,
        period2: int = 14,
        period3: int = 28,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Ultimate Oscillator.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("ultosc", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period1": period1,
            "time_period2": period2,
            "time_period3": period3,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "ultosc": float(v["ultosc"])} for v in data.get("values", [])]
    
    def get_dx(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Directional Movement Index.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("dx", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "dx": float(v["dx"])} for v in data.get("values", [])]
    
    def get_plus_di(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Plus Directional Indicator (+DI).
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("plus_di", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "plus_di": float(v["plus_di"])} for v in data.get("values", [])]
    
    def get_minus_di(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Minus Directional Indicator (-DI).
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("minus_di", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "minus_di": float(v["minus_di"])} for v in data.get("values", [])]
    
    # ==========================================================================
    # VOLATILITY INDICATORS
    # ==========================================================================
    
    def get_atr(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Average True Range.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("atr", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "atr": float(v["atr"])} for v in data.get("values", [])]
    
    def get_natr(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 14,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Normalized Average True Range.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("natr", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "natr": float(v["natr"])} for v in data.get("values", [])]
    
    def get_trange(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get True Range.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("trange", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "trange": float(v["trange"])} for v in data.get("values", [])]
    
    def get_stddev(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 5,
        sd: float = 1.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Standard Deviation.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("stddev", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "sd": sd,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "stddev": float(v["stddev"])} for v in data.get("values", [])]
    
    # ==========================================================================
    # VOLUME INDICATORS
    # ==========================================================================
    
    def get_obv(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get On Balance Volume.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("obv", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "obv": float(v["obv"])} for v in data.get("values", [])]
    
    def get_ad(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Accumulation/Distribution Line.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("ad", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "ad": float(v["ad"])} for v in data.get("values", [])]
    
    def get_adosc(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        fast_period: int = 3,
        slow_period: int = 10,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Accumulation/Distribution Oscillator (Chaikin A/D Oscillator).
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("adosc", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "fast_period": fast_period,
            "slow_period": slow_period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "adosc": float(v["adosc"])} for v in data.get("values", [])]
    
    def get_vwma(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Volume Weighted Moving Average.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("vwma", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "vwma": float(v["vwma"])} for v in data.get("values", [])]
    
    def get_cmf(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 20,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Chaikin Money Flow.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("cmf", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "cmf": float(v["cmf"])} for v in data.get("values", [])]
    
    def get_force_index(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        period: int = 13,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Force Index.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("force_index", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "time_period": period,
            "outputsize": limit,
        })
        return [{"datetime": v["datetime"], "force_index": float(v["force_index"])} for v in data.get("values", [])]
    
    # ==========================================================================
    # CANDLESTICK PATTERNS
    # ==========================================================================
    
    def get_cdl_pattern(
        self,
        pattern: str,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get any candlestick pattern.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            pattern: Pattern name (e.g., "cdl_doji", "cdl_hammer", "cdl_engulfing")
            symbol: Symbol
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of pattern signals (100 = bullish, -100 = bearish, 0 = no pattern)
            
        Common Patterns:
            - cdl_doji: Doji (indecision)
            - cdl_hammer: Hammer (bullish reversal)
            - cdl_engulfing: Engulfing pattern
            - cdl_morning_star: Morning Star (bullish)
            - cdl_evening_star: Evening Star (bearish)
            - cdl_three_white_soldiers: Three White Soldiers
            - cdl_three_black_crows: Three Black Crows
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request(pattern.lower(), {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
            "outputsize": limit,
        })
        return data.get("values", [])
    
    # --- Reference Data ---
    
    def get_stocks_list(
        self,
        exchange: Optional[str] = None,
        country: Optional[str] = None,
        type_filter: Optional[str] = None,  # "stock", "etf", "fund"
    ) -> List[Dict[str, str]]:
        """Get list of available stocks.
        
        Args:
            exchange: Filter by exchange
            country: Filter by country code
            type_filter: Filter by type
            
        Returns:
            List of stock metadata
        """
        params: Dict[str, Any] = {}
        if exchange:
            params["exchange"] = exchange
        if country:
            params["country"] = country
        if type_filter:
            params["type"] = type_filter
        
        data = self._request("stocks", params)
        return data.get("data", [])
    
    def get_forex_pairs(self) -> List[Dict[str, str]]:
        """Get list of available forex pairs."""
        data = self._request("forex_pairs", {})
        return data.get("data", [])
    
    def get_cryptocurrencies(self) -> List[Dict[str, str]]:
        """Get list of available cryptocurrencies."""
        data = self._request("cryptocurrencies", {})
        return data.get("data", [])
    
    def get_exchanges(self, type_filter: Optional[str] = None) -> List[Dict[str, str]]:
        """Get list of supported exchanges.
        
        Args:
            type_filter: "stock", "etf", "index"
            
        Returns:
            List of exchange metadata
        """
        params: Dict[str, Any] = {}
        if type_filter:
            params["type"] = type_filter
        
        data = self._request("exchanges", params)
        return data.get("data", [])
    
    def get_market_state(self, exchange: str) -> Dict[str, Any]:
        """Get market state (open/closed) for an exchange.
        
        Args:
            exchange: Exchange code (e.g., "NYSE", "NASDAQ")
            
        Returns:
            Market state info
        """
        data = self._request("market_state", {"exchange": exchange})
        return data
    
    def get_earliest_timestamp(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
    ) -> datetime:
        """Get earliest available timestamp for a symbol.
        
        Args:
            symbol: Symbol
            timeframe: Bar timeframe
            
        Returns:
            Earliest available datetime
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        data = self._request("earliest_timestamp", {
            "symbol": symbol,
            "interval": self._convert_timeframe(timeframe),
        })
        
        return datetime.strptime(data["datetime"], "%Y-%m-%d")


# Popular forex pairs for convenience
FOREX_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "AUD/USD", "USD/CAD", "NZD/USD",
    "EUR/GBP", "EUR/JPY", "GBP/JPY",
]

# Popular crypto pairs
CRYPTO_PAIRS = [
    "BTC/USD", "ETH/USD", "BNB/USD", "XRP/USD",
    "SOL/USD", "ADA/USD", "DOGE/USD", "DOT/USD",
]
