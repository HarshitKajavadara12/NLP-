"""
Structural Alpha Engine — 5 Structural Alpha Gaps
===================================================
Implements: Contrarian Signal Generation, Mean Reversion Framework,
Momentum Framework, Cross-Event Memory, Market Microstructure Alpha.
"""
import time
import math
import logging
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import deque

logger = logging.getLogger("cme.structural_alpha")


# ─────────────────────────────────────────────────────────────
# Shared
# ─────────────────────────────────────────────────────────────

@dataclass
class StructuralSignal:
    """Output of a structural alpha model."""
    source: str
    direction: str   # "bullish", "bearish", "neutral"
    strength: float  # 0–1
    confidence: float
    asset: str
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


# ─────────────────────────────────────────────────────────────
# 1. Contrarian Signal Generator
# ─────────────────────────────────────────────────────────────

class ContrarianSignalGenerator:
    """
    Generates 'fade the consensus' signals when crowd sentiment
    reaches extremes.  Integrates NLP consensus detection from
    hidden_truth module with quantitative positioning data to
    identify when the majority is likely wrong.

    Methodology:
    - Consensus strength (how aligned are analysts/media)
    - Positioning extremes (how crowded is the trade)
    - Valuation divergence (price vs fundamentals)
    - Timing (historical success rate of contrarian bets at these levels)
    """

    def __init__(self, lookback: int = 100):
        self._consensus_history: List[Dict] = []
        self._contrarian_hit_rate: float = 0.55  # baseline
        self._lookback = lookback
        self._min_consensus_trigger = 0.80  # 80% agreement = trigger

    def record_consensus(self, data: Dict[str, Any]) -> None:
        """Record a consensus reading.
        data: {timestamp, asset, consensus_direction, consensus_strength,
               analyst_agreement, media_agreement, positioning_zscore, price}
        """
        data.setdefault("timestamp", time.time())
        self._consensus_history.append(data)
        if len(self._consensus_history) > self._lookback * 5:
            self._consensus_history = self._consensus_history[-self._lookback * 5:]

    def _compute_consensus_extremity(self, data: Dict) -> float:
        """How extreme is the current consensus? 0=no consensus, 1=unanimity."""
        strength = data.get("consensus_strength", 0.5)
        analyst = data.get("analyst_agreement", 0.5)
        media = data.get("media_agreement", 0.5)

        # Weighted composite
        extremity = 0.4 * strength + 0.35 * analyst + 0.25 * media
        return extremity

    def _check_positioning_confirmation(self, data: Dict) -> bool:
        """Positioning data confirms the consensus extreme."""
        zscore = data.get("positioning_zscore", 0)
        direction = data.get("consensus_direction", "neutral")

        if direction == "bullish" and zscore > 1.5:
            return True  # Extremely long and consensus bullish
        if direction == "bearish" and zscore < -1.5:
            return True  # Extremely short and consensus bearish
        return False

    def _valuation_divergence(self, data: Dict) -> float:
        """How far has price deviated from fundamental value?"""
        price = data.get("price", 0)
        fair_value = data.get("fair_value", 0)
        if fair_value <= 0 or price <= 0:
            return 0
        return (price - fair_value) / fair_value

    def generate_contrarian_signal(self, data: Dict) -> Optional[StructuralSignal]:
        """Generate contrarian signal when consensus is extreme."""
        self.record_consensus(data)
        extremity = self._compute_consensus_extremity(data)

        if extremity < self._min_consensus_trigger:
            return None  # Not extreme enough for contrarian bet

        positioning_confirms = self._check_positioning_confirmation(data)
        val_div = self._valuation_divergence(data)

        consensus_dir = data.get("consensus_direction", "neutral")
        contrarian_dir = "bearish" if consensus_dir == "bullish" else "bullish"

        # Confidence factors
        conf_positioning = 0.25 if positioning_confirms else 0.0
        conf_extremity = (extremity - 0.8) * 2.5  # 0-0.5
        conf_valuation = min(0.25, abs(val_div) * 2) if (
            (consensus_dir == "bullish" and val_div > 0.1) or
            (consensus_dir == "bearish" and val_div < -0.1)
        ) else 0.0

        total_conf = 0.3 + conf_positioning + conf_extremity + conf_valuation

        parts = [
            f"Consensus {consensus_dir} at {extremity:.0%} extremity",
        ]
        if positioning_confirms:
            parts.append("Positioning data confirms crowding")
        if abs(val_div) > 0.1:
            parts.append(f"Valuation divergence {val_div:+.1%}")

        return StructuralSignal(
            source="contrarian",
            direction=contrarian_dir,
            strength=min(1.0, extremity * 0.6 + (0.3 if positioning_confirms else 0)),
            confidence=min(0.85, total_conf),
            asset=data.get("asset", "unknown"),
            reasoning="; ".join(parts),
            metadata={"extremity": extremity, "positioning_confirms": positioning_confirms,
                      "valuation_divergence": val_div, "consensus_direction": consensus_dir},
        )


