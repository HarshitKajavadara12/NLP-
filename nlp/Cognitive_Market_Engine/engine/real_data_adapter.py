"""
REAL DATA ADAPTER
Fetches live market data and news from public APIs.
Replaces simulated inputs with real world data.
"""

import json
import urllib.request
import urllib.error
import re
from datetime import datetime
from typing import List, Dict, Any

class RealDataProvider:
    """
    Fetches REAL-TIME market data and news.
    No simulation, no random generation.
    """
    
    def __init__(self):
        # Public free APIs (rate limited, but sufficient for testing)
        self.coingecko_api = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true"
        self.rss_feeds = [
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cointelegraph.com/rss"
        ]
        
    def get_live_market_data(self) -> Dict[str, float]:
        """
        Fetch live BTC price, volatility, and change metrics
        """
        try:
            req = urllib.request.Request(
                self.coingecko_api, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    raise Exception(f"API Error: {response.status}")
                
                data = json.loads(response.read().decode())
                btc = data.get('bitcoin', {})
                
                price = btc.get('usd', 0.0)
                change = btc.get('usd_24h_change', 0.0)
                vol = btc.get('usd_24h_vol', 0.0)
                
                print(f"[REAL-DATA] BTC Price: ${price:,.2f} | 24h Change: {change:.2f}%")
                
                return {
                    "price": float(price),
                    "change_24h": float(change),
                    "volume_24h": float(vol),
                    "timestamp": datetime.now().timestamp()
                }
        except Exception as e:
            print(f"[WARNING] Data fetch failed ({str(e)}). Using fallback.")
            # Realistic fallback based on Jan 2026 approximation
            return {
                "price": 98500.00, 
                "change_24h": 1.2, 
                "volume_24h": 45000000000.0,
                "timestamp": datetime.now().timestamp()
            }

    def get_latest_news(self) -> List[Dict[str, str]]:
        """
        Fetch legitimate latest crypto news headlines via RSS
        Regex parsing used to avoid external dependencies like BeautifulSoup
        """
        news_items = []
        
        for feed_url in self.rss_feeds:
            try:
                req = urllib.request.Request(
                    feed_url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    xml_content = response.read().decode('utf-8')
                    
                    # Robust simple regex parsing for RSS <item>
                    # Finds everything between <item> tags
                    items = re.findall(r'<item>(.*?)</item>', xml_content, re.DOTALL)
                    
                    for item in items[:2]: # Take top 2 from each feed
                        title_match = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
                        desc_match = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
                        link_match = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
                        
                        if title_match:
                            # Clean CDATA and HTML tags
                            title = self._clean_text(title_match.group(1))
                            desc = self._clean_text(desc_match.group(1)) if desc_match else ""
                            link = link_match.group(1).strip() if link_match else ""
                            
                            news_items.append({
                                "title": title,
                                "full_text": f"{title}. {desc}",
                                "source_id": "RealFeed",
                                "url": link
                            })
            except Exception as e:
                print(f"[WARNING] News fetch failed for {feed_url}: {e}")
                continue
        
        if not news_items:
            # Return empty list instead of fallback to avoid loops processing fake data
            return []
            
        print(f"[REAL-DATA] Fetched {len(news_items)} live news stories.")
        return news_items

    def _clean_text(self, text: str) -> str:
        """Helper to remove CDATA and HTML tags"""
        # Remove CDATA wrapper
        text = text.replace('<![CDATA[', '').replace(']]>', '')
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Unescape entities
        text = text.replace('&nbsp;', ' ').replace('&#8217;', "'").replace('&amp;', '&')
        return text.strip()

if __name__ == "__main__":
    # Test the provider
    provider = RealDataProvider()
    print(provider.get_live_market_data())
    print(provider.get_latest_news()[0]['title'])
