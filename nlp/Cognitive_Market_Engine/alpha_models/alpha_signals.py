"""
Alpha Signal Models — 12 Alpha-Generating Concepts
====================================================
Implements: Positioning Data, Order Flow Analysis, Volatility Surface,
Cross-Asset Lead-Lag, Sentiment Extremes, Flow-of-Funds, Calendar Effects,
Earnings Estimate Revisions, Insider Trading, Credit Market Signals,
Macro Surprise Indices, Central Bank Balance Sheet.
"""
import time
import math
import logging
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger("cme.alpha_signals")


# ─────────────────────────────────────────────────────────────
# Shared Data Structures
# ─────────────────────────────────────────────────────────────

class SignalDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class AlphaSignal:
    """Standardized alpha signal output."""
    source: str
    direction: SignalDirection
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    asset: str
    horizon: str  # "intraday", "short_term", "medium_term", "long_term"
    reasoning: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# 1. Positioning Data (CFTC COT, Options OI, Futures)
# ─────────────────────────────────────────────────────────────

class PositioningAnalyzer:
    """
    Analyzes CFTC Commitment of Traders reports, options open interest,
    and futures positioning to detect crowded trades and positioning extremes.
    
    Key metrics:
    - Net speculative positioning (commercial vs non-commercial)
    - Positioning z-score vs 3-year history
    - Options put/call open interest ratio
    - Futures basis (spot vs near-month spread)
    """

    def __init__(self, lookback_weeks: int = 156):
        self._lookback = lookback_weeks  # 3 years
        self._cot_history: Dict[str, List[Dict]] = {}  # asset -> weekly reports
        self._oi_history: Dict[str, List[Dict]] = {}
        self._thresholds = {
            "extreme_long_zscore": 2.0,
            "extreme_short_zscore": -2.0,
            "crowded_threshold": 1.5,
            "reversal_threshold": -0.5,
        }

    def ingest_cot_report(self, asset: str, report: Dict[str, Any]) -> None:
        """Ingest a weekly CFTC COT report.
        report: {date, commercial_long, commercial_short, noncommercial_long,
                 noncommercial_short, nonreportable_long, nonreportable_short,
                 open_interest_total}
        """
        if asset not in self._cot_history:
            self._cot_history[asset] = []
        self._cot_history[asset].append(report)
        if len(self._cot_history[asset]) > self._lookback:
            self._cot_history[asset] = self._cot_history[asset][-self._lookback:]

    def ingest_options_oi(self, asset: str, data: Dict[str, Any]) -> None:
        """Ingest options open interest snapshot.
        data: {date, call_oi, put_oi, total_oi, max_pain_strike,
               near_expiry_put_call_ratio}
        """
        if asset not in self._oi_history:
            self._oi_history[asset] = []
        self._oi_history[asset].append(data)
        if len(self._oi_history[asset]) > 252:
            self._oi_history[asset] = self._oi_history[asset][-252:]

    def analyze_positioning(self, asset: str) -> Optional[AlphaSignal]:
        """Compute positioning signal from COT data."""
        history = self._cot_history.get(asset, [])
        if len(history) < 26:  # need 6 months minimum
            return None

        net_specs = []
        for r in history:
            net = (r.get("noncommercial_long", 0) - r.get("noncommercial_short", 0))
            net_specs.append(net)

        current = net_specs[-1]
        mean_val = statistics.mean(net_specs)
        stdev = statistics.stdev(net_specs) if len(net_specs) > 1 else 1.0
        if stdev == 0:
            stdev = 1.0
        zscore = (current - mean_val) / stdev

        # Positioning change velocity (4 week delta)
        if len(net_specs) >= 5:
            velocity = net_specs[-1] - net_specs[-5]
            velocity_pct = velocity / (abs(mean_val) + 1)
        else:
            velocity = 0
            velocity_pct = 0

        # Commercial hedger positioning (smart money)
        last_report = history[-1]
        comm_net = (last_report.get("commercial_long", 0) -
                    last_report.get("commercial_short", 0))
        spec_net = current

        # Signal generation
        direction = SignalDirection.NEUTRAL
        strength = 0.0
        reasoning_parts = []

        if zscore > self._thresholds["extreme_long_zscore"]:
            direction = SignalDirection.BEARISH  # Contrarian: extreme long → bearish
            strength = min(1.0, (zscore - 1.5) / 2.0)
            reasoning_parts.append(
                f"Speculative positioning extreme long (z={zscore:.2f}), "
                f"mean-reversion risk elevated"
            )
        elif zscore < self._thresholds["extreme_short_zscore"]:
            direction = SignalDirection.BULLISH  # Contrarian: extreme short → bullish
            strength = min(1.0, (abs(zscore) - 1.5) / 2.0)
            reasoning_parts.append(
                f"Speculative positioning extreme short (z={zscore:.2f}), "
                f"short-squeeze risk elevated"
            )

        # Commercial vs speculative divergence
        if comm_net > 0 and spec_net > 0:
            reasoning_parts.append("Commercials and specs aligned long — trend confirmation")
        elif comm_net > 0 and spec_net < 0:
            reasoning_parts.append(
                "Commercials long vs specs short — smart money divergence (bullish signal)"
            )
            if direction == SignalDirection.NEUTRAL:
                direction = SignalDirection.BULLISH
                strength = 0.5
        elif comm_net < 0 and spec_net > 0:
            reasoning_parts.append(
                "Commercials short vs specs long — smart money divergence (bearish signal)"
            )
            if direction == SignalDirection.NEUTRAL:
                direction = SignalDirection.BEARISH
                strength = 0.5

        if abs(velocity_pct) > 0.1:
            reasoning_parts.append(
                f"Positioning velocity {velocity_pct:+.1%} over 4 weeks"
            )

        confidence = min(0.9, 0.5 + len(history) / 300)

        return AlphaSignal(
            source="positioning_cot",
            direction=direction,
            strength=strength,
            confidence=confidence,
            asset=asset,
            horizon="medium_term",
            reasoning="; ".join(reasoning_parts) if reasoning_parts else "No extreme positioning",
            metadata={
                "zscore": zscore,
                "net_speculative": current,
                "commercial_net": comm_net,
                "velocity_4w": velocity,
                "history_weeks": len(history),
            }
        )

    def analyze_options_oi(self, asset: str) -> Optional[AlphaSignal]:
        """Compute signal from options open interest distribution."""
        history = self._oi_history.get(asset, [])
        if not history:
            return None
        latest = history[-1]
        call_oi = latest.get("call_oi", 0)
        put_oi = latest.get("put_oi", 0)
        if call_oi == 0:
            return None

        pc_ratio = put_oi / call_oi if call_oi > 0 else 1.0

        # Historical context
        pc_history = []
        for h in history:
            c = h.get("call_oi", 1)
            p = h.get("put_oi", 0)
            if c > 0:
                pc_history.append(p / c)

        if len(pc_history) >= 20:
            pc_mean = statistics.mean(pc_history)
            pc_std = statistics.stdev(pc_history) if len(pc_history) > 1 else 0.1
            pc_zscore = (pc_ratio - pc_mean) / max(pc_std, 0.01)
        else:
            pc_zscore = 0.0

        direction = SignalDirection.NEUTRAL
        strength = 0.0
        if pc_zscore > 1.5:
            direction = SignalDirection.BULLISH  # Extreme fear → contrarian bullish
            strength = min(1.0, (pc_zscore - 1.0) / 2.0)
        elif pc_zscore < -1.5:
            direction = SignalDirection.BEARISH  # Extreme complacency → contrarian bearish
            strength = min(1.0, (abs(pc_zscore) - 1.0) / 2.0)

        return AlphaSignal(
            source="options_open_interest",
            direction=direction,
            strength=strength,
            confidence=min(0.85, 0.4 + len(pc_history) / 200),
            asset=asset,
            horizon="short_term",
            reasoning=f"Put/Call OI ratio={pc_ratio:.2f}, z-score={pc_zscore:.2f}",
            metadata={"put_call_ratio": pc_ratio, "pc_zscore": pc_zscore,
                      "max_pain": latest.get("max_pain_strike")}
        )


