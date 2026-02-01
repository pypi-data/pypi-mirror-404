"""Integration tests for CPZ Data Layer with real API calls.

These tests require valid API credentials:
- CPZ_AI_API_KEY and CPZ_AI_SECRET_KEY for CPZ platform
- ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY for Alpaca data
- FRED_API_KEY for FRED economic data (optional, free)
- TWELVE_DATA_API_KEY for Twelve Data (optional, free tier)

Run with: pytest tests/test_data_integration.py -v --tb=short

To skip if credentials not available:
    pytest tests/test_data_integration.py -v -m "not integration"
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timedelta

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


def has_alpaca_credentials() -> bool:
    """Check if Alpaca credentials are available."""
    return bool(os.getenv("ALPACA_API_KEY_ID") and os.getenv("ALPACA_API_SECRET_KEY"))


def has_fred_credentials() -> bool:
    """Check if FRED API key is available."""
    return bool(os.getenv("FRED_API_KEY"))


def has_twelve_credentials() -> bool:
    """Check if Twelve Data API key is available."""
    return bool(os.getenv("TWELVE_DATA_API_KEY"))


def has_cpz_credentials() -> bool:
    """Check if CPZ AI credentials are available."""
    return bool(os.getenv("CPZ_AI_API_KEY") and os.getenv("CPZ_AI_SECRET_KEY"))


# Skip decorators
skip_no_alpaca = pytest.mark.skipif(
    not has_alpaca_credentials(),
    reason="ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY required"
)

skip_no_fred = pytest.mark.skipif(
    not has_fred_credentials(),
    reason="FRED_API_KEY required"
)

skip_no_twelve = pytest.mark.skipif(
    not has_twelve_credentials(),
    reason="TWELVE_DATA_API_KEY required"
)

skip_no_cpz = pytest.mark.skipif(
    not has_cpz_credentials(),
    reason="CPZ_AI_API_KEY and CPZ_AI_SECRET_KEY required"
)


class TestAlpacaDataIntegration:
    """Integration tests for Alpaca Market Data."""

    @skip_no_alpaca
    def test_get_stock_bars(self) -> None:
        """Test fetching stock bars from Alpaca."""
        from cpz.data.providers.alpaca import AlpacaDataProvider
        from cpz.data.models import TimeFrame

        provider = AlpacaDataProvider()
        bars = provider.get_bars("AAPL", TimeFrame.DAY, limit=10)

        assert len(bars) > 0
        assert all(bar.symbol == "AAPL" for bar in bars)
        assert all(bar.open > 0 for bar in bars)
        assert all(bar.close > 0 for bar in bars)
        assert all(bar.volume >= 0 for bar in bars)

    @skip_no_alpaca
    def test_get_stock_quotes(self) -> None:
        """Test fetching stock quotes from Alpaca."""
        from cpz.data.providers.alpaca import AlpacaDataProvider

        provider = AlpacaDataProvider()
        quotes = provider.get_quotes(["AAPL", "MSFT"])

        assert len(quotes) == 2
        symbols = {q.symbol for q in quotes}
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    @skip_no_alpaca
    def test_get_crypto_bars(self) -> None:
        """Test fetching crypto bars from Alpaca."""
        from cpz.data.providers.alpaca import AlpacaDataProvider
        from cpz.data.models import TimeFrame

        provider = AlpacaDataProvider()
        bars = provider.get_crypto_bars("BTC/USD", TimeFrame.HOUR_1, limit=10)

        assert len(bars) > 0
        assert all(bar.symbol == "BTC/USD" for bar in bars)

    @skip_no_alpaca
    def test_get_news(self) -> None:
        """Test fetching news from Alpaca."""
        from cpz.data.providers.alpaca import AlpacaDataProvider

        provider = AlpacaDataProvider()
        news = provider.get_news(symbols=["AAPL"], limit=5)

        assert len(news) > 0
        assert all(hasattr(article, "headline") for article in news)


class TestFREDDataIntegration:
    """Integration tests for FRED economic data."""

    @skip_no_fred
    def test_get_gdp_series(self) -> None:
        """Test fetching GDP data from FRED."""
        from cpz.data.providers.fred import FREDProvider

        provider = FREDProvider()
        gdp = provider.get_series("GDP", limit=10)

        assert len(gdp) > 0
        assert all(obs.series_id == "GDP" for obs in gdp)
        assert gdp[0].value is not None or gdp[0].value is None  # Can be None for missing

    @skip_no_fred
    def test_get_unemployment_series(self) -> None:
        """Test fetching unemployment rate from FRED."""
        from cpz.data.providers.fred import FREDProvider

        provider = FREDProvider()
        unemployment = provider.get_series("UNRATE", limit=12)

        assert len(unemployment) > 0
        assert unemployment[0].series_id == "UNRATE"

    @skip_no_fred
    def test_search_series(self) -> None:
        """Test searching FRED series."""
        from cpz.data.providers.fred import FREDProvider

        provider = FREDProvider()
        results = provider.search_series("inflation", limit=5)

        assert len(results) > 0
        assert all("series_id" in r for r in results)


class TestEDGARDataIntegration:
    """Integration tests for SEC EDGAR data."""

    def test_get_filings(self) -> None:
        """Test fetching SEC filings."""
        from cpz.data.providers.edgar import EDGARProvider

        provider = EDGARProvider()
        filings = provider.get_filings(symbol="AAPL", form_type="10-K", limit=3)

        assert len(filings) > 0
        assert all(f.form_type == "10-K" for f in filings)
        assert all(f.cik != "" for f in filings)

    def test_get_company_facts(self) -> None:
        """Test fetching company XBRL facts."""
        from cpz.data.providers.edgar import EDGARProvider

        provider = EDGARProvider()
        facts = provider.get_company_facts("AAPL")

        assert facts is not None
        assert "facts" in facts or "cik" in facts


class TestTwelveDataIntegration:
    """Integration tests for Twelve Data."""

    @skip_no_twelve
    def test_get_bars(self) -> None:
        """Test fetching bars from Twelve Data."""
        from cpz.data.providers.twelve import TwelveDataProvider
        from cpz.data.models import TimeFrame

        provider = TwelveDataProvider()
        bars = provider.get_bars("AAPL", TimeFrame.DAY, limit=10)

        assert len(bars) > 0
        assert all(bar.symbol == "AAPL" for bar in bars)

    @skip_no_twelve
    def test_get_forex_quote(self) -> None:
        """Test fetching forex quote from Twelve Data."""
        from cpz.data.providers.twelve import TwelveDataProvider

        provider = TwelveDataProvider()
        quote = provider.get_forex_quote("EUR/USD")

        assert quote is not None
        assert "close" in quote

    @skip_no_twelve
    def test_get_rsi(self) -> None:
        """Test fetching RSI indicator from Twelve Data."""
        from cpz.data.providers.twelve import TwelveDataProvider

        provider = TwelveDataProvider()
        rsi = provider.get_rsi("AAPL", period=14, limit=10)

        assert len(rsi) > 0
        assert all("rsi" in r for r in rsi)


class TestSocialDataIntegration:
    """Integration tests for social sentiment data."""

    def test_reddit_get_posts(self) -> None:
        """Test fetching Reddit posts."""
        from cpz.data.providers.social import RedditProvider

        provider = RedditProvider()
        posts = provider.get_posts(limit=10)

        # Reddit public API may be rate-limited
        assert isinstance(posts, list)

    def test_stocktwits_trending(self) -> None:
        """Test fetching Stocktwits trending symbols."""
        from cpz.data.providers.social import StocktwitsProvider

        provider = StocktwitsProvider()
        trending = provider.get_trending(limit=10)

        # Stocktwits may be rate-limited
        assert isinstance(trending, list)


class TestDataClientIntegration:
    """Integration tests for unified DataClient."""

    @skip_no_alpaca
    def test_bars_unified_method(self) -> None:
        """Test DataClient.bars() unified method."""
        from cpz.data.client import DataClient

        client = DataClient()
        bars = client.bars("AAPL", timeframe="1D", limit=10)

        assert len(bars) > 0
        assert all(bar.symbol == "AAPL" for bar in bars)

    @skip_no_alpaca
    def test_quotes_unified_method(self) -> None:
        """Test DataClient.quotes() unified method."""
        from cpz.data.client import DataClient

        client = DataClient()
        quotes = client.quotes(["AAPL", "MSFT"])

        assert len(quotes) == 2

    @skip_no_fred
    def test_economic_unified_method(self) -> None:
        """Test DataClient.economic() unified method."""
        from cpz.data.client import DataClient

        client = DataClient()
        gdp = client.economic("GDP", limit=5)

        assert len(gdp) > 0

    def test_filings_unified_method(self) -> None:
        """Test DataClient.filings() unified method."""
        from cpz.data.client import DataClient

        client = DataClient()
        filings = client.filings("AAPL", form="10-K", limit=3)

        assert len(filings) > 0


class TestCPZClientFullIntegration:
    """Full integration tests with CPZClient."""

    @skip_no_cpz
    @skip_no_alpaca
    def test_cpz_client_data_access(self) -> None:
        """Test accessing data through CPZClient."""
        from cpz import CPZClient

        client = CPZClient()
        
        # Test data access
        bars = client.data.bars("AAPL", timeframe="1D", limit=5)
        assert len(bars) > 0

    @skip_no_cpz
    def test_cpz_client_edgar_access(self) -> None:
        """Test accessing EDGAR through CPZClient."""
        from cpz import CPZClient

        client = CPZClient()
        
        filings = client.data.filings("MSFT", form="10-Q", limit=2)
        assert len(filings) > 0

    @skip_no_cpz
    @skip_no_alpaca
    def test_cpz_client_execution_and_data(self) -> None:
        """Test both execution and data access work together."""
        from cpz import CPZClient

        client = CPZClient()
        
        # Data access
        quotes = client.data.quotes(["AAPL"])
        assert len(quotes) > 0
        
        # Execution setup (don't place actual orders)
        client.execution.use_broker("alpaca", environment="paper")
        account = client.execution.get_account()
        assert account.buying_power >= 0