# ─────────────────────────────────────────────────────────────
# 2. Mean Reversion Framework
# ─────────────────────────────────────────────────────────────

class MeanReversionFramework:
    """
    Detects mean-reversion opportunities using:
    - Z-score vs rolling mean
    - Bollinger Band extremes
    - RSI overbought/oversold
    - Price deviation from VWAP
    - Half-life estimation for reversion speed

    Produces 'revert' signals when assets are statistically
    stretched beyond sustainable levels.
    """

    def __init__(self, lookback: int = 60, zscore_threshold: float = 2.0):
        self._lookback = lookback
        self._zscore_threshold = zscore_threshold
        self._price_history: Dict[str, deque] = {}
        self._volume_history: Dict[str, deque] = {}

    def update_price(self, asset: str, price: float, volume: float = 0) -> None:
        if asset not in self._price_history:
            self._price_history[asset] = deque(maxlen=self._lookback * 3)
            self._volume_history[asset] = deque(maxlen=self._lookback * 3)
        self._price_history[asset].append(price)
        self._volume_history[asset].append(volume)

    def compute_zscore(self, asset: str) -> Optional[float]:
        prices = list(self._price_history.get(asset, []))
        if len(prices) < self._lookback:
            return None
        window = prices[-self._lookback:]
        mu = statistics.mean(window)
        sigma = statistics.stdev(window) if len(window) > 1 else 1
        if sigma == 0:
            return 0
        return (prices[-1] - mu) / sigma

    def compute_bollinger(self, asset: str, period: int = 20, num_std: float = 2.0) -> Optional[Dict]:
        prices = list(self._price_history.get(asset, []))
        if len(prices) < period:
            return None
        window = prices[-period:]
        mu = statistics.mean(window)
        sigma = statistics.stdev(window) if len(window) > 1 else 1
        upper = mu + num_std * sigma
        lower = mu - num_std * sigma
        current = prices[-1]
        pct_b = (current - lower) / (upper - lower) if upper != lower else 0.5
        return {
            "upper": upper, "middle": mu, "lower": lower,
            "pct_b": pct_b, "bandwidth": (upper - lower) / mu if mu > 0 else 0,
        }

    def compute_rsi(self, asset: str, period: int = 14) -> Optional[float]:
        prices = list(self._price_history.get(asset, []))
        if len(prices) < period + 1:
            return None
        changes = [prices[i] - prices[i - 1] for i in range(len(prices) - period, len(prices))]
        gains = [c for c in changes if c > 0]
        losses = [abs(c) for c in changes if c < 0]
        avg_gain = statistics.mean(gains) if gains else 0
        avg_loss = statistics.mean(losses) if losses else 0.001
        rs = avg_gain / avg_loss
        return 100 - 100 / (1 + rs)

    def estimate_halflife(self, asset: str) -> Optional[float]:
        """Estimate mean-reversion half-life using OLS on lag-1 regression."""
        prices = list(self._price_history.get(asset, []))
        if len(prices) < 30:
            return None
        log_prices = [math.log(p) for p in prices if p > 0]
        if len(log_prices) < 30:
            return None
        y = [log_prices[i] - log_prices[i - 1] for i in range(1, len(log_prices))]
        x = log_prices[:-1]
        n = len(y)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
        var_x = statistics.variance(x)
        if var_x == 0:
            return None
        beta = cov / var_x
        if beta >= 0:
            return None  # Not mean-reverting
        halflife = -math.log(2) / beta
        return halflife

    def generate_signal(self, asset: str) -> Optional[StructuralSignal]:
        zscore = self.compute_zscore(asset)
        if zscore is None:
            return None

        bb = self.compute_bollinger(asset)
        rsi = self.compute_rsi(asset)
        halflife = self.estimate_halflife(asset)

        direction = "neutral"
        strength = 0.0
        parts = []

        # Z-score signal
        if abs(zscore) > self._zscore_threshold:
            direction = "bullish" if zscore < 0 else "bearish"
            strength = min(1.0, (abs(zscore) - 1.5) / 2)
            parts.append(f"Z-score {zscore:+.2f} (threshold ±{self._zscore_threshold})")

        # Bollinger confirmation
        if bb:
            if bb["pct_b"] > 1.0:
                parts.append(f"Above upper Bollinger (%B={bb['pct_b']:.2f})")
                if direction == "neutral":
                    direction = "bearish"
                    strength = 0.4
            elif bb["pct_b"] < 0.0:
                parts.append(f"Below lower Bollinger (%B={bb['pct_b']:.2f})")
                if direction == "neutral":
                    direction = "bullish"
                    strength = 0.4

        # RSI confirmation
        if rsi is not None:
            if rsi > 75:
                parts.append(f"RSI overbought ({rsi:.0f})")
                if direction != "bullish":
                    strength = min(1.0, strength + 0.2)
            elif rsi < 25:
                parts.append(f"RSI oversold ({rsi:.0f})")
                if direction != "bearish":
                    strength = min(1.0, strength + 0.2)

        # Half-life context
        if halflife is not None:
            parts.append(f"Estimated reversion half-life: {halflife:.1f} periods")

        if not parts:
            return None

        confidence = 0.5
        confirmations = 0
        if abs(zscore) > self._zscore_threshold:
            confirmations += 1
        if bb and (bb["pct_b"] > 1 or bb["pct_b"] < 0):
            confirmations += 1
        if rsi and (rsi > 75 or rsi < 25):
            confirmations += 1
        confidence = min(0.9, 0.4 + confirmations * 0.15)

        return StructuralSignal(
            source="mean_reversion",
            direction=direction,
            strength=strength,
            confidence=confidence,
            asset=asset,
            reasoning="; ".join(parts),
            metadata={"zscore": zscore, "bollinger": bb, "rsi": rsi,
                      "halflife": halflife, "confirmations": confirmations},
        )