# ─────────────────────────────────────────────────────────────
# 2. Order Flow Analysis
# ─────────────────────────────────────────────────────────────

class OrderFlowAnalyzer:
    """
    Analyzes real-time order book imbalance, trade-by-trade aggressor detection,
    cumulative delta, and volume profile.
    
    Processes Level 2 data and trade prints to detect:
    - Aggressive buyer/seller imbalance
    - Iceberg order detection (repeated fills at same price)
    - Absorption (large resting orders absorbing aggressor flow)
    - Sweep patterns (hitting multiple price levels rapidly)
    """

    def __init__(self, depth_levels: int = 10):
        self._depth_levels = depth_levels
        self._trade_buffer: List[Dict] = []  # recent trades
        self._buffer_max = 10000
        self._cumulative_delta = 0.0
        self._volume_profile: Dict[float, Dict[str, float]] = {}  # price → {buy_vol, sell_vol}
        self._iceberg_candidates: Dict[float, int] = {}  # price → refill_count

    def process_trade(self, trade: Dict[str, Any]) -> None:
        """Process a single trade print.
        trade: {price, size, side ('buy'|'sell'), timestamp, is_aggressor}
        """
        self._trade_buffer.append(trade)
        if len(self._trade_buffer) > self._buffer_max:
            self._trade_buffer = self._trade_buffer[-self._buffer_max:]

        side = trade.get("side", "buy")
        size = trade.get("size", 0)
        price = trade.get("price", 0)

        if side == "buy":
            self._cumulative_delta += size
        else:
            self._cumulative_delta -= size

        # Volume profile
        rounded_price = round(price, 2)
        if rounded_price not in self._volume_profile:
            self._volume_profile[rounded_price] = {"buy_vol": 0, "sell_vol": 0, "count": 0}
        self._volume_profile[rounded_price][f"{side}_vol"] += size
        self._volume_profile[rounded_price]["count"] += 1

        # Iceberg detection: repeated fills at same price
        if trade.get("is_aggressor", False):
            self._iceberg_candidates[rounded_price] = (
                self._iceberg_candidates.get(rounded_price, 0) + 1
            )

    def process_order_book(self, book: Dict[str, Any]) -> Dict[str, float]:
        """Analyze order book snapshot.
        book: {bids: [(price, size), ...], asks: [(price, size), ...], timestamp}
        """
        bids = book.get("bids", [])
        asks = book.get("asks", [])

        bid_depth = sum(s for _, s in bids[:self._depth_levels])
        ask_depth = sum(s for _, s in asks[:self._depth_levels])
        total_depth = bid_depth + ask_depth

        imbalance = (bid_depth - ask_depth) / max(total_depth, 1)

        # Depth concentration — how much is at top of book
        top_bid = bids[0][1] if bids else 0
        top_ask = asks[0][1] if asks else 0
        bid_concentration = top_bid / max(bid_depth, 1)
        ask_concentration = top_ask / max(ask_depth, 1)

        # Spread
        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else 0
        spread = best_ask - best_bid if best_bid > 0 else 0
        mid = (best_bid + best_ask) / 2 if best_bid > 0 else 0
        spread_bps = (spread / mid * 10000) if mid > 0 else 0

        return {
            "imbalance": imbalance,
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "bid_concentration": bid_concentration,
            "ask_concentration": ask_concentration,
            "spread_bps": spread_bps,
            "mid_price": mid,
        }

    def detect_sweep(self, window_seconds: float = 1.0) -> Optional[Dict]:
        """Detect sweep patterns (hitting multiple levels rapidly)."""
        if len(self._trade_buffer) < 5:
            return None

        now = self._trade_buffer[-1].get("timestamp", time.time())
        recent = [t for t in self._trade_buffer
                  if now - t.get("timestamp", 0) <= window_seconds]
        if len(recent) < 3:
            return None

        prices = [t["price"] for t in recent]
        sides = [t.get("side", "buy") for t in recent]
        total_size = sum(t.get("size", 0) for t in recent)

        buy_count = sides.count("buy")
        sell_count = sides.count("sell")
        price_range = max(prices) - min(prices) if prices else 0

        is_sweep = False
        sweep_side = "neutral"

        if buy_count > len(recent) * 0.8 and price_range > 0:
            is_sweep = True
            sweep_side = "buy"
        elif sell_count > len(recent) * 0.8 and price_range > 0:
            is_sweep = True
            sweep_side = "sell"

        if is_sweep:
            return {
                "type": "sweep",
                "side": sweep_side,
                "levels_hit": len(set(round(p, 2) for p in prices)),
                "total_size": total_size,
                "price_range": price_range,
                "trade_count": len(recent),
            }
        return None

    def detect_icebergs(self, min_refills: int = 5) -> List[Dict]:
        """Detect iceberg orders (repeated fills at same price)."""
        icebergs = []
        for price, count in self._iceberg_candidates.items():
            if count >= min_refills:
                vp = self._volume_profile.get(price, {})
                icebergs.append({
                    "price": price,
                    "refill_count": count,
                    "total_volume": vp.get("buy_vol", 0) + vp.get("sell_vol", 0),
                    "buy_ratio": vp.get("buy_vol", 0) / max(
                        vp.get("buy_vol", 0) + vp.get("sell_vol", 0), 1),
                })
        return sorted(icebergs, key=lambda x: x["refill_count"], reverse=True)

    def generate_signal(self, asset: str, book: Dict) -> AlphaSignal:
        """Generate order flow alpha signal."""
        metrics = self.process_order_book(book)
        sweep = self.detect_sweep()
        icebergs = self.detect_icebergs()

        imb = metrics["imbalance"]
        direction = SignalDirection.NEUTRAL
        strength = 0.0
        parts = []

        if abs(imb) > 0.3:
            direction = SignalDirection.BULLISH if imb > 0 else SignalDirection.BEARISH
            strength = min(1.0, abs(imb))
            parts.append(f"Order book imbalance {imb:+.2f}")

        if self._cumulative_delta != 0:
            delta_dir = "positive" if self._cumulative_delta > 0 else "negative"
            parts.append(f"Cumulative delta {delta_dir} ({self._cumulative_delta:+.0f})")

        if sweep:
            parts.append(f"Sweep detected: {sweep['side']} across {sweep['levels_hit']} levels")
            if direction == SignalDirection.NEUTRAL:
                direction = (SignalDirection.BULLISH if sweep["side"] == "buy"
                             else SignalDirection.BEARISH)
                strength = 0.7

        if icebergs:
            parts.append(f"{len(icebergs)} iceberg(s) detected at "
                         f"{', '.join(str(i['price']) for i in icebergs[:3])}")

        return AlphaSignal(
            source="order_flow",
            direction=direction,
            strength=strength,
            confidence=min(0.8, 0.3 + len(self._trade_buffer) / 5000),
            asset=asset,
            horizon="intraday",
            reasoning="; ".join(parts) if parts else "Balanced order flow",
            metadata={**metrics, "cumulative_delta": self._cumulative_delta,
                      "iceberg_count": len(icebergs)},
        )


