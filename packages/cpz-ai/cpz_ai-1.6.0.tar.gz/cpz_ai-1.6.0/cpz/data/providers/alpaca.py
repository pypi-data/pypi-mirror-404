"""Alpaca Market Data provider.

Supports:
- Stocks: bars, quotes, trades (historical + real-time)
- Crypto: bars, quotes, trades (historical + real-time)  
- Options: chains, quotes
- News: articles with sentiment

Docs: https://docs.alpaca.markets/docs/about-market-data-api
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional

from ..models import (
    Bar,
    Quote,
    Trade,
    News,
    OptionQuote,
    OptionContract,
    TimeFrame,
)


class AlpacaDataProvider:
    """Alpaca Market Data API provider.
    
    Usage:
        provider = AlpacaDataProvider()
        bars = provider.get_bars("AAPL", TimeFrame.DAY, limit=100)
        quotes = provider.get_quotes(["AAPL", "MSFT"])
    """
    
    name = "alpaca"
    supported_assets = ["stocks", "crypto", "options", "news"]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        feed: str = "iex",  # "iex" (free) or "sip" (paid)
    ):
        """Initialize Alpaca data provider.
        
        Args:
            api_key: Alpaca API key (defaults to ALPACA_API_KEY_ID env var or CPZAI platform)
            api_secret: Alpaca API secret (defaults to ALPACA_API_SECRET_KEY env var or CPZAI platform)
            feed: Data feed - "iex" (free, 15min delayed) or "sip" (paid, real-time)
        """
        self._api_key = api_key or ""
        self._api_secret = api_secret or ""
        
        # Fetch credentials from CPZAI platform (the ONLY supported method)
        if not self._api_key or not self._api_secret:
            try:
                from ...common.cpz_ai import CPZAIClient
                cpz_client = CPZAIClient.from_env()
                creds = cpz_client.get_data_credentials(provider="alpaca")
                if not self._api_key:
                    self._api_key = creds.get("alpaca_api_key", "")
                if not self._api_secret:
                    self._api_secret = creds.get("alpaca_api_secret", "")
            except Exception as e:
                print(f"[CPZ SDK] Could not fetch Alpaca credentials from platform: {e}")
        
        # Warn if still missing
        if not self._api_key or not self._api_secret:
            print("[CPZ SDK] Alpaca credentials not found. Connect your Alpaca account in the CPZ platform (Settings > Broker Connections).")
        
        self._feed = feed
        self._stock_client: Any = None
        self._crypto_client: Any = None
        self._option_client: Any = None
        self._news_client: Any = None
    
    def _get_stock_client(self) -> Any:
        """Lazy-load Alpaca stock historical client."""
        if self._stock_client is None:
            try:
                from alpaca.data.historical import StockHistoricalDataClient
                self._stock_client = StockHistoricalDataClient(
                    api_key=self._api_key,
                    secret_key=self._api_secret,
                )
            except ImportError:
                raise ImportError(
                    "alpaca-py is required for Alpaca data. Install with: pip install alpaca-py"
                )
        return self._stock_client
    
    def _get_crypto_client(self) -> Any:
        """Lazy-load Alpaca crypto historical client."""
        if self._crypto_client is None:
            try:
                from alpaca.data.historical import CryptoHistoricalDataClient
                self._crypto_client = CryptoHistoricalDataClient(
                    api_key=self._api_key,
                    secret_key=self._api_secret,
                )
            except ImportError:
                raise ImportError(
                    "alpaca-py is required for Alpaca data. Install with: pip install alpaca-py"
                )
        return self._crypto_client
    
    def _get_option_client(self) -> Any:
        """Lazy-load Alpaca option historical client."""
        if self._option_client is None:
            try:
                from alpaca.data.historical import OptionHistoricalDataClient
                self._option_client = OptionHistoricalDataClient(
                    api_key=self._api_key,
                    secret_key=self._api_secret,
                )
            except ImportError:
                raise ImportError(
                    "alpaca-py is required for options data. Install with: pip install alpaca-py"
                )
        return self._option_client
    
    def _convert_timeframe(self, tf: TimeFrame) -> Any:
        """Convert TimeFrame to Alpaca TimeFrame."""
        from alpaca.data.timeframe import TimeFrame as AlpacaTF, TimeFrameUnit
        
        mapping = {
            TimeFrame.MINUTE_1: AlpacaTF(1, TimeFrameUnit.Minute),
            TimeFrame.MINUTE_5: AlpacaTF(5, TimeFrameUnit.Minute),
            TimeFrame.MINUTE_15: AlpacaTF(15, TimeFrameUnit.Minute),
            TimeFrame.MINUTE_30: AlpacaTF(30, TimeFrameUnit.Minute),
            TimeFrame.HOUR_1: AlpacaTF(1, TimeFrameUnit.Hour),
            TimeFrame.HOUR_4: AlpacaTF(4, TimeFrameUnit.Hour),
            TimeFrame.DAY: AlpacaTF(1, TimeFrameUnit.Day),
            TimeFrame.WEEK: AlpacaTF(1, TimeFrameUnit.Week),
            TimeFrame.MONTH: AlpacaTF(1, TimeFrameUnit.Month),
        }
        return mapping.get(tf, AlpacaTF(1, TimeFrameUnit.Day))
    
    # --- Stock Data ---
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
        adjustment: str = "raw",  # "raw", "split", "dividend", "all"
    ) -> List[Bar]:
        """Get historical stock bars.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            timeframe: Bar timeframe
            start: Start datetime (defaults to 30 days ago)
            end: End datetime (defaults to now)
            limit: Maximum bars to return
            adjustment: Price adjustment type
            
        Returns:
            List of Bar objects
        """
        from alpaca.data.requests import StockBarsRequest
        
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        if start is None:
            start = datetime.utcnow() - timedelta(days=30)
        if end is None:
            end = datetime.utcnow()
        
        client = self._get_stock_client()
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=self._convert_timeframe(timeframe),
            start=start,
            end=end,
            limit=limit,
            adjustment=adjustment,
            feed=self._feed,
        )
        
        try:
            response = client.get_stock_bars(request)
        except Exception as e:
            print(f"[CPZ SDK] Error fetching bars for {symbol}: {e}")
            return []
        
        bars: List[Bar] = []
        
        # BarSet is dict-like but check symbol exists
        try:
            symbol_bars = response.get(symbol) if hasattr(response, 'get') else response[symbol] if symbol in response else None
            if symbol_bars:
                for bar in symbol_bars:
                    bars.append(Bar(
                        symbol=symbol,
                        timestamp=bar.timestamp,
                        open=float(bar.open),
                        high=float(bar.high),
                        low=float(bar.low),
                        close=float(bar.close),
                        volume=float(bar.volume),
                        vwap=float(bar.vwap) if bar.vwap else None,
                        trade_count=bar.trade_count if hasattr(bar, 'trade_count') else None,
                    ))
            else:
                print(f"[CPZ SDK] No bars returned for {symbol}")
        except (KeyError, TypeError) as e:
            print(f"[CPZ SDK] Error accessing bars for {symbol}: {e}")
        
        return bars
    
    def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get latest quotes for stock symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            List of Quote objects
        """
        from alpaca.data.requests import StockLatestQuoteRequest
        
        client = self._get_stock_client()
        request = StockLatestQuoteRequest(
            symbol_or_symbols=symbols,
            feed=self._feed,
        )
        
        response = client.get_stock_latest_quote(request)
        quotes: List[Quote] = []
        
        for symbol, quote in response.items():
            quotes.append(Quote(
                symbol=symbol,
                timestamp=quote.timestamp,
                bid=float(quote.bid_price) if quote.bid_price else 0.0,
                ask=float(quote.ask_price) if quote.ask_price else 0.0,
                bid_size=float(quote.bid_size) if quote.bid_size else 0.0,
                ask_size=float(quote.ask_size) if quote.ask_size else 0.0,
            ))
        
        return quotes
    
    def get_trades(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Trade]:
        """Get historical stock trades.
        
        Args:
            symbol: Stock symbol
            start: Start datetime
            end: End datetime  
            limit: Maximum trades to return
            
        Returns:
            List of Trade objects
        """
        from alpaca.data.requests import StockTradesRequest
        
        if start is None:
            start = datetime.utcnow() - timedelta(days=1)
        if end is None:
            end = datetime.utcnow()
        
        client = self._get_stock_client()
        request = StockTradesRequest(
            symbol_or_symbols=symbol,
            start=start,
            end=end,
            limit=limit,
            feed=self._feed,
        )
        
        response = client.get_stock_trades(request)
        trades: List[Trade] = []
        
        if symbol in response:
            for trade in response[symbol]:
                trades.append(Trade(
                    symbol=symbol,
                    timestamp=trade.timestamp,
                    price=float(trade.price),
                    size=float(trade.size),
                    exchange=trade.exchange if hasattr(trade, 'exchange') else None,
                    conditions=list(trade.conditions) if hasattr(trade, 'conditions') and trade.conditions else None,
                ))
        
        return trades
    
    # --- Crypto Data ---
    
    def get_crypto_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str = TimeFrame.DAY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Bar]:
        """Get historical crypto bars.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC/USD")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum bars to return
            
        Returns:
            List of Bar objects
        """
        from alpaca.data.requests import CryptoBarsRequest
        
        if isinstance(timeframe, str):
            timeframe = TimeFrame.from_string(timeframe)
        
        if start is None:
            start = datetime.utcnow() - timedelta(days=30)
        if end is None:
            end = datetime.utcnow()
        
        client = self._get_crypto_client()
        request = CryptoBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=self._convert_timeframe(timeframe),
            start=start,
            end=end,
            limit=limit,
        )
        
        response = client.get_crypto_bars(request)
        bars: List[Bar] = []
        
        if symbol in response:
            for bar in response[symbol]:
                bars.append(Bar(
                    symbol=symbol,
                    timestamp=bar.timestamp,
                    open=float(bar.open),
                    high=float(bar.high),
                    low=float(bar.low),
                    close=float(bar.close),
                    volume=float(bar.volume),
                    vwap=float(bar.vwap) if bar.vwap else None,
                    trade_count=bar.trade_count if hasattr(bar, 'trade_count') else None,
                ))
        
        return bars
    
    def get_crypto_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get latest crypto quotes.
        
        Args:
            symbols: List of crypto symbols (e.g., ["BTC/USD", "ETH/USD"])
            
        Returns:
            List of Quote objects
        """
        from alpaca.data.requests import CryptoLatestQuoteRequest
        
        client = self._get_crypto_client()
        request = CryptoLatestQuoteRequest(symbol_or_symbols=symbols)
        
        response = client.get_crypto_latest_quote(request)
        quotes: List[Quote] = []
        
        for symbol, quote in response.items():
            quotes.append(Quote(
                symbol=symbol,
                timestamp=quote.timestamp,
                bid=float(quote.bid_price) if quote.bid_price else 0.0,
                ask=float(quote.ask_price) if quote.ask_price else 0.0,
                bid_size=float(quote.bid_size) if quote.bid_size else 0.0,
                ask_size=float(quote.ask_size) if quote.ask_size else 0.0,
            ))
        
        return quotes
    
    # --- Options Data ---
    
    def _parse_option_symbol(self, symbol: str) -> tuple[str, datetime, float, str]:
        """Parse OCC option symbol to extract contract details.
        
        Format: AAPL240119C00150000
        - Underlying: variable length letters at start
        - Expiration: YYMMDD (6 digits)
        - Option type: C (call) or P (put)
        - Strike: 8 digits representing price * 1000 (e.g., 00150000 = $150.00)
        
        Args:
            symbol: Option symbol in OCC format
            
        Returns:
            Tuple of (underlying, expiration, strike, option_type)
        """
        # Find where the date starts (first digit after letters)
        underlying_end = 0
        for i, c in enumerate(symbol):
            if c.isdigit():
                underlying_end = i
                break
        
        underlying = symbol[:underlying_end]
        
        # Extract date (6 digits: YYMMDD)
        date_str = symbol[underlying_end:underlying_end + 6]
        year = 2000 + int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])
        expiration = datetime(year, month, day)
        
        # Option type is the character after the date
        option_type_char = symbol[underlying_end + 6]
        option_type = "call" if option_type_char == "C" else "put"
        
        # Strike price is the last 8 digits, divided by 1000
        strike_str = symbol[underlying_end + 7:]
        strike = float(strike_str) / 1000.0
        
        return underlying, expiration, strike, option_type
    
    def get_options_chain(
        self,
        underlying: str,
        expiration_date: Optional[datetime] = None,
        expiration_date_gte: Optional[datetime] = None,
        expiration_date_lte: Optional[datetime] = None,
        option_type: Optional[str] = None,  # "call" or "put"
        strike_price_gte: Optional[float] = None,
        strike_price_lte: Optional[float] = None,
    ) -> List[OptionContract]:
        """Get options chain for underlying symbol.
        
        Args:
            underlying: Underlying stock symbol (e.g., "AAPL")
            expiration_date: Exact expiration date
            expiration_date_gte: Minimum expiration date
            expiration_date_lte: Maximum expiration date
            option_type: "call" or "put"
            strike_price_gte: Minimum strike price
            strike_price_lte: Maximum strike price
            
        Returns:
            List of OptionContract objects
        """
        from alpaca.data.requests import OptionChainRequest
        
        client = self._get_option_client()
        
        request_params: Dict[str, Any] = {
            "underlying_symbol": underlying,
        }
        
        if expiration_date:
            request_params["expiration_date"] = expiration_date.date()
        if expiration_date_gte:
            request_params["expiration_date_gte"] = expiration_date_gte.date()
        if expiration_date_lte:
            request_params["expiration_date_lte"] = expiration_date_lte.date()
        if option_type:
            request_params["type"] = option_type.lower()
        if strike_price_gte is not None:
            request_params["strike_price_gte"] = strike_price_gte
        if strike_price_lte is not None:
            request_params["strike_price_lte"] = strike_price_lte
        
        request = OptionChainRequest(**request_params)
        response = client.get_option_chain(request)
        
        contracts: List[OptionContract] = []
        for symbol, snapshots in response.items():
            # Parse option symbol to extract expiration, strike, and option type
            try:
                parsed_underlying, expiration, strike, option_type = self._parse_option_symbol(symbol)
            except (ValueError, IndexError):
                # Fallback if parsing fails
                expiration = datetime.utcnow()
                strike = 0.0
                option_type = "call" if "C" in symbol else "put"
            
            contracts.append(OptionContract(
                symbol=symbol,
                underlying=underlying,
                expiration=expiration,
                strike=strike,
                option_type=option_type,
            ))
        
        return contracts
    
    def get_option_quotes(self, symbols: List[str]) -> List[OptionQuote]:
        """Get quotes for option symbols.
        
        Args:
            symbols: List of option symbols (e.g., ["AAPL240119C00150000"])
            
        Returns:
            List of OptionQuote objects
        """
        from alpaca.data.requests import OptionLatestQuoteRequest
        
        client = self._get_option_client()
        request = OptionLatestQuoteRequest(symbol_or_symbols=symbols)
        
        response = client.get_option_latest_quote(request)
        quotes: List[OptionQuote] = []
        
        for symbol, quote in response.items():
            # Extract underlying from option symbol (first part before date)
            underlying = ""
            for i, c in enumerate(symbol):
                if c.isdigit():
                    underlying = symbol[:i]
                    break
            
            quotes.append(OptionQuote(
                symbol=symbol,
                underlying=underlying,
                timestamp=quote.timestamp,
                bid=float(quote.bid_price) if quote.bid_price else 0.0,
                ask=float(quote.ask_price) if quote.ask_price else 0.0,
                bid_size=int(quote.bid_size) if quote.bid_size else 0,
                ask_size=int(quote.ask_size) if quote.ask_size else 0,
            ))
        
        return quotes
    
    # --- News Data ---
    
    def get_news(
        self,
        symbols: Optional[List[str]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50,
        include_content: bool = False,
    ) -> List[News]:
        """Get news articles.
        
        Args:
            symbols: Filter by symbols (optional)
            start: Start datetime
            end: End datetime
            limit: Maximum articles to return
            include_content: Include full article content
            
        Returns:
            List of News objects
        """
        from alpaca.data.requests import NewsRequest
        from alpaca.data.historical.news import NewsClient
        
        if self._news_client is None:
            self._news_client = NewsClient(
                api_key=self._api_key,
                secret_key=self._api_secret,
            )
        
        request_params: Dict[str, Any] = {
            "limit": limit,
            "include_content": include_content,
        }
        if symbols:
            # Alpaca expects symbols as a comma-separated string, not a list
            if isinstance(symbols, list):
                request_params["symbols"] = ",".join(symbols)
            else:
                request_params["symbols"] = symbols
        if start:
            request_params["start"] = start
        if end:
            request_params["end"] = end
        
        request = NewsRequest(**request_params)
        response = self._news_client.get_news(request)
        
        articles: List[News] = []
        # NewsSet.data is a Dict[str, List[NewsArticle]] - flatten all articles
        all_articles = []
        if hasattr(response, 'data') and response.data:
            for symbol_articles in response.data.values():
                all_articles.extend(symbol_articles)
        elif hasattr(response, 'news'):
            all_articles = response.news
        
        for article in all_articles:
            articles.append(News(
                id=str(article.id),
                headline=article.headline,
                summary=article.summary if hasattr(article, 'summary') else None,
                author=article.author if hasattr(article, 'author') else None,
                source=article.source,
                url=article.url if hasattr(article, 'url') else None,
                symbols=list(article.symbols) if article.symbols else [],
                created_at=article.created_at,
                updated_at=article.updated_at if hasattr(article, 'updated_at') else None,
                images=article.images if hasattr(article, 'images') else None,
            ))
        
        return articles
    
    # --- Streaming ---
    
    async def stream_quotes(self, symbols: List[str]) -> AsyncIterator[Quote]:
        """Stream real-time stock quotes.
        
        Args:
            symbols: List of symbols to stream
            
        Yields:
            Quote objects as they arrive
            
        Note:
            Uses thread-safe queue for cross-event-loop communication since
            Alpaca's stream.run() creates its own internal event loop.
        """
        import asyncio
        import queue as thread_queue
        from alpaca.data.live import StockDataStream
        
        # Use thread-safe queue since handler runs in Alpaca's event loop
        sync_queue: thread_queue.Queue[Quote | None] = thread_queue.Queue()
        
        stream = StockDataStream(
            api_key=self._api_key,
            secret_key=self._api_secret,
            feed=self._feed,
        )
        
        # Handler runs in Alpaca's event loop - use sync queue operations
        async def quote_handler(data: Any) -> None:
            quote = Quote(
                symbol=data.symbol,
                timestamp=data.timestamp,
                bid=float(data.bid_price),
                ask=float(data.ask_price),
                bid_size=float(data.bid_size),
                ask_size=float(data.ask_size),
            )
            sync_queue.put_nowait(quote)
        
        stream.subscribe_quotes(quote_handler, *symbols)
        
        loop = asyncio.get_running_loop()
        
        def run_stream() -> None:
            try:
                stream.run()
            finally:
                sync_queue.put(None)  # Signal end of stream
        
        stream_task = loop.run_in_executor(None, run_stream)
        
        def get_next() -> Quote | None:
            try:
                return sync_queue.get(timeout=0.5)
            except thread_queue.Empty:
                return ...  # type: ignore[return-value] # Sentinel for "try again"
        
        try:
            while True:
                item = await loop.run_in_executor(None, get_next)
                if item is None:
                    break
                if item is ...:
                    continue
                yield item
        finally:
            stream.stop()
    
    async def stream_trades(self, symbols: List[str]) -> AsyncIterator[Trade]:
        """Stream real-time trades.
        
        Args:
            symbols: List of symbols to stream
            
        Yields:
            Trade objects as they arrive
            
        Note:
            Uses thread-safe queue for cross-event-loop communication since
            Alpaca's stream.run() creates its own internal event loop.
        """
        import asyncio
        import queue as thread_queue
        from alpaca.data.live import StockDataStream
        
        # Use thread-safe queue since handler runs in Alpaca's event loop
        sync_queue: thread_queue.Queue[Trade | None] = thread_queue.Queue()
        
        stream = StockDataStream(
            api_key=self._api_key,
            secret_key=self._api_secret,
            feed=self._feed,
        )
        
        # Handler runs in Alpaca's event loop - use sync queue operations
        async def trade_handler(data: Any) -> None:
            trade = Trade(
                symbol=data.symbol,
                timestamp=data.timestamp,
                price=float(data.price),
                size=float(data.size),
                exchange=getattr(data, 'exchange', None),
                conditions=list(data.conditions) if hasattr(data, 'conditions') and data.conditions else None,
            )
            sync_queue.put_nowait(trade)
        
        stream.subscribe_trades(trade_handler, *symbols)
        
        loop = asyncio.get_running_loop()
        
        def run_stream() -> None:
            try:
                stream.run()
            finally:
                sync_queue.put(None)  # Signal end of stream
        
        stream_task = loop.run_in_executor(None, run_stream)
        
        def get_next() -> Trade | None:
            try:
                return sync_queue.get(timeout=0.5)
            except thread_queue.Empty:
                return ...  # type: ignore[return-value] # Sentinel for "try again"
        
        try:
            while True:
                item = await loop.run_in_executor(None, get_next)
                if item is None:
                    break
                if item is ...:
                    continue
                yield item
        finally:
            stream.stop()
    
    async def stream_bars(
        self, symbols: List[str], timeframe: TimeFrame = TimeFrame.MINUTE_1
    ) -> AsyncIterator[Bar]:
        """Stream real-time bars.
        
        Args:
            symbols: List of symbols to stream
            timeframe: Bar timeframe (default: 1 minute)
            
        Yields:
            Bar objects as they arrive
            
        Note:
            Uses thread-safe queue for cross-event-loop communication since
            Alpaca's stream.run() creates its own internal event loop.
        """
        import asyncio
        import queue as thread_queue
        from alpaca.data.live import StockDataStream
        
        # Use thread-safe queue since handler runs in Alpaca's event loop
        sync_queue: thread_queue.Queue[Bar | None] = thread_queue.Queue()
        
        stream = StockDataStream(
            api_key=self._api_key,
            secret_key=self._api_secret,
            feed=self._feed,
        )
        
        # Handler runs in Alpaca's event loop - use sync queue operations
        async def bar_handler(data: Any) -> None:
            bar = Bar(
                symbol=data.symbol,
                timestamp=data.timestamp,
                open=float(data.open),
                high=float(data.high),
                low=float(data.low),
                close=float(data.close),
                volume=float(data.volume),
                vwap=float(data.vwap) if hasattr(data, 'vwap') and data.vwap else None,
                trade_count=int(data.trade_count) if hasattr(data, 'trade_count') and data.trade_count else None,
            )
            sync_queue.put_nowait(bar)
        
        stream.subscribe_bars(bar_handler, *symbols)
        
        loop = asyncio.get_running_loop()
        
        def run_stream() -> None:
            try:
                stream.run()
            finally:
                sync_queue.put(None)  # Signal end of stream
        
        stream_task = loop.run_in_executor(None, run_stream)
        
        def get_next() -> Bar | None:
            try:
                return sync_queue.get(timeout=0.5)
            except thread_queue.Empty:
                return ...  # type: ignore[return-value] # Sentinel for "try again"
        
        try:
            while True:
                item = await loop.run_in_executor(None, get_next)
                if item is None:
                    break
                if item is ...:
                    continue
                yield item
        finally:
            stream.stop()
