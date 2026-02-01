"""Tests for the use_broker account_id priority fix.

This tests the fix where account_id takes priority over environment matching.
When account_id is provided, the credential lookup should ignore environment entirely.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class TestCredentialMatchingPriority:
    """Tests for credential matching priority logic."""

    # Valid test key format for CPZAIClient
    # API key: cpz_key_ + 24 hex chars = 32 total
    TEST_API_KEY = "cpz_key_0123456789abcdef01234567"
    # Secret: cpz_secret_ + 48 alphanumeric chars = 59 total
    TEST_SECRET = "cpz_secret_000000000000000000000000000000000000000000000000"

    def test_account_id_takes_priority_over_environment(self) -> None:
        """When account_id is provided, environment should be ignored."""
        from cpz.common.cpz_ai import CPZAIClient

        # Mock credentials data with paper account
        mock_credentials = [
            {
                "broker": "alpaca",
                "account_id": "PA3FHUB575J3",
                "env": "paper",
                "is_paper": True,
                "api_key_id": "paper_key",
                "api_secret_key": "paper_secret",
            },
            {
                "broker": "alpaca",
                "account_id": "LA1LIVE12345",
                "env": "live",
                "is_paper": False,
                "api_key_id": "live_key",
                "api_secret_key": "live_secret",
            },
        ]

        with patch("cpz.common.cpz_ai.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_credentials
            mock_get.return_value = mock_response

            client = CPZAIClient(
                url="https://test.com",
                api_key=self.TEST_API_KEY,
                secret_key=self.TEST_SECRET,
            )

            # When account_id is provided, should find the matching account
            # even if environment doesn't match
            creds = client.get_broker_credentials(
                broker="alpaca",
                env="live",  # This should be IGNORED
                account_id="PA3FHUB575J3",  # Paper account
            )

            assert creds is not None
            assert creds["api_key_id"] == "paper_key"
            assert creds["account_id"] == "PA3FHUB575J3"

    def test_account_id_without_environment(self) -> None:
        """When only account_id is provided, should find the account."""
        from cpz.common.cpz_ai import CPZAIClient

        mock_credentials = [
            {
                "broker": "alpaca",
                "account_id": "MYACCOUNT123",
                "env": "paper",
                "api_key_id": "my_key",
                "api_secret_key": "my_secret",
            },
        ]

        with patch("cpz.common.cpz_ai.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_credentials
            mock_get.return_value = mock_response

            client = CPZAIClient(
                url="https://test.com",
                api_key=self.TEST_API_KEY,
                secret_key=self.TEST_SECRET,
            )

            creds = client.get_broker_credentials(
                broker="alpaca",
                account_id="MYACCOUNT123",
            )

            assert creds is not None
            assert creds["api_key_id"] == "my_key"
            assert creds["account_id"] == "MYACCOUNT123"

    def test_environment_only_when_no_account_id(self) -> None:
        """When no account_id, environment matching should work."""
        from cpz.common.cpz_ai import CPZAIClient

        mock_credentials = [
            {
                "broker": "alpaca",
                "account_id": "PAPER123",
                "env": "paper",
                "is_paper": True,
                "api_key_id": "paper_key",
                "api_secret_key": "paper_secret",
            },
            {
                "broker": "alpaca",
                "account_id": "LIVE456",
                "env": "live",
                "is_paper": False,
                "api_key_id": "live_key",
                "api_secret_key": "live_secret",
            },
        ]

        with patch("cpz.common.cpz_ai.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_credentials
            mock_get.return_value = mock_response

            client = CPZAIClient(
                url="https://test.com",
                api_key=self.TEST_API_KEY,
                secret_key=self.TEST_SECRET,
            )

            # Should find live account when env=live and no account_id
            creds = client.get_broker_credentials(
                broker="alpaca",
                env="live",
            )

            assert creds is not None
            assert creds["api_key_id"] == "live_key"
            assert creds["env"] == "live"

    def test_account_number_field_variant(self) -> None:
        """Test account_number field is also checked."""
        from cpz.common.cpz_ai import CPZAIClient

        mock_credentials = [
            {
                "broker": "alpaca",
                "account_number": "ACCT789",  # Different field name
                "env": "paper",
                "api_key_id": "the_key",
                "api_secret_key": "the_secret",
            },
        ]

        with patch("cpz.common.cpz_ai.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_credentials
            mock_get.return_value = mock_response

            client = CPZAIClient(
                url="https://test.com",
                api_key=self.TEST_API_KEY,
                secret_key=self.TEST_SECRET,
            )

            creds = client.get_broker_credentials(
                broker="alpaca",
                account_id="ACCT789",
            )

            assert creds is not None
            assert creds["api_key_id"] == "the_key"

    def test_no_match_returns_none(self) -> None:
        """Test no matching credentials returns None."""
        from cpz.common.cpz_ai import CPZAIClient

        mock_credentials = [
            {
                "broker": "alpaca",
                "account_id": "OTHER_ACCOUNT",
                "env": "paper",
                "api_key_id": "other_key",
                "api_secret_key": "other_secret",
            },
        ]

        with patch("cpz.common.cpz_ai.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_credentials
            mock_get.return_value = mock_response

            client = CPZAIClient(
                url="https://test.com",
                api_key=self.TEST_API_KEY,
                secret_key=self.TEST_SECRET,
            )

            creds = client.get_broker_credentials(
                broker="alpaca",
                account_id="NONEXISTENT",
            )

            assert creds is None


class TestUseBrokerIntegration:
    """Tests for use_broker method with new logic."""

    def test_use_broker_with_account_id(self) -> None:
        """Test use_broker passes account_id correctly."""
        from cpz.execution.router import BrokerRouter

        router = BrokerRouter()

        # Mock the registry
        mock_factory = MagicMock()
        mock_adapter = MagicMock()
        mock_factory.return_value = mock_adapter
        router._registry["alpaca"] = mock_factory

        # Call use_broker with account_id
        router.use_broker("alpaca", environment="paper", account_id="PA3FHUB575J3")

        # Verify factory was called with correct kwargs
        mock_factory.assert_called_once()
        call_kwargs = mock_factory.call_args[1]
        assert call_kwargs.get("env") == "paper"
        assert call_kwargs.get("account_id") == "PA3FHUB575J3"

    def test_use_broker_environment_to_env_conversion(self) -> None:
        """Test that environment parameter is converted to env."""
        from cpz.execution.router import BrokerRouter

        router = BrokerRouter()

        mock_factory = MagicMock()
        mock_adapter = MagicMock()
        mock_factory.return_value = mock_adapter
        router._registry["alpaca"] = mock_factory

        router.use_broker("alpaca", environment="live")

        call_kwargs = mock_factory.call_args[1]
        assert call_kwargs.get("env") == "live"
        assert "environment" not in call_kwargs

    def test_active_selection_returns_correct_kwargs(self) -> None:
        """Test active_selection returns the correct broker and kwargs."""
        from cpz.execution.router import BrokerRouter

        router = BrokerRouter()

        mock_factory = MagicMock()
        mock_adapter = MagicMock()
        mock_factory.return_value = mock_adapter
        router._registry["alpaca"] = mock_factory

        router.use_broker("alpaca", environment="paper", account_id="TEST123")

        selection = router.active_selection()
        assert selection is not None
        name, kwargs = selection
        assert name == "alpaca"
        assert kwargs.get("env") == "paper"
        assert kwargs.get("account_id") == "TEST123"
