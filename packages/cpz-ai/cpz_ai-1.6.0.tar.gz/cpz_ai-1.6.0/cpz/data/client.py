"""Unified Data Client with hybrid namespace design.

The DataClient provides:
1. Simple unified methods (client.data.bars, client.data.news, etc.)
2. Direct provider access for power users (client.data.alpaca, client.data.fred, etc.)

Usage:
    from cpz import CPZClient
    
    client = CPZClient()
    
    # Simple unified interface (smart routing)
    bars = client.data.bars("AAPL", timeframe="1D")
    quotes = client.data.quotes(["AAPL", "MSFT"])
    news = client.data.news("AAPL")
    economic = client.data.economic("GDP")
    filings = client.data.filings("AAPL", form="10-K")
    social = client.data.social("AAPL", source="reddit")
    
    # Direct provider access (power users)
    options = client.data.alpaca.get_options_chain("AAPL")
    series = client.data.fred.get_series("UNRATE")
    rsi = client.data.twelve.get_rsi("AAPL")
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

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


class _AlpacaNamespace:
    """Direct access to Alpaca Market Data API."""
    
    def __init__(self, parent: "DataClient"):
        self._parent = parent
        self._provider: Any = None
    
    def _get_provider(self) -> Any:
        if self._provider is None:
            # Load credentials from CPZAI platform if not already set
            self._parent._load_credentials_from_cpzai()
            from .providers.alpaca import AlpacaDataProvider
            self._provider = AlpacaDataProvider(
                api_key=self._parent._config.get("alpaca_api_key"),
                api_secret=self._parent._config.get("alpaca_api_secret"),
                feed=self._parent._config.get("alpaca_feed", "iex"),
            )
        return self._provider
    
    def get_bars(self, symbol: str, timeframe: TimeFrame | str = TimeFrame.DAY, **kwargs: Any) -> List[Bar]:
        """Get stock bars from Alpaca."""
        return self._get_provider().get_bars(symbol, timeframe, **kwargs)
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get stock quotes from Alpaca."""
        return self._get_provider().get_quotes(symbols)
    
    def get_trades(self, symbol: str, **kwargs: Any) -> List[Trade]:
        """Get stock trades from Alpaca."""
        return self._get_provider().get_trades(symbol, **kwargs)
    
    def get_crypto_bars(self, symbol: str, timeframe: TimeFrame | str = TimeFrame.DAY, **kwargs: Any) -> List[Bar]:
        """Get crypto bars from Alpaca."""
        return self._get_provider().get_crypto_bars(symbol, timeframe, **kwargs)
    
    def get_crypto_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get crypto quotes from Alpaca."""
        return self._get_provider().get_crypto_quotes(symbols)
    
    def get_options_chain(self, underlying: str, **kwargs: Any) -> List[OptionContract]:
        """Get options chain from Alpaca."""
        return self._get_provider().get_options_chain(underlying, **kwargs)
    
    def get_option_quotes(self, symbols: List[str]) -> List[OptionQuote]:
        """Get option quotes from Alpaca."""
        return self._get_provider().get_option_quotes(symbols)
    
    def get_news(self, symbols: Optional[List[str]] = None, **kwargs: Any) -> List[News]:
        """Get news from Alpaca."""
        return self._get_provider().get_news(symbols, **kwargs)


class _FREDNamespace:
    """Direct access to FRED economic data."""
    
    def __init__(self, parent: "DataClient"):
        self._parent = parent
        self._provider: Any = None
    
    def _get_provider(self) -> Any:
        if self._provider is None:
            # Load credentials from CPZAI platform if not already set
            self._parent._load_credentials_from_cpzai()
            from .providers.fred import FREDProvider
            self._provider = FREDProvider(
                api_key=self._parent._config.get("fred_api_key"),
            )
        return self._provider
    
    def get_series(self, series_id: str, **kwargs: Any) -> List[EconomicSeries]:
        """Get economic data series."""
        return self._get_provider().get_series(series_id, **kwargs)
    
    def search(self, query: str, **kwargs: Any) -> List[Dict[str, str]]:
        """Search for series."""
        return self._get_provider().search_series(query, **kwargs)
    
    def categories(self, category_id: int = 0) -> List[Dict[str, Any]]:
        """Get categories."""
        return self._get_provider().get_categories(category_id)


class _EDGARNamespace:
    """Direct access to SEC EDGAR filings."""
    
    def __init__(self, parent: "DataClient"):
        self._parent = parent
        self._provider: Any = None
    
    def _get_provider(self) -> Any:
        if self._provider is None:
            from .providers.edgar import EDGARProvider
            self._provider = EDGARProvider()
        return self._provider
    
    def get_filings(self, symbol: str, **kwargs: Any) -> List[Filing]:
        """Get SEC filings."""
        return self._get_provider().get_filings(symbol=symbol, **kwargs)
    
    def get_content(self, accession_number: str) -> str:
        """Get filing content."""
        return self._get_provider().get_filing_content(accession_number)
    
    def get_facts(self, symbol: str) -> Dict[str, Any]:
        """Get company XBRL facts."""
        return self._get_provider().get_company_facts(symbol)
    
    def get_concept(self, symbol: str, concept: str, taxonomy: str = "us-gaap") -> List[Dict[str, Any]]:
        """Get specific XBRL concept values."""
        return self._get_provider().get_company_concept(symbol, taxonomy, concept)
    
    def insider_transactions(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get insider transactions."""
        return self._get_provider().get_insider_transactions(symbol, limit)


