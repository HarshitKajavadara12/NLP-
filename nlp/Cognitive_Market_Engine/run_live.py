"""
COGNITIVE MARKET ENGINE - LIVE INTERFACE
=============================================
Connects the Cognitive Market System to Real-World Data.

Status: LIVE MODE (Real Data / No Simulation)
"""

import time
import sys
import os
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Core Engine
from engine.cognitive_market_system import CognitiveMarketSystem
# Import Structures
from engine.tradable_signal_translator import SignalType

# Try importing the new NewsAggregator first, fall back to legacy adapter
try:
    from news_ingestion.news_aggregator import NewsAggregator
    _HAS_AGGREGATOR = True
except ImportError:
    _HAS_AGGREGATOR = False

try:
    from engine.real_data_adapter import RealDataProvider
    _HAS_LEGACY = True
except ImportError:
    _HAS_LEGACY = False

# Optional: storage + feedback for full integration
try:
    from storage.database import DatabaseManager
    _HAS_STORAGE = True
except ImportError:
    _HAS_STORAGE = False

try:
    from learning.feedback_loop import FeedbackLoop
    _HAS_FEEDBACK = True
except ImportError:
    _HAS_FEEDBACK = False


def main():
    print("\n" + "="*80)
    print("COGNITIVE MARKET ENGINE - LIVE INITIALIZATION")
    print("="*80)
    
    # 0. Initialize optional integrations
    storage = None
    feedback = None
    
    if _HAS_STORAGE:
        try:
            storage = DatabaseManager()
            print("[STORAGE] Database connected")
        except Exception as e:
            print(f"[STORAGE] Database unavailable: {e}")
    
    if _HAS_FEEDBACK:
        try:
            feedback = FeedbackLoop(storage=storage)
            print("[FEEDBACK] Learning loop active")
        except Exception as e:
            print(f"[FEEDBACK] Feedback loop unavailable: {e}")
    
    # 1. Initialize data source (prefer NewsAggregator)
    data_provider = None
    news_aggregator = None
    
    if _HAS_AGGREGATOR:
        print("[SYSTEM] Connecting via NewsAggregator (multi-source)...")
        try:
            api_key = os.environ.get("NEWSAPI_KEY", "")
            news_aggregator = NewsAggregator(
                newsapi_key=api_key if api_key else None,
                enable_newsapi=bool(api_key),
                enable_gdelt=True,
                enable_rss=True,
            )
            print("[DATA] NewsAggregator ready")
        except Exception as e:
            print(f"[DATA] NewsAggregator failed: {e}")
    
    if news_aggregator is None and _HAS_LEGACY:
        print("[SYSTEM] Falling back to legacy RealDataProvider...")
        try:
            data_provider = RealDataProvider()
            market_data = data_provider.get_live_market_data()
            print(f"[DATA] Connected. BTC: ${market_data['price']:,.2f}")
        except Exception as e:
            print(f"[FATAL] No data source available: {e}")
            return
    
    if news_aggregator is None and data_provider is None:
        print("[FATAL] No data source available. Install news_ingestion or real_data_adapter.")
        return

    # 2. Initialize Cognitive System with integrations
    print("[SYSTEM] Initializing Cognitive Models...")
    engine = CognitiveMarketSystem(
        asset="BTC",
        enable_logging=True,
        storage=storage,
        feedback_loop=feedback,
    )
    
    # 3. Start Loop
    print("\n[LOOP] Starting Continuous Market Scanner (Ctrl+C to stop)...")
    processed_news_hashes = set()
    
    while True:
        try:
            news_items = []
            market_data = {"price": 0.0}
            
            # Fetch via NewsAggregator
            if news_aggregator:
                try:
                    articles = news_aggregator.fetch_latest(
                        hours_back=1, financial_only=True, max_per_source=10
                    )
                    for article in articles:
                        item_hash = article.content_hash
                        if item_hash not in processed_news_hashes:
                            news_items.append({
                                "title": article.title,
                                "full_text": article.content or article.title,
                                "source_id": article.source,
                                "url": article.url,
                            })
                            processed_news_hashes.add(item_hash)
                except Exception as e:
                    print(f"\n[WARN] Aggregator fetch error: {e}")
            
            # Fetch via legacy adapter  
            elif data_provider:
                try:
                    raw_items = data_provider.get_latest_news()
                    market_data = data_provider.get_live_market_data()
                    for item in raw_items:
                        item_hash = item.get('url') or item.get('title')
                        if item_hash not in processed_news_hashes:
                            news_items.append(item)
                            processed_news_hashes.add(item_hash)
                except Exception as e:
                    print(f"\n[WARN] Legacy fetch error: {e}")
            
            if not news_items:
                timestamp = datetime.now().strftime("%H:%M:%S")
                sys.stdout.write(f"\r[{timestamp}] Monitoring... (No new events)   ")
                sys.stdout.flush()
                time.sleep(60)
                continue
                
            for latest_news in news_items:
                print(f"\n\n{'='*80}")
                print(f">>> NEW EVENT: {latest_news['title']}")
                print(f"{'='*80}")
                
                signal = engine.process_news_event(
                    source_id=latest_news.get('source_id', 'RealFeed'),
                    raw_text=latest_news.get('full_text', latest_news.get('title', '')),
                    asset_scope=["BTC", "ETH", "CRYPTO"],
                    macro_scope=["finance", "rates"],
                )
                
                print(f"\n   SIGNAL: {signal.signal_type.value.upper()}")
                print(f"   REASON: {signal.reason}")
                
                if signal.signal_type != SignalType.NO_TRADE:
                    print(f"\n   >>> TRADE SIGNAL: {signal.direction}, "
                          f"strength={signal.strength:.2f}")

        except KeyboardInterrupt:
            print("\n\n[STOP] Monitoring stopped by user.")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
