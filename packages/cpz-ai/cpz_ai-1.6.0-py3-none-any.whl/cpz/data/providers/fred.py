"""FRED (Federal Reserve Economic Data) provider.

Provides access to 800,000+ economic time series from the Federal Reserve.

Popular Series:
- GDP: Gross Domestic Product
- UNRATE: Unemployment Rate
- CPIAUCSL: Consumer Price Index
- FEDFUNDS: Federal Funds Rate
- DGS10: 10-Year Treasury Rate
- SP500: S&P 500 Index

Docs: https://fred.stlouisfed.org/docs/api/fred/
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from ..models import EconomicSeries


class FREDProvider:
    """FRED (Federal Reserve Economic Data) provider.
    
    Usage:
        provider = FREDProvider()
        gdp = provider.get_series("GDP")
        unemployment = provider.get_series("UNRATE", limit=12)
    """
    
    name = "fred"
    supported_assets = ["economic"]
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize FRED provider.
        
        Args:
            api_key: FRED API key (fetched from CPZAI platform)
        """
        self._api_key = api_key or ""
        
        # Fetch credentials from CPZAI platform (the ONLY supported method)
        if not self._api_key:
            try:
                from ...common.cpz_ai import CPZAIClient
                cpz_client = CPZAIClient.from_env()
                creds = cpz_client.get_data_credentials(provider="fred")
                self._api_key = creds.get("fred_api_key", "")
            except Exception as e:
                print(f"[CPZ SDK] Could not fetch FRED credentials from platform: {e}")
        
        if not self._api_key:
            raise ValueError(
                "FRED API key not found. Connect FRED in the CPZ platform (Settings > API Connections)."
            )
    
    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to FRED API."""
        params["api_key"] = self._api_key
        params["file_type"] = "json"
        
        response = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    
    def get_series(
        self,
        series_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
        sort_order: str = "desc",  # "asc" or "desc"
        frequency: Optional[str] = None,  # "d", "w", "bw", "m", "q", "sa", "a"
        aggregation: Optional[str] = None,  # "avg", "sum", "eop"
    ) -> List[EconomicSeries]:
        """Get economic data series observations.
        
        Args:
            series_id: FRED series ID (e.g., "GDP", "UNRATE")
            start: Start date
            end: End date
            limit: Maximum observations to return
            sort_order: "asc" (oldest first) or "desc" (newest first)
            frequency: Frequency conversion (d=daily, w=weekly, m=monthly, q=quarterly, a=annual)
            aggregation: Aggregation method for frequency conversion
            
        Returns:
            List of EconomicSeries observations
        """
        params: Dict[str, Any] = {
            "series_id": series_id,
            "limit": limit,
            "sort_order": sort_order,
        }
        
        if start:
            params["observation_start"] = start.strftime("%Y-%m-%d")
        if end:
            params["observation_end"] = end.strftime("%Y-%m-%d")
        if frequency:
            params["frequency"] = frequency
        if aggregation:
            params["aggregation_method"] = aggregation
        
        # Get series info for metadata
        series_info = self._get_series_info(series_id)
        
        # Get observations
        data = self._request("series/observations", params)
        
        observations: List[EconomicSeries] = []
        for obs in data.get("observations", []):
            value = obs.get("value")
            # FRED uses "." for missing values
            parsed_value = None if value == "." else float(value)
            
            observations.append(EconomicSeries(
                series_id=series_id,
                title=series_info.get("title", series_id),
                observation_date=datetime.strptime(obs["date"], "%Y-%m-%d"),
                value=parsed_value,
                units=series_info.get("units"),
                frequency=series_info.get("frequency"),
                seasonal_adjustment=series_info.get("seasonal_adjustment"),
            ))
        
        return observations
    
    def _get_series_info(self, series_id: str) -> Dict[str, Any]:
        """Get series metadata."""
        try:
            data = self._request("series", {"series_id": series_id})
            if data.get("seriess"):
                series = data["seriess"][0]
                return {
                    "title": series.get("title", ""),
                    "units": series.get("units", ""),
                    "frequency": series.get("frequency", ""),
                    "seasonal_adjustment": series.get("seasonal_adjustment", ""),
                }
        except Exception:
            pass
        return {}
    
    def search_series(
        self,
        query: str,
        limit: int = 50,
        order_by: str = "popularity",  # "search_rank", "series_id", "title", "popularity"
        filter_variable: Optional[str] = None,  # "frequency", "units", etc.
        filter_value: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Search for available series.
        
        Args:
            query: Search text
            limit: Maximum results
            order_by: Sort order
            filter_variable: Filter field
            filter_value: Filter value
            
        Returns:
            List of series metadata dicts
        """
        params: Dict[str, Any] = {
            "search_text": query,
            "limit": limit,
            "order_by": order_by,
        }
        
        if filter_variable and filter_value:
            params["filter_variable"] = filter_variable
            params["filter_value"] = filter_value
        
        data = self._request("series/search", params)
        
        results: List[Dict[str, str]] = []
        for series in data.get("seriess", []):
            results.append({
                "series_id": series.get("id", ""),
                "title": series.get("title", ""),
                "units": series.get("units", ""),
                "frequency": series.get("frequency", ""),
                "seasonal_adjustment": series.get("seasonal_adjustment", ""),
                "popularity": str(series.get("popularity", 0)),
                "observation_start": series.get("observation_start", ""),
                "observation_end": series.get("observation_end", ""),
            })
        
        return results
    
    def get_categories(self, category_id: int = 0) -> List[Dict[str, Any]]:
        """Get FRED categories.
        
        Args:
            category_id: Parent category ID (0 for root)
            
        Returns:
            List of category dicts
        """
        data = self._request("category/children", {"category_id": category_id})
        return data.get("categories", [])
    
    def get_series_in_category(
        self, category_id: int, limit: int = 100
    ) -> List[Dict[str, str]]:
        """Get all series in a category.
        
        Args:
            category_id: Category ID
            limit: Maximum results
            
        Returns:
            List of series metadata dicts
        """
        data = self._request("category/series", {
            "category_id": category_id,
            "limit": limit,
        })
        
        results: List[Dict[str, str]] = []
        for series in data.get("seriess", []):
            results.append({
                "series_id": series.get("id", ""),
                "title": series.get("title", ""),
                "units": series.get("units", ""),
                "frequency": series.get("frequency", ""),
            })
        
        return results
    
    def get_release_dates(
        self,
        series_id: str,
        limit: int = 10,
    ) -> List[datetime]:
        """Get release/revision dates for a series.
        
        Args:
            series_id: FRED series ID
            limit: Maximum dates to return
            
        Returns:
            List of release dates
        """
        data = self._request("series/release", {
            "series_id": series_id,
        })
        
        dates: List[datetime] = []
        for release in data.get("releases", [])[:limit]:
            if release.get("realtime_start"):
                dates.append(datetime.strptime(release["realtime_start"], "%Y-%m-%d"))
        
        return dates


# Popular FRED series constants for convenience
FRED_SERIES = {
    # GDP & Growth
    "GDP": "Gross Domestic Product",
    "GDPC1": "Real GDP",
    "A191RL1Q225SBEA": "Real GDP Growth Rate",
    
    # Employment
    "UNRATE": "Unemployment Rate",
    "PAYEMS": "Total Nonfarm Payrolls",
    "ICSA": "Initial Jobless Claims",
    
    # Inflation
    "CPIAUCSL": "Consumer Price Index",
    "PCEPI": "PCE Price Index",
    "CPILFESL": "Core CPI",
    
    # Interest Rates
    "FEDFUNDS": "Federal Funds Rate",
    "DGS10": "10-Year Treasury",
    "DGS2": "2-Year Treasury",
    "T10Y2Y": "10Y-2Y Spread",
    
    # Housing
    "CSUSHPISA": "Case-Shiller Home Price Index",
    "HOUST": "Housing Starts",
    "MORTGAGE30US": "30-Year Mortgage Rate",
    
    # Markets
    "SP500": "S&P 500",
    "VIXCLS": "VIX Volatility Index",
    
    # Money Supply
    "M2SL": "M2 Money Stock",
    "WALCL": "Fed Balance Sheet",
}
