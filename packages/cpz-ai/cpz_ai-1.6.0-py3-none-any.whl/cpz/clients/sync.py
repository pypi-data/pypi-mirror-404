from __future__ import annotations

import os
from typing import Any, Optional

from ..common.cpz_ai import CPZAIClient
from ..data.client import DataClient
from ..execution.models import Account, Order, OrderReplaceRequest, OrderSubmitRequest, Position
from ..execution.enums import OrderSide, OrderType, TimeInForce
from ..execution.router import BrokerRouter
from .base import BaseClient


class _ExecutionNamespace:
    def __init__(self, router: BrokerRouter) -> None:
        self.router = router

    def use_broker(
        self, name: str, environment: str = "paper", account_id: Optional[str] = None
    ) -> None:
        self.router.use_broker(name, environment=environment, account_id=account_id)

    def get_account(self) -> Account:
        return self.router.get_account()

    def get_positions(self) -> list[Position]:
        return self.router.get_positions()

    def submit_order(self, req: OrderSubmitRequest) -> Order:
        return self.router.submit_order(req)

    def get_order(self, order_id: str) -> Order:
        return self.router.get_order(order_id)

    def cancel_order(self, order_id: str) -> Order:
        return self.router.cancel_order(order_id)

    def replace_order(self, order_id: str, req: OrderReplaceRequest) -> Order:
        return self.router.replace_order(order_id, req)

    # Convenience: one-call order placement with CPZ-managed broker creds
    def order(
        self,
        *,
        symbol: str,
        qty: float,
        side: str | OrderSide = "buy",
        order_type: str | OrderType = "market",
        time_in_force: str | TimeInForce = "DAY",
        limit_price: float | None = None,
        strategy_id: str | None = None,
    ) -> Order:
        # Validate strategy_id is provided (required for all orders)
        if not strategy_id:
            strategy_id = os.getenv("CPZ_AI_STRATEGY_ID") or os.getenv("CPZ_STRATEGY_ID")
        if not strategy_id:
            raise ValueError(
                "strategy_id is required for all orders. "
                "Provide it as a parameter or set CPZ_AI_STRATEGY_ID environment variable."
            )
        # Ensure a broker is selected; adapter will fetch creds from CPZAI
        # If no active broker, this will raise appropriately
        _active = self.router.active_selection()
        if _active is None:
            # Common ergonomic fallback: default to Alpaca paper if nothing selected
            self.router.use_broker("alpaca", environment="paper")

        side_enum = (
            side
            if isinstance(side, OrderSide)
            else (OrderSide.BUY if str(side).lower() == "buy" else OrderSide.SELL)
        )
        type_enum = (
            order_type
            if isinstance(order_type, OrderType)
            else (OrderType.MARKET if str(order_type).lower() == "market" else OrderType.LIMIT)
        )
        tif_enum = (
            time_in_force
            if isinstance(time_in_force, TimeInForce)
            else TimeInForce(str(time_in_force).upper())
        )

        req = OrderSubmitRequest(
            symbol=symbol,
            side=side_enum,
            qty=qty,
            order_type=type_enum,
            time_in_force=tif_enum,
            limit_price=limit_price,
            strategy_id=strategy_id,
        )
        return self.router.submit_order(req)


class _PlatformNamespace:
    def __init__(self) -> None:
        self._sb: CPZAIClient | None = None

    def configure(
        self, *, url: str | None = None, anon: str | None = None, service: str | None = None
    ) -> None:
        if url and anon:
            self._sb = CPZAIClient(url=url, api_key=anon, secret_key=service or "")
        else:
            self._sb = CPZAIClient.from_env()

    def _require(self) -> CPZAIClient:
        if self._sb is None:
            self._sb = CPZAIClient.from_env()
        return self._sb

    def health(self) -> bool:
        return self._require().health()

    def echo(self) -> dict[str, object]:
        return self._require().echo()

    def list_tables(self) -> list[str]:
        return self._require().list_tables()


