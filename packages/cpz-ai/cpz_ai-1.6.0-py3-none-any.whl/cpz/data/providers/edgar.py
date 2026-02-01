"""SEC EDGAR provider for company filings and financial data.

Provides access to:
- 10-K (Annual Reports)
- 10-Q (Quarterly Reports)
- 8-K (Current Reports)
- DEF 14A (Proxy Statements)
- 13F (Institutional Holdings)
- And more...

Docs: https://www.sec.gov/developer
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from ..models import Filing


class EDGARProvider:
    """SEC EDGAR filings provider.
    
    Usage:
        provider = EDGARProvider()
        filings = provider.get_filings("AAPL", form_type="10-K")
        content = provider.get_filing_content(accession_number)
    """
    
    name = "edgar"
    supported_assets = ["filings"]
    
    BASE_URL = "https://data.sec.gov"
    COMPANY_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
    
    # SEC requires identifying user agent
    HEADERS = {
        "User-Agent": "CPZ-AI contact@cpz-lab.com",
        "Accept-Encoding": "gzip, deflate",
    }
    
    # CIK lookup cache
    _cik_cache: Dict[str, str] = {}
    
    def __init__(self, user_agent: Optional[str] = None):
        """Initialize EDGAR provider.
        
        Args:
            user_agent: Custom user agent (SEC requires identification)
        """
        if user_agent:
            self.HEADERS["User-Agent"] = user_agent
    
    def _request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make request to SEC API."""
        response = requests.get(
            url,
            params=params,
            headers=self.HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    
    def _get_cik(self, symbol: str) -> str:
        """Get CIK (Central Index Key) for a ticker symbol."""
        symbol = symbol.upper()
        
        if symbol in self._cik_cache:
            return self._cik_cache[symbol]
        
        # Primary method: Use SEC EDGAR company search
        # This is the most reliable and always-available method
        try:
            import re
            response = requests.get(
                "https://www.sec.gov/cgi-bin/browse-edgar",
                params={
                    "action": "getcompany",
                    "CIK": symbol,
                    "type": "",
                    "dateb": "",
                    "owner": "include",
                    "count": "0",
                    "output": "atom",
                },
                headers=self.HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            
            # Extract CIK from response
            match = re.search(r'CIK=(\d+)', response.text)
            if match:
                cik = match.group(1).zfill(10)
                self._cik_cache[symbol] = cik
                return cik
        except Exception:
            pass
        
        # Fallback: Try direct submissions endpoint with CIK
        # Some symbols might be stored differently
        try:
            # Common CIK mappings for major companies (hardcoded fallback)
            common_ciks = {
                "AAPL": "0000320193",
                "MSFT": "0000789019",
                "GOOGL": "0001652044",
                "GOOG": "0001652044",
                "AMZN": "0001018724",
                "TSLA": "0001318605",
                "META": "0001326801",
                "NVDA": "0001045810",
                "JPM": "0000019617",
                "V": "0001403161",
                "JNJ": "0000200406",
                "WMT": "0000104169",
                "PG": "0000080424",
                "MA": "0001141391",
                "UNH": "0000731766",
                "HD": "0000354950",
                "BAC": "0000070858",
                "DIS": "0001744489",
                "NFLX": "0001065280",
                "INTC": "0000050863",
            }
            if symbol in common_ciks:
                cik = common_ciks[symbol]
                self._cik_cache[symbol] = cik
                return cik
        except Exception:
            pass
        
        raise ValueError(f"Could not find CIK for symbol: {symbol}")
    
    def get_filings(
        self,
        symbol: Optional[str] = None,
        cik: Optional[str] = None,
        form_type: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Filing]:
        """Get SEC filings.
        
        Args:
            symbol: Ticker symbol (e.g., "AAPL")
            cik: CIK number (alternative to symbol)
            form_type: Form type filter (e.g., "10-K", "10-Q", "8-K")
            start: Start date
            end: End date
            limit: Maximum filings to return
            
        Returns:
            List of Filing objects
        """
        if not symbol and not cik:
            raise ValueError("Either symbol or cik is required")
        
        if symbol and not cik:
            cik = self._get_cik(symbol)
        
        # Normalize CIK
        cik = str(cik).zfill(10)
        
        # Fetch company submissions
        data = self._request(f"{self.BASE_URL}/submissions/CIK{cik}.json")
        
        company_name = data.get("name", "")
        filings_data = data.get("filings", {}).get("recent", {})
        
        # Parse filings
        filings: List[Filing] = []
        
        accession_numbers = filings_data.get("accessionNumber", [])
        form_types_list = filings_data.get("form", [])
        filing_dates = filings_data.get("filingDate", [])
        acceptance_times = filings_data.get("acceptanceDateTime", [])
        primary_docs = filings_data.get("primaryDocument", [])
        items = filings_data.get("items", [])
        
        # Iterate through ALL filings, not just first N
        for i in range(len(accession_numbers)):
            # Stop if we've found enough
            if len(filings) >= limit:
                break
            
            # Filter by form type (exact match or prefix match for variants like 10-K/A)
            if form_type:
                current_form = form_types_list[i] if i < len(form_types_list) else ""
                if current_form != form_type and not current_form.startswith(form_type + "/"):
                    continue
            
            # Parse dates
            try:
                filed_date = datetime.strptime(filing_dates[i], "%Y-%m-%d")
            except (IndexError, ValueError):
                continue
            
            # Filter by date range
            if start and filed_date < start:
                continue
            if end and filed_date > end:
                continue
            
            # Parse acceptance time
            accepted_date = None
            if i < len(acceptance_times) and acceptance_times[i]:
                try:
                    accepted_date = datetime.fromisoformat(
                        acceptance_times[i].replace("Z", "+00:00")
                    )
                except Exception:
                    pass
            
            # Build URLs
            accession_clean = accession_numbers[i].replace("-", "")
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}"
            primary_doc = primary_docs[i] if i < len(primary_docs) else ""
            document_url = f"{filing_url}/{primary_doc}" if primary_doc else None
            
            # Parse 8-K items
            item_list = None
            if i < len(items) and items[i]:
                item_list = [x.strip() for x in str(items[i]).split(",")]
            
            filings.append(Filing(
                accession_number=accession_numbers[i],
                cik=cik,
                company_name=company_name,
                form_type=form_types_list[i] if i < len(form_types_list) else "",
                filed_date=filed_date,
                accepted_date=accepted_date,
                document_url=document_url,
                filing_url=filing_url,
                items=item_list,
            ))
        
        return filings
    
    def get_filing_content(
        self,
        accession_number: str,
        document_type: str = "primary",  # "primary", "full", "exhibits"
    ) -> str:
        """Get full filing content.
        
        Args:
            accession_number: SEC accession number
            document_type: Type of document to retrieve
            
        Returns:
            Filing content as text
        """
        # Parse accession number to build URL
        # Format: 0000320193-23-000077 -> 000032019323000077
        accession_clean = accession_number.replace("-", "")
        
        # Get filing index
        url = f"https://www.sec.gov/Archives/edgar/data/{accession_clean[:10]}/{accession_clean}/{accession_number}-index.htm"
        
        response = requests.get(url, headers=self.HEADERS, timeout=30)
        response.raise_for_status()
        
        return response.text
    
    def get_company_facts(self, symbol: str) -> Dict[str, Any]:
        """Get all company XBRL facts (structured financial data).
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Dictionary of financial facts
        """
        cik = self._get_cik(symbol)
        data = self._request(f"{self.BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json")
        return data
    
    def get_company_concept(
        self,
        symbol: str,
        taxonomy: str = "us-gaap",
        concept: str = "Revenue",
    ) -> List[Dict[str, Any]]:
        """Get specific XBRL concept values over time.
        
        Args:
            symbol: Ticker symbol
            taxonomy: XBRL taxonomy (e.g., "us-gaap", "dei")
            concept: XBRL concept name (e.g., "Revenue", "Assets")
            
        Returns:
            List of concept values with dates
        """
        cik = self._get_cik(symbol)
        data = self._request(
            f"{self.BASE_URL}/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{concept}.json"
        )
        
        results: List[Dict[str, Any]] = []
        for unit_type, values in data.get("units", {}).items():
            for v in values:
                results.append({
                    "value": v.get("val"),
                    "unit": unit_type,
                    "filed": v.get("filed"),
                    "end_date": v.get("end"),
                    "start_date": v.get("start"),
                    "form": v.get("form"),
                    "accession": v.get("accn"),
                    "frame": v.get("frame"),
                })
        
        return results
    
    def search_filings(
        self,
        query: str,
        form_types: Optional[List[str]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Full-text search across SEC filings.
        
        Args:
            query: Search text
            form_types: Filter by form types
            start: Start date
            end: End date
            limit: Maximum results
            
        Returns:
            List of matching filing metadata
        """
        params: Dict[str, Any] = {
            "q": query,
            "dateRange": "custom",
            "startdt": (start or datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            "enddt": (end or datetime.now()).strftime("%Y-%m-%d"),
        }
        
        if form_types:
            params["forms"] = ",".join(form_types)
        
        response = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params=params,
            headers=self.HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        
        return data.get("hits", {}).get("hits", [])[:limit]
    
    def get_insider_transactions(
        self,
        symbol: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get insider trading transactions (Form 4 filings).
        
        Args:
            symbol: Ticker symbol
            limit: Maximum transactions
            
        Returns:
            List of insider transactions
        """
        filings = self.get_filings(symbol=symbol, form_type="4", limit=limit)
        
        transactions: List[Dict[str, Any]] = []
        for filing in filings:
            transactions.append({
                "filed_date": filing.filed_date,
                "accession_number": filing.accession_number,
                "filing_url": filing.filing_url,
            })
        
        return transactions
    
    def get_institutional_holdings(
        self,
        symbol: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get institutional holdings (13F filings).
        
        Args:
            symbol: Ticker symbol
            limit: Maximum holdings
            
        Returns:
            List of institutional holdings
        """
        filings = self.get_filings(symbol=symbol, form_type="13F-HR", limit=limit)
        
        holdings: List[Dict[str, Any]] = []
        for filing in filings:
            holdings.append({
                "filed_date": filing.filed_date,
                "company_name": filing.company_name,
                "accession_number": filing.accession_number,
                "filing_url": filing.filing_url,
            })
        
        return holdings


# Common SEC form types for reference
SEC_FORMS = {
    "10-K": "Annual Report",
    "10-Q": "Quarterly Report",
    "8-K": "Current Report",
    "DEF 14A": "Proxy Statement",
    "S-1": "Registration Statement (IPO)",
    "4": "Insider Transaction",
    "13F-HR": "Institutional Holdings",
    "SC 13D": "Beneficial Ownership (>5%)",
    "SC 13G": "Beneficial Ownership (Passive)",
    "424B": "Prospectus",
}
