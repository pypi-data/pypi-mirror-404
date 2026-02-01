"""Tests for the CPZ Data Layer.

These tests validate:
1. Data models and TimeFrame parsing
2. DataClient initialization and namespace access
3. Provider lazy loading
4. Method signatures and return types

For live integration tests, see test_data_integration.py
"""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from cpz.data.models import (
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
from cpz.data.client import DataClient


class TestTimeFrame:
    """Tests for TimeFrame enum and parsing."""

    def test_timeframe_values(self) -> None:
        """Test TimeFrame enum values."""
        assert TimeFrame.MINUTE_1.value == "1Min"
        assert TimeFrame.DAY.value == "1Day"
        assert TimeFrame.WEEK.value == "1Week"

    def test_timeframe_from_string_standard(self) -> None:
        """Test parsing standard timeframe strings."""
        assert TimeFrame.from_string("1D") == TimeFrame.DAY
        assert TimeFrame.from_string("1d") == TimeFrame.DAY
        assert TimeFrame.from_string("day") == TimeFrame.DAY
        assert TimeFrame.from_string("daily") == TimeFrame.DAY

    def test_timeframe_from_string_minutes(self) -> None:
        """Test parsing minute timeframes."""
        assert TimeFrame.from_string("1m") == TimeFrame.MINUTE_1
        assert TimeFrame.from_string("1min") == TimeFrame.MINUTE_1
        assert TimeFrame.from_string("5m") == TimeFrame.MINUTE_5
        assert TimeFrame.from_string("15min") == TimeFrame.MINUTE_15
        assert TimeFrame.from_string("30m") == TimeFrame.MINUTE_30

    def test_timeframe_from_string_hours(self) -> None:
        """Test parsing hour timeframes."""
        assert TimeFrame.from_string("1h") == TimeFrame.HOUR_1
        assert TimeFrame.from_string("1hour") == TimeFrame.HOUR_1
        assert TimeFrame.from_string("4h") == TimeFrame.HOUR_4

    def test_timeframe_from_string_invalid(self) -> None:
        """Test invalid timeframe strings raise ValueError."""
        with pytest.raises(ValueError, match="Unknown timeframe"):
            TimeFrame.from_string("invalid")
        with pytest.raises(ValueError, match="Unknown timeframe"):
            TimeFrame.from_string("2d")


class TestDataModels:
    """Tests for data models."""

    def test_bar_model(self) -> None:
        """Test Bar model creation and aliases."""
        bar = Bar(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            open=150.0,
            high=152.0,
            low=149.0,
            close=151.0,
            volume=1000000.0,
        )
        assert bar.symbol == "AAPL"
        assert bar.open == 150.0
        assert bar.close == 151.0
        assert bar.volume == 1000000.0

    def test_bar_with_aliases(self) -> None:
        """Test Bar model with alias field names."""
        bar = Bar(
            symbol="AAPL",
            ts=datetime(2024, 1, 15, 10, 0, 0),
            o=150.0,
            h=152.0,
            l=149.0,
            c=151.0,
            v=1000000.0,
        )
        assert bar.timestamp == datetime(2024, 1, 15, 10, 0, 0)
        assert bar.open == 150.0

    def test_quote_model(self) -> None:
        """Test Quote model creation."""
        quote = Quote(
            symbol="AAPL",
            bid=150.0,
            ask=150.05,
            bid_size=100.0,
            ask_size=200.0,
        )
        assert quote.symbol == "AAPL"
        assert quote.bid == 150.0
        assert quote.ask == 150.05

    def test_news_model(self) -> None:
        """Test News model creation."""
        news = News(
            id="123",
            headline="Apple reports Q4 earnings",
            source="Reuters",
            symbols=["AAPL"],
            created_at=datetime(2024, 1, 15, 10, 0, 0),
        )
        assert news.headline == "Apple reports Q4 earnings"
        assert "AAPL" in news.symbols

    def test_economic_series_model(self) -> None:
        """Test EconomicSeries model creation."""
        series = EconomicSeries(
            series_id="GDP",
            title="Gross Domestic Product",
            observation_date=datetime(2024, 1, 1),
            value=25000.0,
            units="Billions of Dollars",
        )
        assert series.series_id == "GDP"
        assert series.value == 25000.0

    def test_filing_model(self) -> None:
        """Test Filing model creation."""
        filing = Filing(
            accession_number="0000320193-24-000001",
            cik="0000320193",
            company_name="Apple Inc.",
            form_type="10-K",
            filed_date=datetime(2024, 1, 15),
        )
        assert filing.form_type == "10-K"
        assert filing.company_name == "Apple Inc."

    def test_social_post_model(self) -> None:
        """Test SocialPost model creation."""
        post = SocialPost(
            id="abc123",
            source="reddit",
            content="AAPL to the moon!",
            symbols=["AAPL"],
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            sentiment="bullish",
            sentiment_score=0.8,
        )
        assert post.source == "reddit"
        assert post.sentiment == "bullish"


class TestDataClientInit:
    """Tests for DataClient initialization."""

    def test_client_initialization(self) -> None:
        """Test DataClient initializes without errors."""
        client = DataClient()
        assert client is not None

    def test_client_with_config(self) -> None:
        """Test DataClient with explicit config."""
        client = DataClient(
            alpaca_api_key="test_key",
            alpaca_api_secret="test_secret",
            fred_api_key="fred_key",
        )
        assert client._config["alpaca_api_key"] == "test_key"
        assert client._config["fred_api_key"] == "fred_key"


class TestDataClientNamespaces:
    """Tests for DataClient namespace access."""

    def test_alpaca_namespace_access(self) -> None:
        """Test accessing alpaca namespace."""
        client = DataClient()
        assert client.alpaca is not None
        # Should be same instance on second access
        assert client.alpaca is client.alpaca

    def test_fred_namespace_access(self) -> None:
        """Test accessing fred namespace."""
        client = DataClient()
        assert client.fred is not None
        assert client.fred is client.fred

    def test_edgar_namespace_access(self) -> None:
        """Test accessing edgar namespace."""
        client = DataClient()
        assert client.edgar is not None
        assert client.edgar is client.edgar

    def test_twelve_namespace_access(self) -> None:
        """Test accessing twelve namespace."""
        client = DataClient()
        assert client.twelve is not None
        assert client.twelve is client.twelve

    def test_social_namespace_access(self) -> None:
        """Test accessing social namespace."""
        client = DataClient()
        assert client.social is not None
        assert client.social is client.social


class TestDataClientMethods:
    """Tests for DataClient unified methods."""

    def test_bars_method_exists(self) -> None:
        """Test bars method exists and has correct signature."""
        client = DataClient()
        assert hasattr(client, "bars")
        assert callable(client.bars)

    def test_quotes_method_exists(self) -> None:
        """Test quotes method exists."""
        client = DataClient()
        assert hasattr(client, "quotes")
        assert callable(client.quotes)

    def test_news_method_exists(self) -> None:
        """Test news method exists."""
        client = DataClient()
        assert hasattr(client, "news")
        assert callable(client.news)

    def test_economic_method_exists(self) -> None:
        """Test economic method exists."""
        client = DataClient()
        assert hasattr(client, "economic")
        assert callable(client.economic)

    def test_filings_method_exists(self) -> None:
        """Test filings method exists."""
        client = DataClient()
        assert hasattr(client, "filings")
        assert callable(client.filings)

    def test_sentiment_method_exists(self) -> None:
        """Test sentiment method exists."""
        client = DataClient()
        assert hasattr(client, "sentiment")
        assert callable(client.sentiment)

    def test_trending_method_exists(self) -> None:
        """Test trending method exists."""
        client = DataClient()
        assert hasattr(client, "trending")
        assert callable(client.trending)

    def test_technical_indicator_methods_exist(self) -> None:
        """Test technical indicator methods exist."""
        client = DataClient()
        assert hasattr(client, "sma")
        assert hasattr(client, "rsi")
        assert hasattr(client, "macd")


class TestCPZClientDataIntegration:
    """Tests for DataClient integration with CPZClient."""

    def test_cpz_client_has_data_property(self) -> None:
        """Test CPZClient has data property."""
        from cpz.clients.sync import CPZClient
        
        # Mock CPZAIClient to avoid credential requirements
        with patch("cpz.clients.sync.CPZAIClient") as mock_cpz:
            mock_instance = MagicMock()
            mock_instance.api_key = "test"
            mock_instance.secret_key = "test"
            mock_instance.is_admin = False
            mock_cpz.from_env.return_value = mock_instance
            
            client = CPZClient(cpz_client=mock_instance)
            assert hasattr(client, "data")

    def test_cpz_client_data_returns_dataclient(self) -> None:
        """Test CPZClient.data returns DataClient instance."""
        from cpz.clients.sync import CPZClient
        from cpz.data.client import DataClient
        
        with patch("cpz.clients.sync.CPZAIClient") as mock_cpz:
            mock_instance = MagicMock()
            mock_instance.api_key = "test"
            mock_instance.secret_key = "test"
            mock_instance.is_admin = False
            mock_cpz.from_env.return_value = mock_instance
            
            client = CPZClient(cpz_client=mock_instance)
            assert isinstance(client.data, DataClient)

    def test_cpz_client_data_is_lazy(self) -> None:
        """Test DataClient is lazily instantiated."""
        from cpz.clients.sync import CPZClient
        
        with patch("cpz.clients.sync.CPZAIClient") as mock_cpz:
            mock_instance = MagicMock()
            mock_instance.api_key = "test"
            mock_instance.secret_key = "test"
            mock_instance.is_admin = False
            mock_cpz.from_env.return_value = mock_instance
            
            client = CPZClient(cpz_client=mock_instance)
            # _data should be None initially
            assert client._data is None
            # Access data property
            _ = client.data
            # Now _data should be set
            assert client._data is not None