class _TwelveNamespace:
    """Direct access to Twelve Data for market data and 100+ technical indicators.
    
    IMPORTANT: To use technical indicators, you must have Twelve Data connected
    in the CPZAI platform. Go to the Data page and connect your Twelve Data API key.
    
    Available indicator categories:
    - Overlap Studies: SMA, EMA, BBANDS, Ichimoku, VWAP, Supertrend, etc.
    - Momentum: RSI, MACD, Stochastic, ADX, CCI, Williams %R, MFI, etc.
    - Volatility: ATR, Keltner Channels, Donchian Channels, etc.
    - Volume: OBV, AD, CMF, VWMA, Force Index, etc.
    - Pattern Recognition: 50+ candlestick patterns
    """
    
    def __init__(self, parent: "DataClient"):
        self._parent = parent
        self._provider: Any = None
    
    def _get_provider(self) -> Any:
        if self._provider is None:
            # Load credentials from CPZAI platform if not already set
            self._parent._load_credentials_from_cpzai()
            from .providers.twelve import TwelveDataProvider
            self._provider = TwelveDataProvider(
                api_key=self._parent._config.get("twelve_api_key"),
            )
        return self._provider
    
    def get_bars(self, symbol: str, timeframe: TimeFrame | str = TimeFrame.DAY, **kwargs: Any) -> List[Bar]:
        """Get bars from Twelve Data."""
        return self._get_provider().get_bars(symbol, timeframe, **kwargs)
    
    def get_quote(self, symbol: str) -> Quote:
        """Get quote from Twelve Data."""
        return self._get_provider().get_quote(symbol)
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get quotes for multiple symbols from Twelve Data."""
        return self._get_provider().get_quotes(symbols)
    
    def get_forex(self, symbol: str) -> Dict[str, Any]:
        """Get forex quote."""
        return self._get_provider().get_forex_quote(symbol)
    
    def get_crypto(self, symbol: str) -> Dict[str, Any]:
        """Get crypto quote."""
        return self._get_provider().get_crypto_quote(symbol)
    
    # ==========================================================================
    # OVERLAP STUDIES (Trend Indicators)
    # ==========================================================================
    
    def get_sma(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Simple Moving Average."""
        return self._get_provider().get_sma(symbol, period=period, **kwargs)
    
    def get_ema(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Exponential Moving Average."""
        return self._get_provider().get_ema(symbol, period=period, **kwargs)
    
    def get_wma(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Weighted Moving Average."""
        return self._get_provider().get_wma(symbol, period=period, **kwargs)
    
    def get_dema(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Double Exponential Moving Average."""
        return self._get_provider().get_dema(symbol, period=period, **kwargs)
    
    def get_tema(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Triple Exponential Moving Average."""
        return self._get_provider().get_tema(symbol, period=period, **kwargs)
    
    def get_t3(self, symbol: str, period: int = 5, v_factor: float = 0.7, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Tillson T3 Moving Average."""
        return self._get_provider().get_t3(symbol, period=period, v_factor=v_factor, **kwargs)
    
    def get_kama(self, symbol: str, period: int = 10, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Kaufman Adaptive Moving Average."""
        return self._get_provider().get_kama(symbol, period=period, **kwargs)
    
    def get_trima(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Triangular Moving Average."""
        return self._get_provider().get_trima(symbol, period=period, **kwargs)
    
    def get_bbands(self, symbol: str, period: int = 20, std_dev: float = 2.0, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Bollinger Bands (upper, middle, lower)."""
        return self._get_provider().get_bbands(symbol, period=period, std_dev=std_dev, **kwargs)
    
    def get_vwap(self, symbol: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Volume Weighted Average Price."""
        return self._get_provider().get_vwap(symbol, **kwargs)
    
    def get_sar(self, symbol: str, acceleration: float = 0.02, maximum: float = 0.2, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Parabolic SAR."""
        return self._get_provider().get_sar(symbol, acceleration=acceleration, maximum=maximum, **kwargs)
    
    def get_supertrend(self, symbol: str, period: int = 10, multiplier: float = 3.0, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Supertrend indicator."""
        return self._get_provider().get_supertrend(symbol, period=period, multiplier=multiplier, **kwargs)
    
    def get_ichimoku(self, symbol: str, tenkan: int = 9, kijun: int = 26, senkou: int = 52, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Ichimoku Cloud (tenkan, kijun, senkou spans, chikou)."""
        return self._get_provider().get_ichimoku(symbol, tenkan=tenkan, kijun=kijun, senkou=senkou, **kwargs)
    
    def get_keltner(self, symbol: str, period: int = 20, atr_period: int = 10, multiplier: float = 2.0, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Keltner Channels."""
        return self._get_provider().get_keltner(symbol, period=period, atr_period=atr_period, multiplier=multiplier, **kwargs)
    
    def get_donchian(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Donchian Channels."""
        return self._get_provider().get_donchian(symbol, period=period, **kwargs)
    
    # ==========================================================================
    # MOMENTUM INDICATORS
    # ==========================================================================
    
    def get_rsi(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Relative Strength Index (RSI)."""
        return self._get_provider().get_rsi(symbol, period=period, **kwargs)
    
    def get_macd(self, symbol: str, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get MACD (macd, macd_signal, macd_hist)."""
        return self._get_provider().get_macd(symbol, fast_period=fast_period, slow_period=slow_period, signal_period=signal_period, **kwargs)
    
    def get_stoch(self, symbol: str, fast_k: int = 14, slow_k: int = 3, slow_d: int = 3, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Stochastic Oscillator (slow_k, slow_d)."""
        return self._get_provider().get_stoch(symbol, fast_k_period=fast_k, slow_k_period=slow_k, slow_d_period=slow_d, **kwargs)
    
    def get_stochrsi(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Stochastic RSI."""
        return self._get_provider().get_stochrsi(symbol, period=period, **kwargs)
    
    def get_adx(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Average Directional Index (trend strength)."""
        return self._get_provider().get_adx(symbol, period=period, **kwargs)
    
    def get_cci(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Commodity Channel Index."""
        return self._get_provider().get_cci(symbol, period=period, **kwargs)
    
    def get_willr(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Williams %R."""
        return self._get_provider().get_willr(symbol, period=period, **kwargs)
    
    def get_mfi(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Money Flow Index (volume-weighted RSI)."""
        return self._get_provider().get_mfi(symbol, period=period, **kwargs)
    
    def get_aroon(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Aroon indicator (aroon_up, aroon_down)."""
        return self._get_provider().get_aroon(symbol, period=period, **kwargs)
    
    def get_ppo(self, symbol: str, fast_period: int = 12, slow_period: int = 26, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Percentage Price Oscillator."""
        return self._get_provider().get_ppo(symbol, fast_period=fast_period, slow_period=slow_period, **kwargs)
    
    def get_mom(self, symbol: str, period: int = 10, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Momentum."""
        return self._get_provider().get_mom(symbol, period=period, **kwargs)
    
    def get_roc(self, symbol: str, period: int = 10, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Rate of Change."""
        return self._get_provider().get_roc(symbol, period=period, **kwargs)
    
    def get_trix(self, symbol: str, period: int = 18, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get TRIX (triple smoothed EMA rate of change)."""
        return self._get_provider().get_trix(symbol, period=period, **kwargs)
    
    def get_ultosc(self, symbol: str, period1: int = 7, period2: int = 14, period3: int = 28, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Ultimate Oscillator."""
        return self._get_provider().get_ultosc(symbol, period1=period1, period2=period2, period3=period3, **kwargs)
    
    def get_dx(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Directional Movement Index."""
        return self._get_provider().get_dx(symbol, period=period, **kwargs)
    
    def get_plus_di(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Plus Directional Indicator (+DI)."""
        return self._get_provider().get_plus_di(symbol, period=period, **kwargs)
    
    def get_minus_di(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Minus Directional Indicator (-DI)."""
        return self._get_provider().get_minus_di(symbol, period=period, **kwargs)
    
    # ==========================================================================
    # VOLATILITY INDICATORS
    # ==========================================================================
    
    def get_atr(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Average True Range."""
        return self._get_provider().get_atr(symbol, period=period, **kwargs)
    
    def get_natr(self, symbol: str, period: int = 14, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Normalized Average True Range."""
        return self._get_provider().get_natr(symbol, period=period, **kwargs)
    
    def get_trange(self, symbol: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get True Range."""
        return self._get_provider().get_trange(symbol, **kwargs)
    
    def get_stddev(self, symbol: str, period: int = 5, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Standard Deviation."""
        return self._get_provider().get_stddev(symbol, period=period, **kwargs)
    
    # ==========================================================================
    # VOLUME INDICATORS
    # ==========================================================================
    
    def get_obv(self, symbol: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get On Balance Volume."""
        return self._get_provider().get_obv(symbol, **kwargs)
    
    def get_ad(self, symbol: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Accumulation/Distribution Line."""
        return self._get_provider().get_ad(symbol, **kwargs)
    
    def get_adosc(self, symbol: str, fast_period: int = 3, slow_period: int = 10, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Chaikin A/D Oscillator."""
        return self._get_provider().get_adosc(symbol, fast_period=fast_period, slow_period=slow_period, **kwargs)
    
    def get_vwma(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Volume Weighted Moving Average."""
        return self._get_provider().get_vwma(symbol, period=period, **kwargs)
    
    def get_cmf(self, symbol: str, period: int = 20, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Chaikin Money Flow."""
        return self._get_provider().get_cmf(symbol, period=period, **kwargs)
    
    def get_force_index(self, symbol: str, period: int = 13, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get Force Index."""
        return self._get_provider().get_force_index(symbol, period=period, **kwargs)
    
    # ==========================================================================
    # CANDLESTICK PATTERNS
    # ==========================================================================
    
    def get_pattern(self, pattern: str, symbol: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get candlestick pattern signals.
        
        Args:
            pattern: Pattern name (e.g., "cdl_doji", "cdl_hammer", "cdl_engulfing")
            symbol: Symbol
            
        Returns:
            List of pattern signals (100=bullish, -100=bearish, 0=no pattern)
        """
        return self._get_provider().get_cdl_pattern(pattern, symbol, **kwargs)
    
    # ==========================================================================
    # GENERIC INDICATOR
    # ==========================================================================
    
    def indicator(self, name: str, symbol: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get any technical indicator by name.
        
        This is a generic method for accessing any TwelveData indicator.
        For specific indicators with proper typing, use dedicated methods.
        
        Args:
            name: Indicator name (e.g., "stoch", "adx", "mama")
            symbol: Symbol
            **kwargs: Indicator-specific parameters
            
        Returns:
            List of indicator values
        """
        return self._get_provider().get_indicator(name, symbol, **kwargs)


class _SocialNamespace:
    """Direct access to social sentiment data."""
    
    def __init__(self, parent: "DataClient"):
        self._parent = parent
        self._reddit: Any = None
        self._stocktwits: Any = None
    
    def _get_reddit(self) -> Any:
        if self._reddit is None:
            from .providers.social import RedditProvider
            self._reddit = RedditProvider()
        return self._reddit
    
    def _get_stocktwits(self) -> Any:
        if self._stocktwits is None:
            from .providers.social import StocktwitsProvider
            self._stocktwits = StocktwitsProvider()
        return self._stocktwits
    
    def get_posts(
        self,
        symbols: Optional[List[str]] = None,
        source: str = "reddit",
        **kwargs: Any,
    ) -> List[SocialPost]:
        """Get social media posts."""
        if source.lower() == "stocktwits":
            return self._get_stocktwits().get_posts(symbols=symbols, **kwargs)
        return self._get_reddit().get_posts(symbols=symbols, **kwargs)
    
    def trending(self, source: str = "reddit", limit: int = 20) -> List[str]:
        """Get trending symbols."""
        if source.lower() == "stocktwits":
            return self._get_stocktwits().get_trending(limit=limit)
        return self._get_reddit().get_trending(limit=limit)
    
    def sentiment(self, symbol: str, source: str = "reddit") -> Dict[str, float]:
        """Get aggregated sentiment."""
        if source.lower() == "stocktwits":
            return self._get_stocktwits().get_sentiment(symbol)
        return self._get_reddit().get_sentiment(symbol)


class _DatabentoNamespace:
    """Direct access to Databento Market Data."""
    
    def __init__(self, parent: "DataClient"):
        self._parent = parent
        self._provider: Any = None
    
    def _get_provider(self) -> Any:
        if self._provider is None:
            self._parent._load_credentials_from_cpzai()
            from .providers.databento import DatabentoProvider
            self._provider = DatabentoProvider(
                api_key=self._parent._config.get("databento_api_key"),
            )
        return self._provider
    
    def get_bars(self, symbol: str, timeframe: TimeFrame | str = TimeFrame.DAY, **kwargs: Any) -> List[Bar]:
        """Get bars from Databento."""
        return self._get_provider().get_bars(symbol, timeframe, **kwargs)
    
    def get_quotes(self, symbols: List[str], **kwargs: Any) -> List[Quote]:
        """Get quotes from Databento."""
        return self._get_provider().get_quotes(symbols, **kwargs)


class _YFinanceNamespace:
    """Direct access to Yahoo Finance data (free, no API key required).
    
    Perfect for backtesting with historical data.
    Supports stocks, ETFs, indices, and crypto.
    """
    
    def __init__(self, parent: "DataClient"):
        self._parent = parent
        self._provider: Any = None
    
    def _get_provider(self) -> Any:
        if self._provider is None:
            from .providers.yfinance import YFinanceProvider
            self._provider = YFinanceProvider()
        return self._provider
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Bar]:
        """Get historical bars from Yahoo Finance.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "BTC-USD", "^VIX")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum bars
            
        Returns:
            List of Bar objects
        """
        return self._get_provider().get_bars(symbol, timeframe, start=start, end=end, limit=limit)
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get latest quote."""
        return self._get_provider().get_quote(symbol)
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get latest quotes for multiple symbols."""
        return self._get_provider().get_quotes(symbols)
    
    def download(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        timeframe: TimeFrame | str = TimeFrame.DAY,
    ) -> Dict[str, List[Bar]]:
        """Batch download historical data for multiple symbols.
        
        Optimized for backtesting.
        
        Args:
            symbols: List of symbols
            start: Start datetime
            end: End datetime
            timeframe: Bar timeframe
            
        Returns:
            Dict mapping symbol to list of bars
        """
        return self._get_provider().download(symbols, start, end, timeframe)


class _AlphaVantageNamespace:
    """Direct access to Alpha Vantage data.
    
    Premium market data with extensive historical coverage.
    Free tier: 25 requests/day.
    """
    
    def __init__(self, parent: "DataClient"):
        self._parent = parent
        self._provider: Any = None
    
    def _get_provider(self) -> Any:
        if self._provider is None:
            self._parent._load_credentials_from_cpzai()
            from .providers.alphavantage import AlphaVantageProvider
            self._provider = AlphaVantageProvider(
                api_key=self._parent._config.get("alphavantage_api_key"),
            )
        return self._provider
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Bar]:
        """Get historical bars from Alpha Vantage."""
        return self._get_provider().get_bars(symbol, timeframe, start=start, end=end, limit=limit)
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get latest quote."""
        return self._get_provider().get_quote(symbol)
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get quotes for multiple symbols."""
        return self._get_provider().get_quotes(symbols)
    
    def get_forex(
        self,
        from_currency: str,
        to_currency: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Bar]:
        """Get forex data."""
        return self._get_provider().get_forex(from_currency, to_currency, timeframe, start, end)
    
    def get_crypto(
        self,
        symbol: str,
        market: str = "USD",
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Bar]:
        """Get cryptocurrency data."""
        return self._get_provider().get_crypto(symbol, market, timeframe, start, end)


class _PolygonNamespace:
    """Direct access to Polygon.io data.
    
    Real-time and historical data for stocks, options, forex, crypto.
    """
    
    def __init__(self, parent: "DataClient"):
        self._parent = parent
        self._provider: Any = None
    
    def _get_provider(self) -> Any:
        if self._provider is None:
            self._parent._load_credentials_from_cpzai()
            from .providers.polygon import PolygonProvider
            self._provider = PolygonProvider(
                api_key=self._parent._config.get("polygon_api_key"),
            )
        return self._provider
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50000,
    ) -> List[Bar]:
        """Get historical bars from Polygon."""
        return self._get_provider().get_bars(symbol, timeframe, start=start, end=end, limit=limit)
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get latest quote."""
        return self._get_provider().get_quote(symbol)
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get quotes for multiple symbols."""
        return self._get_provider().get_quotes(symbols)
    
    def get_trades(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50000,
    ) -> List[Trade]:
        """Get historical trades."""
        return self._get_provider().get_trades(symbol, start, end, limit)
    
    def get_news(
        self,
        symbols: Optional[List[str]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[News]:
        """Get news articles."""
        return self._get_provider().get_news(symbols, start, end, limit)
    
    def get_crypto_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Bar]:
        """Get crypto bars."""
        return self._get_provider().get_crypto_bars(symbol, timeframe, start, end)
    
    def get_forex_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Bar]:
        """Get forex bars."""
        return self._get_provider().get_forex_bars(symbol, timeframe, start, end)
    
    def get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """Get ticker details/fundamentals."""
        return self._get_provider().get_ticker_details(symbol)
    
    def get_financials(
        self,
        symbol: str,
        limit: int = 10,
        timeframe: str = "annual",
    ) -> List[Dict[str, Any]]:
        """Get company financials."""
        return self._get_provider().get_financials(symbol, limit, timeframe)


class DataClient:
    """Unified data client with hybrid namespace design.
    
    All data API credentials are managed through the CPZAI platform.
    Users only need their CPZAI API keys to access all data sources.
    
    Simple Usage:
        client.data.bars("AAPL")           # Stock bars (routes to Alpaca)
        client.data.quotes(["AAPL"])       # Stock quotes
        client.data.news("AAPL")           # News articles
        client.data.economic("GDP")        # Economic data (routes to FRED)
        client.data.filings("AAPL")        # SEC filings (routes to EDGAR)
        client.data.social("AAPL")         # Social sentiment
    
    Power User Access:
        client.data.alpaca.get_options_chain("AAPL")
        client.data.fred.get_series("UNRATE")
        client.data.twelve.get_rsi("AAPL")
    """
    
    def __init__(
        self,
        cpz_client: Any = None,
        alpaca_api_key: Optional[str] = None,
        alpaca_api_secret: Optional[str] = None,
        alpaca_feed: str = "iex",
        fred_api_key: Optional[str] = None,
        twelve_api_key: Optional[str] = None,
    ):
        """Initialize data client.
        
        Credentials are fetched automatically from the CPZAI platform.
        Users only need their CPZAI API keys configured.
        
        Args:
            cpz_client: CPZAIClient instance for fetching credentials from platform
            alpaca_api_key: Override Alpaca API key (optional)
            alpaca_api_secret: Override Alpaca API secret (optional)
            alpaca_feed: Alpaca data feed ("iex" or "sip")
            fred_api_key: Override FRED API key (optional)
            twelve_api_key: Override Twelve Data API key (optional)
        """
        self._cpz_client = cpz_client
        self._credentials_loaded = False
        
        # Start with any explicitly provided credentials
        self._config: Dict[str, Any] = {
            "alpaca_api_key": alpaca_api_key,
            "alpaca_api_secret": alpaca_api_secret,
            "alpaca_feed": alpaca_feed,
            "fred_api_key": fred_api_key,
            "twelve_api_key": twelve_api_key,
        }
        
        # Provider namespaces (lazy-loaded)
        self._alpaca: Optional[_AlpacaNamespace] = None
        self._alphavantage: Optional[_AlphaVantageNamespace] = None
        self._databento: Optional[_DatabentoNamespace] = None
        self._fred: Optional[_FREDNamespace] = None
        self._edgar: Optional[_EDGARNamespace] = None
        self._polygon: Optional[_PolygonNamespace] = None
        self._twelve: Optional[_TwelveNamespace] = None
        self._social: Optional[_SocialNamespace] = None
        self._yfinance: Optional[_YFinanceNamespace] = None
    
    def _load_credentials_from_cpzai(self) -> None:
        """Load data API credentials from CPZAI platform.
        
        All data provider API keys are managed on the CPZAI platform.
        This method fetches them automatically when needed.
        """
        if self._credentials_loaded:
            return
        self._credentials_loaded = True
        
        if self._cpz_client is None:
            return
        
        try:
            creds = self._cpz_client.get_data_credentials()
            
            # Only update config for credentials not already explicitly set
            if not self._config.get("fred_api_key") and creds.get("fred_api_key"):
                self._config["fred_api_key"] = creds["fred_api_key"]
            
            if not self._config.get("alpaca_api_key") and creds.get("alpaca_api_key"):
                self._config["alpaca_api_key"] = creds["alpaca_api_key"]
            
            if not self._config.get("alpaca_api_secret") and creds.get("alpaca_api_secret"):
                self._config["alpaca_api_secret"] = creds["alpaca_api_secret"]
            
            if not self._config.get("twelve_api_key") and creds.get("twelve_api_key"):
                self._config["twelve_api_key"] = creds["twelve_api_key"]
            
            if not self._config.get("databento_api_key") and creds.get("databento_api_key"):
                self._config["databento_api_key"] = creds["databento_api_key"]
        except Exception:
            pass  # Continue without platform credentials
    
    # --- Provider Namespaces (Power User Access) ---
    
    @property
    def alpaca(self) -> _AlpacaNamespace:
        """Direct access to Alpaca Market Data."""
        if self._alpaca is None:
            self._alpaca = _AlpacaNamespace(self)
        return self._alpaca
    
    @property
    def databento(self) -> _DatabentoNamespace:
        """Direct access to Databento Market Data."""
        if self._databento is None:
            self._databento = _DatabentoNamespace(self)
        return self._databento
    
    @property
    def fred(self) -> _FREDNamespace:
        """Direct access to FRED economic data."""
        if self._fred is None:
            self._fred = _FREDNamespace(self)
        return self._fred
    
    @property
    def edgar(self) -> _EDGARNamespace:
        """Direct access to SEC EDGAR filings."""
        if self._edgar is None:
            self._edgar = _EDGARNamespace(self)
        return self._edgar
    
    @property
    def twelve(self) -> _TwelveNamespace:
        """Direct access to Twelve Data."""
        if self._twelve is None:
            self._twelve = _TwelveNamespace(self)
        return self._twelve
    
    @property
    def social(self) -> _SocialNamespace:
        """Direct access to social sentiment data."""
        if self._social is None:
            self._social = _SocialNamespace(self)
        return self._social
    
    @property
    def yfinance(self) -> _YFinanceNamespace:
        """Direct access to Yahoo Finance data (free, no API key required).
        
        Perfect for backtesting. Supports stocks, ETFs, indices, crypto.
        
        Examples:
            >>> bars = client.data.yfinance.get_bars("AAPL", start=datetime(2023, 1, 1))
            >>> data = client.data.yfinance.download(["AAPL", "MSFT"], start, end)
        """
        if self._yfinance is None:
            self._yfinance = _YFinanceNamespace(self)
        return self._yfinance
    
    @property
    def alphavantage(self) -> _AlphaVantageNamespace:
        """Direct access to Alpha Vantage data.
        
        Premium data with extensive history. Free tier: 25 requests/day.
        
        Examples:
            >>> bars = client.data.alphavantage.get_bars("AAPL", start=datetime(2020, 1, 1))
            >>> forex = client.data.alphavantage.get_forex("EUR", "USD")
        """
        if self._alphavantage is None:
            self._alphavantage = _AlphaVantageNamespace(self)
        return self._alphavantage
    
    @property
    def polygon(self) -> _PolygonNamespace:
        """Direct access to Polygon.io data.
        
        Real-time and historical data for stocks, options, forex, crypto.
        
        Examples:
            >>> bars = client.data.polygon.get_bars("AAPL", start=datetime(2023, 1, 1))
            >>> news = client.data.polygon.get_news(["AAPL", "TSLA"])
        """
        if self._polygon is None:
            self._polygon = _PolygonNamespace(self)
        return self._polygon
    
    # --- Unified Simple Interface ---
    
    def bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
        provider: str = "auto",  # "auto", "alpaca", "twelve"
    ) -> List[Bar]:
        """Get historical price bars.
        
        Smart routing: Uses Alpaca for US stocks and all crypto pairs.
        Crypto pairs are detected by "/" in the symbol (e.g., "BTC/USD", "DOGE/USD").
        For forex data, explicitly specify provider="twelve".
        
        Args:
            symbol: Symbol (e.g., "AAPL", "BTC/USD", "DOGE/USD")
            timeframe: Bar timeframe (e.g., "1D", "1H", TimeFrame.DAY)
            start: Start datetime
            end: End datetime
            limit: Maximum bars to return
            provider: Force specific provider or "auto" for smart routing
            
        Returns:
            List of Bar objects
            
        Examples:
            >>> bars = client.data.bars("AAPL", timeframe="1D", limit=100)
            >>> crypto = client.data.bars("BTC/USD", timeframe="1H")
            >>> altcoin = client.data.bars("DOGE/USD", timeframe="1D")
            >>> forex = client.data.bars("EUR/USD", provider="twelve")
        """
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        # Route through CPZ backend - supports ANY provider the user has connected
        if self._cpz_client is not None:
            try:
                result = self._cpz_client.fetch_data(
                    action="bars",
                    symbols=[symbol],
                    timeframe=timeframe.value if isinstance(timeframe, TimeFrame) else timeframe,
                    start=start.isoformat() if start else None,
                    end=end.isoformat() if end else None,
                    limit=limit,
                    provider=provider if provider != "auto" else None,
                )
                if result and "bars" in result:
                    bars_data = result["bars"].get(symbol, [])
                    return [
                        Bar(
                            symbol=symbol,
                            timestamp=b.get("timestamp"),
                            open=float(b.get("open", 0)),
                            high=float(b.get("high", 0)),
                            low=float(b.get("low", 0)),
                            close=float(b.get("close", 0)),
                            volume=float(b.get("volume", 0)),
                            vwap=float(b.get("vwap")) if b.get("vwap") else None,
                        )
                        for b in bars_data
                    ]
            except Exception as e:
                print(f"[CPZ SDK] Backend data fetch failed, falling back to direct provider: {e}")
        
        # Fallback to direct provider calls (legacy behavior)
        if provider == "auto":
            provider = "alpaca"
        
        if provider == "databento":
            return self.databento.get_bars(symbol, timeframe, start=start, end=end, limit=limit)
        
        if provider == "twelve":
            return self.twelve.get_bars(symbol, timeframe, start=start, end=end, limit=limit)
        
        # Alpaca - detect crypto vs stock
        if "/" in symbol:
            return self.alpaca.get_crypto_bars(symbol, timeframe, start=start, end=end, limit=limit)
        return self.alpaca.get_bars(symbol, timeframe, start=start, end=end, limit=limit)
    
    def history(
        self,
        symbols: Union[str, List[str]],
        start: Union[str, datetime],
        end: Optional[Union[str, datetime]] = None,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        provider: str = "auto",
    ) -> Dict[str, List[Bar]]:
        """Get historical data for backtesting - SIMPLIFIED API.
        
        This is the recommended method for backtesting. It returns data in a 
        format ready for use with backtrader, vectorbt, or custom backtests.
        
        Provider priority (when auto):
            1. Alpaca (if connected) - best for recent US stocks/crypto
            2. Yahoo Finance (free fallback) - works for any historical period
        
        Args:
            symbols: Single symbol or list of symbols (e.g., "AAPL" or ["AAPL", "MSFT"])
            start: Start date (string "YYYY-MM-DD" or datetime)
            end: End date (string "YYYY-MM-DD" or datetime, defaults to today)
            timeframe: Bar timeframe ("1D", "1H", etc.)
            provider: Data provider:
                - "auto": Tries Alpaca first, falls back to Yahoo Finance
                - "alpaca": Alpaca Markets (requires API key)
                - "yfinance": Yahoo Finance (free, no API key)
                - "polygon": Polygon.io (requires API key)
                - "alphavantage": Alpha Vantage (free tier: 25/day)
                - "databento": Databento (requires API key)
                - "twelve": Twelve Data (requires API key)
            
        Returns:
            Dict mapping symbol to list of Bar objects
            
        Examples:
            >>> # Simple usage - get 1 year of daily AAPL data
            >>> data = client.data.history("AAPL", "2023-01-01", "2024-01-01")
            
            >>> # Multiple symbols for portfolio backtest
            >>> data = client.data.history(
            ...     ["AAPL", "MSFT", "GOOGL"],
            ...     start="2023-01-01",
            ...     end="2024-01-01",
            ... )
            
            >>> # Force Yahoo Finance (free, no API key needed)
            >>> data = client.data.history("AAPL", "2020-01-01", provider="yfinance")
            
            >>> # Use Polygon for premium data
            >>> data = client.data.history("AAPL", "2020-01-01", provider="polygon")
            
            >>> # Access bars like this:
            >>> for bar in data["AAPL"]:
            ...     print(f"{bar.timestamp}: {bar.close}")
        """
        # Normalize inputs
        if isinstance(symbols, str):
            symbols = [symbols]
        
        if isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d")
        
        if end is None:
            end = datetime.utcnow()
        elif isinstance(end, str):
            end = datetime.strptime(end, "%Y-%m-%d")
        
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        result: Dict[str, List[Bar]] = {}
        
        # Route to specific provider
        if provider == "yfinance":
            return self.yfinance.download(symbols, start, end, timeframe)
        
        if provider == "polygon":
            for symbol in symbols:
                bars = self.polygon.get_bars(symbol, timeframe, start=start, end=end)
                if bars:
                    result[symbol] = bars
            return result
        
        if provider == "alphavantage":
            for symbol in symbols:
                bars = self.alphavantage.get_bars(symbol, timeframe, start=start, end=end)
                if bars:
                    result[symbol] = bars
            return result
        
        if provider == "databento":
            for symbol in symbols:
                bars = self.databento.get_bars(symbol, timeframe, start=start, end=end)
                if bars:
                    result[symbol] = bars
            return result
        
        if provider == "twelve":
            for symbol in symbols:
                bars = self.twelve.get_bars(symbol, timeframe, start=start, end=end)
                if bars:
                    result[symbol] = bars
            return result
        
        if provider == "alpaca":
            for symbol in symbols:
                if "/" in symbol:
                    bars = self.alpaca.get_crypto_bars(symbol, timeframe, start=start, end=end)
                else:
                    bars = self.alpaca.get_bars(symbol, timeframe, start=start, end=end)
                if bars:
                    result[symbol] = bars
            return result
        
        # Auto mode: try Alpaca first, fall back to Yahoo Finance
        for symbol in symbols:
            bars: List[Bar] = []
            
            # Try Alpaca first (if credentials available)
            try:
                if "/" in symbol:
                    bars = self.alpaca.get_crypto_bars(symbol, timeframe, start=start, end=end)
                else:
                    bars = self.alpaca.get_bars(symbol, timeframe, start=start, end=end)
            except Exception as e:
                print(f"[CPZ SDK] Alpaca failed for {symbol}: {e}")
            
            # Fall back to Yahoo Finance if Alpaca returned no data
            if not bars:
                try:
                    bars = self.yfinance.get_bars(symbol, timeframe, start=start, end=end)
                except Exception as e:
                    print(f"[CPZ SDK] Yahoo Finance also failed for {symbol}: {e}")
            
            if bars:
                result[symbol] = bars
        
        return result
    
    def quotes(
        self,
        symbols: Union[str, List[str]],
        provider: str = "auto",
    ) -> List[Quote]:
        """Get latest quotes.
        
        Args:
            symbols: Symbol or list of symbols
            provider: Force specific provider ("alpaca", "twelve") or "auto"
            
        Returns:
            List of Quote objects
            
        Examples:
            >>> quotes = client.data.quotes(["AAPL", "MSFT", "GOOGL"])
            >>> quote = client.data.quotes("AAPL")[0]
            >>> forex = client.data.quotes("EUR/USD", provider="twelve")
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        
        # Route through CPZ backend - supports ANY provider the user has connected
        if self._cpz_client is not None:
            try:
                result = self._cpz_client.fetch_data(
                    action="quotes",
                    symbols=symbols,
                    provider=provider if provider != "auto" else None,
                )
                if result and "quotes" in result:
                    quotes_data = result["quotes"]
                    return [
                        Quote(
                            symbol=sym,
                            bid=float(q.get("bid_price", 0) or q.get("bid", 0)),
                            ask=float(q.get("ask_price", 0) or q.get("ask", 0)),
                            bid_size=float(q.get("bid_size", 0)),
                            ask_size=float(q.get("ask_size", 0)),
                            timestamp=q.get("timestamp"),
                        )
                        for sym, q in quotes_data.items()
                    ]
            except Exception as e:
                print(f"[CPZ SDK] Backend quotes fetch failed, falling back to direct provider: {e}")
        
        # Fallback to direct provider calls (legacy behavior)
        # Smart routing when auto
        if provider == "auto":
            # Check if any symbols are forex (contain "/" but not crypto)
            has_forex = any(
                "/" in s and not any(c in s for c in ["BTC", "ETH", "SOL"])
                for s in symbols
            )
            if has_forex:
                provider = "twelve"
            else:
                provider = "alpaca"
        
        # Route to Databento
        if provider == "databento":
            return self.databento.get_quotes(symbols)
        
        # Route to Twelve Data
        if provider == "twelve":
            return self.twelve.get_quotes(symbols)
        
        # Alpaca - handle crypto vs stock
        has_crypto = any("/" in s for s in symbols)
        
        if has_crypto:
            crypto_symbols = [s for s in symbols if "/" in s]
            stock_symbols = [s for s in symbols if "/" not in s]
            
            quotes: List[Quote] = []
            if crypto_symbols:
                quotes.extend(self.alpaca.get_crypto_quotes(crypto_symbols))
            if stock_symbols:
                quotes.extend(self.alpaca.get_quotes(stock_symbols))
            return quotes
        
        return self.alpaca.get_quotes(symbols)
    
    def trades(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Trade]:
        """Get historical trades.
        
        Args:
            symbol: Stock symbol
            start: Start datetime
            end: End datetime
            limit: Maximum trades
            
        Returns:
            List of Trade objects
        """
        return self.alpaca.get_trades(symbol, start=start, end=end, limit=limit)
    
    def news(
        self,
        symbols: Optional[Union[str, List[str]]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[News]:
        """Get news articles.
        
        Args:
            symbols: Filter by symbols (optional)
            start: Start datetime
            end: End datetime
            limit: Maximum articles
            
        Returns:
            List of News objects
            
        Examples:
            >>> news = client.data.news("AAPL", limit=10)
            >>> news = client.data.news(["AAPL", "TSLA"])
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        return self.alpaca.get_news(symbols, start=start, end=end, limit=limit)
    
    def options(
        self,
        underlying: str,
        expiration: Optional[datetime] = None,
        option_type: Optional[str] = None,
        strike_min: Optional[float] = None,
        strike_max: Optional[float] = None,
    ) -> List[OptionContract]:
        """Get options chain.
        
        Args:
            underlying: Underlying stock symbol
            expiration: Expiration date filter
            option_type: "call" or "put"
            strike_min: Minimum strike price
            strike_max: Maximum strike price
            
        Returns:
            List of OptionContract objects
            
        Examples:
            >>> chain = client.data.options("AAPL")
            >>> calls = client.data.options("AAPL", option_type="call")
        """
        return self.alpaca.get_options_chain(
            underlying,
            expiration_date=expiration,
            option_type=option_type,
            strike_price_gte=strike_min,
            strike_price_lte=strike_max,
        )
    
    def economic(
        self,
        series_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[EconomicSeries]:
        """Get economic data series from FRED.
        
        Args:
            series_id: FRED series ID (e.g., "GDP", "UNRATE", "CPIAUCSL")
            start: Start datetime
            end: End datetime
            limit: Maximum observations
            
        Returns:
            List of EconomicSeries observations
            
        Examples:
            >>> gdp = client.data.economic("GDP")
            >>> unemployment = client.data.economic("UNRATE", limit=12)
            >>> cpi = client.data.economic("CPIAUCSL", start=datetime(2020, 1, 1))
        """
        return self.fred.get_series(series_id, start=start, end=end, limit=limit)
    
    def filings(
        self,
        symbol: str,
        form: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Filing]:
        """Get SEC filings.
        
        Args:
            symbol: Stock symbol
            form: Form type (e.g., "10-K", "10-Q", "8-K")
            start: Start datetime
            end: End datetime
            limit: Maximum filings
            
        Returns:
            List of Filing objects
            
        Examples:
            >>> filings = client.data.filings("AAPL", form="10-K")
            >>> recent = client.data.filings("TSLA", limit=5)
        """
        return self.edgar.get_filings(
            symbol, form_type=form, start=start, end=end, limit=limit
        )
    
    def sentiment(
        self,
        symbol: str,
        source: str = "all",  # "all", "reddit", "stocktwits"
    ) -> Dict[str, Any]:
        """Get social sentiment for a symbol.
        
        Args:
            symbol: Stock symbol
            source: "reddit", "stocktwits", or "all"
            
        Returns:
            Aggregated sentiment data
            
        Examples:
            >>> sentiment = client.data.sentiment("AAPL")
            >>> reddit = client.data.sentiment("GME", source="reddit")
        """
        if source == "all":
            reddit = self.social.sentiment(symbol, source="reddit")
            stocktwits = self.social.sentiment(symbol, source="stocktwits")
            
            # Combine sentiments
            total_posts = reddit.get("post_count", 0) + stocktwits.get("post_count", 0)
            if total_posts == 0:
                return {
                    "score": 0.0,
                    "bullish_pct": 0.0,
                    "bearish_pct": 0.0,
                    "neutral_pct": 1.0,
                    "post_count": 0,
                    "sources": {"reddit": reddit, "stocktwits": stocktwits},
                }
            
            # Weighted average
            reddit_weight = reddit.get("post_count", 0) / total_posts
            stocktwits_weight = stocktwits.get("post_count", 0) / total_posts
            
            return {
                "score": reddit.get("score", 0) * reddit_weight + stocktwits.get("score", 0) * stocktwits_weight,
                "bullish_pct": reddit.get("bullish_pct", 0) * reddit_weight + stocktwits.get("bullish_pct", 0) * stocktwits_weight,
                "bearish_pct": reddit.get("bearish_pct", 0) * reddit_weight + stocktwits.get("bearish_pct", 0) * stocktwits_weight,
                "neutral_pct": reddit.get("neutral_pct", 0) * reddit_weight + stocktwits.get("neutral_pct", 0) * stocktwits_weight,
                "post_count": total_posts,
                "sources": {"reddit": reddit, "stocktwits": stocktwits},
            }
        
        return self.social.sentiment(symbol, source=source)
    
    def trending(self, source: str = "stocktwits", limit: int = 20) -> List[str]:
        """Get trending stock symbols.
        
        Args:
            source: "reddit" or "stocktwits"
            limit: Maximum symbols
            
        Returns:
            List of trending symbols
            
        Examples:
            >>> trending = client.data.trending()
            >>> reddit_trending = client.data.trending(source="reddit")
        """
        return self.social.trending(source=source, limit=limit)
    
    # --- Technical Indicators (convenience) ---
    
    def sma(
        self,
        symbol: str,
        period: int = 20,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Simple Moving Average.
        
        Args:
            symbol: Stock symbol
            period: SMA period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of SMA values with timestamps
        """
        return self.twelve.get_sma(symbol, period=period, timeframe=timeframe, limit=limit)
    
    def rsi(
        self,
        symbol: str,
        period: int = 14,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Relative Strength Index.
        
        Args:
            symbol: Stock symbol
            period: RSI period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of RSI values with timestamps
        """
        return self.twelve.get_rsi(symbol, period=period, timeframe=timeframe, limit=limit)
    
    def macd(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get MACD.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of MACD values with timestamps (macd, macd_signal, macd_hist)
        """
        return self.twelve.get_macd(symbol, timeframe=timeframe, limit=limit)
    
    def ema(
        self,
        symbol: str,
        period: int = 20,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Exponential Moving Average.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            period: EMA period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of EMA values with timestamps
        """
        return self.twelve.get_ema(symbol, period=period, timeframe=timeframe, limit=limit)
    
    def bbands(
        self,
        symbol: str,
        period: int = 20,
        std_dev: float = 2.0,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Bollinger Bands.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            period: Period for moving average
            std_dev: Standard deviation multiplier
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of Bollinger Band values (upper_band, middle_band, lower_band)
        """
        return self.twelve.get_bbands(symbol, period=period, std_dev=std_dev, timeframe=timeframe, limit=limit)
    
    def stoch(
        self,
        symbol: str,
        fast_k: int = 14,
        slow_k: int = 3,
        slow_d: int = 3,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Stochastic Oscillator.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            fast_k: Fast %K period
            slow_k: Slow %K period
            slow_d: Slow %D period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of Stochastic values (slow_k, slow_d)
        """
        return self.twelve.get_stoch(symbol, fast_k=fast_k, slow_k=slow_k, slow_d=slow_d, timeframe=timeframe, limit=limit)
    
    def adx(
        self,
        symbol: str,
        period: int = 14,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Average Directional Index (trend strength indicator).
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            period: ADX period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of ADX values with timestamps
        """
        return self.twelve.get_adx(symbol, period=period, timeframe=timeframe, limit=limit)
    
    def atr(
        self,
        symbol: str,
        period: int = 14,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Average True Range (volatility indicator).
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            period: ATR period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of ATR values with timestamps
        """
        return self.twelve.get_atr(symbol, period=period, timeframe=timeframe, limit=limit)
    
    def obv(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get On Balance Volume.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of OBV values with timestamps
        """
        return self.twelve.get_obv(symbol, timeframe=timeframe, limit=limit)
    
    def vwap(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Volume Weighted Average Price.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of VWAP values with timestamps
        """
        return self.twelve.get_vwap(symbol, timeframe=timeframe, limit=limit)
    
    def ichimoku(
        self,
        symbol: str,
        tenkan: int = 9,
        kijun: int = 26,
        senkou: int = 52,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Ichimoku Cloud.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            tenkan: Tenkan-sen (conversion line) period
            kijun: Kijun-sen (base line) period
            senkou: Senkou Span B period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of Ichimoku values (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span)
        """
        return self.twelve.get_ichimoku(symbol, tenkan=tenkan, kijun=kijun, senkou=senkou, timeframe=timeframe, limit=limit)
    
    def cci(
        self,
        symbol: str,
        period: int = 20,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Commodity Channel Index.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            period: CCI period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of CCI values with timestamps
        """
        return self.twelve.get_cci(symbol, period=period, timeframe=timeframe, limit=limit)
    
    def mfi(
        self,
        symbol: str,
        period: int = 14,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Money Flow Index (volume-weighted RSI).
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            period: MFI period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of MFI values with timestamps
        """
        return self.twelve.get_mfi(symbol, period=period, timeframe=timeframe, limit=limit)
    
    def willr(
        self,
        symbol: str,
        period: int = 14,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Williams %R.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            period: Williams %R period
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of Williams %R values with timestamps
        """
        return self.twelve.get_willr(symbol, period=period, timeframe=timeframe, limit=limit)
    
    def supertrend(
        self,
        symbol: str,
        period: int = 10,
        multiplier: float = 3.0,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get Supertrend indicator.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            symbol: Stock symbol
            period: ATR period
            multiplier: ATR multiplier
            timeframe: Bar timeframe
            limit: Number of data points
            
        Returns:
            List of Supertrend values with timestamps
        """
        return self.twelve.get_supertrend(symbol, period=period, multiplier=multiplier, timeframe=timeframe, limit=limit)
    
    def indicator(
        self,
        name: str,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        limit: int = 100,
        **params: Any,
    ) -> List[Dict[str, Any]]:
        """Get any technical indicator by name.
        
        This is a generic method for accessing any TwelveData indicator.
        For specific indicators with proper typing, use dedicated methods like
        rsi(), macd(), bbands(), etc.
        
        IMPORTANT: Requires Twelve Data connection on the Data page.
        
        Args:
            name: Indicator name (e.g., "stochrsi", "aroon", "keltner")
            symbol: Stock symbol
            timeframe: Bar timeframe
            limit: Number of data points
            **params: Additional indicator-specific parameters
            
        Returns:
            List of indicator values with timestamps
            
        Examples:
            >>> client.data.indicator("aroon", "AAPL", time_period=14)
            >>> client.data.indicator("keltner", "AAPL", time_period=20, multiplier=2)
        """
        return self.twelve.indicator(name, symbol, timeframe=timeframe, limit=limit, **params)