# ─────────────────────────────────────────────────────────────
# 3. Volatility Surface Analyzer
# ─────────────────────────────────────────────────────────────

class VolatilitySurfaceAnalyzer:
    """
    Analyzes options implied volatility surface: skew, term structure, smile.

    Key signals:
    - Put skew steepening → demand for downside protection (bearish)
    - Term structure inversion → near-term event risk
    - Volatility smile asymmetry → directional positioning
    - IV percentile rank → cheap/expensive options
    """

    def __init__(self):
        self._surfaces: Dict[str, List[Dict]] = {}
        self._iv_history: Dict[str, List[float]] = {}

    def ingest_surface(self, asset: str, surface: Dict[str, Any]) -> None:
        """Ingest volatility surface snapshot.
        surface: {timestamp, atm_iv, 25d_put_iv, 25d_call_iv, 10d_put_iv, 10d_call_iv,
                  term_structure: {7d, 30d, 60d, 90d, 180d, 365d},
                  spot_price, risk_free_rate}
        """
        if asset not in self._surfaces:
            self._surfaces[asset] = []
        self._surfaces[asset].append(surface)
        if len(self._surfaces[asset]) > 252:
            self._surfaces[asset] = self._surfaces[asset][-252:]

        atm_iv = surface.get("atm_iv", 0)
        if atm_iv > 0:
            if asset not in self._iv_history:
                self._iv_history[asset] = []
            self._iv_history[asset].append(atm_iv)
            if len(self._iv_history[asset]) > 252:
                self._iv_history[asset] = self._iv_history[asset][-252:]

    def compute_skew(self, surface: Dict) -> Dict[str, float]:
        """Compute skew metrics from surface snapshot."""
        put_25d = surface.get("25d_put_iv", 0)
        call_25d = surface.get("25d_call_iv", 0)
        atm = surface.get("atm_iv", 0)

        skew_25d = put_25d - call_25d  # "risk reversal"
        butterfly = (put_25d + call_25d) / 2 - atm if atm > 0 else 0  # smile curvature

        put_10d = surface.get("10d_put_iv", 0)
        call_10d = surface.get("10d_call_iv", 0)
        skew_10d = put_10d - call_10d

        return {
            "skew_25d": skew_25d,
            "skew_10d": skew_10d,
            "butterfly_25d": butterfly,
            "put_premium": put_25d - atm if atm else 0,
            "call_premium": call_25d - atm if atm else 0,
        }

    def compute_term_structure(self, surface: Dict) -> Dict[str, Any]:
        """Analyze term structure for inversion and slope."""
        ts = surface.get("term_structure", {})
        if not ts:
            return {"slope": 0, "inverted": False}

        tenors = sorted(ts.items(), key=lambda x: int(x[0].replace("d", "")))
        if len(tenors) < 2:
            return {"slope": 0, "inverted": False}

        near = tenors[0][1]
        far = tenors[-1][1]
        slope = far - near  # positive = normal, negative = inverted

        inversions = 0
        for i in range(1, len(tenors)):
            if tenors[i][1] < tenors[i - 1][1]:
                inversions += 1

        return {
            "slope": slope,
            "inverted": slope < 0,
            "near_term_iv": near,
            "far_term_iv": far,
            "inversion_count": inversions,
        }

    def iv_percentile(self, asset: str) -> float:
        """Compute IV percentile rank (0-100) vs 1-year history."""
        hist = self._iv_history.get(asset, [])
        if len(hist) < 20:
            return 50.0
        current = hist[-1]
        below = sum(1 for v in hist[:-1] if v < current)
        return below / (len(hist) - 1) * 100

    def analyze(self, asset: str) -> Optional[AlphaSignal]:
        """Generate volatility surface alpha signal."""
        surfaces = self._surfaces.get(asset, [])
        if not surfaces:
            return None
        latest = surfaces[-1]

        skew = self.compute_skew(latest)
        term = self.compute_term_structure(latest)
        iv_pct = self.iv_percentile(asset)

        direction = SignalDirection.NEUTRAL
        strength = 0.0
        parts = []

        # Skew analysis
        if skew["skew_25d"] > 5:
            parts.append(f"Put skew elevated ({skew['skew_25d']:.1f}vol) — demand for downside protection")
            direction = SignalDirection.BEARISH
            strength = min(1.0, skew["skew_25d"] / 15)
        elif skew["skew_25d"] < -3:
            parts.append(f"Call skew elevated ({skew['skew_25d']:.1f}vol) — upside demand")
            direction = SignalDirection.BULLISH
            strength = min(1.0, abs(skew["skew_25d"]) / 10)

        # Term structure
        if term["inverted"]:
            parts.append("Term structure INVERTED — near-term event risk priced in")
            strength = min(1.0, strength + 0.2)

        # IV percentile
        if iv_pct > 90:
            parts.append(f"IV at {iv_pct:.0f}th percentile — historically expensive")
        elif iv_pct < 10:
            parts.append(f"IV at {iv_pct:.0f}th percentile — historically cheap")

        return AlphaSignal(
            source="volatility_surface",
            direction=direction,
            strength=strength,
            confidence=0.75,
            asset=asset,
            horizon="short_term",
            reasoning="; ".join(parts) if parts else "Vol surface neutral",
            metadata={"skew": skew, "term_structure": term, "iv_percentile": iv_pct},
        )


# ─────────────────────────────────────────────────────────────
# 4. Cross-Asset Lead-Lag Detection
# ─────────────────────────────────────────────────────────────

class CrossAssetLeadLag:
    """
    Detects which assets move first during regime changes.
    Uses rolling cross-correlation at multiple lags to identify
    dynamic lead-lag relationships.
    """

    def __init__(self, window: int = 60, max_lag: int = 10):
        self._window = window
        self._max_lag = max_lag
        self._price_series: Dict[str, List[float]] = {}
        self._relationships: Dict[str, Dict] = {}

    def update_price(self, asset: str, price: float) -> None:
        if asset not in self._price_series:
            self._price_series[asset] = []
        self._price_series[asset].append(price)
        if len(self._price_series[asset]) > self._window * 3:
            self._price_series[asset] = self._price_series[asset][-self._window * 3:]

    def _compute_returns(self, prices: List[float]) -> List[float]:
        return [(prices[i] - prices[i - 1]) / prices[i - 1]
                for i in range(1, len(prices)) if prices[i - 1] != 0]

    def _cross_correlation(self, x: List[float], y: List[float], lag: int) -> float:
        """Pearson correlation of x[lag:] with y[:len-lag]."""
        if lag >= 0:
            a = x[lag:]
            b = y[:len(y) - lag] if lag > 0 else y
        else:
            a = x[:len(x) + lag]
            b = y[-lag:]
        n = min(len(a), len(b))
        if n < 10:
            return 0.0
        a, b = a[:n], b[:n]
        mean_a = statistics.mean(a)
        mean_b = statistics.mean(b)
        cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / n
        std_a = statistics.stdev(a) if len(a) > 1 else 1
        std_b = statistics.stdev(b) if len(b) > 1 else 1
        return cov / (std_a * std_b) if std_a * std_b > 0 else 0

    def compute_lead_lag(self, asset_a: str, asset_b: str) -> Dict[str, Any]:
        """Compute lead-lag between two assets."""
        prices_a = self._price_series.get(asset_a, [])
        prices_b = self._price_series.get(asset_b, [])

        if len(prices_a) < self._window or len(prices_b) < self._window:
            return {"leader": None, "lag": 0, "correlation": 0}

        ret_a = self._compute_returns(prices_a[-self._window:])
        ret_b = self._compute_returns(prices_b[-self._window:])

        best_lag = 0
        best_corr = 0.0
        for lag in range(-self._max_lag, self._max_lag + 1):
            corr = self._cross_correlation(ret_a, ret_b, lag)
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag

        leader = asset_a if best_lag > 0 else asset_b if best_lag < 0 else None
        result = {
            "leader": leader,
            "lag": abs(best_lag),
            "correlation": best_corr,
            "relationship": "positive" if best_corr > 0 else "negative",
        }
        key = f"{asset_a}_{asset_b}"
        self._relationships[key] = result
        return result

    def scan_all_pairs(self) -> List[Dict]:
        """Scan all asset pairs for lead-lag relationships."""
        assets = list(self._price_series.keys())
        results = []
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                result = self.compute_lead_lag(assets[i], assets[j])
                if result["leader"] and abs(result["correlation"]) > 0.3:
                    result["pair"] = (assets[i], assets[j])
                    results.append(result)
        return sorted(results, key=lambda x: abs(x["correlation"]), reverse=True)


