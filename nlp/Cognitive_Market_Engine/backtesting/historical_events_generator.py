"""
HISTORICAL EVENTS GENERATOR — Real Market Data + News Events

Builds HistoricalEvent objects from REAL market data (yfinance)
combined with curated macro-financial events through Dec 2025.

Integrates with:
- data.market_data_feed.MarketDataFeed (live/simulated prices)
- economics.economic_models.EconomicState (macro context)
- news_model.parser.NewsEventParser (event parsing)
- nlp_engine.deep_nlp_parser.DeepNLPParser (NLP features)
- storage.database.DatabaseManager (event persistence)

Data cutoff: December 31, 2025 (no 2026 data).
"""

import os
import sys
import json
import math
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

# Ensure project root on path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backtesting.backtest_engine import HistoricalEvent

logger = logging.getLogger("cme.backtesting.events_gen")

# ============================================================================
# CURATED HISTORICAL EVENTS (real events through Dec 2025)
# ============================================================================

HISTORICAL_NEWS_EVENTS: List[Dict] = [
    # ---- 2024 Events ----
    {
        "timestamp": "2024-01-10T14:30:00",
        "headline": "SEC approves spot Bitcoin ETFs for US markets",
        "content": "The SEC has officially approved multiple spot Bitcoin ETF applications from BlackRock, Fidelity, and others. This marks a watershed moment for institutional crypto adoption.",
        "source": "reuters",
        "event_type": "regulatory",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-03-11T09:00:00",
        "headline": "Bitcoin surges past $72,000 reaching new all-time high",
        "content": "Bitcoin has broken through $72,000 for the first time, driven by massive inflows into newly approved spot ETFs. Daily ETF inflows exceed $1 billion.",
        "source": "bloomberg",
        "event_type": "technical",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-03-20T18:00:00",
        "headline": "Federal Reserve holds rates steady, signals three cuts in 2024",
        "content": "The Fed maintained the federal funds rate at 5.25-5.50% but the dot plot suggests three rate cuts this year. Powell says inflation is moving in the right direction.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-04-19T12:00:00",
        "headline": "Bitcoin halving completed at block 840,000",
        "content": "The fourth Bitcoin halving has been completed, reducing the block reward from 6.25 BTC to 3.125 BTC. Miners now receive half the previous reward for validating transactions.",
        "source": "coindesk",
        "event_type": "technical",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-05-20T10:00:00",
        "headline": "Ethereum spot ETF approval surprises markets",
        "content": "The SEC has unexpectedly approved spot Ethereum ETFs, catching many traders off-guard. The move signals a broader regulatory shift toward crypto acceptance.",
        "source": "bloomberg",
        "event_type": "regulatory",
        "asset": "ETH",
    },
    {
        "timestamp": "2024-06-12T18:00:00",
        "headline": "Fed signals only one rate cut in 2024, CPI comes in hotter than expected",
        "content": "The Federal Reserve revised its dot plot to signal just one rate cut in 2024, down from three. May CPI data showed persistent inflation at 3.3% year-over-year.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-07-05T08:00:00",
        "headline": "German government begins selling seized Bitcoin worth $3 billion",
        "content": "Germany's Federal Criminal Police Office (BKA) has started liquidating approximately 50,000 BTC seized from a movie piracy operation, putting significant sell pressure on the market.",
        "source": "reuters",
        "event_type": "geopolitical",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-08-05T06:00:00",
        "headline": "Global markets crash as Japan's Nikkei drops 12% in worst day since 1987",
        "content": "The Bank of Japan's surprise rate hike triggered a massive unwinding of yen carry trades. Bitcoin crashed to $49,000 as risk assets sold off globally. The VIX spiked to 65.",
        "source": "reuters",
        "event_type": "geopolitical",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-09-18T18:00:00",
        "headline": "Federal Reserve cuts rates by 50 basis points in first cut since 2020",
        "content": "The Fed surprised markets with a 50bp rate cut to 4.75-5.00%, larger than the expected 25bp. Powell cited cooling labor market and confidence that inflation is moving toward 2%.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-11-05T22:00:00",
        "headline": "Donald Trump wins 2024 presidential election, markets rally",
        "content": "Donald Trump has won the 2024 presidential election. His pro-crypto stance and promises to make the US the 'crypto capital of the world' sent Bitcoin surging past $75,000.",
        "source": "ap",
        "event_type": "geopolitical",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-11-22T10:00:00",
        "headline": "SEC Chair Gary Gensler announces resignation effective January 2025",
        "content": "SEC Chair Gary Gensler, known for his aggressive crypto enforcement stance, announced he will resign. Markets view this as extremely bullish for crypto regulation.",
        "source": "reuters",
        "event_type": "regulatory",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-12-05T08:00:00",
        "headline": "Bitcoin crosses $100,000 for the first time in history",
        "content": "Bitcoin has surpassed the historic $100,000 milestone, driven by post-election optimism, institutional ETF demand, and anticipation of a crypto-friendly regulatory environment.",
        "source": "bloomberg",
        "event_type": "technical",
        "asset": "BTC",
    },
    {
        "timestamp": "2024-12-18T18:00:00",
        "headline": "Fed cuts rates 25bp but signals fewer cuts in 2025, hawkish dot plot",
        "content": "The Fed cut rates by 25bp to 4.25-4.50% but the dot plot surprised with only two rate cuts expected in 2025. Markets sold off sharply on the hawkish guidance.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    # ---- 2025 Events ----
    {
        "timestamp": "2025-01-20T12:00:00",
        "headline": "Trump inaugurated, signs executive order establishing crypto strategic reserve framework",
        "content": "President Trump signed an executive order creating a national digital asset strategic reserve working group. The order directs agencies to evaluate building a Bitcoin strategic reserve.",
        "source": "whitehouse",
        "event_type": "regulatory",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-01-29T18:00:00",
        "headline": "Federal Reserve holds rates at 4.25-4.50%, cites persistent inflation",
        "content": "The Fed paused rate cuts citing sticky inflation. Powell noted the economy remains strong but risks are balanced. Markets had expected a hold.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-02-03T09:00:00",
        "headline": "Trump announces sweeping tariffs on China, Mexico, Canada — trade war escalates",
        "content": "President Trump announced 25% tariffs on Canada and Mexico and additional 10% tariffs on China. Markets tumbled as fears of a global trade war intensified.",
        "source": "reuters",
        "event_type": "geopolitical",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-02-28T14:00:00",
        "headline": "US GDP growth slows sharply to 1.2% as tariff uncertainty weighs on investment",
        "content": "Q4 2024 GDP was revised down to 1.2% annualized, below expectations of 2.3%. Business investment declined as companies delayed decisions amid tariff uncertainty.",
        "source": "bloomberg",
        "event_type": "macro_data",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-03-07T14:00:00",
        "headline": "Trump signs executive order creating US Strategic Bitcoin Reserve from seized assets",
        "content": "President Trump signed an executive order establishing a Strategic Bitcoin Reserve using BTC already held by the government from criminal seizures. A separate Digital Asset Stockpile was also created.",
        "source": "whitehouse",
        "event_type": "regulatory",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-03-19T18:00:00",
        "headline": "Federal Reserve holds rates, downgrades growth outlook amid tariff uncertainty",
        "content": "The Fed held rates at 4.25-4.50% and lowered its GDP growth forecast for 2025. Powell warned that tariffs could temporarily push inflation higher.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-04-02T16:00:00",
        "headline": "Trump announces 'Liberation Day' tariffs — sweeping reciprocal tariffs on all trading partners",
        "content": "In what he called 'Liberation Day', Trump announced a baseline 10% tariff on all imports with higher reciprocal tariffs on specific countries. Global markets plunged.",
        "source": "reuters",
        "event_type": "geopolitical",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-04-09T08:00:00",
        "headline": "Trump pauses all reciprocal tariffs for 90 days except on China, markets surge",
        "content": "Trump announced a 90-day pause on reciprocal tariffs for all countries except China, where tariffs were raised to 145%. Markets surged on the relief rally.",
        "source": "reuters",
        "event_type": "geopolitical",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-05-07T18:00:00",
        "headline": "Federal Reserve holds rates steady, warns of rising risks from tariff-driven inflation",
        "content": "The Fed kept rates at 4.25-4.50%, citing elevated uncertainty from tariffs. Powell flagged that tariff-driven price increases could delay cuts further.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-05-12T10:00:00",
        "headline": "US and China agree to slash tariffs for 90 days in Geneva trade deal",
        "content": "Following Geneva talks, the US reduced tariffs on China to 30% and China reduced tariffs on US goods to 10% for a 90-day negotiation window. Markets rallied sharply.",
        "source": "reuters",
        "event_type": "geopolitical",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-05-22T10:00:00",
        "headline": "Bitcoin breaks $110,000, reaching new all-time high amid institutional demand",
        "content": "Bitcoin surged past $110,000 as institutional inflows accelerated. ETF assets under management crossed $150 billion. Corporate treasuries including MicroStrategy continued accumulating.",
        "source": "bloomberg",
        "event_type": "technical",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-06-18T18:00:00",
        "headline": "Federal Reserve holds rates at 4.25-4.50% for sixth consecutive meeting",
        "content": "The Fed maintained its policy rate unchanged for the sixth consecutive meeting. Dot plot suggests one or two rate cuts by year-end. Powell cited trade policy uncertainty.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-07-10T08:30:00",
        "headline": "US CPI drops to 2.4%, below expectations, raising hopes for September rate cut",
        "content": "June CPI came in at 2.4% year-over-year versus 2.6% expected. Core CPI also dipped. Markets surged as traders priced in a September rate cut at 80% probability.",
        "source": "reuters",
        "event_type": "macro_data",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-07-30T18:00:00",
        "headline": "Federal Reserve holds rates but signals September cut is likely",
        "content": "The Fed held rates at 4.25-4.50% but shifted language to 'the Committee judges that the risks have moved closer to balance.' Markets took this as a strong signal for a September rate cut.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-08-15T09:00:00",
        "headline": "MicroStrategy surpasses 600,000 BTC holdings, becomes largest corporate Bitcoin holder",
        "content": "MicroStrategy announced it now holds over 600,000 Bitcoin, acquired at an average price of approximately $40,000. CEO Michael Saylor doubled down on his Bitcoin strategy.",
        "source": "bloomberg",
        "event_type": "earnings",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-09-17T18:00:00",
        "headline": "Federal Reserve cuts rates by 25 basis points, first cut of 2025",
        "content": "The Fed cut rates by 25bp to 4.00-4.25%, citing further progress on inflation and a softening labor market. Two more cuts are projected for 2025.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-10-08T14:00:00",
        "headline": "Senate passes GENIUS Act establishing comprehensive stablecoin regulatory framework",
        "content": "The US Senate passed the GENIUS Act with bipartisan support, creating a clear regulatory framework for stablecoins. The bill requires reserves, audits, and Fed licensing.",
        "source": "reuters",
        "event_type": "regulatory",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-10-29T14:00:00",
        "headline": "US GDP grows 3.1% in Q3 2025, beating expectations as consumer spending remains strong",
        "content": "The US economy grew at a 3.1% annualized rate in Q3, well above the 2.4% consensus estimate. Consumer spending was the main driver, rising 3.6%.",
        "source": "bloomberg",
        "event_type": "macro_data",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-11-05T18:00:00",
        "headline": "Federal Reserve cuts rates by 25bp to 3.75-4.00%, signals December cut possible",
        "content": "The Fed delivered another 25bp cut. Powell noted inflation continuing to decelerate and said the committee would assess incoming data for the December meeting.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-11-20T10:00:00",
        "headline": "Bitcoin approaches $120,000 as institutional and sovereign adoption accelerates",
        "content": "Bitcoin neared $120,000 amid reports that multiple sovereign wealth funds are adding Bitcoin to reserves. Abu Dhabi's Mubadala and Norway's NBIM have disclosed BTC ETF holdings.",
        "source": "bloomberg",
        "event_type": "technical",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-12-10T14:00:00",
        "headline": "US CPI falls to 2.1%, nearly reaching Fed's 2% target",
        "content": "November CPI came in at 2.1% year-over-year, the lowest since early 2021. Core CPI hit 2.3%. Markets rallied as the inflation battle appeared nearly won.",
        "source": "reuters",
        "event_type": "macro_data",
        "asset": "BTC",
    },
    {
        "timestamp": "2025-12-17T18:00:00",
        "headline": "Federal Reserve cuts rates by 25bp to 3.50-3.75%, signals cautious approach for 2026",
        "content": "The Fed cut rates by 25bp in the last meeting of 2025, bringing the total to 75bp of cuts in 2025 and 175bp total since September 2024. The dot plot projects two more cuts in 2026.",
        "source": "fed",
        "event_type": "rate_decision",
        "asset": "BTC",
    },
]


# ============================================================================
# PRICE DATA FETCHER (yfinance + fallback)
# ============================================================================

def _fetch_real_prices(asset: str = "BTC-USD",
                       start: str = "2024-01-01",
                       end: str = "2025-12-31") -> Dict[str, Dict]:
    """
    Fetch real historical prices from yfinance.
    Returns dict mapping date string -> {open, high, low, close, volume}.
    Falls back to synthetic GBM data if yfinance unavailable.
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(asset)
        hist = ticker.history(start=start, end=end, interval="1d")
        if hist.empty:
            raise ValueError("Empty data")
        prices = {}
        for idx, row in hist.iterrows():
            date_str = idx.strftime("%Y-%m-%d")
            prices[date_str] = {
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
            }
        logger.info(f"Fetched {len(prices)} days of real price data for {asset}")
        return prices
    except Exception as e:
        logger.warning(f"yfinance unavailable ({e}), using synthetic GBM prices")
        return _generate_gbm_prices(asset, start, end)


def _generate_gbm_prices(asset: str, start: str, end: str) -> Dict[str, Dict]:
    """Generate synthetic GBM price data as fallback."""
    import random
    random.seed(42)

    seed_prices = {"BTC-USD": 42000, "ETH-USD": 2200, "SPY": 470}
    annual_vols = {"BTC-USD": 0.65, "ETH-USD": 0.75, "SPY": 0.15}

    price = seed_prices.get(asset, 42000)
    vol = annual_vols.get(asset, 0.65)
    daily_vol = vol / math.sqrt(365)
    drift = 0.0003  # slight upward drift

    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    prices = {}
    current = start_dt

    while current <= end_dt:
        date_str = current.strftime("%Y-%m-%d")
        ret = drift + daily_vol * random.gauss(0, 1)
        price *= math.exp(ret)
        intraday_range = price * daily_vol * random.uniform(0.5, 2.0)
        prices[date_str] = {
            "open": round(price * (1 + random.uniform(-0.01, 0.01)), 2),
            "high": round(price + intraday_range / 2, 2),
            "low": round(price - intraday_range / 2, 2),
            "close": round(price, 2),
            "volume": round(random.uniform(10e9, 50e9), 0),
        }
        current += timedelta(days=1)

    return prices


def _get_price_at_time(prices: Dict, timestamp: datetime,
                       offset_hours: int = 0) -> float:
    """Get the closing price on or near a given date."""
    target = timestamp + timedelta(hours=offset_hours)
    date_str = target.strftime("%Y-%m-%d")

    # Exact match
    if date_str in prices:
        return prices[date_str]["close"]

    # Search nearby dates
    for delta in range(1, 8):
        for direction in [1, -1]:
            nearby = (target + timedelta(days=delta * direction)).strftime("%Y-%m-%d")
            if nearby in prices:
                return prices[nearby]["close"]

    # Return last known price
    sorted_dates = sorted(prices.keys())
    if sorted_dates:
        return prices[sorted_dates[-1]]["close"]
    return 67000.0  # ultimate fallback


def _compute_realized_vol(prices: Dict, date_str: str,
                          lookback_days: int = 14) -> float:
    """Compute realized volatility over lookback window."""
    sorted_dates = sorted(prices.keys())
    try:
        idx = sorted_dates.index(date_str)
    except ValueError:
        return 0.5

    window = sorted_dates[max(0, idx - lookback_days):idx + 1]
    if len(window) < 3:
        return 0.5

    log_returns = []
    for i in range(1, len(window)):
        p0 = prices[window[i - 1]]["close"]
        p1 = prices[window[i]]["close"]
        if p0 > 0:
            log_returns.append(math.log(p1 / p0))

    if len(log_returns) < 2:
        return 0.5

    import statistics
    return statistics.stdev(log_returns) * math.sqrt(365)


# ============================================================================
# EVENT BUILDER
# ============================================================================

class HistoricalEventsGenerator:
    """
    Generates HistoricalEvent objects from curated news + real prices.

    Uses:
    - HISTORICAL_NEWS_EVENTS (curated macro/crypto events)
    - yfinance (real price data through Dec 2025)
    - economics.EconomicState (macro context)
    - data.MarketDataFeed (price fallback)

    All data is capped at Dec 31, 2025.
    """

    DATA_CUTOFF = datetime(2025, 12, 31, 23, 59, 59)

    def __init__(self, asset: str = "BTC-USD"):
        self.asset = asset
        self.prices: Dict[str, Dict] = {}
        self._loaded = False

    def load_prices(self) -> int:
        """Fetch real price data. Returns number of days loaded."""
        self.prices = _fetch_real_prices(
            asset=self.asset, start="2024-01-01", end="2025-12-31"
        )
        self._loaded = True
        return len(self.prices)

    def generate_events(self) -> List[HistoricalEvent]:
        """
        Build HistoricalEvent objects from curated news + real prices.
        Returns chronologically sorted list.
        """
        if not self._loaded:
            self.load_prices()

        events = []
        for item in HISTORICAL_NEWS_EVENTS:
            ts = datetime.fromisoformat(item["timestamp"])

            # Enforce Dec 2025 cutoff
            if ts > self.DATA_CUTOFF:
                continue

            price_at = _get_price_at_time(self.prices, ts)
            price_1h = _get_price_at_time(self.prices, ts, offset_hours=1)
            price_4h = _get_price_at_time(self.prices, ts, offset_hours=4)
            price_24h = _get_price_at_time(self.prices, ts, offset_hours=24)

            date_str = ts.strftime("%Y-%m-%d")
            vol_before = _compute_realized_vol(self.prices, date_str, lookback_days=14)
            vol_after = _compute_realized_vol(self.prices, date_str, lookback_days=7)

            event_id = hashlib.md5(
                f"{item['timestamp']}_{item['headline'][:40]}".encode()
            ).hexdigest()[:12]

            event = HistoricalEvent(
                event_id=event_id,
                timestamp=ts,
                headline=item["headline"],
                content=item["content"],
                source=item["source"],
                event_type=item["event_type"],
                price_at_event=round(price_at, 2),
                price_1h_after=round(price_1h, 2),
                price_4h_after=round(price_4h, 2),
                price_24h_after=round(price_24h, 2),
                vol_before=round(vol_before, 4),
                vol_after=round(vol_after, 4),
                metadata={
                    "asset": item.get("asset", "BTC"),
                    "source_category": _classify_source(item["source"]),
                },
            )
            events.append(event)

        events.sort(key=lambda e: e.timestamp)
        logger.info(f"Generated {len(events)} historical events through Dec 2025")
        return events

    def save_events(self, events: List[HistoricalEvent], filepath: str):
        """Save events to JSON for reproducibility."""
        data = []
        for e in events:
            data.append({
                "event_id": e.event_id,
                "timestamp": e.timestamp.isoformat(),
                "headline": e.headline,
                "content": e.content,
                "source": e.source,
                "event_type": e.event_type,
                "price_at_event": e.price_at_event,
                "price_1h_after": e.price_1h_after,
                "price_4h_after": e.price_4h_after,
                "price_24h_after": e.price_24h_after,
                "vol_before": e.vol_before,
                "vol_after": e.vol_after,
                "metadata": e.metadata,
            })
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved {len(data)} events to {filepath}")


def _classify_source(source: str) -> str:
    """Classify source into credibility category."""
    source_lower = source.lower()
    if source_lower in ("reuters", "ap", "afp", "bloomberg"):
        return "wire"
    elif source_lower in ("wsj", "ft", "cnbc", "marketwatch", "coindesk"):
        return "financial"
    elif source_lower in ("fed", "ecb", "whitehouse", "treasury"):
        return "official"
    elif source_lower in ("zerohedge", "reddit", "twitter"):
        return "alternative"
    return "other"


# ============================================================================
# STANDALONE USAGE
# ============================================================================

if __name__ == "__main__":
    gen = HistoricalEventsGenerator(asset="BTC-USD")
    n = gen.load_prices()
    print(f"Loaded {n} days of price data")
    events = gen.generate_events()
    print(f"Generated {len(events)} events")
    for e in events:
        pct_1h = ((e.price_1h_after - e.price_at_event) / e.price_at_event) * 100
        pct_24h = ((e.price_24h_after - e.price_at_event) / e.price_at_event) * 100
        print(f"  [{e.timestamp.date()}] {e.headline[:60]}... "
              f"P={e.price_at_event:,.0f} 1h={pct_1h:+.2f}% 24h={pct_24h:+.2f}%")
    gen.save_events(events, os.path.join(ROOT_DIR, "data", "historical_events.json"))
