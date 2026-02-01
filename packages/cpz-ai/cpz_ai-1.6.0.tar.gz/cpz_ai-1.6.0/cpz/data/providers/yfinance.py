"""Yahoo Finance data provider.

Free historical market data for backtesting and research.
No API key required.

Docs: https://github.com/ranaroussi/yfinance
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, List, Optional

from ..models import Bar, Quote, TimeFrame


class YFinanceProvider:
    """Yahoo Finance data provider.
    
    Free, no API key required. Great for backtesting historical data.
    
    Usage:
        provider = YFinanceProvider()
        bars = provider.get_bars("AAPL", start=datetime(2023, 1, 1), end=datetime(2024, 1, 1))
    """
    
    name = "yfinance"
    supported_assets = ["stocks", "etfs", "indices", "crypto"]
    
    def __init__(self) -> None:
        """Initialize Yahoo Finance provider. No API key needed."""
        self._yf: Any = None
    
    def _get_yf(self) -> Any:
        """Lazy-load yfinance."""
        if self._yf is None:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                raise ImportError(
                    "yfinance is required for Yahoo Finance data. Install with: pip install yfinance"
                )
        return self._yf
    
    def _convert_timeframe(self, tf: TimeFrame) -> str:
        """Convert TimeFrame to yfinance interval string."""
        mapping = {
            TimeFrame.MINUTE_1: "1m",
            TimeFrame.MINUTE_5: "5m",
            TimeFrame.MINUTE_15: "15m",
            TimeFrame.MINUTE_30: "30m",
            TimeFrame.HOUR_1: "1h",
            TimeFrame.HOUR_4: "4h",  # Not supported, will use 1h
            TimeFrame.DAY: "1d",
            TimeFrame.WEEK: "1wk",
            TimeFrame.MONTH: "1mo",
        }
        return mapping.get(tf, "1d")
    
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
            symbol: Stock/ETF/crypto symbol (e.g., "AAPL", "BTC-USD")
            timeframe: Bar timeframe
            start: Start datetime (required for historical data)
            end: End datetime (defaults to now)
            limit: Maximum bars to return (applied after fetching)
            
        Returns:
            List of Bar objects
            
        Examples:
            >>> bars = provider.get_bars("AAPL", start=datetime(2023, 1, 1))
            >>> bars = provider.get_bars("BTC-USD", timeframe="1D", limit=100)
        """
        yf = self._get_yf()
        
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        interval = self._convert_timeframe(timeframe)
        
        # Default to 1 year of data if no start specified
        if start is None:
            start = datetime.utcnow() - timedelta(days=365)
        if end is None:
            end = datetime.utcnow()
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                interval=interval,
                auto_adjust=True,  # Adjust for splits/dividends
            )
            
            if df is None or df.empty:
                print(f"[CPZ SDK] No data returned from Yahoo Finance for {symbol}")
                return []
            
            bars: List[Bar] = []
            for idx, row in df.iterrows():
                bars.append(Bar(
                    symbol=symbol,
                    timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
                    open=float(row.get("Open", 0)),
                    high=float(row.get("High", 0)),
                    low=float(row.get("Low", 0)),
                    close=float(row.get("Close", 0)),
                    volume=float(row.get("Volume", 0)),
                    vwap=None,  # yfinance doesn't provide VWAP
                ))
            
            # Apply limit if specified
            if limit and len(bars) > limit:
                bars = bars[-limit:]  # Return most recent bars
            
            return bars
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Yahoo Finance data for {symbol}: {e}")
            return []
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get latest quote from Yahoo Finance.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote object or None if not available
        """
        yf = self._get_yf()
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            # Yahoo Finance provides bid/ask for some securities
            bid = float(info.get("bid", 0) or 0)
            ask = float(info.get("ask", 0) or 0)
            
            # Fall back to regularMarketPrice if no bid/ask
            if bid == 0 and ask == 0:
                price = float(info.get("regularMarketPrice", 0) or 0)
                bid = price
                ask = price
            
            return Quote(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                bid=bid,
                ask=ask,
                bid_size=float(info.get("bidSize", 0) or 0),
                ask_size=float(info.get("askSize", 0) or 0),
            )
            
        except Exception as e:
            print(f"[CPZ SDK] Error fetching Yahoo Finance quote for {symbol}: {e}")
            return None
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get latest quotes for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            List of Quote objects
        """
        quotes: List[Quote] = []
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes.append(quote)
        return quotes
    
    def download(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        timeframe: TimeFrame | str = TimeFrame.DAY,
    ) -> dict[str, List[Bar]]:
        """Download historical data for multiple symbols.
        
        Optimized batch download for backtesting.
        
        Args:
            symbols: List of symbols
            start: Start datetime
            end: End datetime
            timeframe: Bar timeframe
            
        Returns:
            Dict mapping symbol to list of bars
        """
        yf = self._get_yf()
        
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        interval = self._convert_timeframe(timeframe)
        result: dict[str, List[Bar]] = {}
        
        try:
            # Use yfinance batch download for efficiency
            df = yf.download(
                tickers=symbols,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                interval=interval,
                auto_adjust=True,
                group_by="ticker",
                progress=False,
            )
            
            if df is None or df.empty:
                print(f"[CPZ SDK] No data returned from Yahoo Finance for batch download")
                return result
            
            # Handle single symbol case (no MultiIndex columns)
            if len(symbols) == 1:
                symbol = symbols[0]
                bars: List[Bar] = []
                for idx, row in df.iterrows():
                    bars.append(Bar(
                        symbol=symbol,
                        timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
                        open=float(row.get("Open", 0)),
                        high=float(row.get("High", 0)),
                        low=float(row.get("Low", 0)),
                        close=float(row.get("Close", 0)),
                        volume=float(row.get("Volume", 0)),
                        vwap=None,
                    ))
                result[symbol] = bars
            else:
                # Multiple symbols - MultiIndex columns
                for symbol in symbols:
                    if symbol not in df.columns.get_level_values(0):
                        continue
                    
                    symbol_df = df[symbol]
                    bars = []
                    for idx, row in symbol_df.iterrows():
                        # Skip rows with all NaN
                        if row.isna().all():
                            continue
                        bars.append(Bar(
                            symbol=symbol,
                            timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
                            open=float(row.get("Open", 0) or 0),
                            high=float(row.get("High", 0) or 0),
                            low=float(row.get("Low", 0) or 0),
                            close=float(row.get("Close", 0) or 0),
                            volume=float(row.get("Volume", 0) or 0),
                            vwap=None,
                        ))
                    if bars:
                        result[symbol] = bars
            
            return result
            
        except Exception as e:
            print(f"[CPZ SDK] Error in batch download: {e}")
            # Fall back to individual downloads
            for symbol in symbols:
                bars = self.get_bars(symbol, timeframe, start, end)
                if bars:
                    result[symbol] = bars
            return result
