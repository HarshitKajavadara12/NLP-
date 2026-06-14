"""
RSS READER — RSS/Atom feed reader for custom news sources

Reads RSS/Atom feeds from any source:
- Central bank press releases
- Financial news outlets
- Government publications
- Economic data calendars
"""

import re
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class RSSArticle:
    """Article from RSS feed."""
    article_id: str
    title: str
    summary: str
    content: str
    link: str
    source_feed: str
    source_name: str
    author: str
    published_at: datetime
    categories: List[str] = field(default_factory=list)
    content_hash: str = ""
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                (self.title + self.content).encode()
            ).hexdigest()[:16]


# Pre-configured financial RSS feeds
FINANCIAL_FEEDS = {
    # Central Banks
    "fed_press": "https://www.federalreserve.gov/feeds/press_all.xml",
    "ecb_press": "https://www.ecb.europa.eu/rss/press.html",
    
    # Major Outlets
    "reuters_business": "https://feeds.reuters.com/reuters/businessNews",
    "reuters_markets": "https://feeds.reuters.com/reuters/marketsNews",
    "bbc_business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "cnbc_top": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "ft_markets": "https://www.ft.com/markets?format=rss",
    "wsj_markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "bloomberg_markets": "https://feeds.bloomberg.com/markets/news.rss",
    
    # Economic Data
    "bls_releases": "https://www.bls.gov/feed/bls_latest.rss",
    
    # Crypto
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    
    # General
    "ap_top": "https://rsshub.app/apnews/topics/apf-topnews",
}


class RSSReader:
    """
    RSS/Atom feed reader for financial news.
    
    Features:
    - Pre-configured financial feeds
    - Custom feed support
    - Automatic deduplication
    - HTML content stripping
    - Date parsing
    """
    
    def __init__(self, custom_feeds: Dict[str, str] = None):
        """
        Initialize RSS reader.
        
        Args:
            custom_feeds: Dict of {name: url} for additional feeds
        """
        self.feeds = dict(FINANCIAL_FEEDS)
        if custom_feeds:
            self.feeds.update(custom_feeds)
        
        self._seen_hashes: set = set()
        self._read_count = 0
        
        if not FEEDPARSER_AVAILABLE:
            print("[RSS] 'feedparser' not installed. pip install feedparser")
    
    def read_feed(self, feed_url: str, source_name: str = "") -> List[RSSArticle]:
        """
        Read articles from a single RSS feed.
        
        Args:
            feed_url: URL of the RSS/Atom feed
            source_name: Human-readable name for the source
        """
        if not FEEDPARSER_AVAILABLE:
            return []
        
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and not feed.entries:
                print(f"[RSS] Failed to parse: {feed_url}")
                return []
            
            articles = []
            feed_title = feed.feed.get("title", source_name or feed_url)
            
            for entry in feed.entries:
                try:
                    article = self._parse_entry(entry, feed_url, feed_title)
                    if article and article.content_hash not in self._seen_hashes:
                        self._seen_hashes.add(article.content_hash)
                        articles.append(article)
                        self._read_count += 1
                except Exception:
                    continue
            
            return articles
        
        except Exception as e:
            print(f"[RSS] Error reading {feed_url}: {e}")
            return []
    
    def read_all_financial(self) -> List[RSSArticle]:
        """Read all preconfigured financial feeds."""
        all_articles = []
        
        for name, url in self.feeds.items():
            articles = self.read_feed(url, name)
            all_articles.extend(articles)
        
        # Sort by date (newest first)
        all_articles.sort(key=lambda a: a.published_at, reverse=True)
        return all_articles
    
    def read_selected(self, feed_names: List[str]) -> List[RSSArticle]:
        """Read specific named feeds."""
        all_articles = []
        
        for name in feed_names:
            if name in self.feeds:
                articles = self.read_feed(self.feeds[name], name)
                all_articles.extend(articles)
        
        all_articles.sort(key=lambda a: a.published_at, reverse=True)
        return all_articles
    
    def add_feed(self, name: str, url: str):
        """Add a custom feed."""
        self.feeds[name] = url
    
    def _parse_entry(self, entry, feed_url: str, feed_title: str) -> Optional[RSSArticle]:
        """Parse a single feed entry into RSSArticle."""
        title = entry.get("title", "")
        if not title:
            return None
        
        # Get content (try multiple fields)
        content = ""
        if "content" in entry and entry["content"]:
            content = entry["content"][0].get("value", "")
        elif "summary" in entry:
            content = entry.get("summary", "")
        elif "description" in entry:
            content = entry.get("description", "")
        
        # Strip HTML
        content = self._strip_html(content)
        summary = self._strip_html(entry.get("summary", ""))
        
        # Parse date
        published = None
        for date_field in ["published_parsed", "updated_parsed", "created_parsed"]:
            parsed = entry.get(date_field)
            if parsed:
                try:
                    published = datetime(*parsed[:6])
                    break
                except (TypeError, ValueError):
                    pass
        
        if not published:
            published = datetime.now()
        
        # Categories
        categories = []
        for tag in entry.get("tags", []):
            if isinstance(tag, dict):
                categories.append(tag.get("term", ""))
            elif isinstance(tag, str):
                categories.append(tag)
        
        return RSSArticle(
            article_id=entry.get("id", entry.get("link", "")),
            title=title,
            summary=summary[:500],
            content=content if content else summary,
            link=entry.get("link", ""),
            source_feed=feed_url,
            source_name=feed_title,
            author=entry.get("author", ""),
            published_at=published,
            categories=categories,
        )
    
    @staticmethod
    def _strip_html(html: str) -> str:
        """Remove HTML tags from text."""
        if not html:
            return ""
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        # Decode common HTML entities
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
        return text
    
    def get_status(self) -> Dict:
        """Get reader status."""
        return {
            "feeds_configured": len(self.feeds),
            "feed_names": list(self.feeds.keys()),
            "articles_read": self._read_count,
            "unique_hashes": len(self._seen_hashes),
            "feedparser_available": FEEDPARSER_AVAILABLE,
        }
