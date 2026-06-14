"""
NEWS AGGREGATOR — Combines all news sources with deduplication

Single interface across:
- NewsAPI (80,000+ sources)
- GDELT (global events, free)
- RSS feeds (custom sources)

Features:
- Cross-source deduplication (semantic + hash)
- Source priority ranking
- Unified article format
- Real-time monitoring mode
"""

import asyncio
import hashlib
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field

from .news_api_client import NewsAPIClient, NewsArticle
from .gdelt_client import GDELTClient, GDELTArticle
from .rss_reader import RSSReader, RSSArticle


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """
    Token-bucket rate limiter for API calls.
    
    Tracks per-source request counts and enforces configurable limits
    with sliding windows.
    """
    
    def __init__(self, limits: Dict[str, Dict] = None):
        self.limits = limits or {
            "newsapi": {"max_requests": 95, "window_seconds": 86400},  # ~100/day with margin
            "gdelt": {"max_requests": 500, "window_seconds": 3600},    # 500/hour
            "rss": {"max_requests": 1000, "window_seconds": 3600},     # Generous for RSS
        }
        self._request_log: Dict[str, List[float]] = {k: [] for k in self.limits}
        self._lock = threading.Lock()
    
    def can_request(self, source: str) -> bool:
        """Check if a request is allowed for this source."""
        if source not in self.limits:
            return True
        
        with self._lock:
            now = time.time()
            window = self.limits[source]["window_seconds"]
            max_req = self.limits[source]["max_requests"]
            
            # Prune old entries
            self._request_log[source] = [
                t for t in self._request_log[source] if now - t < window
            ]
            
            return len(self._request_log[source]) < max_req
    
    def record_request(self, source: str):
        """Record that a request was made."""
        with self._lock:
            self._request_log.setdefault(source, []).append(time.time())
    
    def remaining(self, source: str) -> int:
        """Get remaining requests in current window."""
        if source not in self.limits:
            return 9999
        with self._lock:
            now = time.time()
            window = self.limits[source]["window_seconds"]
            active = [t for t in self._request_log.get(source, []) if now - t < window]
            return max(0, self.limits[source]["max_requests"] - len(active))


# ============================================================================
# RETRY WITH EXPONENTIAL BACKOFF
# ============================================================================