class CPZClient(BaseClient):
    """CPZAI SDK Client - Unified interface for trading, data, and platform services.
    
    Usage:
        from cpz import CPZClient
        
        client = CPZClient()
        
        # Execution (Trading)
        client.execution.use_broker("alpaca", environment="paper")
        order = client.execution.order(symbol="AAPL", qty=1, side="buy", strategy_id="my-strat")
        
        # Market Data
        bars = client.data.bars("AAPL", timeframe="1D", limit=100)
        quotes = client.data.quotes(["AAPL", "MSFT"])
        news = client.data.news("AAPL")
        
        # Economic Data
        gdp = client.data.economic("GDP")
        
        # SEC Filings
        filings = client.data.filings("AAPL", form="10-K")
        
        # Social Sentiment
        sentiment = client.data.sentiment("AAPL")
    """
    
    def __init__(self, cpz_client: Optional[CPZAIClient] = None) -> None:
        super().__init__()
        # Create or use provided client - validation happens in CPZAIClient.__init__()
        self._cpz_client = cpz_client or CPZAIClient.from_env()
        # Additional validation: ensure credentials are present (unless admin client)
        if not (cpz_client and cpz_client.is_admin):
            if not self._cpz_client.api_key or not self._cpz_client.secret_key:
                raise ValueError(
                    "CPZ API credentials are missing. Set CPZ_AI_API_KEY and CPZ_AI_SECRET_KEY "
                    "environment variables or provide a cpz_client with valid credentials."
                )
        # Router currently fetches CPZ client from env internally
        self.execution = _ExecutionNamespace(BrokerRouter.default())
        self.platform = _PlatformNamespace()
        
        # Data client (lazy-loaded)
        self._data: Optional[DataClient] = None

    @classmethod
    def from_keys(
        cls, api_key: str, secret_key: str, user_id: Optional[str] = None, is_admin: bool = False
    ) -> "CPZClient":
        """Create a CPZClient with explicit API credentials.
        
        This is useful when you want to pass credentials directly instead of relying
        on environment variables, which can be helpful in some execution environments.
        
        Args:
            api_key: Your CPZAI API key
            secret_key: Your CPZAI secret key
            user_id: Optional user ID (usually auto-resolved from credentials)
            is_admin: Whether this is an admin client (default: False)
        
        Returns:
            CPZClient instance configured with the provided credentials
        """
        cpz_client = CPZAIClient.from_keys(api_key=api_key, secret_key=secret_key, user_id=user_id, is_admin=is_admin)
        return cls(cpz_client=cpz_client)

    @property
    def router(self) -> BrokerRouter:
        return self.execution.router
    
    @property
    def data(self) -> DataClient:
        """Access market data, economic data, SEC filings, and social sentiment.
        
        Simple unified methods:
            client.data.bars("AAPL")          # Stock/crypto bars
            client.data.quotes(["AAPL"])      # Latest quotes
            client.data.news("AAPL")          # News articles
            client.data.economic("GDP")       # FRED economic data
            client.data.filings("AAPL")       # SEC filings
            client.data.sentiment("AAPL")     # Social sentiment
        
        Direct provider access:
            client.data.alpaca.get_options_chain("AAPL")
            client.data.fred.get_series("UNRATE")
            client.data.twelve.get_rsi("AAPL")
            client.data.edgar.get_facts("AAPL")
        """
        if self._data is None:
            self._data = DataClient(cpz_client=self._cpz_client)
        return self._data

    # File operations - delegate to CPZAIClient
    def upload_dataframe(
        self, bucket_name: str, file_path: str, df: Any, format: str = "csv", **kwargs
    ) -> Optional[dict[str, Any]]:
        """Upload a pandas DataFrame to storage"""
        return self._cpz_client.upload_dataframe(bucket_name, file_path, df, format=format, **kwargs)

    def download_csv_to_dataframe(
        self, bucket_name: str, file_path: str, encoding: str = "utf-8", **kwargs
    ) -> Optional[Any]:
        """Download a CSV file and load it into a pandas DataFrame"""
        return self._cpz_client.download_csv_to_dataframe(
            bucket_name, file_path, encoding=encoding, **kwargs
        )

    def download_json_to_dataframe(
        self, bucket_name: str, file_path: str, **kwargs
    ) -> Optional[Any]:
        """Download a JSON file and load it into a pandas DataFrame"""
        return self._cpz_client.download_json_to_dataframe(bucket_name, file_path, **kwargs)

    def download_parquet_to_dataframe(
        self, bucket_name: str, file_path: str, **kwargs
    ) -> Optional[Any]:
        """Download a Parquet file and load it into a pandas DataFrame"""
        return self._cpz_client.download_parquet_to_dataframe(bucket_name, file_path, **kwargs)

    def list_files_in_bucket(
        self, bucket_name: str, prefix: str = "", limit: int = 100
    ) -> list[dict[str, Any]]:
        """List files in a storage bucket with optional prefix filtering"""
        return self._cpz_client.list_files_in_bucket(bucket_name, prefix=prefix, limit=limit)

    def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """Delete a file from storage"""
        return self._cpz_client.delete_file(bucket_name, file_path)

    # Strategy operations - delegate to CPZAIClient
    def list_strategies(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """List your trading strategies."""
        return self._cpz_client.get_strategies(limit=limit, offset=offset)

    def get_strategy(self, strategy_id: str) -> Optional[dict[str, Any]]:
        """Get a specific strategy by ID."""
        return self._cpz_client.get_strategy(strategy_id)

    def create_strategy(self, strategy_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Create a new strategy."""
        return self._cpz_client.create_strategy(strategy_data)

    def update_strategy(self, strategy_id: str, strategy_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Update an existing strategy."""
        return self._cpz_client.update_strategy(strategy_id, strategy_data)

    def delete_strategy(self, strategy_id: str) -> bool:
        """Delete a strategy."""
        return self._cpz_client.delete_strategy(strategy_id)

    @staticmethod
    def display_with_sticky_header(
        df: Any, max_rows: int = 1000, max_height: str = "600px", show_index: bool = True
    ) -> None:
        """
        Display a pandas DataFrame with a sticky/fixed header that stays visible while scrolling.
        
        This is useful for viewing long tables where you want the header row to remain visible
        while scrolling through the data.
        
        Args:
            df: The pandas DataFrame to display
            max_rows: Maximum number of rows to display (default: 1000)
            max_height: Maximum height of the table container before scrolling (default: "600px")
            show_index: Whether to show the DataFrame index column (default: True)
        
        Example:
            >>> df = client.download_csv_to_dataframe("user-data", "file.csv")
            >>> client.display_with_sticky_header(df)
        """
        try:
            import pandas as pd
            from ..common.display import display_dataframe_with_sticky_header
            if isinstance(df, pd.DataFrame):
                display_dataframe_with_sticky_header(df, max_rows=max_rows, max_height=max_height, show_index=show_index)
            else:
                print("Error: df must be a pandas DataFrame")
        except ImportError:
            print("Error: pandas is required for display_with_sticky_header")
