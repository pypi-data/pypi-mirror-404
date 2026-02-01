"""Social sentiment data providers (Reddit, Stocktwits).

Provides access to:
- Reddit posts from investing subreddits
- Stocktwits messages and sentiment
- Trending tickers
- Aggregated sentiment analysis

Note: These providers use public APIs with rate limits.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from ..models import SocialPost


class RedditProvider:
    """Reddit social sentiment provider.
    
    Accesses investing-related subreddits for sentiment analysis.
    Uses Reddit's public JSON API (no authentication required for basic access).
    
    Usage:
        provider = RedditProvider()
        posts = provider.get_posts(symbols=["AAPL", "TSLA"])
        trending = provider.get_trending()
    """
    
    name = "reddit"
    supported_assets = ["social"]
    
    BASE_URL = "https://www.reddit.com"
    
    # Popular investing subreddits
    SUBREDDITS = [
        "wallstreetbets",
        "stocks",
        "investing",
        "stockmarket",
        "options",
        "SecurityAnalysis",
        "ValueInvesting",
    ]
    
    HEADERS = {
        "User-Agent": "CPZ-AI/1.0 (contact@cpz-lab.com)",
    }
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """Initialize Reddit provider.
        
        Args:
            client_id: Reddit API client ID (optional, for higher rate limits)
            client_secret: Reddit API client secret (optional)
        """
        self._client_id = client_id or ""
        self._client_secret = client_secret or ""
        
        # Try to fetch from CPZAI platform
        if not self._client_id:
            try:
                from ...common.cpz_ai import CPZAIClient
                cpz_client = CPZAIClient.from_env()
                creds = cpz_client.get_data_credentials(provider="reddit")
                self._client_id = creds.get("reddit_client_id", "")
                self._client_secret = creds.get("reddit_client_secret", "")
            except Exception:
                pass  # Reddit works without auth, just slower
        self._access_token: Optional[str] = None
    
    def _request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make request to Reddit API."""
        response = requests.get(
            url,
            params=params,
            headers=self.HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    
    def get_posts(
        self,
        symbols: Optional[List[str]] = None,
        subreddits: Optional[List[str]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        sort: str = "hot",  # "hot", "new", "top", "rising"
    ) -> List[SocialPost]:
        """Get Reddit posts mentioning symbols.
        
        Args:
            symbols: Filter by stock symbols (searches in title/body)
            subreddits: Subreddits to search (defaults to investing subs)
            start: Start datetime (limited by Reddit API)
            end: End datetime
            limit: Maximum posts to return
            sort: Sort order
            
        Returns:
            List of SocialPost objects
        """
        subs = subreddits or self.SUBREDDITS[:3]  # Limit to top 3 by default
        posts: List[SocialPost] = []
        
        for subreddit in subs:
            if len(posts) >= limit:
                break
            
            try:
                url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
                data = self._request(url, {"limit": min(50, limit - len(posts))})
                
                for child in data.get("data", {}).get("children", []):
                    post_data = child.get("data", {})
                    
                    # Extract symbols mentioned
                    mentioned_symbols = self._extract_symbols(
                        post_data.get("title", "") + " " + post_data.get("selftext", "")
                    )
                    
                    # Filter by symbols if provided
                    if symbols:
                        if not any(s.upper() in [m.upper() for m in mentioned_symbols] for s in symbols):
                            continue
                    
                    # Parse creation time
                    created_utc = post_data.get("created_utc", 0)
                    created_at = datetime.utcfromtimestamp(created_utc)
                    
                    # Filter by date range
                    if start and created_at < start:
                        continue
                    if end and created_at > end:
                        continue
                    
                    # Simple sentiment analysis based on upvote ratio
                    upvote_ratio = post_data.get("upvote_ratio", 0.5)
                    sentiment = "neutral"
                    sentiment_score = 0.0
                    if upvote_ratio > 0.7:
                        sentiment = "bullish"
                        sentiment_score = (upvote_ratio - 0.5) * 2
                    elif upvote_ratio < 0.3:
                        sentiment = "bearish"
                        sentiment_score = (upvote_ratio - 0.5) * 2
                    
                    posts.append(SocialPost(
                        id=post_data.get("id", ""),
                        source="reddit",
                        content=post_data.get("title", ""),
                        author=post_data.get("author", ""),
                        symbols=mentioned_symbols,
                        created_at=created_at,
                        sentiment=sentiment,
                        sentiment_score=sentiment_score,
                        likes=post_data.get("ups", 0),
                        comments=post_data.get("num_comments", 0),
                        url=f"https://reddit.com{post_data.get('permalink', '')}",
                    ))
                    
                    if len(posts) >= limit:
                        break
                        
            except Exception:
                continue
        
        return posts[:limit]
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text.
        
        Looks for $SYMBOL patterns and common ticker formats.
        """
        import re
        
        # Match $SYMBOL pattern
        dollar_symbols = re.findall(r'\$([A-Z]{1,5})\b', text.upper())
        
        # Match standalone capital letter sequences that look like tickers
        # Be conservative to avoid false positives
        standalone = re.findall(r'\b([A-Z]{2,5})\b', text)
        
        # Common stock symbols to help filtering
        common_symbols = {
            "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "TSLA", "META", "NVDA",
            "AMD", "INTC", "NFLX", "DIS", "BA", "JPM", "GS", "BAC", "WFC",
            "SPY", "QQQ", "IWM", "VTI", "VOO", "GME", "AMC", "PLTR", "NIO",
            "COIN", "HOOD", "SOFI", "RIVN", "LCID", "F", "GM", "UBER", "LYFT",
        }
        
        symbols = set(dollar_symbols)
        for s in standalone:
            if s in common_symbols:
                symbols.add(s)
        
        return list(symbols)
    
    def get_trending(
        self,
        subreddits: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[str]:
        """Get trending stock symbols on Reddit.
        
        Args:
            subreddits: Subreddits to analyze
            limit: Maximum symbols to return
            
        Returns:
            List of trending symbols sorted by mention count
        """
        posts = self.get_posts(subreddits=subreddits, limit=100)
        
        # Count symbol mentions
        symbol_counts: Dict[str, int] = {}
        for post in posts:
            for symbol in post.symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # Sort by count
        sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_symbols[:limit]]
    
    def get_sentiment(
        self,
        symbol: str,
        subreddits: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Get aggregated sentiment for a symbol.
        
        Args:
            symbol: Stock symbol
            subreddits: Subreddits to analyze
            
        Returns:
            Sentiment metrics
        """
        posts = self.get_posts(symbols=[symbol], subreddits=subreddits, limit=50)
        
        if not posts:
            return {
                "score": 0.0,
                "bullish_pct": 0.0,
                "bearish_pct": 0.0,
                "neutral_pct": 1.0,
                "post_count": 0,
            }
        
        bullish = sum(1 for p in posts if p.sentiment == "bullish")
        bearish = sum(1 for p in posts if p.sentiment == "bearish")
        neutral = sum(1 for p in posts if p.sentiment == "neutral")
        total = len(posts)
        
        avg_score = sum(p.sentiment_score or 0 for p in posts) / total
        
        return {
            "score": avg_score,
            "bullish_pct": bullish / total,
            "bearish_pct": bearish / total,
            "neutral_pct": neutral / total,
            "post_count": total,
        }


class StocktwitsProvider:
    """Stocktwits social sentiment provider.
    
    Usage:
        provider = StocktwitsProvider()
        posts = provider.get_posts(symbols=["AAPL"])
        trending = provider.get_trending()
    """
    
    name = "stocktwits"
    supported_assets = ["social"]
    
    BASE_URL = "https://api.stocktwits.com/api/2"
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize Stocktwits provider.
        
        Args:
            access_token: Stocktwits access token (optional, for higher rate limits)
        """
        self._access_token = access_token or ""
        
        # Try to fetch from CPZAI platform
        if not self._access_token:
            try:
                from ...common.cpz_ai import CPZAIClient
                cpz_client = CPZAIClient.from_env()
                creds = cpz_client.get_data_credentials(provider="stocktwits")
                self._access_token = creds.get("stocktwits_access_token", "")
            except Exception:
                pass  # Stocktwits works without auth, just slower
    
    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make request to Stocktwits API."""
        params = params or {}
        if self._access_token:
            params["access_token"] = self._access_token
        
        response = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    
    def get_posts(
        self,
        symbols: Optional[List[str]] = None,
        source: Optional[str] = None,  # Ignored, for interface compatibility
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[SocialPost]:
        """Get Stocktwits messages for symbols.
        
        Args:
            symbols: Stock symbols to fetch messages for
            source: Ignored (always "stocktwits")
            start: Start datetime
            end: End datetime
            limit: Maximum posts per symbol
            
        Returns:
            List of SocialPost objects
        """
        if not symbols:
            # Get from trending if no symbols provided
            symbols = self.get_trending(limit=5)
        
        posts: List[SocialPost] = []
        
        for symbol in symbols:
            try:
                data = self._request(f"streams/symbol/{symbol}.json", {"limit": min(30, limit)})
                
                for message in data.get("messages", []):
                    # Parse creation time
                    created_str = message.get("created_at", "")
                    try:
                        created_at = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%SZ")
                    except Exception:
                        created_at = datetime.utcnow()
                    
                    # Filter by date range
                    if start and created_at < start:
                        continue
                    if end and created_at > end:
                        continue
                    
                    # Extract sentiment from Stocktwits tags
                    entities = message.get("entities", {})
                    sentiment_data = entities.get("sentiment", {})
                    sentiment_basic = sentiment_data.get("basic")
                    
                    sentiment = "neutral"
                    sentiment_score = 0.0
                    if sentiment_basic == "Bullish":
                        sentiment = "bullish"
                        sentiment_score = 1.0
                    elif sentiment_basic == "Bearish":
                        sentiment = "bearish"
                        sentiment_score = -1.0
                    
                    # Extract mentioned symbols
                    mentioned_symbols = [symbol]
                    for sym in entities.get("symbols", []):
                        if sym.get("symbol"):
                            mentioned_symbols.append(sym["symbol"])
                    mentioned_symbols = list(set(mentioned_symbols))
                    
                    posts.append(SocialPost(
                        id=str(message.get("id", "")),
                        source="stocktwits",
                        content=message.get("body", ""),
                        author=message.get("user", {}).get("username", ""),
                        symbols=mentioned_symbols,
                        created_at=created_at,
                        sentiment=sentiment,
                        sentiment_score=sentiment_score,
                        likes=message.get("likes", {}).get("total", 0),
                        comments=message.get("conversation", {}).get("replies", 0),
                        url=f"https://stocktwits.com/{message.get('user', {}).get('username', '')}/message/{message.get('id', '')}",
                    ))
                    
            except Exception:
                continue
        
        return posts[:limit]
    
    def get_trending(self, limit: int = 20) -> List[str]:
        """Get trending symbols on Stocktwits.
        
        Args:
            limit: Maximum symbols to return
            
        Returns:
            List of trending symbols
        """
        try:
            data = self._request("trending/symbols.json")
            symbols = [s.get("symbol", "") for s in data.get("symbols", [])]
            return symbols[:limit]
        except Exception:
            return []
    
    def get_sentiment(
        self,
        symbol: str,
        source: Optional[str] = None,  # Ignored
    ) -> Dict[str, float]:
        """Get aggregated sentiment for a symbol.
        
        Args:
            symbol: Stock symbol
            source: Ignored
            
        Returns:
            Sentiment metrics
        """
        posts = self.get_posts(symbols=[symbol], limit=30)
        
        if not posts:
            return {
                "score": 0.0,
                "bullish_pct": 0.0,
                "bearish_pct": 0.0,
                "neutral_pct": 1.0,
                "post_count": 0,
            }
        
        bullish = sum(1 for p in posts if p.sentiment == "bullish")
        bearish = sum(1 for p in posts if p.sentiment == "bearish")
        neutral = sum(1 for p in posts if p.sentiment == "neutral")
        total = len(posts)
        
        # Calculate weighted score
        avg_score = sum(p.sentiment_score or 0 for p in posts) / total
        
        return {
            "score": avg_score,
            "bullish_pct": bullish / total,
            "bearish_pct": bearish / total,
            "neutral_pct": neutral / total,
            "post_count": total,
        }
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information and stats from Stocktwits.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Symbol information
        """
        try:
            data = self._request(f"streams/symbol/{symbol}.json")
            symbol_data = data.get("symbol", {})
            
            return {
                "symbol": symbol_data.get("symbol", symbol),
                "title": symbol_data.get("title", ""),
                "watchlist_count": symbol_data.get("watchlist_count", 0),
                "sentiment": symbol_data.get("sentiment", {}),
            }
        except Exception:
            return {"symbol": symbol}