# ─────────────────────────────────────────────────────────────
# 5. Sentiment Extremes Analyzer
# ─────────────────────────────────────────────────────────────

class SentimentExtremesAnalyzer:
    """
    Aggregates institutional sentiment indicators beyond social media:
    - CNN Fear & Greed Index (7 components)
    - AAII Bull/Bear Survey
    - Put/Call Ratio (equity + index)
    - VIX term structure
    - Safe haven flows (gold, treasuries, JPY, CHF)
    """

    def __init__(self):
        self._indicators: Dict[str, List[Dict]] = {}
        self._weights = {
            "fear_greed": 0.20,
            "aaii_survey": 0.15,
            "put_call_ratio": 0.20,
            "vix_term": 0.15,
            "safe_haven": 0.15,
            "margin_debt": 0.15,
        }

    def update_indicator(self, name: str, data: Dict[str, Any]) -> None:
        """Update an indicator reading. data must include 'value' and 'timestamp'."""
        if name not in self._indicators:
            self._indicators[name] = []
        self._indicators[name].append(data)
        if len(self._indicators[name]) > 252:
            self._indicators[name] = self._indicators[name][-252:]

    def _normalize_to_fear_greed(self, name: str) -> float:
        """Normalize any indicator to 0-100 fear/greed scale."""
        history = self._indicators.get(name, [])
        if not history:
            return 50.0
        current = history[-1].get("value", 50)

        if name == "fear_greed":
            return float(current)
        elif name == "aaii_survey":
            # Bull% - Bear% → remap [-100, 100] to [0, 100]
            return (current + 100) / 2
        elif name == "put_call_ratio":
            # High P/C = fear, Low P/C = greed → invert and scale
            # Normal range 0.6-1.2
            return max(0, min(100, (1.2 - current) / 0.6 * 100))
        elif name == "vix_term":
            # Negative slope (backwardation) = fear
            return max(0, min(100, 50 + current * 10))
        elif name == "safe_haven":
            # Positive flows = fear → invert
            return max(0, min(100, 50 - current * 10))
        elif name == "margin_debt":
            # High margin debt = greed
            return max(0, min(100, current))
        return 50.0

    def compute_composite(self) -> Dict[str, Any]:
        """Compute composite sentiment score."""
        total_weight = 0.0
        weighted_sum = 0.0
        components = {}

        for name, weight in self._weights.items():
            if name in self._indicators and self._indicators[name]:
                score = self._normalize_to_fear_greed(name)
                components[name] = score
                weighted_sum += score * weight
                total_weight += weight

        composite = weighted_sum / max(total_weight, 0.01)

        zone = "neutral"
        if composite < 20:
            zone = "extreme_fear"
        elif composite < 35:
            zone = "fear"
        elif composite > 80:
            zone = "extreme_greed"
        elif composite > 65:
            zone = "greed"

        return {
            "composite": composite,
            "zone": zone,
            "components": components,
            "active_indicators": len(components),
        }

    def generate_signal(self, asset: str = "SPX") -> AlphaSignal:
        result = self.compute_composite()
        composite = result["composite"]

        if composite < 20:
            direction = SignalDirection.BULLISH  # Contrarian: extreme fear → buy
            strength = (20 - composite) / 20
        elif composite > 80:
            direction = SignalDirection.BEARISH  # Contrarian: extreme greed → sell
            strength = (composite - 80) / 20
        else:
            direction = SignalDirection.NEUTRAL
            strength = 0.0

        return AlphaSignal(
            source="sentiment_extremes",
            direction=direction,
            strength=min(1.0, strength),
            confidence=min(0.85, 0.3 + result["active_indicators"] * 0.1),
            asset=asset,
            horizon="medium_term",
            reasoning=f"Composite sentiment {composite:.0f}/100 — {result['zone']}",
            metadata=result,
        )


# ─────────────────────────────────────────────────────────────
# 6. Flow-of-Funds Analyzer
# ─────────────────────────────────────────────────────────────

class FlowOfFundsAnalyzer:
    """
    Tracks ETF flows, mutual fund flows, margin debt levels, and
    institutional vs retail flow composition.
    """

    def __init__(self):
        self._etf_flows: Dict[str, List[Dict]] = {}
        self._fund_flows: List[Dict] = []
        self._margin_debt: List[Dict] = []

    def record_etf_flow(self, ticker: str, data: Dict[str, Any]) -> None:
        """data: {date, flow_usd, aum, pct_aum, shares_outstanding_change}"""
        if ticker not in self._etf_flows:
            self._etf_flows[ticker] = []
        self._etf_flows[ticker].append(data)
        if len(self._etf_flows[ticker]) > 252:
            self._etf_flows[ticker] = self._etf_flows[ticker][-252:]

    def record_fund_flow(self, data: Dict[str, Any]) -> None:
        """data: {date, category, flow_usd, asset_class}"""
        self._fund_flows.append(data)
        if len(self._fund_flows) > 1000:
            self._fund_flows = self._fund_flows[-1000:]

    def record_margin_debt(self, data: Dict[str, Any]) -> None:
        """data: {date, total_margin_debt, free_credit_cash, net_margin}"""
        self._margin_debt.append(data)
        if len(self._margin_debt) > 120:
            self._margin_debt = self._margin_debt[-120:]

    def analyze_etf_flows(self, sector: str = "equity") -> Dict[str, Any]:
        """Analyze net ETF flows for a sector."""
        sector_tickers = {
            "equity": ["SPY", "QQQ", "IWM", "DIA", "VTI"],
            "bonds": ["TLT", "IEF", "LQD", "HYG", "AGG"],
            "commodities": ["GLD", "SLV", "USO", "DBC"],
            "international": ["EFA", "EEM", "VEA", "IEMG"],
        }
        tickers = sector_tickers.get(sector, [])
        total_flow = 0
        flow_details = {}
        for t in tickers:
            flows = self._etf_flows.get(t, [])
            if flows:
                recent = sum(f.get("flow_usd", 0) for f in flows[-5:])
                total_flow += recent
                flow_details[t] = recent
        return {
            "sector": sector,
            "net_flow_5d": total_flow,
            "detail": flow_details,
            "direction": "inflow" if total_flow > 0 else "outflow",
        }

    def margin_debt_signal(self) -> Dict[str, Any]:
        """Analyze margin debt for leverage extremes."""
        if len(self._margin_debt) < 6:
            return {"signal": "insufficient_data"}
        recent = self._margin_debt[-1].get("total_margin_debt", 0)
        six_months_ago = self._margin_debt[-6].get("total_margin_debt", 0) if len(self._margin_debt) >= 6 else recent
        change = (recent - six_months_ago) / max(abs(six_months_ago), 1)
        return {
            "current": recent,
            "6m_change": change,
            "signal": "extreme_leverage" if change > 0.15 else
                      "deleveraging" if change < -0.10 else "normal",
        }

    def generate_signal(self, asset: str = "SPX") -> AlphaSignal:
        eq_flows = self.analyze_etf_flows("equity")
        margin = self.margin_debt_signal()

        direction = SignalDirection.NEUTRAL
        strength = 0.0
        parts = []

        if eq_flows["net_flow_5d"] > 0:
            parts.append(f"Equity ETF inflow ${eq_flows['net_flow_5d'] / 1e9:.1f}B (5d)")
            direction = SignalDirection.BULLISH
            strength = 0.4
        elif eq_flows["net_flow_5d"] < 0:
            parts.append(f"Equity ETF outflow ${abs(eq_flows['net_flow_5d']) / 1e9:.1f}B (5d)")
            direction = SignalDirection.BEARISH
            strength = 0.4

        if margin["signal"] == "extreme_leverage":
            parts.append(f"Margin debt elevated (6m change {margin.get('6m_change', 0):+.1%})")
            if direction == SignalDirection.BULLISH:
                strength *= 0.7
            elif direction == SignalDirection.NEUTRAL:
                direction = SignalDirection.BEARISH
                strength = 0.3
        elif margin["signal"] == "deleveraging":
            parts.append("Active deleveraging in progress")

        return AlphaSignal(
            source="flow_of_funds", direction=direction, strength=strength,
            confidence=0.6, asset=asset, horizon="medium_term",
            reasoning="; ".join(parts) if parts else "Flows neutral",
            metadata={"equity_flows": eq_flows, "margin": margin},
        )


