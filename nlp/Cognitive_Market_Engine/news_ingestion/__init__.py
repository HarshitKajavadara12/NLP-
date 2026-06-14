"""
NEWS INGESTION — Real-time news feed integration

Connects to real-world news sources:
- NewsAPI (global news aggregator)
- GDELT (global event database)
- RSS feeds (custom source feeds)
- News aggregator that combines all sources with deduplication
"""

from .news_api_client import NewsAPIClient
from .gdelt_client import GDELTClient
from .rss_reader import RSSReader
from .news_aggregator import NewsAggregator

__all__ = [
    "NewsAPIClient",
    "GDELTClient",
    "RSSReader",
    "NewsAggregator",
]