# ─────────────────────────────────────────────────────────────
# 3. Momentum Framework
# ─────────────────────────────────────────────────────────────

class MomentumFramework:
    """
    Trend-following signal generation from price data.
    Implements:
    - Dual moving average crossover
    - Rate of change (ROC)
    - ADX (Average Directional Index) for trend strength
    - Breakout detection (Donchian channels)
    - Time-series momentum (autocorrelation)
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 50):
        self._fast = fast_period
        self._slow = slow_period
        self._price_history: Dict[str, deque] = {}
        self._high_history: Dict[str, deque] = {}
        self._low_history: Dict[str, deque] = {}

    def update_price(self, asset: str, price: float,
                     high: float = 0, low: float = 0) -> None:
        if asset not in self._price_history:
            self._price_history[asset] = deque(maxlen=self._slow * 5)
            self._high_history[asset] = deque(maxlen=self._slow * 5)
            self._low_history[asset] = deque(maxlen=self._slow * 5)
        self._price_history[asset].append(price)
        self._high_history[asset].append(high if high > 0 else price)
        self._low_history[asset].append(low if low > 0 else price)

    def _ema(self, data: List[float], period: int) -> List[float]:
        if not data:
            return []
        k = 2 / (period + 1)
        ema = [data[0]]
        for i in range(1, len(data)):
            ema.append(data[i] * k + ema[-1] * (1 - k))
        return ema

    def ma_crossover(self, asset: str) -> Optional[Dict]:
        """Dual MA crossover signal."""
        prices = list(self._price_history.get(asset, []))
        if len(prices) < self._slow + 5:
            return None
        fast_ma = self._ema(prices, self._fast)
        slow_ma = self._ema(prices, self._slow)

        current_fast = fast_ma[-1]
        current_slow = slow_ma[-1]
        prev_fast = fast_ma[-2]
        prev_slow = slow_ma[-2]

        crossover = "none"
        if prev_fast <= prev_slow and current_fast > current_slow:
            crossover = "golden"  # bullish
        elif prev_fast >= prev_slow and current_fast < current_slow:
            crossover = "death"  # bearish

        spread = (current_fast - current_slow) / current_slow if current_slow > 0 else 0

        return {"crossover": crossover, "spread": spread,
                "fast_ma": current_fast, "slow_ma": current_slow}

    def rate_of_change(self, asset: str, periods: List[int] = None) -> Dict[str, float]:
        """Multi-period rate of change."""
        if periods is None:
            periods = [5, 10, 20, 60]
        prices = list(self._price_history.get(asset, []))
        rocs = {}
        for p in periods:
            if len(prices) > p:
                roc = (prices[-1] - prices[-p - 1]) / prices[-p - 1] if prices[-p - 1] != 0 else 0
                rocs[f"roc_{p}"] = roc
        return rocs

    def compute_adx(self, asset: str, period: int = 14) -> Optional[Dict]:
        """Average Directional Index for trend strength."""
        highs = list(self._high_history.get(asset, []))
        lows = list(self._low_history.get(asset, []))
        closes = list(self._price_history.get(asset, []))
        if len(closes) < period * 2:
            return None

        # True Range + Directional Movement
        tr_list = []
        plus_dm = []
        minus_dm = []
        for i in range(1, len(closes)):
            h = highs[i]
            l = lows[i]
            prev_c = closes[i - 1]
            prev_h = highs[i - 1]
            prev_l = lows[i - 1]
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            tr_list.append(tr)

            up = h - prev_h
            down = prev_l - l
            plus_dm.append(up if up > down and up > 0 else 0)
            minus_dm.append(down if down > up and down > 0 else 0)

        if len(tr_list) < period:
            return None

        # Smoothed averages
        atr = self._ema(tr_list[-period * 3:], period)[-1]
        smooth_plus = self._ema(plus_dm[-period * 3:], period)[-1]
        smooth_minus = self._ema(minus_dm[-period * 3:], period)[-1]

        if atr == 0:
            return None

        plus_di = (smooth_plus / atr) * 100
        minus_di = (smooth_minus / atr) * 100
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        adx = dx  # simplified — single period

        return {
            "adx": adx,
            "plus_di": plus_di,
            "minus_di": minus_di,
            "trend_strength": ("strong" if adx > 25 else "moderate" if adx > 15 else "weak"),
            "trend_direction": "bullish" if plus_di > minus_di else "bearish",
        }

    def donchian_breakout(self, asset: str, period: int = 20) -> Optional[Dict]:
        """Donchian channel breakout detection."""
        highs = list(self._high_history.get(asset, []))
        lows = list(self._low_history.get(asset, []))
        closes = list(self._price_history.get(asset, []))
        if len(closes) < period + 1:
            return None

        upper = max(highs[-period - 1:-1])
        lower = min(lows[-period - 1:-1])
        current = closes[-1]

        breakout = "none"
        if current > upper:
            breakout = "upside"
        elif current < lower:
            breakout = "downside"

        return {
            "upper": upper,
            "lower": lower,
            "current": current,
            "breakout": breakout,
            "channel_width_pct": (upper - lower) / lower if lower > 0 else 0,
        }

    def time_series_momentum(self, asset: str, lookback: int = 20) -> Optional[float]:
        """Autocorrelation-based time-series momentum."""
        prices = list(self._price_history.get(asset, []))
        if len(prices) < lookback + 5:
            return None
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1]
                   for i in range(len(prices) - lookback, len(prices))
                   if prices[i - 1] != 0]
        if len(returns) < 5:
            return None
        # Sign of cumulative return = TSM signal
        cum_return = sum(returns)
        return cum_return

    def generate_signal(self, asset: str) -> Optional[StructuralSignal]:
        ma = self.ma_crossover(asset)
        rocs = self.rate_of_change(asset)
        adx = self.compute_adx(asset)
        breakout = self.donchian_breakout(asset)
        tsm = self.time_series_momentum(asset)

        direction = "neutral"
        strength = 0.0
        parts = []

        # MA crossover
        if ma:
            if ma["crossover"] == "golden":
                direction = "bullish"
                strength += 0.4
                parts.append("Golden cross (fast MA > slow MA)")
            elif ma["crossover"] == "death":
                direction = "bearish"
                strength += 0.4
                parts.append("Death cross (fast MA < slow MA)")
            elif ma["spread"] > 0.02:
                direction = "bullish"
                strength += 0.2
                parts.append(f"Bullish MA spread ({ma['spread']:+.2%})")
            elif ma["spread"] < -0.02:
                direction = "bearish"
                strength += 0.2
                parts.append(f"Bearish MA spread ({ma['spread']:+.2%})")

        # ADX trend strength
        if adx and adx["adx"] > 20:
            if adx["trend_direction"] == direction or direction == "neutral":
                direction = adx["trend_direction"]
                strength += 0.2
                parts.append(f"ADX={adx['adx']:.0f} ({adx['trend_strength']} {adx['trend_direction']})")

        # Breakout
        if breakout and breakout["breakout"] != "none":
            bd = "bullish" if breakout["breakout"] == "upside" else "bearish"
            if direction == "neutral" or direction == bd:
                direction = bd
                strength += 0.3
                parts.append(f"Donchian {breakout['breakout']} breakout")

        # ROC
        if "roc_20" in rocs:
            roc20 = rocs["roc_20"]
            if abs(roc20) > 0.05:
                parts.append(f"ROC(20) = {roc20:+.1%}")

        # TSM
        if tsm is not None and abs(tsm) > 0.03:
            tsm_dir = "bullish" if tsm > 0 else "bearish"
            parts.append(f"TSM = {tsm:+.2%} ({tsm_dir})")

        if not parts:
            return None

        return StructuralSignal(
            source="momentum",
            direction=direction,
            strength=min(1.0, strength),
            confidence=min(0.85, 0.4 + (0.1 if ma else 0) + (0.15 if adx else 0) + (0.1 if breakout else 0)),
            asset=asset,
            reasoning="; ".join(parts),
            metadata={"ma": ma, "rocs": rocs, "adx": adx, "breakout": breakout, "tsm": tsm},
        )


# ─────────────────────────────────────────────────────────────
# 4. Cross-Event Memory
# ─────────────────────────────────────────────────────────────

class CrossEventMemory:
    """
    Maintains memory across news events to detect accumulation patterns:
    - "This is the 3rd hawkish Fed signal in 2 weeks"
    - "Insider buying cluster: 4 filings in 5 days"
    - "Third consecutive miss on employment data"
    
    Enables pattern recognition that single-event processing cannot achieve.
    """

    def __init__(self, memory_days: int = 90):
        self._memory_days = memory_days
        self._events: List[Dict] = []
        self._pattern_counts: Dict[str, List[Dict]] = {}  # category → events
        self._streaks: Dict[str, Dict] = {}  # asset → current streak info

    def record_event(self, event: Dict[str, Any]) -> None:
        """Record a market event.
        event: {timestamp, category, direction, asset, magnitude, source, description}
        """
        event.setdefault("timestamp", time.time())
        self._events.append(event)

        # Index by category
        cat = event.get("category", "unknown")
        if cat not in self._pattern_counts:
            self._pattern_counts[cat] = []
        self._pattern_counts[cat].append(event)

        # Update streak
        asset = event.get("asset", "all")
        direction = event.get("direction", "neutral")
        if asset not in self._streaks:
            self._streaks[asset] = {"direction": direction, "count": 1, "events": [event]}
        else:
            if self._streaks[asset]["direction"] == direction:
                self._streaks[asset]["count"] += 1
                self._streaks[asset]["events"].append(event)
            else:
                self._streaks[asset] = {"direction": direction, "count": 1, "events": [event]}

        # Prune old events
        cutoff = time.time() - self._memory_days * 86400
        self._events = [e for e in self._events if e.get("timestamp", 0) > cutoff]
        for cat_key in self._pattern_counts:
            self._pattern_counts[cat_key] = [
                e for e in self._pattern_counts[cat_key]
                if e.get("timestamp", 0) > cutoff
            ]

    def count_recent(self, category: str, days: int = 14) -> int:
        """Count events of a category in the last N days."""
        cutoff = time.time() - days * 86400
        return sum(1 for e in self._pattern_counts.get(category, [])
                   if e.get("timestamp", 0) > cutoff)

    def detect_accumulation(self, category: str, threshold: int = 3,
                            window_days: int = 14) -> Optional[Dict]:
        """Detect accumulation patterns in a category."""
        count = self.count_recent(category, window_days)
        if count < threshold:
            return None

        events = [e for e in self._pattern_counts.get(category, [])
                  if e.get("timestamp", 0) > time.time() - window_days * 86400]

        directions = [e.get("direction", "neutral") for e in events]
        bull = directions.count("bullish")
        bear = directions.count("bearish")
        dominant = "bullish" if bull > bear else "bearish" if bear > bull else "mixed"

        magnitudes = [e.get("magnitude", 0) for e in events]
        avg_magnitude = statistics.mean(magnitudes) if magnitudes else 0

        # Acceleration check — are events happening faster?
        if len(events) >= 3:
            gaps = []
            sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
            for i in range(1, len(sorted_events)):
                gap = sorted_events[i]["timestamp"] - sorted_events[i - 1]["timestamp"]
                gaps.append(gap)
            if len(gaps) >= 2:
                recent_gap = statistics.mean(gaps[-2:])
                early_gap = statistics.mean(gaps[:2]) if len(gaps) >= 4 else gaps[0]
                accelerating = recent_gap < early_gap * 0.7
            else:
                accelerating = False
        else:
            accelerating = False

        return {
            "category": category,
            "count": count,
            "window_days": window_days,
            "dominant_direction": dominant,
            "bullish_count": bull,
            "bearish_count": bear,
            "avg_magnitude": avg_magnitude,
            "accelerating": accelerating,
        }

    def get_streak(self, asset: str) -> Dict:
        """Get current event streak for an asset."""
        return self._streaks.get(asset, {"direction": "neutral", "count": 0, "events": []})

    def detect_all_patterns(self, threshold: int = 3, window_days: int = 14) -> List[Dict]:
        """Scan all categories for accumulation patterns."""
        patterns = []
        for cat in self._pattern_counts:
            p = self.detect_accumulation(cat, threshold, window_days)
            if p:
                patterns.append(p)
        return sorted(patterns, key=lambda x: x["count"], reverse=True)

    def generate_signal(self, asset: str) -> Optional[StructuralSignal]:
        streak = self.get_streak(asset)
        patterns = self.detect_all_patterns()

        if streak["count"] < 3 and not patterns:
            return None

        parts = []
        direction = "neutral"
        strength = 0.0

        if streak["count"] >= 3:
            direction = streak["direction"]
            strength = min(1.0, streak["count"] * 0.15)
            parts.append(
                f"Event streak: {streak['count']} consecutive {streak['direction']} events"
            )

        for p in patterns[:3]:
            parts.append(
                f"Accumulation: {p['count']}× {p['category']} in {p['window_days']}d "
                f"({p['dominant_direction']}"
                f"{', accelerating' if p['accelerating'] else ''})"
            )
            if direction == "neutral":
                direction = p["dominant_direction"] if p["dominant_direction"] != "mixed" else "neutral"
                strength = min(1.0, p["count"] * 0.1)

        if not parts:
            return None

        return StructuralSignal(
            source="cross_event_memory",
            direction=direction,
            strength=strength,
            confidence=min(0.8, 0.3 + streak["count"] * 0.05 + len(patterns) * 0.1),
            asset=asset,
            reasoning="; ".join(parts),
            metadata={"streak": {"direction": streak["direction"], "count": streak["count"]},
                      "pattern_count": len(patterns)},
        )


# ─────────────────────────────────────────────────────────────
# 5. Market Microstructure Alpha
# ─────────────────────────────────────────────────────────────

class MicrostructureAlpha:
    """
    Trading logic based on market microstructure:
    - Spread capture (earning the bid-ask spread as a passive market maker)
    - Queue priority estimation
    - Adverse selection measurement (toxic vs non-toxic flow)
    - PIN (Probability of Informed Trading)
    - Kyle's Lambda estimation (price impact per unit flow)
    """

    def __init__(self):
        self._trade_data: Dict[str, List[Dict]] = {}
        self._book_snapshots: Dict[str, List[Dict]] = {}

    def process_trade(self, asset: str, trade: Dict) -> None:
        """trade: {timestamp, price, size, side, venue}"""
        if asset not in self._trade_data:
            self._trade_data[asset] = []
        self._trade_data[asset].append(trade)
        if len(self._trade_data[asset]) > 50000:
            self._trade_data[asset] = self._trade_data[asset][-50000:]

    def process_book_snapshot(self, asset: str, snapshot: Dict) -> None:
        """snapshot: {timestamp, best_bid, best_ask, bid_size, ask_size, depth_5_bid, depth_5_ask}"""
        if asset not in self._book_snapshots:
            self._book_snapshots[asset] = []
        self._book_snapshots[asset].append(snapshot)
        if len(self._book_snapshots[asset]) > 10000:
            self._book_snapshots[asset] = self._book_snapshots[asset][-10000:]

    def estimate_spread_opportunity(self, asset: str) -> Dict[str, float]:
        """Estimate bid-ask spread capture opportunity."""
        snaps = self._book_snapshots.get(asset, [])
        if len(snaps) < 10:
            return {"avg_spread_bps": 0, "spread_vol": 0, "capture_potential": 0}

        spreads = []
        for s in snaps[-100:]:
            bid = s.get("best_bid", 0)
            ask = s.get("best_ask", 0)
            if bid > 0 and ask > bid:
                mid = (bid + ask) / 2
                spread_bps = (ask - bid) / mid * 10000
                spreads.append(spread_bps)

        if not spreads:
            return {"avg_spread_bps": 0, "spread_vol": 0, "capture_potential": 0}

        avg = statistics.mean(spreads)
        vol = statistics.stdev(spreads) if len(spreads) > 1 else 0

        # Capture potential = avg spread minus estimated adverse selection
        adverse = self.estimate_adverse_selection(asset)
        capture = max(0, avg - adverse.get("adverse_selection_bps", 0))

        return {
            "avg_spread_bps": avg,
            "spread_vol": vol,
            "capture_potential_bps": capture,
            "profitability": "viable" if capture > 1.0 else "marginal" if capture > 0.3 else "unprofitable",
        }

    def estimate_adverse_selection(self, asset: str) -> Dict[str, float]:
        """Estimate adverse selection cost using realized spread decomposition."""
        trades = self._trade_data.get(asset, [])
        if len(trades) < 50:
            return {"adverse_selection_bps": 0, "toxicity": 0}

        # Simplified: measure how often price moves against the maker post-trade
        adverse_moves = 0
        total_evaluated = 0
        for i in range(len(trades) - 5):
            side = trades[i].get("side", "buy")
            price_at_trade = trades[i].get("price", 0)
            price_after = trades[i + 5].get("price", 0)
            if price_at_trade > 0:
                total_evaluated += 1
                if side == "buy" and price_after > price_at_trade:
                    adverse_moves += 1  # Buyer was informed — price went up
                elif side == "sell" and price_after < price_at_trade:
                    adverse_moves += 1  # Seller was informed — price went down

        toxicity = adverse_moves / max(total_evaluated, 1)
        return {
            "adverse_selection_bps": toxicity * 10,  # rough estimate
            "toxicity": toxicity,
            "trades_evaluated": total_evaluated,
        }

    def estimate_pin(self, asset: str) -> Dict[str, float]:
        """Estimate Probability of Informed Trading (simplified Easley-O'Hara)."""
        trades = self._trade_data.get(asset, [])
        if len(trades) < 100:
            return {"pin": 0, "alpha": 0, "mu": 0}

        buys = sum(1 for t in trades if t.get("side") == "buy")
        sells = sum(1 for t in trades if t.get("side") == "sell")
        total = buys + sells

        # Simplified PIN: imbalance as proxy
        epsilon_b = buys / max(total, 1)  # uninformed buy rate
        epsilon_s = sells / max(total, 1)  # uninformed sell rate
        imbalance = abs(buys - sells) / max(total, 1)

        # PIN ≈ α*μ / (α*μ + 2*ε) where α=prob of information event, μ=informed trade rate
        alpha = min(0.5, imbalance * 2)  # heuristic
        mu = abs(buys - sells)
        epsilon = min(buys, sells)
        pin = (alpha * mu) / (alpha * mu + 2 * epsilon) if (alpha * mu + 2 * epsilon) > 0 else 0

        return {
            "pin": pin,
            "alpha": alpha,
            "mu": mu,
            "epsilon": epsilon,
            "informed_ratio": "high" if pin > 0.3 else "moderate" if pin > 0.15 else "low",
        }

    def estimate_kyle_lambda(self, asset: str) -> Optional[float]:
        """Estimate Kyle's Lambda (permanent price impact per unit flow)."""
        trades = self._trade_data.get(asset, [])
        if len(trades) < 100:
            return None

        # Regress price change on signed volume
        price_changes = []
        signed_volumes = []
        for i in range(1, len(trades)):
            dp = trades[i]["price"] - trades[i - 1]["price"]
            sv = trades[i]["size"] * (1 if trades[i].get("side") == "buy" else -1)
            price_changes.append(dp)
            signed_volumes.append(sv)

        n = len(price_changes)
        if n < 20:
            return None

        mean_dp = statistics.mean(price_changes)
        mean_sv = statistics.mean(signed_volumes)
        cov = sum((price_changes[i] - mean_dp) * (signed_volumes[i] - mean_sv) for i in range(n)) / n
        var_sv = statistics.variance(signed_volumes) if len(signed_volumes) > 1 else 1
        if var_sv == 0:
            return None

        return cov / var_sv  # Kyle's Lambda

    def generate_signal(self, asset: str) -> StructuralSignal:
        spread = self.estimate_spread_opportunity(asset)
        adverse = self.estimate_adverse_selection(asset)
        pin = self.estimate_pin(asset)
        kyle = self.estimate_kyle_lambda(asset)

        parts = []
        if spread["avg_spread_bps"] > 0:
            parts.append(f"Spread {spread['avg_spread_bps']:.1f}bps, "
                         f"capture potential {spread.get('capture_potential_bps', 0):.1f}bps "
                         f"({spread.get('profitability', 'unknown')})")
        if adverse["toxicity"] > 0:
            parts.append(f"Flow toxicity {adverse['toxicity']:.1%}")
        if pin["pin"] > 0:
            parts.append(f"PIN={pin['pin']:.2f} ({pin['informed_ratio']})")
        if kyle is not None:
            parts.append(f"Kyle's λ={kyle:.6f}")

        # High toxicity → avoid, low toxicity → safe to make markets
        direction = "neutral"
        strength = 0.0
        if adverse["toxicity"] > 0.6:
            direction = "bearish"
            strength = 0.5
            parts.append("WARNING: High toxic flow — likely informed selling")
        elif adverse["toxicity"] < 0.35 and spread.get("capture_potential_bps", 0) > 1.0:
            parts.append("Favorable microstructure for spread capture")

        return StructuralSignal(
            source="microstructure",
            direction=direction,
            strength=strength,
            confidence=0.6,
            asset=asset,
            reasoning="; ".join(parts) if parts else "Insufficient microstructure data",
            metadata={"spread": spread, "adverse_selection": adverse,
                      "pin": pin, "kyle_lambda": kyle},
        )


# ─────────────────────────────────────────────────────────────
# Unified Structural Alpha Engine
# ─────────────────────────────────────────────────────────────

class StructuralAlphaEngine:
    """Orchestrates all 5 structural alpha models."""

    def __init__(self):
        self.contrarian = ContrarianSignalGenerator()
        self.mean_reversion = MeanReversionFramework()
        self.momentum = MomentumFramework()
        self.event_memory = CrossEventMemory()
        self.microstructure = MicrostructureAlpha()

    def scan_all(self, asset: str) -> List[StructuralSignal]:
        """Run all structural alpha models for an asset."""
        signals = []

        mr_sig = self.mean_reversion.generate_signal(asset)
        if mr_sig:
            signals.append(mr_sig)

        mom_sig = self.momentum.generate_signal(asset)
        if mom_sig:
            signals.append(mom_sig)

        mem_sig = self.event_memory.generate_signal(asset)
        if mem_sig:
            signals.append(mem_sig)

        micro_sig = self.microstructure.generate_signal(asset)
        if micro_sig:
            signals.append(micro_sig)

        return signals

    def detect_conflicts(self, signals: List[StructuralSignal]) -> Dict[str, Any]:
        """Detect conflicting signals (e.g., momentum bullish vs mean-reversion bearish)."""
        if len(signals) < 2:
            return {"conflicts": [], "aligned": True}

        conflicts = []
        for i in range(len(signals)):
            for j in range(i + 1, len(signals)):
                if (signals[i].direction != "neutral" and
                        signals[j].direction != "neutral" and
                        signals[i].direction != signals[j].direction):
                    conflicts.append({
                        "signal_a": signals[i].source,
                        "direction_a": signals[i].direction,
                        "signal_b": signals[j].source,
                        "direction_b": signals[j].direction,
                    })
        return {"conflicts": conflicts, "aligned": len(conflicts) == 0}