# ─────────────────────────────────────────────────────────────
# 7. Calendar Effects Analyzer
# ─────────────────────────────────────────────────────────────

class CalendarEffectsAnalyzer:
    """
    Identifies predictable non-news-driven market moves:
    - Month-end rebalancing (pension, index)
    - Options expiration effects
    - Turn of month (TOM) effect
    - Holiday effects
    - January effect
    - Quadruple witching
    - FOMC drift
    """

    EFFECTS = {
        "month_end_rebalance": {
            "days_before_eom": [3, 2, 1, 0],
            "bias": "bullish",
            "strength": 0.3,
            "description": "Pension fund month-end rebalancing typically adds buying pressure",
        },
        "turn_of_month": {
            "days": [1, 2, 3],  # first 3 days of month
            "bias": "bullish",
            "strength": 0.25,
            "description": "401(k) inflows and pension buying at start of month",
        },
        "opex_week": {
            "days_to_opex": [5, 4, 3, 2, 1, 0],
            "bias": "neutral",
            "strength": 0.2,
            "description": "Options expiration increases gamma hedging, pins to max pain",
        },
        "fomc_drift": {
            "days_before_fomc": [1, 0],
            "bias": "bullish",
            "strength": 0.35,
            "description": "Pre-FOMC announcement drift — equities tend to rise 24h before decision",
        },
        "january_effect": {
            "month": 1,
            "bias": "bullish",
            "strength": 0.2,
            "description": "Small-cap outperformance in January (tax-loss selling reversal)",
        },
        "sell_in_may": {
            "months": [5, 6, 7, 8, 9, 10],
            "bias": "bearish",
            "strength": 0.15,
            "description": "Historically weaker returns May-October",
        },
        "quarter_end_window_dressing": {
            "days_before_eoq": [5, 4, 3, 2, 1, 0],
            "bias": "bullish",
            "strength": 0.2,
            "description": "Fund managers buy winners before quarter-end reporting",
        },
    }

    def __init__(self):
        self._fomc_dates: List[str] = []
        self._opex_dates: List[str] = []

    def set_fomc_dates(self, dates: List[str]) -> None:
        """Set FOMC meeting dates (YYYY-MM-DD format)."""
        self._fomc_dates = sorted(dates)

    def set_opex_dates(self, dates: List[str]) -> None:
        """Set monthly options expiration dates."""
        self._opex_dates = sorted(dates)

    def detect_active_effects(self, date_str: str) -> List[Dict[str, Any]]:
        """Detect which calendar effects are active on a given date."""
        import datetime
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        active = []

        # Month-end check
        import calendar
        _, days_in_month = calendar.monthrange(dt.year, dt.month)
        days_to_eom = days_in_month - dt.day
        if days_to_eom <= 3:
            active.append({
                "effect": "month_end_rebalance",
                "days_remaining": days_to_eom,
                **self.EFFECTS["month_end_rebalance"],
            })

        # Turn of month
        if dt.day <= 3:
            active.append({
                "effect": "turn_of_month",
                "day_of_month": dt.day,
                **self.EFFECTS["turn_of_month"],
            })

        # Quarter end
        if dt.month in [3, 6, 9, 12] and days_to_eom <= 5:
            active.append({
                "effect": "quarter_end_window_dressing",
                "days_remaining": days_to_eom,
                **self.EFFECTS["quarter_end_window_dressing"],
            })

        # January effect
        if dt.month == 1:
            active.append({
                "effect": "january_effect",
                **self.EFFECTS["january_effect"],
            })

        # Sell in May
        if dt.month in [5, 6, 7, 8, 9, 10]:
            active.append({
                "effect": "sell_in_may",
                "month": dt.month,
                **self.EFFECTS["sell_in_may"],
            })

        # FOMC proximity
        for fomc_date in self._fomc_dates:
            fomc_dt = datetime.datetime.strptime(fomc_date, "%Y-%m-%d")
            delta = (fomc_dt - dt).days
            if 0 <= delta <= 1:
                active.append({
                    "effect": "fomc_drift",
                    "days_to_fomc": delta,
                    **self.EFFECTS["fomc_drift"],
                })
                break

        # OpEx proximity
        for opex_date in self._opex_dates:
            opex_dt = datetime.datetime.strptime(opex_date, "%Y-%m-%d")
            delta = (opex_dt - dt).days
            if 0 <= delta <= 5:
                active.append({
                    "effect": "opex_week",
                    "days_to_opex": delta,
                    **self.EFFECTS["opex_week"],
                })
                break

        return active

    def generate_signal(self, asset: str, date_str: str) -> AlphaSignal:
        active = self.detect_active_effects(date_str)
        if not active:
            return AlphaSignal(
                source="calendar_effects", direction=SignalDirection.NEUTRAL,
                strength=0, confidence=0.5, asset=asset, horizon="short_term",
                reasoning="No active calendar effects",
            )

        bullish_strength = sum(
            e["strength"] for e in active if e["bias"] == "bullish"
        )
        bearish_strength = sum(
            e["strength"] for e in active if e["bias"] == "bearish"
        )
        net = bullish_strength - bearish_strength

        direction = (SignalDirection.BULLISH if net > 0 else
                     SignalDirection.BEARISH if net < 0 else SignalDirection.NEUTRAL)

        return AlphaSignal(
            source="calendar_effects",
            direction=direction,
            strength=min(1.0, abs(net)),
            confidence=0.6,
            asset=asset,
            horizon="short_term",
            reasoning=f"{len(active)} active effect(s): " +
                      ", ".join(e["effect"] for e in active),
            metadata={"active_effects": active, "net_bias": net},
        )


# ─────────────────────────────────────────────────────────────
# 8. Earnings Estimate Revision Tracker
# ─────────────────────────────────────────────────────────────