def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0,
                       max_delay: float = 30.0, source_name: str = "unknown"):
    """
    Execute a function with exponential backoff on failure.
    
    Delay formula: min(max_delay, base_delay * 2^attempt + jitter)
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(max_delay, base_delay * (2 ** attempt))
                jitter = random.uniform(0, delay * 0.3)  # 30% jitter
                total_delay = delay + jitter
                print(f"[Aggregator] {source_name} attempt {attempt+1} failed: {e}. "
                      f"Retrying in {total_delay:.1f}s...")
                time.sleep(total_delay)
            else:
                print(f"[Aggregator] {source_name} failed after {max_retries+1} attempts: {e}")
    return []  # Return empty on exhaustion


# ============================================================================
# WEBSOCKET NEWS LISTENER
# ============================================================================

class WebSocketNewsListener:
    """
    WebSocket-based real-time news listener.
    
    Supports configurable WebSocket endpoints for streaming news.
    Falls back to polling if WebSocket connection fails.
    """
    
    def __init__(self, ws_urls: Dict[str, str] = None):
        self.ws_urls = ws_urls or {}
        self._connections: Dict[str, Any] = {}
        self._running = False
        self._callbacks: List[Callable] = []
        self._ws_available = False
        
        try:
            import websockets
            self._ws_available = True
        except ImportError:
            print("[WebSocket] websockets library not installed. "
                  "Install with: pip install websockets")
    
    def add_endpoint(self, name: str, url: str):
        """Add a WebSocket endpoint."""
        self.ws_urls[name] = url
    
    def on_message(self, callback: Callable):
        """Register a callback for incoming messages."""
        self._callbacks.append(callback)
    
    async def connect_all(self):
        """Connect to all configured WebSocket endpoints."""
        if not self._ws_available:
            print("[WebSocket] Cannot connect — websockets not installed")
            return
        
        import websockets
        self._running = True
        
        tasks = []
        for name, url in self.ws_urls.items():
            tasks.append(self._listen(name, url))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _listen(self, name: str, url: str):
        """Listen to a single WebSocket endpoint with auto-reconnect."""
        import websockets
        reconnect_delay = 1.0
        
        while self._running:
            try:
                async with websockets.connect(url) as ws:
                    self._connections[name] = ws
                    reconnect_delay = 1.0  # Reset on success
                    print(f"[WebSocket] Connected to {name}")
                    
                    async for message in ws:
                        for cb in self._callbacks:
                            try:
                                cb(name, message)
                            except Exception as e:
                                print(f"[WebSocket] Callback error: {e}")
            
            except Exception as e:
                print(f"[WebSocket] {name} disconnected: {e}. "
                      f"Reconnecting in {reconnect_delay:.1f}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(60.0, reconnect_delay * 2)
    
    def stop(self):
        """Stop all WebSocket connections."""
        self._running = False
        self._connections.clear()
    
    @property
    def is_available(self) -> bool:
        return self._ws_available


@dataclass
class UnifiedArticle:
    """Unified article format across all sources."""
    article_id: str
    title: str
    content: str
    summary: str
    source: str
    source_type: str  # "newsapi", "gdelt", "rss"
    url: str
    published_at: datetime
    fetched_at: datetime = field(default_factory=datetime.now)
    language: str = "en"
    author: str = ""
    categories: List[str] = field(default_factory=list)
    tone: float = 0.0
    entities: List[str] = field(default_factory=list)
    content_hash: str = ""
    duplicate_of: str = ""  # ID of original if this is a duplicate
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                (self.title + self.content[:200]).encode()
            ).hexdigest()[:16]
        if not self.article_id:
            self.article_id = f"{self.source_type}_{self.content_hash}"


class NewsAggregator:
    """
    Aggregates news from all sources into a unified stream.
    
    Usage:
        aggregator = NewsAggregator(newsapi_key="...")
        articles = aggregator.fetch_latest(hours_back=6)
        
        # Or monitor continuously:
        aggregator.start_monitoring(callback=process_article, interval=300)
    """
    
    def __init__(self, 
                 newsapi_key: str = None,
                 custom_rss_feeds: Dict[str, str] = None,
                 enable_newsapi: bool = True,
                 enable_gdelt: bool = True,
                 enable_rss: bool = True):
        """
        Initialize the news aggregator.
        
        Args:
            newsapi_key: API key for NewsAPI
            custom_rss_feeds: Additional RSS feeds {name: url}
            enable_newsapi: Whether to use NewsAPI
            enable_gdelt: Whether to use GDELT
            enable_rss: Whether to use RSS feeds
        """
        self.sources = {}
        
        if enable_newsapi:
            self.sources["newsapi"] = NewsAPIClient(api_key=newsapi_key)
        
        if enable_gdelt:
            self.sources["gdelt"] = GDELTClient()
        
        if enable_rss:
            self.sources["rss"] = RSSReader(custom_feeds=custom_rss_feeds)
        
        # Rate limiting
        self._rate_limiter = RateLimiter()
        
        # WebSocket support
        self._ws_listener = WebSocketNewsListener()
        
        # Deduplication
        self._seen_hashes: set = set()
        self._article_store: Dict[str, UnifiedArticle] = {}
        
        # Monitoring
        self._monitoring = False
        self._monitor_thread = None
        
        # Backoff configuration
        self._max_retries = 3
        self._base_delay = 1.0
        self._consecutive_failures: Dict[str, int] = {k: 0 for k in self.sources}
        
        print(f"[Aggregator] Initialized with sources: {list(self.sources.keys())}")
    
    def fetch_latest(self, 
                     query: str = None,
                     hours_back: int = 24,
                     max_per_source: int = 30,
                     financial_only: bool = True) -> List[UnifiedArticle]:
        """
        Fetch latest articles from all enabled sources.
        
        Args:
            query: Search query (None = general financial news)
            hours_back: How far back to search
            max_per_source: Max articles per source
            financial_only: Only financial/economic news
        
        Returns:
            Deduplicated list of UnifiedArticle, sorted by date
        """
        all_articles = []
        
        # 1. NewsAPI
        if "newsapi" in self.sources:
            if not self._rate_limiter.can_request("newsapi"):
                print(f"[Aggregator] NewsAPI rate limit reached "
                      f"({self._rate_limiter.remaining('newsapi')} remaining)")
            else:
                def _fetch_newsapi_inner():
                    client: NewsAPIClient = self.sources["newsapi"]
                    if query:
                        return client.search_everything(
                            query=query,
                            from_date=datetime.now() - timedelta(hours=hours_back),
                            page_size=max_per_source,
                        )
                    elif financial_only:
                        return client.search_financial_news(hours_back=hours_back)
                    else:
                        return client.get_top_headlines(page_size=max_per_source)
                
                articles = retry_with_backoff(
                    _fetch_newsapi_inner,
                    max_retries=self._max_retries,
                    base_delay=self._base_delay,
                    source_name="NewsAPI",
                )
                self._rate_limiter.record_request("newsapi")
                if articles:
                    self._consecutive_failures["newsapi"] = 0
                    for a in articles:
                        unified = self._convert_newsapi(a)
                        all_articles.append(unified)
                else:
                    self._consecutive_failures["newsapi"] = \
                        self._consecutive_failures.get("newsapi", 0) + 1
        
        # 2. GDELT
        if "gdelt" in self.sources:
            if not self._rate_limiter.can_request("gdelt"):
                print(f"[Aggregator] GDELT rate limit reached")
            else:
                def _fetch_gdelt_inner():
                    client: GDELTClient = self.sources["gdelt"]
                    if query:
                        return client.search_articles(
                            query=query,
                            timespan=f"{hours_back}h",
                            max_records=max_per_source,
                        )
                    elif financial_only:
                        return client.search_financial_news(
                            hours_back=hours_back,
                            max_records=max_per_source,
                        )
                    else:
                        return client.search_articles(
                            query="economy OR market",
                            timespan=f"{hours_back}h",
                            max_records=max_per_source,
                        )
                
                articles = retry_with_backoff(
                    _fetch_gdelt_inner,
                    max_retries=self._max_retries,
                    base_delay=self._base_delay,
                    source_name="GDELT",
                )
                self._rate_limiter.record_request("gdelt")
                if articles:
                    self._consecutive_failures["gdelt"] = 0
                    for a in articles:
                        unified = self._convert_gdelt(a)
                        all_articles.append(unified)
                else:
                    self._consecutive_failures["gdelt"] = \
                        self._consecutive_failures.get("gdelt", 0) + 1
        
        # 3. RSS
        if "rss" in self.sources:
            def _fetch_rss_inner():
                reader: RSSReader = self.sources["rss"]
                if financial_only:
                    return reader.read_all_financial()
                else:
                    return reader.read_all_financial()
            
            articles = retry_with_backoff(
                _fetch_rss_inner,
                max_retries=self._max_retries,
                base_delay=self._base_delay,
                source_name="RSS",
            )
            if articles:
                self._consecutive_failures["rss"] = 0
                for a in articles[:max_per_source]:
                    unified = self._convert_rss(a)
                    all_articles.append(unified)
            else:
                self._consecutive_failures["rss"] = \
                    self._consecutive_failures.get("rss", 0) + 1
        
        # Deduplicate
        deduplicated = self._deduplicate(all_articles)
        
        # Sort by date (newest first)
        deduplicated.sort(key=lambda a: a.published_at, reverse=True)
        
        # Store
        for article in deduplicated:
            self._article_store[article.article_id] = article
        
        return deduplicated
    
    def start_monitoring(self, 
                         callback: Callable[[UnifiedArticle], None],
                         interval: int = 300,
                         query: str = None,
                         financial_only: bool = True):
        """
        Start continuous news monitoring.
        
        Args:
            callback: Function called for each new article
            interval: Seconds between polls
            query: Search query
            financial_only: Only financial news
        """
        self._monitoring = True
        
        def _monitor_loop():
            backoff_multiplier = 1.0
            while self._monitoring:
                try:
                    articles = self.fetch_latest(
                        query=query,
                        hours_back=1,
                        financial_only=financial_only,
                    )
                    
                    for article in articles:
                        if article.content_hash not in self._seen_hashes:
                            self._seen_hashes.add(article.content_hash)
                            callback(article)
                    
                    backoff_multiplier = 1.0  # Reset on success
                
                except Exception as e:
                    print(f"[Monitor] Error: {e}")
                    backoff_multiplier = min(10.0, backoff_multiplier * 1.5)
                
                effective_interval = interval * backoff_multiplier
                time.sleep(effective_interval)
        
        self._monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
        self._monitor_thread.start()
        print(f"[Aggregator] Monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self._monitoring = False
        print("[Aggregator] Monitoring stopped")
    
    def get_article(self, article_id: str) -> Optional[UnifiedArticle]:
        """Retrieve a stored article by ID."""
        return self._article_store.get(article_id)
    
    # ========================================================================
    # CONVERSION METHODS
    # ========================================================================
    
    def _convert_newsapi(self, article: NewsArticle) -> UnifiedArticle:
        """Convert NewsAPI article to unified format."""
        return UnifiedArticle(
            article_id="",
            title=article.title,
            content=article.content,
            summary=article.description,
            source=article.source_name,
            source_type="newsapi",
            url=article.url,
            published_at=article.published_at,
            language=article.language,
            author=article.author,
        )
    
    def _convert_gdelt(self, article: GDELTArticle) -> UnifiedArticle:
        """Convert GDELT article to unified format."""
        return UnifiedArticle(
            article_id="",
            title=article.title,
            content=article.title,  # GDELT often only has titles
            summary=article.title,
            source=article.source,
            source_type="gdelt",
            url=article.url,
            published_at=article.published_at,
            language=article.language,
            tone=article.tone,
            entities=article.persons + article.organizations,
            categories=article.themes[:5],
        )
    
    def _convert_rss(self, article: RSSArticle) -> UnifiedArticle:
        """Convert RSS article to unified format."""
        return UnifiedArticle(
            article_id="",
            title=article.title,
            content=article.content,
            summary=article.summary,
            source=article.source_name,
            source_type="rss",
            url=article.link,
            published_at=article.published_at,
            author=article.author,
            categories=article.categories,
        )
    
    # ========================================================================
    # DEDUPLICATION
    # ========================================================================
    
    def _deduplicate(self, articles: List[UnifiedArticle]) -> List[UnifiedArticle]:
        """Remove duplicate articles using content hash and title similarity."""
        seen_hashes = set()
        seen_titles = {}
        unique = []
        
        for article in articles:
            # Skip exact content duplicates
            if article.content_hash in seen_hashes:
                continue
            
            # Check title similarity (simple word overlap)
            title_words = set(article.title.lower().split())
            is_duplicate = False
            
            for seen_title, seen_id in seen_titles.items():
                seen_words = set(seen_title.split())
                if len(title_words) > 3 and len(seen_words) > 3:
                    overlap = len(title_words & seen_words) / min(len(title_words), len(seen_words))
                    if overlap > 0.7:  # 70% word overlap = likely duplicate
                        article.duplicate_of = seen_id
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                seen_hashes.add(article.content_hash)
                seen_titles[article.title.lower()] = article.article_id
                unique.append(article)
        
        return unique
    
    # ========================================================================
    # ASYNC SUPPORT
    # ========================================================================

    async def async_fetch_latest(
        self,
        query: str = None,
        hours_back: int = 24,
        max_per_source: int = 30,
        financial_only: bool = True,
    ) -> List[UnifiedArticle]:
        """
        Async-aware version of fetch_latest.

        Runs each source fetch in a thread pool so callers in an
        asyncio event loop are not blocked.

        Usage:
            articles = await aggregator.async_fetch_latest()
        """
        loop = asyncio.get_running_loop()

        source_fetchers = []
        if "newsapi" in self.sources:
            source_fetchers.append(("newsapi", self._fetch_newsapi, query, hours_back, max_per_source, financial_only))
        if "gdelt" in self.sources:
            source_fetchers.append(("gdelt", self._fetch_gdelt, query, hours_back, max_per_source, financial_only))
        if "rss" in self.sources:
            source_fetchers.append(("rss", self._fetch_rss, query, hours_back, max_per_source, financial_only))

        all_articles: List[UnifiedArticle] = []

        with ThreadPoolExecutor(max_workers=len(source_fetchers) or 1) as pool:
            futures = []
            for name, fetcher, *args in source_fetchers:
                futures.append(loop.run_in_executor(pool, fetcher, *args))

            results = await asyncio.gather(*futures, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    print(f"[Aggregator:async] source error: {result}")
                    continue
                if isinstance(result, list):
                    all_articles.extend(result)

        deduplicated = self._deduplicate(all_articles)
        deduplicated.sort(key=lambda a: a.published_at, reverse=True)

        for article in deduplicated:
            self._article_store[article.article_id] = article

        return deduplicated

    # -- Per-source fetch helpers (synchronous, run in thread pool) ----------

    def _fetch_newsapi(self, query, hours_back, max_per_source, financial_only):
        """Fetch from NewsAPI (thread-safe helper)."""
        client: NewsAPIClient = self.sources["newsapi"]
        articles = []
        if query:
            articles = client.search_everything(
                query=query,
                from_date=datetime.now() - timedelta(hours=hours_back),
                page_size=max_per_source,
            )
        elif financial_only:
            articles = client.search_financial_news(hours_back=hours_back)
        else:
            articles = client.get_top_headlines(page_size=max_per_source)
        return [self._convert_newsapi(a) for a in articles]

    def _fetch_gdelt(self, query, hours_back, max_per_source, financial_only):
        """Fetch from GDELT (thread-safe helper)."""
        client: GDELTClient = self.sources["gdelt"]
        articles = []
        if query:
            articles = client.search_articles(
                query=query, timespan=f"{hours_back}h", max_records=max_per_source,
            )
        elif financial_only:
            articles = client.search_financial_news(
                hours_back=hours_back, max_records=max_per_source,
            )
        else:
            articles = client.search_articles(
                query="economy OR market",
                timespan=f"{hours_back}h",
                max_records=max_per_source,
            )
        return [self._convert_gdelt(a) for a in articles]

    def _fetch_rss(self, query, hours_back, max_per_source, financial_only):
        """Fetch from RSS (thread-safe helper)."""
        reader: RSSReader = self.sources["rss"]
        articles = reader.read_all_financial()
        return [self._convert_rss(a) for a in articles[:max_per_source]]

    def get_status(self) -> Dict:
        """Get aggregator status."""
        source_status = {}
        for name, source in self.sources.items():
            source_status[name] = source.get_status()
        
        return {
            "sources": source_status,
            "total_articles_stored": len(self._article_store),
            "unique_hashes": len(self._seen_hashes),
            "monitoring_active": self._monitoring,
        }
