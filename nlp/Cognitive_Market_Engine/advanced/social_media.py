"""
SOCIAL MEDIA SENTIMENT — Reddit + Twitter sentiment fusion.

Aggregates retail sentiment from social platforms:
- Reddit (r/wallstreetbets, r/stocks, r/investing, r/options)
- Twitter/X financial feeds
- Comment/post volume tracking
- Sentiment trend detection
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

# Graceful imports
try:
    import praw
    HAS_PRAW = True
except ImportError:
    HAS_PRAW = False

try:
    import tweepy
    HAS_TWEEPY = True
except ImportError:
    HAS_TWEEPY = False


@dataclass
class SocialPost:
    """A social media post/comment."""
    platform: str  # reddit, twitter
    text: str
    author: str = ""
    timestamp: str = ""
    score: int = 0
    sentiment: float = 0.0  # -1 to 1
    ticker_mentions: List[str] = None
    subreddit: str = ""
    url: str = ""
    
    def __post_init__(self):
        if self.ticker_mentions is None:
            self.ticker_mentions = []
    
    def to_dict(self) -> Dict:
        return {
            "platform": self.platform,
            "text": self.text[:200],
            "author": self.author,
            "timestamp": self.timestamp,
            "score": self.score,
            "sentiment": self.sentiment,
            "ticker_mentions": self.ticker_mentions,
            "subreddit": self.subreddit,
        }


class SocialMediaSentiment:
    """
    Social media sentiment aggregator for Reddit and Twitter.
    
    Features:
    - Subreddit monitoring (WSB, stocks, investing, options)
    - Twitter financial hashtag tracking
    - Ticker mention counting and trending detection
    - Simple sentiment scoring (keyword-based)
    - Volume spike detection
    """
    
    MONITORED_SUBREDDITS = [
        "wallstreetbets", "stocks", "investing", "options",
        "stockmarket", "forex", "cryptocurrency",
    ]
    
    BULLISH_WORDS = {
        "moon", "rocket", "calls", "bull", "buy", "long", "squeeze",
        "breakout", "undervalued", "diamond hands", "tendies", "yolo",
        "surge", "rally", "pump", "green", "ath", "new high",
    }
    
    BEARISH_WORDS = {
        "puts", "bear", "sell", "short", "crash", "dump", "overvalued",
        "paper hands", "rug pull", "bagholder", "red", "drill",
        "recession", "bubble", "correction", "plunge",
    }
    
    COMMON_TICKERS = {
        "SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "NVDA", "META", "AMD", "NFLX", "JPM", "BAC", "GS",
        "BTC", "ETH", "GME", "AMC", "PLTR", "SOFI",
    }
    
    def __init__(self, reddit_credentials: Dict = None,
                 twitter_credentials: Dict = None):
        """
        Args:
            reddit_credentials: {client_id, client_secret, user_agent}
            twitter_credentials: {bearer_token} or {api_key, api_secret, ...}
        """
        self.reddit = None
        self.twitter = None
        self.post_cache: List[SocialPost] = []
        self.ticker_counts: Dict[str, int] = defaultdict(int)
        self.ticker_sentiment: Dict[str, List[float]] = defaultdict(list)
        
        # Initialize Reddit
        if HAS_PRAW and reddit_credentials:
            try:
                self.reddit = praw.Reddit(
                    client_id=reddit_credentials.get("client_id", ""),
                    client_secret=reddit_credentials.get("client_secret", ""),
                    user_agent=reddit_credentials.get("user_agent",
                                                       "CognitiveMarketEngine/1.0"),
                )
                print("[SOCIAL] Reddit connected")
            except Exception as e:
                print(f"[SOCIAL] Reddit init failed: {e}")
        
        # Initialize Twitter
        if HAS_TWEEPY and twitter_credentials:
            try:
                bearer = twitter_credentials.get("bearer_token", "")
                if bearer:
                    self.twitter = tweepy.Client(bearer_token=bearer)
                    print("[SOCIAL] Twitter connected")
            except Exception as e:
                print(f"[SOCIAL] Twitter init failed: {e}")
        
        if not self.reddit and not self.twitter:
            print("[SOCIAL] No social APIs configured — using demo mode")
    
    def scan_reddit(self, subreddits: List[str] = None,
                    limit: int = 50) -> List[SocialPost]:
        """
        Scan Reddit for financial posts.
        
        Args:
            subreddits: Subreddits to scan (defaults to MONITORED_SUBREDDITS)
            limit: Posts per subreddit
            
        Returns:
            List of SocialPost objects
        """
        if not self.reddit:
            return self._demo_reddit_posts()
        
        posts = []
        subs = subreddits or self.MONITORED_SUBREDDITS
        
        for sub_name in subs:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                for submission in subreddit.hot(limit=limit):
                    text = f"{submission.title} {submission.selftext}"
                    tickers = self._extract_tickers(text)
                    sentiment = self._score_sentiment(text)
                    
                    post = SocialPost(
                        platform="reddit",
                        text=text[:500],
                        author=str(submission.author),
                        timestamp=datetime.fromtimestamp(
                            submission.created_utc
                        ).isoformat(),
                        score=submission.score,
                        sentiment=sentiment,
                        ticker_mentions=tickers,
                        subreddit=sub_name,
                        url=submission.url,
                    )
                    posts.append(post)
                    
                    # Track tickers
                    for t in tickers:
                        self.ticker_counts[t] += 1
                        self.ticker_sentiment[t].append(sentiment)
                
                time.sleep(0.5)  # Rate limit
            except Exception as e:
                print(f"[SOCIAL] Reddit error on r/{sub_name}: {e}")
        
        self.post_cache.extend(posts)
        return posts
    
    def scan_twitter(self, query: str = "stocks OR market OR trading",
                     limit: int = 50) -> List[SocialPost]:
        """Scan Twitter for financial tweets."""
        if not self.twitter:
            return []
        
        posts = []
        try:
            tweets = self.twitter.search_recent_tweets(
                query=query,
                max_results=min(limit, 100),
                tweet_fields=["created_at", "public_metrics", "author_id"],
            )
            
            if tweets.data:
                for tweet in tweets.data:
                    text = tweet.text
                    tickers = self._extract_tickers(text)
                    sentiment = self._score_sentiment(text)
                    metrics = tweet.public_metrics or {}
                    
                    post = SocialPost(
                        platform="twitter",
                        text=text,
                        author=str(tweet.author_id),
                        timestamp=tweet.created_at.isoformat() if tweet.created_at else "",
                        score=metrics.get("like_count", 0) + metrics.get("retweet_count", 0),
                        sentiment=sentiment,
                        ticker_mentions=tickers,
                    )
                    posts.append(post)
                    
                    for t in tickers:
                        self.ticker_counts[t] += 1
                        self.ticker_sentiment[t].append(sentiment)
        except Exception as e:
            print(f"[SOCIAL] Twitter error: {e}")
        
        self.post_cache.extend(posts)
        return posts
    
    def get_trending_tickers(self, top_n: int = 10) -> List[Dict]:
        """Get most mentioned tickers with sentiment."""
        trending = []
        
        for ticker, count in sorted(self.ticker_counts.items(),
                                     key=lambda x: -x[1])[:top_n]:
            sentiments = self.ticker_sentiment.get(ticker, [0])
            avg_sent = sum(sentiments) / len(sentiments)
            
            trending.append({
                "ticker": ticker,
                "mentions": count,
                "avg_sentiment": round(avg_sent, 3),
                "sentiment_label": (
                    "bullish" if avg_sent > 0.2 else
                    "bearish" if avg_sent < -0.2 else "neutral"
                ),
                "data_points": len(sentiments),
            })
        
        return trending
    
    def get_aggregate_sentiment(self) -> Dict:
        """Get overall social media sentiment."""
        if not self.post_cache:
            return {
                "overall_sentiment": 0.0,
                "label": "neutral",
                "post_count": 0,
                "platforms": {},
            }
        
        all_sentiments = [p.sentiment for p in self.post_cache]
        avg = sum(all_sentiments) / len(all_sentiments)
        
        by_platform = defaultdict(list)
        for p in self.post_cache:
            by_platform[p.platform].append(p.sentiment)
        
        platforms = {}
        for plat, sents in by_platform.items():
            platforms[plat] = {
                "avg_sentiment": round(sum(sents) / len(sents), 3),
                "count": len(sents),
            }
        
        return {
            "overall_sentiment": round(avg, 3),
            "label": (
                "bullish" if avg > 0.15 else
                "bearish" if avg < -0.15 else "neutral"
            ),
            "post_count": len(self.post_cache),
            "platforms": platforms,
            "trending_tickers": self.get_trending_tickers(5),
        }
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock ticker symbols from text."""
        import re
        tickers = []
        
        # Match $TICKER patterns
        dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
        tickers.extend(dollar_tickers)
        
        # Match known tickers
        words = set(text.upper().split())
        for ticker in self.COMMON_TICKERS:
            if ticker in words:
                tickers.append(ticker)
        
        return list(set(tickers))
    
    def _score_sentiment(self, text: str) -> float:
        """Simple keyword-based sentiment scoring."""
        text_lower = text.lower()
        
        bullish_count = sum(1 for w in self.BULLISH_WORDS if w in text_lower)
        bearish_count = sum(1 for w in self.BEARISH_WORDS if w in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0.0
        
        return (bullish_count - bearish_count) / total
    
    def _demo_reddit_posts(self) -> List[SocialPost]:
        """Generate demo posts when Reddit API is not configured."""
        demos = [
            SocialPost(
                platform="reddit", subreddit="wallstreetbets",
                text="SPY calls printing! Market looking strong 🚀",
                score=1500, sentiment=0.8, ticker_mentions=["SPY"],
                timestamp=datetime.now().isoformat(),
            ),
            SocialPost(
                platform="reddit", subreddit="stocks",
                text="NVDA earnings beat expectations. AI sector still strong.",
                score=850, sentiment=0.6, ticker_mentions=["NVDA"],
                timestamp=datetime.now().isoformat(),
            ),
            SocialPost(
                platform="reddit", subreddit="investing",
                text="Concerned about recession signals. Moving to bonds.",
                score=320, sentiment=-0.5, ticker_mentions=["TLT"],
                timestamp=datetime.now().isoformat(),
            ),
        ]
        
        for p in demos:
            for t in p.ticker_mentions:
                self.ticker_counts[t] += 1
                self.ticker_sentiment[t].append(p.sentiment)
        
        self.post_cache.extend(demos)
        return demos