class EarningsRevisionTracker:
    """
    Tracks analyst earnings estimate revisions and their momentum.
    Revision momentum often predicts earnings surprises.
    """

    def __init__(self):
        self._estimates: Dict[str, List[Dict]] = {}  # ticker → estimate history

    def record_estimate(self, ticker: str, data: Dict[str, Any]) -> None:
        """data: {date, period (Q1/Q2/FY), eps_consensus, eps_high, eps_low,
                  num_analysts, rev_consensus, rev_high, rev_low}"""
        if ticker not in self._estimates:
            self._estimates[ticker] = []
        self._estimates[ticker].append(data)

    def compute_revision_momentum(self, ticker: str, lookback: int = 30) -> Dict[str, Any]:
        """Compute earnings revision momentum for a ticker."""
        history = self._estimates.get(ticker, [])
        if len(history) < 3:
            return {"momentum": 0, "direction": "insufficient", "revisions": 0}

        recent = history[-lookback:] if len(history) >= lookback else history
        eps_values = [h.get("eps_consensus", 0) for h in recent if h.get("eps_consensus")]
        rev_values = [h.get("rev_consensus", 0) for h in recent if h.get("rev_consensus")]

        if len(eps_values) < 2:
            return {"momentum": 0, "direction": "insufficient", "revisions": 0}

        # Count upward vs downward revisions
        up_revisions = sum(1 for i in range(1, len(eps_values)) if eps_values[i] > eps_values[i - 1])
        down_revisions = sum(1 for i in range(1, len(eps_values)) if eps_values[i] < eps_values[i - 1])
        total_revisions = up_revisions + down_revisions

        # Magnitude of revisions
        eps_change_pct = (eps_values[-1] - eps_values[0]) / abs(eps_values[0]) if eps_values[0] != 0 else 0

        breadth = (up_revisions - down_revisions) / max(total_revisions, 1)

        return {
            "momentum": eps_change_pct,
            "breadth": breadth,
            "up_revisions": up_revisions,
            "down_revisions": down_revisions,
            "total_revisions": total_revisions,
            "current_eps": eps_values[-1],
            "direction": "positive" if breadth > 0.3 else "negative" if breadth < -0.3 else "mixed",
        }

    def generate_signal(self, ticker: str) -> AlphaSignal:
        rev = self.compute_revision_momentum(ticker)

        if rev["direction"] == "insufficient":
            return AlphaSignal(
                source="earnings_revisions", direction=SignalDirection.NEUTRAL,
                strength=0, confidence=0.3, asset=ticker, horizon="medium_term",
                reasoning="Insufficient revision data", metadata=rev,
            )

        direction = SignalDirection.NEUTRAL
        strength = 0.0

        if rev["breadth"] > 0.3 and rev["momentum"] > 0.02:
            direction = SignalDirection.BULLISH
            strength = min(1.0, rev["breadth"] * 0.7 + abs(rev["momentum"]) * 5)
        elif rev["breadth"] < -0.3 and rev["momentum"] < -0.02:
            direction = SignalDirection.BEARISH
            strength = min(1.0, abs(rev["breadth"]) * 0.7 + abs(rev["momentum"]) * 5)

        return AlphaSignal(
            source="earnings_revisions", direction=direction,
            strength=strength, confidence=min(0.8, 0.4 + rev["total_revisions"] * 0.02),
            asset=ticker, horizon="medium_term",
            reasoning=f"EPS revision momentum {rev['momentum']:+.1%}, breadth {rev['breadth']:+.2f}",
            metadata=rev,
        )


# ─────────────────────────────────────────────────────────────
# 9. Insider Trading Analyzer (SEC Form 4)
# ─────────────────────────────────────────────────────────────

class InsiderTradingAnalyzer:
    """
    Analyzes SEC Form 4 filings for insider buying/selling patterns.
    Insider buying is a stronger signal than selling (insiders sell for many reasons).
    """

    def __init__(self):
        self._filings: Dict[str, List[Dict]] = {}

    def record_filing(self, ticker: str, filing: Dict[str, Any]) -> None:
        """filing: {date, insider_name, title, transaction_type ('buy'|'sell'|'exercise'),
                    shares, price, value, ownership_change_pct}"""
        if ticker not in self._filings:
            self._filings[ticker] = []
        self._filings[ticker].append(filing)

    def analyze_insider_activity(self, ticker: str, lookback_days: int = 90) -> Dict:
        filings = self._filings.get(ticker, [])
        if not filings:
            return {"signal": "no_data", "buy_count": 0, "sell_count": 0}

        buys = [f for f in filings if f.get("transaction_type") == "buy"]
        sells = [f for f in filings if f.get("transaction_type") == "sell"]

        buy_value = sum(f.get("value", 0) for f in buys)
        sell_value = sum(f.get("value", 0) for f in sells)

        # Insider titles weighted (CEO/CFO > VP > Director)
        title_weights = {"CEO": 3, "CFO": 2.5, "COO": 2, "CTO": 2,
                         "President": 2, "VP": 1.5, "Director": 1, "Officer": 1.5}
        weighted_buy = 0
        weighted_sell = 0
        for f in buys:
            w = max(title_weights.get(f.get("title", ""), 1), 1)
            weighted_buy += f.get("value", 0) * w
        for f in sells:
            w = max(title_weights.get(f.get("title", ""), 1), 1)
            weighted_sell += f.get("value", 0) * w

        # Cluster detection — multiple insiders buying at same time
        cluster_buying = len(buys) >= 3
        cluster_selling = len(sells) >= 5

        return {
            "buy_count": len(buys),
            "sell_count": len(sells),
            "buy_value": buy_value,
            "sell_value": sell_value,
            "net_value": buy_value - sell_value,
            "weighted_buy": weighted_buy,
            "weighted_sell": weighted_sell,
            "cluster_buying": cluster_buying,
            "cluster_selling": cluster_selling,
            "signal": ("strong_buy" if cluster_buying else
                       "buy" if len(buys) > len(sells) and buy_value > sell_value else
                       "sell" if len(sells) > len(buys) * 3 else "neutral"),
        }

    def generate_signal(self, ticker: str) -> AlphaSignal:
        activity = self.analyze_insider_activity(ticker)

        direction = SignalDirection.NEUTRAL
        strength = 0.0

        if activity["signal"] == "strong_buy":
            direction = SignalDirection.BULLISH
            strength = 0.8
        elif activity["signal"] == "buy":
            direction = SignalDirection.BULLISH
            strength = 0.5
        elif activity["signal"] == "sell":
            direction = SignalDirection.BEARISH
            strength = 0.3  # Selling is weaker signal

        return AlphaSignal(
            source="insider_trading", direction=direction,
            strength=strength,
            confidence=0.7 if activity["buy_count"] + activity["sell_count"] > 3 else 0.4,
            asset=ticker, horizon="medium_term",
            reasoning=(f"Insider {activity['signal']}: "
                       f"{activity['buy_count']} buys (${activity['buy_value']:,.0f}) / "
                       f"{activity['sell_count']} sells (${activity['sell_value']:,.0f})"),
            metadata=activity,
        )


# ─────────────────────────────────────────────────────────────
# 10. Credit Market Signals
# ─────────────────────────────────────────────────────────────

