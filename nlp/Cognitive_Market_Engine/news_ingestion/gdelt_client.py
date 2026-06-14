"""
GDELT CLIENT — Global Database of Events, Language, and Tone

GDELT monitors news media in 100+ languages from every country.
FREE, no API key required.

Data includes:
- Events (who did what to whom, when, where)
- Global Knowledge Graph (entities, themes, tone)
- Document metadata (source, language, tone)
"""

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
class GDELTEvent:
    """A GDELT event record."""
    event_id: str
    date: datetime
    actor1: str
    actor1_country: str
    actor2: str
    actor2_country: str
    event_code: str
    event_description: str
    num_mentions: int
    num_sources: int
    avg_tone: float  # -100 to +100
    goldstein_scale: float  # -10 to +10 (conflict to cooperation)
    source_url: str = ""
    
    @property
    def is_conflict(self) -> bool:
        return self.goldstein_scale < -5
    
    @property
    def is_cooperation(self) -> bool:
        return self.goldstein_scale > 5


@dataclass
class GDELTArticle:
    """A GDELT document/article record."""
    url: str
    title: str
    source: str
    source_country: str
    language: str
    tone: float
    themes: List[str] = field(default_factory=list)
    persons: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    published_at: datetime = field(default_factory=datetime.now)


class GDELTClient:
    """
    Client for GDELT Project APIs.
    
    Endpoints:
    - DOC API: Search articles by keyword, theme, geography
    - GEO API: Geographic search for events
    - TV API: TV news mentions
    
    No API key required. Rate limited by politeness.
    """
    
    DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
    GEO_API_URL = "https://api.gdeltproject.org/api/v2/geo/geo"
    TV_API_URL = "https://api.gdeltproject.org/api/v2/tv/tv"
    
    # GDELT Event codes (CAMEO)
    EVENT_CODES = {
        "01": "Make public statement",
        "02": "Appeal",
        "03": "Express intent to cooperate",
        "04": "Consult",
        "05": "Engage in diplomatic cooperation",
        "06": "Engage in material cooperation",
        "07": "Provide aid",
        "08": "Yield",
        "09": "Investigate",
        "10": "Demand",
        "11": "Disapprove",
        "12": "Reject",
        "13": "Threaten",
        "14": "Protest",
        "15": "Exhibit military posture",
        "16": "Reduce relations",
        "17": "Coerce",
        "18": "Assault",
        "19": "Fight",
        "20": "Engage in unconventional mass violence",
    }
    
    # Themes relevant to markets
    MARKET_THEMES = [
        "ECON_INTEREST_RATE", "ECON_INFLATION", "ECON_DEBT",
        "ECON_TRADE", "ECON_SANCTIONS", "ECON_BANKRUPTCY",
        "ECON_COST_OF_LIVING", "ECON_UNEMPLOYMENT",
        "ECON_CURRENCY", "ECON_STOCKMARKET", "ECON_OIL",
        "ECON_RECESSION", "ECON_GDP", "ECON_STIMULUS",
        "CRISISLEX_CRISISLEXREC", "WB_FINANCIAL_SECTOR",
    ]
    
    def __init__(self):
        """Initialize GDELT client."""
        self._cache: Dict[str, Dict] = {}
        self._request_count = 0
    
    def search_articles(self,
                        query: str,
                        mode: str = "artlist",
                        timespan: str = "24h",
                        max_records: int = 50,
                        source_country: str = None,
                        source_lang: str = "english",
                        theme: str = None,
                        sort: str = "DateDesc") -> List[GDELTArticle]:
        """
        Search GDELT for articles.
        
        Args:
            query: Search terms
            mode: artlist (article list) or timeline
            timespan: Time window (15min, 1h, 24h, 7d, etc.)
            max_records: Maximum articles to return
            source_country: Filter by source country
            source_lang: Filter by language
            theme: GDELT theme filter
            sort: DateDesc, DateAsc, ToneDesc, ToneAsc
        """
        params = {
            "query": query,
            "mode": mode,
            "format": "json",
            "timespan": timespan,
            "maxrecords": str(max_records),
            "sort": sort,
        }
        
        if source_country:
            params["sourcecountry"] = source_country
        if source_lang:
            params["sourcelang"] = source_lang
        if theme:
            params["theme"] = theme
        
        data = self._request(self.DOC_API_URL, params)
        return self._parse_articles(data)
    
    def search_financial_news(self, 
                               hours_back: int = 24,
                               max_records: int = 50) -> List[GDELTArticle]:
        """
        Search specifically for financial/economic news.
        
        Uses GDELT themes to filter for market-relevant content.
        """
        # Build theme query
        theme_query = " OR ".join(f'theme:{t}' for t in self.MARKET_THEMES[:5])
        
        timespan = f"{hours_back}h" if hours_back <= 72 else f"{hours_back // 24}d"
        
        return self.search_articles(
            query=theme_query,
            timespan=timespan,
            max_records=max_records,
            sort="ToneDesc",
        )
    
    def search_geopolitical(self,
                            country: str = None,
                            query: str = "conflict OR sanctions OR military",
                            hours_back: int = 48) -> List[GDELTArticle]:
        """Search for geopolitical events."""
        q = query
        if country:
            q = f"{query} sourcecountry:{country}"
        
        return self.search_articles(
            query=q,
            timespan=f"{hours_back}h",
            max_records=50,
            sort="DateDesc",
        )
    
    def get_tone_timeline(self, 
                          query: str,
                          timespan: str = "7d") -> Optional[Dict]:
        """
        Get tone timeline for a topic.
        
        Returns time series of average tone (sentiment).
        """
        params = {
            "query": query,
            "mode": "timelinetone",
            "format": "json",
            "timespan": timespan,
        }
        return self._request(self.DOC_API_URL, params)
    
    def get_volume_timeline(self,
                            query: str,
                            timespan: str = "7d") -> Optional[Dict]:
        """
        Get volume timeline for a topic.
        
        Returns time series of article counts.
        """
        params = {
            "query": query,
            "mode": "timelinevol",
            "format": "json",
            "timespan": timespan,
        }
        return self._request(self.DOC_API_URL, params)
    
    def _request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make API request with caching."""
        if not REQUESTS_AVAILABLE:
            print("[GDELT] 'requests' library not installed")
            return None
        
        # Cache
        cache_key = hashlib.md5(
            f"{url}_{sorted(params.items())}".encode()
        ).hexdigest()
        
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached["time"] < timedelta(minutes=10):
                return cached["data"]
        
        try:
            response = requests.get(url, params=params, timeout=15)
            self._request_count += 1
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self._cache[cache_key] = {"data": data, "time": datetime.now()}
                    return data
                except Exception:
                    # GDELT sometimes returns non-JSON
                    return {"raw": response.text}
            else:
                print(f"[GDELT] Error {response.status_code}")
        
        except requests.exceptions.Timeout:
            print("[GDELT] Request timeout")
        except Exception as e:
            print(f"[GDELT] Error: {e}")
        
        return None
    
    def _parse_articles(self, data: Optional[Dict]) -> List[GDELTArticle]:
        """Parse GDELT response into GDELTArticle objects."""
        articles = []
        if not data:
            return articles
        
        items = data.get("articles", [])
        if not items and isinstance(data, list):
            items = data
        
        for item in items:
            try:
                article = GDELTArticle(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    source=item.get("domain", item.get("source", "")),
                    source_country=item.get("sourcecountry", ""),
                    language=item.get("language", "English"),
                    tone=float(item.get("tone", 0)),
                    themes=item.get("themes", "").split(";") if isinstance(item.get("themes"), str) else [],
                    persons=item.get("persons", "").split(";") if isinstance(item.get("persons"), str) else [],
                    organizations=item.get("organizations", "").split(";") if isinstance(item.get("organizations"), str) else [],
                    locations=item.get("locations", "").split(";") if isinstance(item.get("locations"), str) else [],
                )
                articles.append(article)
            except Exception:
                continue
        
        return articles
    
    def get_status(self) -> Dict:
        """Get client status."""
        return {
            "requests_made": self._request_count,
            "cache_size": len(self._cache),
            "requires_api_key": False,
            "requests_available": REQUESTS_AVAILABLE,
        }
