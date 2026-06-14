"""
NEWS API CLIENT — Integration with NewsAPI.org

Provides access to 80,000+ sources worldwide.
Rate-limited, paginated, with caching.

Setup:
    1. Get API key from https://newsapi.org
    2. Set environment variable: NEWSAPI_KEY=your_key
    3. Or pass key directly to constructor
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class NewsArticle:
    """Standardized news article from any source."""
    article_id: str
    title: str
    description: str
    content: str
    source_name: str
    source_id: str
    author: str
    url: str
    published_at: datetime
    fetched_at: datetime = field(default_factory=datetime.now)
    language: str = "en"
    country: str = ""
    category: str = ""
    image_url: str = ""
    content_hash: str = ""
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                (self.title + self.content).encode()
            ).hexdigest()[:16]
        if not self.article_id:
            self.article_id = self.content_hash


class NewsAPIClient:
    """
    Client for NewsAPI.org - global news aggregator.
    
    Features:
    - Top headlines by country/category
    - Everything search with date range
    - Source listing
    - Automatic rate limiting
    - Response caching
    """
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: str = None):
        """
        Initialize NewsAPI client.
        
        Args:
            api_key: NewsAPI key. If None, reads from NEWSAPI_KEY env var.
        """
        self.api_key = api_key or os.environ.get("NEWSAPI_KEY", "")
        self._cache: Dict[str, Dict] = {}
        self._request_count = 0
        self._last_request_time = None
        
        if not self.api_key:
            print("[NewsAPI] WARNING: No API key. Set NEWSAPI_KEY environment variable.")
            print("[NewsAPI] Get your key at: https://newsapi.org/register")
    
    def get_top_headlines(self, 
                          country: str = "us",
                          category: str = None,
                          query: str = None,
                          page_size: int = 20) -> List[NewsArticle]:
        """
        Get top headlines.
        
        Args:
            country: 2-letter country code (us, gb, in, cn, etc.)
            category: business, entertainment, general, health, science, sports, technology
            query: Search query within headlines
            page_size: Number of results (max 100)
        """
        params = {
            "country": country,
            "pageSize": min(page_size, 100),
        }
        if category:
            params["category"] = category
        if query:
            params["q"] = query
        
        data = self._request("top-headlines", params)
        return self._parse_response(data)
    
    def search_everything(self,
                          query: str,
                          from_date: datetime = None,
                          to_date: datetime = None,
                          language: str = "en",
                          sort_by: str = "publishedAt",
                          page_size: int = 20,
                          sources: str = None) -> List[NewsArticle]:
        """
        Search all articles.
        
        Args:
            query: Search query (supports AND, OR, NOT operators)
            from_date: Oldest article date
            to_date: Newest article date
            language: Article language (en, es, fr, de, etc.)
            sort_by: relevancy, popularity, publishedAt
            page_size: Number of results
            sources: Comma-separated source IDs
        """
        params = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(page_size, 100),
        }
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%S")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%dT%H:%M:%S")
        if sources:
            params["sources"] = sources
        
        data = self._request("everything", params)
        return self._parse_response(data)
    
    def search_financial_news(self, 
                               topics: List[str] = None,
                               hours_back: int = 24) -> List[NewsArticle]:
        """
        Search specifically for financial/economic news.
        
        Args:
            topics: Specific topics like ["fed", "inflation", "earnings"]
            hours_back: How far back to search
        """
        if topics is None:
            topics = [
                "federal reserve", "inflation", "GDP", "interest rate",
                "stock market", "recession", "earnings", "monetary policy"
            ]
        
        query = " OR ".join(f'"{t}"' for t in topics[:5])
        from_date = datetime.now() - timedelta(hours=hours_back)
        
        return self.search_everything(
            query=query,
            from_date=from_date,
            sort_by="publishedAt",
            page_size=50,
        )
    
    def get_sources(self, category: str = "business", 
                    language: str = "en") -> List[Dict]:
        """Get available news sources."""
        params = {"category": category, "language": language}
        data = self._request("top-headlines/sources", params)
        return data.get("sources", []) if data else []
    
    def _request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make API request with rate limiting and caching."""
        if not REQUESTS_AVAILABLE:
            print("[NewsAPI] 'requests' library not installed. pip install requests")
            return None
        
        if not self.api_key:
            print("[NewsAPI] No API key configured. Returning empty results.")
            return None
        
        # Cache check
        cache_key = hashlib.md5(
            json.dumps({"endpoint": endpoint, **params}, sort_keys=True).encode()
        ).hexdigest()
        
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached["time"] < timedelta(minutes=5):
                return cached["data"]
        
        # Rate limiting (1 request per second)
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < 1.0:
                import time
                time.sleep(1.0 - elapsed)
        
        try:
            params["apiKey"] = self.api_key
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            self._request_count += 1
            self._last_request_time = datetime.now()
            
            if response.status_code == 200:
                data = response.json()
                self._cache[cache_key] = {"data": data, "time": datetime.now()}
                return data
            elif response.status_code == 401:
                print("[NewsAPI] Invalid API key")
            elif response.status_code == 429:
                print("[NewsAPI] Rate limit exceeded")
            else:
                print(f"[NewsAPI] Error {response.status_code}: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            print("[NewsAPI] Request timeout")
        except requests.exceptions.ConnectionError:
            print("[NewsAPI] Connection error")
        except Exception as e:
            print(f"[NewsAPI] Error: {e}")
        
        return None
    
    def _parse_response(self, data: Optional[Dict]) -> List[NewsArticle]:
        """Parse API response into NewsArticle objects."""
        articles = []
        if not data or "articles" not in data:
            return articles
        
        for item in data["articles"]:
            try:
                published = item.get("publishedAt", "")
                if published:
                    try:
                        pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    except ValueError:
                        pub_dt = datetime.now()
                else:
                    pub_dt = datetime.now()
                
                article = NewsArticle(
                    article_id="",
                    title=item.get("title", "") or "",
                    description=item.get("description", "") or "",
                    content=item.get("content", "") or item.get("description", "") or "",
                    source_name=item.get("source", {}).get("name", "Unknown"),
                    source_id=item.get("source", {}).get("id", ""),
                    author=item.get("author", "") or "",
                    url=item.get("url", ""),
                    published_at=pub_dt,
                    image_url=item.get("urlToImage", "") or "",
                )
                articles.append(article)
            except Exception as e:
                print(f"[NewsAPI] Parse error: {e}")
                continue
        
        return articles
    
    def get_status(self) -> Dict:
        """Get client status."""
        return {
            "api_key_configured": bool(self.api_key),
            "requests_made": self._request_count,
            "cache_size": len(self._cache),
            "requests_available": REQUESTS_AVAILABLE,
        }