class CreditMarketSignals:
    """
    Credit markets typically lead equity markets. Monitors:
    - CDS spreads (investment grade + high yield)
    - High-yield bond flows and spreads
    - Repo market stress (overnight rate vs target)
    - TED spread (3m LIBOR/SOFR vs 3m T-bill)
    - Investment grade vs HY spread ratio
    """

    def __init__(self):
        self._cds_spreads: Dict[str, List[Dict]] = {}
        self._hy_spreads: List[Dict] = []
        self._repo_rates: List[Dict] = []
        self._ted_spread: List[Dict] = []

    def update_cds(self, entity: str, data: Dict) -> None:
        """data: {date, spread_bps, recovery_rate, implied_default_prob}"""
        if entity not in self._cds_spreads:
            self._cds_spreads[entity] = []
        self._cds_spreads[entity].append(data)

    def update_hy_spread(self, data: Dict) -> None:
        """data: {date, oas_bps, ig_spread_bps, hy_ig_ratio}"""
        self._hy_spreads.append(data)
        if len(self._hy_spreads) > 252:
            self._hy_spreads = self._hy_spreads[-252:]

    def update_repo_rate(self, data: Dict) -> None:
        """data: {date, overnight_rate, target_rate, spread_to_target}"""
        self._repo_rates.append(data)

    def update_ted_spread(self, data: Dict) -> None:
        """data: {date, ted_spread_bps}"""
        self._ted_spread.append(data)

    def analyze_credit_stress(self) -> Dict[str, Any]:
        """Composite credit stress analysis."""
        stress_score = 0.0
        signals = []
        component_count = 0

        # HY spread analysis
        if len(self._hy_spreads) >= 5:
            current_hy = self._hy_spreads[-1].get("oas_bps", 400)
            hy_5d_ago = self._hy_spreads[-5].get("oas_bps", 400) if len(self._hy_spreads) >= 5 else current_hy
            hy_change = current_hy - hy_5d_ago
            if current_hy > 600:
                stress_score += 0.3
                signals.append(f"HY spreads wide ({current_hy}bps)")
            if hy_change > 50:
                stress_score += 0.2
                signals.append(f"HY spreads widening rapidly (+{hy_change}bps 5d)")
            component_count += 1

        # Repo market
        if self._repo_rates:
            latest_repo = self._repo_rates[-1]
            spread_to_target = latest_repo.get("spread_to_target", 0)
            if abs(spread_to_target) > 25:
                stress_score += 0.25
                signals.append(f"Repo rate stress (spread {spread_to_target:+}bps to target)")
            component_count += 1

        # TED spread
        if self._ted_spread:
            ted = self._ted_spread[-1].get("ted_spread_bps", 20)
            if ted > 50:
                stress_score += 0.3
                signals.append(f"TED spread elevated ({ted}bps) — bank credit risk")
            component_count += 1

        # CDS spreads
        for entity, spreads in self._cds_spreads.items():
            if spreads:
                current = spreads[-1].get("spread_bps", 0)
                if current > 200:
                    stress_score += 0.15
                    signals.append(f"{entity} CDS at {current}bps")
                component_count += 1

        return {
            "stress_score": min(1.0, stress_score),
            "signals": signals,
            "components_active": component_count,
            "level": ("critical" if stress_score > 0.7 else
                      "elevated" if stress_score > 0.4 else
                      "moderate" if stress_score > 0.2 else "normal"),
        }

    def generate_signal(self, asset: str = "SPX") -> AlphaSignal:
        stress = self.analyze_credit_stress()
        direction = SignalDirection.NEUTRAL
        strength = stress["stress_score"]

        if strength > 0.4:
            direction = SignalDirection.BEARISH
        elif strength > 0.2:
            direction = SignalDirection.BEARISH
            strength *= 0.7

        return AlphaSignal(
            source="credit_market",
            direction=direction,
            strength=min(1.0, strength),
            confidence=min(0.85, 0.3 + stress["components_active"] * 0.1),
            asset=asset, horizon="short_term",
            reasoning=f"Credit stress: {stress['level']} ({stress['stress_score']:.2f}). " +
                      "; ".join(stress["signals"][:3]),
            metadata=stress,
        )


# ─────────────────────────────────────────────────────────────
# 11. Macro Surprise Index
# ─────────────────────────────────────────────────────────────

class MacroSurpriseIndex:
    """
    Tracks whether economic data systematically beats or misses consensus.
    Similar to Citigroup Economic Surprise Index.
    """

    def __init__(self, decay_days: int = 90):
        self._releases: List[Dict] = []
        self._decay_hl = decay_days
        self._indicator_weights = {
            "NFP": 3.0, "CPI": 2.5, "GDP": 2.5, "PMI": 2.0,
            "Retail_Sales": 1.5, "ISM": 2.0, "Housing_Starts": 1.0,
            "Industrial_Production": 1.5, "Consumer_Confidence": 1.0,
            "Durable_Goods": 1.5, "Unemployment_Claims": 1.5,
        }

    def record_release(self, data: Dict[str, Any]) -> None:
        """data: {date, indicator, actual, consensus, prior, unit}"""
        consensus = data.get("consensus", 0)
        actual = data.get("actual", 0)
        if consensus != 0:
            surprise = (actual - consensus) / abs(consensus)
        else:
            surprise = 0.0
        data["surprise"] = surprise
        data["surprise_direction"] = "beat" if surprise > 0 else "miss" if surprise < 0 else "inline"
        self._releases.append(data)

    def compute_index(self) -> Dict[str, Any]:
        """Compute current macro surprise index value."""
        if not self._releases:
            return {"index": 0, "direction": "neutral", "data_points": 0}

        now = time.time()
        weighted_sum = 0.0
        weight_total = 0.0

        for rel in self._releases:
            indicator = rel.get("indicator", "")
            w = self._indicator_weights.get(indicator, 1.0)

            # Time decay
            days_ago = min((now - rel.get("timestamp", now)) / 86400, self._decay_hl * 3)
            decay = math.exp(-0.693 * days_ago / self._decay_hl)  # half-life decay

            surprise = rel.get("surprise", 0)
            weighted_sum += surprise * w * decay
            weight_total += w * decay

        index = weighted_sum / max(weight_total, 0.01) * 100  # scale to ~ -100 to +100

        # Trend: are surprises getting more positive or negative?
        recent = self._releases[-10:] if len(self._releases) >= 10 else self._releases
        recent_avg = statistics.mean(r.get("surprise", 0) for r in recent) if recent else 0

        return {
            "index": index,
            "direction": "beating" if index > 10 else "missing" if index < -10 else "inline",
            "trend": "improving" if recent_avg > 0.01 else "deteriorating" if recent_avg < -0.01 else "stable",
            "data_points": len(self._releases),
            "recent_avg_surprise": recent_avg,
        }

    def generate_signal(self, asset: str = "SPX") -> AlphaSignal:
        idx = self.compute_index()

        if idx["index"] > 20:
            direction = SignalDirection.BULLISH
            strength = min(1.0, idx["index"] / 50)
        elif idx["index"] < -20:
            direction = SignalDirection.BEARISH
            strength = min(1.0, abs(idx["index"]) / 50)
        else:
            direction = SignalDirection.NEUTRAL
            strength = 0.0

        return AlphaSignal(
            source="macro_surprise",
            direction=direction,
            strength=strength,
            confidence=min(0.8, 0.3 + idx["data_points"] * 0.02),
            asset=asset, horizon="medium_term",
            reasoning=f"Macro surprise index {idx['index']:+.1f} ({idx['direction']}), trend {idx['trend']}",
            metadata=idx,
        )


# ─────────────────────────────────────────────────────────────
# 12. Central Bank Balance Sheet Monitor
# ─────────────────────────────────────────────────────────────

class CentralBankBalanceSheet:
    """
    Monitors central bank balance sheet changes (Fed, ECB, BoJ, PBoC).
    Liquidity injection/withdrawal directly impacts asset prices.
    """

    def __init__(self):
        self._balance_sheets: Dict[str, List[Dict]] = {}
        self._repo_operations: List[Dict] = []

    def update_balance_sheet(self, bank: str, data: Dict[str, Any]) -> None:
        """data: {date, total_assets, treasuries, mbs, repos, reserves,
                  weekly_change, monthly_change_pct}"""
        if bank not in self._balance_sheets:
            self._balance_sheets[bank] = []
        self._balance_sheets[bank].append(data)
        if len(self._balance_sheets[bank]) > 260:
            self._balance_sheets[bank] = self._balance_sheets[bank][-260:]

    def record_repo_operation(self, data: Dict[str, Any]) -> None:
        """data: {date, type ('repo'|'reverse_repo'), amount, rate, term_days}"""
        self._repo_operations.append(data)
        if len(self._repo_operations) > 500:
            self._repo_operations = self._repo_operations[-500:]

    def analyze_liquidity_impulse(self, bank: str = "Fed") -> Dict[str, Any]:
        """Compute liquidity impulse from balance sheet changes."""
        history = self._balance_sheets.get(bank, [])
        if len(history) < 4:
            return {"impulse": 0, "regime": "unknown", "trend": "unknown"}

        # 4-week change
        current = history[-1].get("total_assets", 0)
        four_weeks_ago = history[-4].get("total_assets", 0) if len(history) >= 4 else current
        change_4w = current - four_weeks_ago
        change_4w_pct = change_4w / max(abs(four_weeks_ago), 1)

        # 13-week (quarterly) change
        thirteen_weeks = history[-13].get("total_assets", 0) if len(history) >= 13 else current
        change_13w_pct = (current - thirteen_weeks) / max(abs(thirteen_weeks), 1)

        # Classify regime
        if change_4w_pct > 0.005:
            regime = "QE"  # Quantitative easing
        elif change_4w_pct < -0.005:
            regime = "QT"  # Quantitative tightening
        else:
            regime = "neutral"

        # Acceleration
        if len(history) >= 8:
            prev_4w_change = history[-4].get("total_assets", 0) - history[-8].get("total_assets", 0)
            acceleration = change_4w - prev_4w_change
        else:
            acceleration = 0

        return {
            "impulse": change_4w_pct,
            "regime": regime,
            "change_4w": change_4w,
            "change_4w_pct": change_4w_pct,
            "change_13w_pct": change_13w_pct,
            "acceleration": acceleration,
            "total_assets": current,
            "trend": (
                "accelerating_expansion" if change_4w_pct > 0 and acceleration > 0 else
                "decelerating_expansion" if change_4w_pct > 0 and acceleration < 0 else
                "accelerating_contraction" if change_4w_pct < 0 and acceleration < 0 else
                "decelerating_contraction" if change_4w_pct < 0 and acceleration > 0 else
                "stable"
            ),
        }

    def global_liquidity_pulse(self) -> Dict[str, Any]:
        """Aggregate global central bank liquidity pulse."""
        impulses = {}
        for bank in self._balance_sheets:
            impulses[bank] = self.analyze_liquidity_impulse(bank)

        global_impulse = 0
        count = 0
        for bank, imp in impulses.items():
            if imp["regime"] != "unknown":
                global_impulse += imp["impulse"]
                count += 1

        avg_impulse = global_impulse / max(count, 1)
        global_regime = ("global_QE" if avg_impulse > 0.003 else
                         "global_QT" if avg_impulse < -0.003 else "mixed")

        return {
            "global_impulse": avg_impulse,
            "global_regime": global_regime,
            "bank_impulses": impulses,
            "banks_tracked": count,
        }

    def generate_signal(self, asset: str = "SPX") -> AlphaSignal:
        pulse = self.global_liquidity_pulse()
        impulse = pulse["global_impulse"]

        if impulse > 0.003:
            direction = SignalDirection.BULLISH
            strength = min(1.0, impulse * 100)
        elif impulse < -0.003:
            direction = SignalDirection.BEARISH
            strength = min(1.0, abs(impulse) * 100)
        else:
            direction = SignalDirection.NEUTRAL
            strength = 0.0

        return AlphaSignal(
            source="central_bank_balance_sheet",
            direction=direction,
            strength=strength,
            confidence=min(0.85, 0.3 + pulse["banks_tracked"] * 0.12),
            asset=asset, horizon="long_term",
            reasoning=f"Global liquidity {pulse['global_regime']} "
                      f"(impulse {impulse:+.3%}), "
                      f"{pulse['banks_tracked']} banks tracked",
            metadata=pulse,
        )


# ─────────────────────────────────────────────────────────────
# Unified Alpha Signal Aggregator
# ─────────────────────────────────────────────────────────────

class AlphaSignalAggregator:
    """
    Aggregates signals from all 12 alpha sources into a unified view.
    Applies conflict resolution, time-horizon weighting, and
    conviction scoring.
    """

    def __init__(self):
        self.positioning = PositioningAnalyzer()
        self.order_flow = OrderFlowAnalyzer()
        self.vol_surface = VolatilitySurfaceAnalyzer()
        self.lead_lag = CrossAssetLeadLag()
        self.sentiment = SentimentExtremesAnalyzer()
        self.flows = FlowOfFundsAnalyzer()
        self.calendar = CalendarEffectsAnalyzer()
        self.earnings = EarningsRevisionTracker()
        self.insider = InsiderTradingAnalyzer()
        self.credit = CreditMarketSignals()
        self.macro = MacroSurpriseIndex()
        self.central_bank = CentralBankBalanceSheet()

        self._source_weights = {
            "positioning_cot": 0.12,
            "options_open_interest": 0.08,
            "order_flow": 0.12,
            "volatility_surface": 0.10,
            "sentiment_extremes": 0.08,
            "flow_of_funds": 0.08,
            "calendar_effects": 0.05,
            "earnings_revisions": 0.08,
            "insider_trading": 0.07,
            "credit_market": 0.10,
            "macro_surprise": 0.06,
            "central_bank_balance_sheet": 0.06,
        }

    def aggregate(self, signals: List[AlphaSignal]) -> Dict[str, Any]:
        """Aggregate multiple alpha signals into a unified view."""
        if not signals:
            return {"direction": "neutral", "conviction": 0, "signal_count": 0}

        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0

        for sig in signals:
            w = self._source_weights.get(sig.source, 0.05) * sig.confidence
            total_weight += w
            score = sig.strength * w
            if sig.direction == SignalDirection.BULLISH:
                bullish_score += score
            elif sig.direction == SignalDirection.BEARISH:
                bearish_score += score

        if total_weight == 0:
            return {"direction": "neutral", "conviction": 0, "signal_count": len(signals)}

        net = (bullish_score - bearish_score) / total_weight
        conviction = abs(net)

        # Agreement ratio
        bullish_count = sum(1 for s in signals if s.direction == SignalDirection.BULLISH)
        bearish_count = sum(1 for s in signals if s.direction == SignalDirection.BEARISH)
        agreement = max(bullish_count, bearish_count) / max(len(signals), 1)

        return {
            "direction": "bullish" if net > 0.05 else "bearish" if net < -0.05 else "neutral",
            "conviction": min(1.0, conviction),
            "net_score": net,
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
            "agreement_ratio": agreement,
            "signal_count": len(signals),
            "horizon_breakdown": self._group_by_horizon(signals),
        }

    def _group_by_horizon(self, signals: List[AlphaSignal]) -> Dict[str, str]:
        horizons = {}
        for sig in signals:
            if sig.horizon not in horizons:
                horizons[sig.horizon] = []
            horizons[sig.horizon].append(sig.direction.value)
        result = {}
        for h, dirs in horizons.items():
            bull = dirs.count("bullish")
            bear = dirs.count("bearish")
            result[h] = "bullish" if bull > bear else "bearish" if bear > bull else "mixed"
        return result
