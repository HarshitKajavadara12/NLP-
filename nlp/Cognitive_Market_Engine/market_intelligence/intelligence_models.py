"""
Market Intelligence Models — 9 Advanced Concepts
==================================================
Implements: Alternative Data Fusion, Regime Detection (HMM),
Crowding Risk, Liquidity Forecasting, Cross-Market Arbitrage,
Sentiment Decay Modeling, Information Cascade Detection,
Reflexivity Modeling, Dark Pool / Private Venue Analysis.
"""
import time
import math
import logging
import statistics
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
from enum import Enum

logger = logging.getLogger("cme.market_intelligence")


@dataclass
class IntelSignal:
    """Standardized market intelligence signal."""
    source: str
    signal_type: str
    severity: float  # 0–1
    description: str
    asset: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


# ─────────────────────────────────────────────────────────────
# 1. Alternative Data Fusion
# ─────────────────────────────────────────────────────────────

class AlternativeDataFusion:
    """
    Fuses non-traditional data sources into market signals:
    - Satellite imagery (parking lot fill, oil storage, shipping)
    - Credit card spending data (consumer health)
    - Web traffic & app downloads (company growth proxy)
    - Job postings (hiring = growth, layoffs = contraction)
    - Patent filings (innovation pipeline)
    - Supply chain data (shipping volumes, port congestion)
    """

    def __init__(self):
        self._data_streams: Dict[str, List[Dict]] = {}
        self._category_weights = {
            "satellite": 0.15,
            "credit_card": 0.20,
            "web_traffic": 0.15,
            "app_downloads": 0.10,
            "job_postings": 0.15,
            "patent_filings": 0.05,
            "supply_chain": 0.10,
            "social_activity": 0.10,
        }

    def ingest_data(self, category: str, data: Dict[str, Any]) -> None:
        """Ingest alternative data point.
        data: {timestamp, asset, value, prior_value, zscore, description}
        """
        if category not in self._data_streams:
            self._data_streams[category] = []
        data.setdefault("timestamp", time.time())
        self._data_streams[category].append(data)
        if len(self._data_streams[category]) > 500:
            self._data_streams[category] = self._data_streams[category][-500:]

    def compute_composite_score(self, asset: str) -> Dict[str, Any]:
        """Compute composite alternative data score for an asset."""
        scores = {}
        total_weight = 0
        weighted_sum = 0

        for cat, weight in self._category_weights.items():
            stream = self._data_streams.get(cat, [])
            relevant = [d for d in stream if d.get("asset") == asset]
            if not relevant:
                continue
            latest = relevant[-1]
            zscore = latest.get("zscore", 0)
            # Normalize to -1 to +1
            normalized = max(-1, min(1, zscore / 3))
            scores[cat] = {
                "zscore": zscore,
                "normalized": normalized,
                "value": latest.get("value"),
                "prior": latest.get("prior_value"),
            }
            weighted_sum += normalized * weight
            total_weight += weight

        composite = weighted_sum / max(total_weight, 0.01)

        return {
            "composite_score": composite,
            "direction": "bullish" if composite > 0.2 else "bearish" if composite < -0.2 else "neutral",
            "components": scores,
            "data_richness": len(scores) / len(self._category_weights),
        }

    def detect_divergences(self, asset: str) -> List[Dict]:
        """Detect divergences between alternative data categories."""
        divergences = []
        scores = {}
        for cat in self._category_weights:
            stream = self._data_streams.get(cat, [])
            relevant = [d for d in stream if d.get("asset") == asset]
            if relevant:
                scores[cat] = relevant[-1].get("zscore", 0)

        categories = list(scores.keys())
        for i in range(len(categories)):
            for j in range(i + 1, len(categories)):
                z1 = scores[categories[i]]
                z2 = scores[categories[j]]
                if (z1 > 1 and z2 < -1) or (z1 < -1 and z2 > 1):
                    divergences.append({
                        "category_a": categories[i],
                        "zscore_a": z1,
                        "category_b": categories[j],
                        "zscore_b": z2,
                        "spread": abs(z1 - z2),
                    })
        return sorted(divergences, key=lambda x: x["spread"], reverse=True)

    def generate_signal(self, asset: str) -> IntelSignal:
        composite = self.compute_composite_score(asset)
        divergences = self.detect_divergences(asset)

        desc_parts = [f"Alt data composite: {composite['composite_score']:+.2f} ({composite['direction']})"]
        if divergences:
            desc_parts.append(f"{len(divergences)} data divergence(s) detected")

        return IntelSignal(
            source="alternative_data",
            signal_type=composite["direction"],
            severity=min(1.0, abs(composite["composite_score"])),
            description="; ".join(desc_parts),
            asset=asset,
            metadata={**composite, "divergences": divergences},
        )


# ─────────────────────────────────────────────────────────────
# 2. Regime Detection (Hidden Markov Model)
# ─────────────────────────────────────────────────────────────

class MarketRegime(Enum):
    BULL_QUIET = "bull_quiet"       # Low vol uptrend
    BULL_VOLATILE = "bull_volatile"  # High vol uptrend
    BEAR_QUIET = "bear_quiet"       # Low vol downtrend
    BEAR_VOLATILE = "bear_volatile"  # Crisis / crash
    RANGING = "ranging"             # Sideways chop


class RegimeDetector:
    """
    Statistical regime change detection using:
    - Hidden Markov Model (simplified Viterbi)
    - CUSUM change-point detection
    - Volatility regime classification
    - Correlation regime (risk-on / risk-off)

    Goes beyond keyword classification to use actual price/vol data.
    """

    def __init__(self, lookback: int = 252):
        self._lookback = lookback
        self._returns: Dict[str, deque] = {}
        self._volatility: Dict[str, deque] = {}
        # Transition probabilities (simplified HMM)
        self._transition_matrix = {
            MarketRegime.BULL_QUIET: {
                MarketRegime.BULL_QUIET: 0.85,
                MarketRegime.BULL_VOLATILE: 0.07,
                MarketRegime.RANGING: 0.05,
                MarketRegime.BEAR_QUIET: 0.02,
                MarketRegime.BEAR_VOLATILE: 0.01,
            },
            MarketRegime.BULL_VOLATILE: {
                MarketRegime.BULL_QUIET: 0.15,
                MarketRegime.BULL_VOLATILE: 0.55,
                MarketRegime.RANGING: 0.10,
                MarketRegime.BEAR_QUIET: 0.05,
                MarketRegime.BEAR_VOLATILE: 0.15,
            },
            MarketRegime.BEAR_QUIET: {
                MarketRegime.BULL_QUIET: 0.05,
                MarketRegime.BULL_VOLATILE: 0.03,
                MarketRegime.RANGING: 0.10,
                MarketRegime.BEAR_QUIET: 0.75,
                MarketRegime.BEAR_VOLATILE: 0.07,
            },
            MarketRegime.BEAR_VOLATILE: {
                MarketRegime.BULL_QUIET: 0.02,
                MarketRegime.BULL_VOLATILE: 0.15,
                MarketRegime.RANGING: 0.08,
                MarketRegime.BEAR_QUIET: 0.10,
                MarketRegime.BEAR_VOLATILE: 0.65,
            },
            MarketRegime.RANGING: {
                MarketRegime.BULL_QUIET: 0.20,
                MarketRegime.BULL_VOLATILE: 0.05,
                MarketRegime.RANGING: 0.50,
                MarketRegime.BEAR_QUIET: 0.15,
                MarketRegime.BEAR_VOLATILE: 0.10,
            },
        }
        self._current_regime: Dict[str, MarketRegime] = {}
        self._regime_duration: Dict[str, int] = {}

    def update_price(self, asset: str, price: float) -> None:
        if asset not in self._returns:
            self._returns[asset] = deque(maxlen=self._lookback)
            self._volatility[asset] = deque(maxlen=self._lookback)
        returns = self._returns[asset]
        if returns:
            prev_price = returns[-1]  # stored as prices for convenience
            ret = (price - prev_price) / prev_price if prev_price != 0 else 0
            self._volatility[asset].append(abs(ret))
        self._returns[asset].append(price)

    def _classify_observation(self, asset: str) -> Optional[MarketRegime]:
        """Classify current observation into a regime."""
        prices = list(self._returns.get(asset, []))
        vols = list(self._volatility.get(asset, []))
        if len(prices) < 20 or len(vols) < 20:
            return None

        # 20-day return
        ret_20d = (prices[-1] - prices[-20]) / prices[-20] if prices[-20] != 0 else 0
        # 20-day volatility
        vol_20d = statistics.mean(vols[-20:]) if vols[-20:] else 0
        # Long-term volatility for comparison
        vol_long = statistics.mean(vols) if vols else vol_20d

        is_bull = ret_20d > 0.005
        is_bear = ret_20d < -0.005
        is_high_vol = vol_20d > vol_long * 1.3

        if is_bull and not is_high_vol:
            return MarketRegime.BULL_QUIET
        elif is_bull and is_high_vol:
            return MarketRegime.BULL_VOLATILE
        elif is_bear and not is_high_vol:
            return MarketRegime.BEAR_QUIET
        elif is_bear and is_high_vol:
            return MarketRegime.BEAR_VOLATILE
        else:
            return MarketRegime.RANGING

    def detect_regime(self, asset: str) -> Dict[str, Any]:
        """Detect current regime with transition probability."""
        observed = self._classify_observation(asset)
        if observed is None:
            return {"regime": "unknown", "confidence": 0}

        prev_regime = self._current_regime.get(asset, MarketRegime.RANGING)
        transition_prob = self._transition_matrix[prev_regime].get(observed, 0.1)

        if observed != prev_regime:
            self._regime_duration[asset] = 1
        else:
            self._regime_duration[asset] = self._regime_duration.get(asset, 0) + 1

        self._current_regime[asset] = observed
        duration = self._regime_duration.get(asset, 1)

        # Confidence increases with duration
        confidence = min(0.95, 0.4 + min(duration, 20) * 0.025)

        return {
            "regime": observed.value,
            "previous_regime": prev_regime.value,
            "transition_prob": transition_prob,
            "duration_days": duration,
            "confidence": confidence,
            "changed": observed != prev_regime,
        }

    def cusum_changepoint(self, asset: str, threshold: float = 2.0) -> Dict[str, Any]:
        """CUSUM change-point detection."""
        prices = list(self._returns.get(asset, []))
        if len(prices) < 30:
            return {"changepoint_detected": False}

        returns = [(prices[i] - prices[i - 1]) / prices[i - 1]
                   for i in range(1, len(prices)) if prices[i - 1] != 0]
        if len(returns) < 20:
            return {"changepoint_detected": False}

        mean_ret = statistics.mean(returns)
        std_ret = statistics.stdev(returns) if len(returns) > 1 else 0.01
        if std_ret == 0:
            std_ret = 0.01

        # Cumulative sum of deviations
        cusum_pos = 0.0
        cusum_neg = 0.0
        max_cusum = 0.0
        changepoint_idx = -1

        for i, r in enumerate(returns):
            z = (r - mean_ret) / std_ret
            cusum_pos = max(0, cusum_pos + z - 0.5)
            cusum_neg = max(0, cusum_neg - z - 0.5)
            current_max = max(cusum_pos, cusum_neg)
            if current_max > max_cusum:
                max_cusum = current_max
                changepoint_idx = i

        detected = max_cusum > threshold

        return {
            "changepoint_detected": detected,
            "cusum_statistic": max_cusum,
            "threshold": threshold,
            "changepoint_index": changepoint_idx if detected else -1,
            "periods_ago": len(returns) - changepoint_idx if detected else 0,
        }

    def generate_signal(self, asset: str) -> IntelSignal:
        regime = self.detect_regime(asset)
        cusum = self.cusum_changepoint(asset)

        parts = [f"Regime: {regime['regime']} (day {regime['duration_days']})"]
        if regime["changed"]:
            parts.append(f"REGIME CHANGE from {regime['previous_regime']}")
        if cusum["changepoint_detected"]:
            parts.append(f"CUSUM changepoint detected (stat={cusum['cusum_statistic']:.2f})")

        return IntelSignal(
            source="regime_detection",
            signal_type="regime_change" if regime["changed"] else "regime_continuation",
            severity=0.8 if regime["changed"] else 0.2,
            description="; ".join(parts),
            asset=asset,
            metadata={**regime, "cusum": cusum},
        )


# ─────────────────────────────────────────────────────────────
# 3. Crowding Risk Detector
# ─────────────────────────────────────────────────────────────

class CrowdingRiskDetector:
    """
    Detects when too many participants are on the same side:
    - Short interest concentration (short squeeze risk)
    - Factor crowding (quant strategies overlap)
    - ETF concentration risk (forced liquidation cascades)
    - Momentum crowding (trend-following pileup)
    """

    def __init__(self):
        self._short_interest: Dict[str, List[Dict]] = {}
        self._factor_exposures: Dict[str, Dict[str, float]] = {}
        self._etf_holdings: Dict[str, Dict[str, float]] = {}

    def update_short_interest(self, asset: str, data: Dict) -> None:
        """data: {date, short_interest, shares_outstanding, short_pct_float,
                  days_to_cover, cost_to_borrow}"""
        if asset not in self._short_interest:
            self._short_interest[asset] = []
        self._short_interest[asset].append(data)

    def update_factor_exposure(self, fund: str, exposures: Dict[str, float]) -> None:
        """Track fund's factor exposures: {momentum, value, size, quality, volatility}"""
        self._factor_exposures[fund] = exposures

    def update_etf_holdings(self, etf: str, holdings: Dict[str, float]) -> None:
        """Track ETF holdings: {ticker: weight}"""
        self._etf_holdings[etf] = holdings

    def analyze_short_squeeze_risk(self, asset: str) -> Dict[str, Any]:
        """Assess short squeeze probability."""
        history = self._short_interest.get(asset, [])
        if not history:
            return {"risk_level": "no_data", "score": 0}

        latest = history[-1]
        short_pct = latest.get("short_pct_float", 0)
        dtc = latest.get("days_to_cover", 0)
        ctb = latest.get("cost_to_borrow", 0)

        score = 0.0
        factors = []

        if short_pct > 30:
            score += 0.35
            factors.append(f"Short interest {short_pct:.0f}% of float (>30% critical)")
        elif short_pct > 20:
            score += 0.2
            factors.append(f"Short interest {short_pct:.0f}% of float (elevated)")

        if dtc > 5:
            score += 0.25
            factors.append(f"Days-to-cover {dtc:.1f} (>5 days = illiquid shorts)")
        elif dtc > 3:
            score += 0.15

        if ctb > 20:
            score += 0.2
            factors.append(f"Cost-to-borrow {ctb:.0f}% (expensive)")

        # Trend: is SI increasing?
        if len(history) >= 4:
            prev_pct = history[-4].get("short_pct_float", short_pct)
            if short_pct > prev_pct * 1.2:
                score += 0.15
                factors.append("Short interest accelerating (+20% over last 4 readings)")

        return {
            "score": min(1.0, score),
            "risk_level": ("critical" if score > 0.7 else
                           "high" if score > 0.5 else
                           "moderate" if score > 0.3 else "low"),
            "factors": factors,
            "short_pct_float": short_pct,
            "days_to_cover": dtc,
        }

    def detect_factor_crowding(self) -> Dict[str, Any]:
        """Detect factor crowding across funds."""
        if len(self._factor_exposures) < 3:
            return {"crowded_factors": [], "risk": "insufficient_data"}

        # Find factors where many funds have same direction
        factor_directions: Dict[str, List[float]] = {}
        for fund, exposures in self._factor_exposures.items():
            for factor, exposure in exposures.items():
                if factor not in factor_directions:
                    factor_directions[factor] = []
                factor_directions[factor].append(exposure)

        crowded = []
        for factor, exposures in factor_directions.items():
            if len(exposures) < 3:
                continue
            avg = statistics.mean(exposures)
            same_sign = sum(1 for e in exposures if (e > 0) == (avg > 0)) / len(exposures)
            if same_sign > 0.75 and abs(avg) > 0.5:
                crowded.append({
                    "factor": factor,
                    "agreement_ratio": same_sign,
                    "avg_exposure": avg,
                    "fund_count": len(exposures),
                })

        return {
            "crowded_factors": crowded,
            "risk": "high" if len(crowded) >= 2 else "moderate" if crowded else "low",
        }

    def detect_etf_concentration(self, asset: str) -> Dict[str, Any]:
        """How many ETFs hold this asset → forced selling cascade risk."""
        etf_count = 0
        total_weight = 0
        for etf, holdings in self._etf_holdings.items():
            if asset in holdings:
                etf_count += 1
                total_weight += holdings[asset]

        return {
            "etfs_holding": etf_count,
            "total_etf_weight": total_weight,
            "concentration_risk": "high" if etf_count > 50 and total_weight > 5 else
                                  "moderate" if etf_count > 20 else "low",
        }

    def generate_signal(self, asset: str) -> IntelSignal:
        squeeze = self.analyze_short_squeeze_risk(asset)
        factor = self.detect_factor_crowding()
        etf = self.detect_etf_concentration(asset)

        parts = [f"Short squeeze risk: {squeeze['risk_level']} ({squeeze['score']:.2f})"]
        if factor["crowded_factors"]:
            parts.append(f"Factor crowding in {', '.join(f['factor'] for f in factor['crowded_factors'])}")
        if etf["concentration_risk"] != "low":
            parts.append(f"ETF concentration {etf['concentration_risk']} ({etf['etfs_holding']} ETFs)")

        return IntelSignal(
            source="crowding_risk",
            signal_type="crowding_warning" if squeeze["score"] > 0.5 else "normal",
            severity=squeeze["score"],
            description="; ".join(parts),
            asset=asset,
            metadata={"short_squeeze": squeeze, "factor_crowding": factor,
                      "etf_concentration": etf},
        )


# ─────────────────────────────────────────────────────────────
# 4. Liquidity Forecasting
# ─────────────────────────────────────────────────────────────

class LiquidityForecaster:
    """
    Predicts when liquidity will evaporate:
    - Pre-event thinning (FOMC, NFP, CPI)
    - Holiday liquidity decay
    - Flash crash condition detection
    - Intraday liquidity cycles
    - Market maker withdrawal detection
    """

    def __init__(self):
        self._volume_history: Dict[str, deque] = {}
        self._spread_history: Dict[str, deque] = {}
        self._depth_history: Dict[str, deque] = {}
        self._scheduled_events: List[Dict] = []

    def update_liquidity_snapshot(self, asset: str, data: Dict) -> None:
        """data: {timestamp, volume, avg_spread_bps, depth_usd, trade_count}"""
        for field_name, history in [
            ("volume", self._volume_history),
            ("avg_spread_bps", self._spread_history),
            ("depth_usd", self._depth_history),
        ]:
            if asset not in history:
                history[asset] = deque(maxlen=500)
            history[asset].append(data.get(field_name, 0))

    def add_scheduled_event(self, event: Dict) -> None:
        """event: {name, timestamp, impact_level (1-5), pre_event_thinning_hours}"""
        self._scheduled_events.append(event)
        self._scheduled_events.sort(key=lambda x: x.get("timestamp", 0))

    def forecast_liquidity(self, asset: str, hours_ahead: int = 24) -> Dict[str, Any]:
        """Forecast liquidity conditions for the next N hours."""
        volumes = list(self._volume_history.get(asset, []))
        spreads = list(self._spread_history.get(asset, []))
        depths = list(self._depth_history.get(asset, []))

        # Current vs average
        current_factors = {}
        if volumes and len(volumes) > 20:
            avg_vol = statistics.mean(volumes[-20:])
            current_vol = volumes[-1] if volumes else avg_vol
            vol_ratio = current_vol / max(avg_vol, 1)
            current_factors["volume_ratio"] = vol_ratio
        else:
            vol_ratio = 1.0

        if spreads and len(spreads) > 20:
            avg_spread = statistics.mean(spreads[-20:])
            current_spread = spreads[-1] if spreads else avg_spread
            spread_ratio = current_spread / max(avg_spread, 0.01)
            current_factors["spread_ratio"] = spread_ratio
        else:
            spread_ratio = 1.0

        if depths and len(depths) > 20:
            avg_depth = statistics.mean(depths[-20:])
            current_depth = depths[-1] if depths else avg_depth
            depth_ratio = current_depth / max(avg_depth, 1)
            current_factors["depth_ratio"] = depth_ratio
        else:
            depth_ratio = 1.0

        # Composite liquidity score (higher = more liquid)
        liquidity_score = (
            0.4 * min(vol_ratio, 2.0) +
            0.3 * min(1.0 / max(spread_ratio, 0.01), 2.0) +
            0.3 * min(depth_ratio, 2.0)
        )

        # Event proximity check
        now = time.time()
        upcoming_events = [
            e for e in self._scheduled_events
            if 0 < (e.get("timestamp", 0) - now) < hours_ahead * 3600
        ]

        event_risk = 0.0
        for ev in upcoming_events:
            hours_to_event = (ev["timestamp"] - now) / 3600
            thinning = ev.get("pre_event_thinning_hours", 4)
            if hours_to_event < thinning:
                event_risk += ev.get("impact_level", 3) * 0.1
                event_risk *= (1 - hours_to_event / thinning)

        # Flash crash conditions
        flash_risk = 0.0
        if vol_ratio < 0.3:
            flash_risk += 0.3
        if spread_ratio > 3.0:
            flash_risk += 0.3
        if depth_ratio < 0.2:
            flash_risk += 0.4

        forecast_level = ("dry" if liquidity_score < 0.5 else
                          "thin" if liquidity_score < 0.8 else
                          "normal" if liquidity_score < 1.2 else "deep")

        return {
            "liquidity_score": liquidity_score,
            "forecast_level": forecast_level,
            "current_factors": current_factors,
            "event_risk": min(1.0, event_risk),
            "flash_crash_risk": min(1.0, flash_risk),
            "upcoming_events": len(upcoming_events),
            "warnings": (
                (["Pre-event liquidity thinning expected"] if event_risk > 0.3 else []) +
                (["Flash crash conditions detected"] if flash_risk > 0.6 else []) +
                (["Abnormally thin liquidity"] if liquidity_score < 0.5 else [])
            ),
        }

    def generate_signal(self, asset: str) -> IntelSignal:
        forecast = self.forecast_liquidity(asset)
        return IntelSignal(
            source="liquidity_forecast",
            signal_type=forecast["forecast_level"],
            severity=max(forecast["event_risk"], forecast["flash_crash_risk"],
                         1.0 - min(forecast["liquidity_score"], 1.0)),
            description=(f"Liquidity {forecast['forecast_level']} "
                         f"(score={forecast['liquidity_score']:.2f})" +
                         (f'; {"; ".join(forecast["warnings"])}' if forecast["warnings"] else "")),
            asset=asset,
            metadata=forecast,
        )


# ─────────────────────────────────────────────────────────────
# 5. Cross-Market Arbitrage
# ─────────────────────────────────────────────────────────────

class CrossMarketArbitrage:
    """
    Detects mispricings between related instruments:
    - Equity vs CDS (Merton model implied)
    - Spot vs futures (basis trade)
    - ADR vs local shares
    - ETF vs NAV
    - Options put-call parity violations
    """

    def __init__(self):
        self._price_pairs: Dict[str, Dict[str, deque]] = {}

    def update_pair(self, pair_name: str, instrument_a: str,
                    price_a: float, instrument_b: str, price_b: float) -> None:
        """Update a price pair for relationship tracking."""
        if pair_name not in self._price_pairs:
            self._price_pairs[pair_name] = {
                "a_name": instrument_a, "b_name": instrument_b,
                "a_prices": deque(maxlen=500),
                "b_prices": deque(maxlen=500),
                "spreads": deque(maxlen=500),
            }
        pair = self._price_pairs[pair_name]
        pair["a_prices"].append(price_a)
        pair["b_prices"].append(price_b)
        if price_b != 0:
            pair["spreads"].append(price_a / price_b - 1)
        else:
            pair["spreads"].append(0)

    def detect_basis_trade(self, pair_name: str) -> Optional[Dict]:
        """Detect futures basis mispricing (spot vs futures)."""
        pair = self._price_pairs.get(pair_name)
        if not pair or len(pair["spreads"]) < 20:
            return None

        spreads = list(pair["spreads"])
        current = spreads[-1]
        mean_spread = statistics.mean(spreads)
        std_spread = statistics.stdev(spreads) if len(spreads) > 1 else 0.001
        if std_spread == 0:
            std_spread = 0.001

        zscore = (current - mean_spread) / std_spread

        if abs(zscore) > 2.0:
            return {
                "pair": pair_name,
                "type": "basis",
                "current_spread": current,
                "mean_spread": mean_spread,
                "zscore": zscore,
                "action": "sell_rich_buy_cheap" if zscore > 0 else "buy_rich_sell_cheap",
                "signal_strength": min(1.0, (abs(zscore) - 1.5) / 2),
            }
        return None

    def detect_etf_nav_deviation(self, etf_name: str) -> Optional[Dict]:
        """Detect ETF premium/discount to NAV."""
        pair = self._price_pairs.get(etf_name)
        if not pair or len(pair["spreads"]) < 5:
            return None

        current_spread = list(pair["spreads"])[-1]
        # ETFs should trade at NAV; >0.5% deviation = signal
        if abs(current_spread) > 0.005:
            return {
                "pair": etf_name,
                "type": "etf_nav",
                "premium_discount": current_spread,
                "action": "sell_etf" if current_spread > 0 else "buy_etf",
                "signal_strength": min(1.0, abs(current_spread) * 100),
            }
        return None

    def detect_put_call_parity_violation(self, data: Dict) -> Optional[Dict]:
        """Check put-call parity: C - P = S*e^(-qT) - K*e^(-rT)
        data: {call_price, put_price, spot, strike, risk_free_rate,
               dividend_yield, time_to_expiry}
        """
        C = data.get("call_price", 0)
        P = data.get("put_price", 0)
        S = data.get("spot", 0)
        K = data.get("strike", 0)
        r = data.get("risk_free_rate", 0.05)
        q = data.get("dividend_yield", 0)
        T = data.get("time_to_expiry", 0.25)

        if S <= 0 or K <= 0 or C <= 0 or P <= 0:
            return None

        theoretical = S * math.exp(-q * T) - K * math.exp(-r * T)
        actual = C - P
        violation = actual - theoretical

        if abs(violation) > 0.01 * S:  # > 1% of spot
            return {
                "type": "put_call_parity",
                "violation_pct": violation / S * 100,
                "theoretical_diff": theoretical,
                "actual_diff": actual,
                "action": ("buy_put_sell_call" if violation > 0 else
                           "buy_call_sell_put"),
            }
        return None

    def scan_all_pairs(self) -> List[Dict]:
        """Scan all tracked pairs for mispricings."""
        opportunities = []
        for pair_name in self._price_pairs:
            basis = self.detect_basis_trade(pair_name)
            if basis:
                opportunities.append(basis)
            etf = self.detect_etf_nav_deviation(pair_name)
            if etf:
                opportunities.append(etf)
        return sorted(opportunities,
                      key=lambda x: x.get("signal_strength", 0), reverse=True)

    def generate_signal(self, asset: str = "all") -> IntelSignal:
        opps = self.scan_all_pairs()
        if not opps:
            return IntelSignal(
                source="cross_market_arb",
                signal_type="no_opportunities",
                severity=0, description="No arbitrage opportunities detected",
                asset=asset,
            )
        best = opps[0]
        return IntelSignal(
            source="cross_market_arb",
            signal_type="arbitrage_opportunity",
            severity=best.get("signal_strength", 0),
            description=(f"{best['type']} opportunity in {best['pair']}: "
                         f"{best.get('action', 'evaluate')}"),
            asset=asset,
            metadata={"opportunities": opps, "best": best},
        )


# ─────────────────────────────────────────────────────────────
# 6. Sentiment Decay Modeling
# ─────────────────────────────────────────────────────────────

class SentimentDecayModel:
    """
    Models how quickly news sentiment impact decays over time.
    Decay varies by: event type, market regime, magnitude.
    
    Uses exponential decay with regime-dependent half-lives.
    """

    # Half-lives in hours
    DECAY_PROFILES = {
        "rate_decision": {"base_halflife": 48, "high_vol_multiplier": 0.6, "low_vol_multiplier": 1.5},
        "earnings": {"base_halflife": 24, "high_vol_multiplier": 0.8, "low_vol_multiplier": 1.2},
        "geopolitical": {"base_halflife": 72, "high_vol_multiplier": 0.5, "low_vol_multiplier": 2.0},
        "economic_data": {"base_halflife": 12, "high_vol_multiplier": 0.7, "low_vol_multiplier": 1.3},
        "regulatory": {"base_halflife": 168, "high_vol_multiplier": 0.8, "low_vol_multiplier": 1.0},
        "rumor": {"base_halflife": 4, "high_vol_multiplier": 0.5, "low_vol_multiplier": 0.8},
        "social_media": {"base_halflife": 2, "high_vol_multiplier": 0.3, "low_vol_multiplier": 0.5},
        "generic": {"base_halflife": 8, "high_vol_multiplier": 0.7, "low_vol_multiplier": 1.2},
    }

    def __init__(self):
        self._active_sentiments: List[Dict] = []
        self._decay_history: List[Dict] = []

    def add_sentiment_event(self, event: Dict[str, Any]) -> None:
        """event: {timestamp, event_type, initial_magnitude, direction, asset}"""
        event.setdefault("timestamp", time.time())
        profile = self.DECAY_PROFILES.get(
            event.get("event_type", "generic"),
            self.DECAY_PROFILES["generic"]
        )
        event["halflife_hours"] = profile["base_halflife"]
        event["profile"] = profile
        self._active_sentiments.append(event)

    def compute_current_impact(self, event: Dict, regime: str = "normal") -> float:
        """Compute remaining sentiment impact at current time."""
        elapsed_hours = (time.time() - event.get("timestamp", time.time())) / 3600
        halflife = event.get("halflife_hours", 8)
        profile = event.get("profile", {})

        if regime == "high_volatility":
            halflife *= profile.get("high_vol_multiplier", 0.7)
        elif regime == "low_volatility":
            halflife *= profile.get("low_vol_multiplier", 1.2)

        if halflife <= 0:
            halflife = 1

        decay_factor = math.exp(-0.693 * elapsed_hours / halflife)
        initial = event.get("initial_magnitude", 1.0)
        return initial * decay_factor

    def compute_aggregate_sentiment(self, asset: str,
                                     regime: str = "normal") -> Dict[str, Any]:
        """Compute aggregate decayed sentiment for an asset."""
        relevant = [e for e in self._active_sentiments if e.get("asset") == asset]

        bullish_impact = 0.0
        bearish_impact = 0.0
        active_count = 0

        for event in relevant:
            impact = self.compute_current_impact(event, regime)
            if impact < 0.01:  # negligible
                continue
            active_count += 1
            if event.get("direction") == "bullish":
                bullish_impact += impact
            else:
                bearish_impact += impact

        net = bullish_impact - bearish_impact
        return {
            "net_sentiment": net,
            "bullish_impact": bullish_impact,
            "bearish_impact": bearish_impact,
            "active_events": active_count,
            "direction": "bullish" if net > 0.1 else "bearish" if net < -0.1 else "neutral",
        }

    def predict_decay_timeline(self, event: Dict, regime: str = "normal",
                                hours: int = 72) -> List[Tuple[float, float]]:
        """Predict impact levels at future time points."""
        timeline = []
        for h in range(0, hours + 1, max(1, hours // 20)):
            saved_time = event.get("timestamp", time.time())
            event["timestamp"] = time.time() - h * 3600  # simulate elapsed time
            impact = self.compute_current_impact(event, regime)
            event["timestamp"] = saved_time
            # Actually compute forward
            halflife = event.get("halflife_hours", 8)
            profile = event.get("profile", {})
            if regime == "high_volatility":
                halflife *= profile.get("high_vol_multiplier", 0.7)
            elif regime == "low_volatility":
                halflife *= profile.get("low_vol_multiplier", 1.2)
            decay = math.exp(-0.693 * h / max(halflife, 1))
            initial = event.get("initial_magnitude", 1.0)
            timeline.append((h, initial * decay))
        return timeline

    def cleanup_expired(self, min_impact: float = 0.01) -> int:
        """Remove events with negligible impact."""
        before = len(self._active_sentiments)
        self._active_sentiments = [
            e for e in self._active_sentiments
            if self.compute_current_impact(e) >= min_impact
        ]
        return before - len(self._active_sentiments)

    def generate_signal(self, asset: str, regime: str = "normal") -> IntelSignal:
        agg = self.compute_aggregate_sentiment(asset, regime)
        return IntelSignal(
            source="sentiment_decay",
            signal_type=agg["direction"],
            severity=min(1.0, abs(agg["net_sentiment"])),
            description=(f"Net decayed sentiment {agg['net_sentiment']:+.2f} "
                         f"({agg['active_events']} active events)"),
            asset=asset,
            metadata=agg,
        )


# ─────────────────────────────────────────────────────────────
# 7. Information Cascade Detection
# ─────────────────────────────────────────────────────────────

class InformationCascadeDetector:
    """
    Identifies when market participants are copying each other
    rather than independently analyzing information.
    
    Signs of cascade:
    - Sequential decisions in same direction with accelerating pace
    - Decreasing decision quality / analysis depth over time
    - Price moving without proportional information
    - Herding metrics (correlation of trades increases)
    """

    def __init__(self):
        self._decision_sequence: List[Dict] = []
        self._analysis_depth_scores: List[float] = []

    def record_decision(self, data: Dict[str, Any]) -> None:
        """data: {timestamp, participant, direction, confidence, has_independent_analysis,
                  information_ratio, asset}"""
        data.setdefault("timestamp", time.time())
        self._decision_sequence.append(data)
        if len(self._decision_sequence) > 1000:
            self._decision_sequence = self._decision_sequence[-1000:]

    def detect_cascade(self, asset: str, window_minutes: int = 60) -> Dict[str, Any]:
        """Detect information cascade in recent decisions."""
        cutoff = time.time() - window_minutes * 60
        recent = [d for d in self._decision_sequence
                  if d.get("timestamp", 0) > cutoff and d.get("asset") == asset]

        if len(recent) < 5:
            return {"cascade_detected": False, "confidence": 0}

        # 1. Directional agreement
        directions = [d.get("direction", "neutral") for d in recent]
        bull = directions.count("bullish")
        bear = directions.count("bearish")
        agreement = max(bull, bear) / len(directions)

        # 2. Declining independent analysis
        independent = [d for d in recent if d.get("has_independent_analysis", True)]
        independent_ratio = len(independent) / len(recent)

        # 3. Accelerating pace (inter-decision time shrinking)
        timestamps = [d.get("timestamp", 0) for d in recent]
        timestamps.sort()
        if len(timestamps) >= 3:
            gaps = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
            early_gap = statistics.mean(gaps[:len(gaps) // 2]) if len(gaps) >= 2 else gaps[0]
            late_gap = statistics.mean(gaps[len(gaps) // 2:]) if len(gaps) >= 2 else gaps[-1]
            acceleration = early_gap / max(late_gap, 1) if late_gap > 0 else 1
        else:
            acceleration = 1.0

        # 4. Information content declining
        info_ratios = [d.get("information_ratio", 1.0) for d in recent]
        if len(info_ratios) >= 4:
            early_ir = statistics.mean(info_ratios[:len(info_ratios) // 2])
            late_ir = statistics.mean(info_ratios[len(info_ratios) // 2:])
            ir_decline = early_ir - late_ir
        else:
            ir_decline = 0

        # Cascade score
        cascade_score = 0.0
        signals = []

        if agreement > 0.8:
            cascade_score += 0.3
            signals.append(f"High directional agreement ({agreement:.0%})")

        if independent_ratio < 0.3:
            cascade_score += 0.25
            signals.append(f"Low independent analysis ({independent_ratio:.0%})")

        if acceleration > 2.0:
            cascade_score += 0.25
            signals.append(f"Decision pace accelerating ({acceleration:.1f}x)")

        if ir_decline > 0.2:
            cascade_score += 0.2
            signals.append(f"Information content declining ({ir_decline:+.2f})")

        cascade_detected = cascade_score > 0.5

        return {
            "cascade_detected": cascade_detected,
            "cascade_score": min(1.0, cascade_score),
            "agreement_ratio": agreement,
            "independent_ratio": independent_ratio,
            "acceleration": acceleration,
            "info_decline": ir_decline,
            "signals": signals,
            "decisions_analyzed": len(recent),
            "dominant_direction": "bullish" if bull > bear else "bearish",
        }

    def generate_signal(self, asset: str) -> IntelSignal:
        result = self.detect_cascade(asset)
        return IntelSignal(
            source="information_cascade",
            signal_type="cascade_warning" if result["cascade_detected"] else "normal",
            severity=result["cascade_score"],
            description=(f"{'CASCADE DETECTED' if result['cascade_detected'] else 'No cascade'}: "
                         f"{'; '.join(result['signals'][:3])}" if result["signals"] else "Normal market"),
            asset=asset,
            metadata=result,
        )


# ─────────────────────────────────────────────────────────────
# 8. Reflexivity Model (Soros)
# ─────────────────────────────────────────────────────────────

class ReflexivityModel:
    """
    Implements George Soros's reflexivity concept:
    Predictions and narratives change the predicted outcome through
    feedback loops between perception and reality.
    
    Models:
    - Narrative → Price → Reinforced Narrative (positive feedback)
    - Narrative → Price → Contradicted Narrative (negative feedback)
    - Identifies when markets are in reflexive boom/bust cycles
    - Measures narrative-price coupling strength
    """

    def __init__(self):
        self._narrative_scores: Dict[str, deque] = {}  # asset → narrative sentiment over time
        self._price_returns: Dict[str, deque] = {}     # asset → returns over time
        self._cycle_state: Dict[str, str] = {}
        self._coupling_history: Dict[str, deque] = {}

    def update(self, asset: str, narrative_score: float, price: float) -> None:
        """Update narrative and price data.
        narrative_score: -1 (very bearish narrative) to +1 (very bullish)
        """
        if asset not in self._narrative_scores:
            self._narrative_scores[asset] = deque(maxlen=252)
            self._price_returns[asset] = deque(maxlen=252)
            self._coupling_history[asset] = deque(maxlen=100)
        self._narrative_scores[asset].append(narrative_score)

        prices = self._price_returns[asset]
        if prices:
            ret = (price - prices[-1]) / prices[-1] if prices[-1] != 0 else 0
        else:
            ret = 0
        self._price_returns[asset].append(price)

    def measure_coupling(self, asset: str, window: int = 20) -> Dict[str, Any]:
        """Measure narrative-price coupling strength."""
        narratives = list(self._narrative_scores.get(asset, []))
        prices = list(self._price_returns.get(asset, []))

        if len(narratives) < window or len(prices) < window:
            return {"coupling": 0, "state": "unknown"}

        narr_window = narratives[-window:]
        price_window = prices[-window:]
        # Compute returns from prices
        returns = [(price_window[i] - price_window[i - 1]) / price_window[i - 1]
                   if price_window[i - 1] != 0 else 0
                   for i in range(1, len(price_window))]
        narr_changes = [(narr_window[i] - narr_window[i - 1])
                        for i in range(1, len(narr_window))]

        n = min(len(returns), len(narr_changes))
        if n < 5:
            return {"coupling": 0, "state": "unknown"}

        returns = returns[:n]
        narr_changes = narr_changes[:n]

        # Correlation between narrative changes and price returns
        mean_r = statistics.mean(returns)
        mean_n = statistics.mean(narr_changes)
        cov = sum((returns[i] - mean_r) * (narr_changes[i] - mean_n)
                  for i in range(n)) / n
        std_r = statistics.stdev(returns) if len(returns) > 1 else 0.001
        std_n = statistics.stdev(narr_changes) if len(narr_changes) > 1 else 0.001
        coupling = cov / (std_r * std_n) if std_r * std_n > 0 else 0

        self._coupling_history[asset].append(coupling)

        # Detect reflexive cycle state
        avg_narrative = statistics.mean(narr_window[-5:])
        avg_coupling = coupling

        if avg_coupling > 0.5 and avg_narrative > 0.3:
            state = "reflexive_boom"
        elif avg_coupling > 0.5 and avg_narrative < -0.3:
            state = "reflexive_bust"
        elif avg_coupling < -0.3:
            state = "negative_feedback"  # Self-correcting
        else:
            state = "normal"

        self._cycle_state[asset] = state

        return {
            "coupling": coupling,
            "state": state,
            "avg_narrative": avg_narrative,
            "narrative_trend": ("intensifying" if len(narr_window) >= 10 and
                                abs(statistics.mean(narr_window[-5:])) > abs(statistics.mean(narr_window[-10:-5])) else
                                "fading"),
        }

    def predict_reflexive_reversal(self, asset: str) -> Dict[str, Any]:
        """Predict when a reflexive cycle might reverse."""
        coupling_hist = list(self._coupling_history.get(asset, []))
        if len(coupling_hist) < 5:
            return {"reversal_risk": 0, "state": self._cycle_state.get(asset, "unknown")}

        state = self._cycle_state.get(asset, "normal")
        recent_coupling = statistics.mean(coupling_hist[-5:])
        earlier_coupling = statistics.mean(coupling_hist[-10:-5]) if len(coupling_hist) >= 10 else recent_coupling

        # Weakening coupling in a boom/bust = reversal warning
        reversal_risk = 0.0
        if state in ("reflexive_boom", "reflexive_bust"):
            if recent_coupling < earlier_coupling:
                reversal_risk = min(1.0, (earlier_coupling - recent_coupling) * 2)

        narratives = list(self._narrative_scores.get(asset, []))
        if narratives and len(narratives) >= 5:
            extremity = abs(statistics.mean(narratives[-5:]))
            if extremity > 0.7:
                reversal_risk = min(1.0, reversal_risk + 0.2)

        return {
            "reversal_risk": reversal_risk,
            "state": state,
            "coupling_trend": "weakening" if recent_coupling < earlier_coupling else "strengthening",
        }

    def generate_signal(self, asset: str) -> IntelSignal:
        coupling = self.measure_coupling(asset)
        reversal = self.predict_reflexive_reversal(asset)

        desc_parts = [f"Reflexive state: {coupling['state']}",
                      f"Coupling: {coupling['coupling']:.2f}"]
        if reversal["reversal_risk"] > 0.3:
            desc_parts.append(f"Reversal risk: {reversal['reversal_risk']:.0%}")

        return IntelSignal(
            source="reflexivity",
            signal_type=coupling["state"],
            severity=max(reversal["reversal_risk"],
                         abs(coupling["coupling"]) if coupling["state"] != "normal" else 0),
            description="; ".join(desc_parts),
            asset=asset,
            metadata={**coupling, **reversal},
        )


# ─────────────────────────────────────────────────────────────
# 9. Dark Pool / Private Venue Analysis
# ─────────────────────────────────────────────────────────────

class DarkPoolAnalyzer:
    """
    Analyzes institutional block trading patterns from dark pools
    and private venues (TRF data, FINRA dark pool volumes).
    
    Key signals:
    - Dark pool volume as % of total (rising = institutional accumulation)
    - Block trade clustering (multiple large trades = coordinated action)
    - Dark vs lit venue price divergence
    - Short sale volume from dark venues
    """

    def __init__(self):
        self._dark_volume: Dict[str, deque] = {}
        self._lit_volume: Dict[str, deque] = {}
        self._block_trades: Dict[str, List[Dict]] = {}
        self._dark_vwap: Dict[str, deque] = {}
        self._lit_vwap: Dict[str, deque] = {}

    def record_volume(self, asset: str, dark_vol: float, lit_vol: float,
                      dark_vwap: float = 0, lit_vwap: float = 0) -> None:
        """Record dark and lit venue volume comparison."""
        for key, history in [
            ("dark", self._dark_volume), ("lit", self._lit_volume),
            ("dark_vwap", self._dark_vwap), ("lit_vwap", self._lit_vwap)
        ]:
            if asset not in history:
                history[asset] = deque(maxlen=252)
            val = {"dark": dark_vol, "lit": lit_vol,
                   "dark_vwap": dark_vwap, "lit_vwap": lit_vwap}[key]
            history[asset].append(val)

    def record_block_trade(self, asset: str, trade: Dict) -> None:
        """trade: {timestamp, size, price, venue, side}"""
        if asset not in self._block_trades:
            self._block_trades[asset] = []
        self._block_trades[asset].append(trade)
        if len(self._block_trades[asset]) > 1000:
            self._block_trades[asset] = self._block_trades[asset][-1000:]

    def analyze_dark_pool_activity(self, asset: str) -> Dict[str, Any]:
        """Analyze dark pool activity for institutional signals."""
        dark = list(self._dark_volume.get(asset, []))
        lit = list(self._lit_volume.get(asset, []))

        if not dark or not lit or len(dark) < 5:
            return {"dark_pct": 0, "signal": "insufficient_data"}

        current_dark_pct = dark[-1] / (dark[-1] + lit[-1]) if (dark[-1] + lit[-1]) > 0 else 0
        avg_dark_pct = statistics.mean(
            d / (d + l) if (d + l) > 0 else 0
            for d, l in zip(dark[-20:], lit[-20:])
        ) if len(dark) >= 20 else current_dark_pct

        # Is dark pool activity elevated?
        dark_ratio = current_dark_pct / max(avg_dark_pct, 0.01)

        # Block trade analysis
        blocks = self._block_trades.get(asset, [])
        recent_blocks = [b for b in blocks if time.time() - b.get("timestamp", 0) < 86400]
        block_buy_vol = sum(b.get("size", 0) for b in recent_blocks if b.get("side") == "buy")
        block_sell_vol = sum(b.get("size", 0) for b in recent_blocks if b.get("side") == "sell")

        # Dark vs lit VWAP divergence
        dark_vwap = list(self._dark_vwap.get(asset, []))
        lit_vwap = list(self._lit_vwap.get(asset, []))
        price_divergence = 0
        if dark_vwap and lit_vwap:
            d_vwap = dark_vwap[-1]
            l_vwap = lit_vwap[-1]
            if l_vwap > 0:
                price_divergence = (d_vwap - l_vwap) / l_vwap

        # Signal interpretation
        signal = "neutral"
        if dark_ratio > 1.5 and block_buy_vol > block_sell_vol * 2:
            signal = "institutional_accumulation"
        elif dark_ratio > 1.5 and block_sell_vol > block_buy_vol * 2:
            signal = "institutional_distribution"
        elif dark_ratio > 1.3:
            signal = "elevated_dark_activity"

        return {
            "dark_pct": current_dark_pct,
            "avg_dark_pct": avg_dark_pct,
            "dark_ratio": dark_ratio,
            "block_buy_vol": block_buy_vol,
            "block_sell_vol": block_sell_vol,
            "block_count": len(recent_blocks),
            "price_divergence": price_divergence,
            "signal": signal,
        }

    def detect_block_clusters(self, asset: str,
                               window_minutes: int = 30) -> List[Dict]:
        """Detect clusters of block trades indicating coordinated institutional action."""
        blocks = self._block_trades.get(asset, [])
        if len(blocks) < 3:
            return []

        cutoff = time.time() - window_minutes * 60
        recent = sorted(
            [b for b in blocks if b.get("timestamp", 0) > cutoff],
            key=lambda b: b.get("timestamp", 0)
        )

        clusters = []
        if len(recent) >= 3:
            total_size = sum(b.get("size", 0) for b in recent)
            sides = [b.get("side", "unknown") for b in recent]
            dominant = max(set(sides), key=sides.count)
            consistency = sides.count(dominant) / len(sides)

            if consistency > 0.7:
                clusters.append({
                    "trade_count": len(recent),
                    "total_size": total_size,
                    "dominant_side": dominant,
                    "consistency": consistency,
                    "duration_minutes": window_minutes,
                })
        return clusters

    def generate_signal(self, asset: str) -> IntelSignal:
        analysis = self.analyze_dark_pool_activity(asset)
        clusters = self.detect_block_clusters(asset)

        desc_parts = [f"Dark pool: {analysis['signal']} ({analysis['dark_pct']:.0%} of volume)"]
        if clusters:
            c = clusters[0]
            desc_parts.append(
                f"Block cluster: {c['trade_count']} trades, {c['dominant_side']} side "
                f"({c['consistency']:.0%} consistent)")

        severity = 0.0
        if analysis["signal"] in ("institutional_accumulation", "institutional_distribution"):
            severity = 0.7
        elif analysis["signal"] == "elevated_dark_activity":
            severity = 0.4

        return IntelSignal(
            source="dark_pool",
            signal_type=analysis["signal"],
            severity=severity,
            description="; ".join(desc_parts),
            asset=asset,
            metadata={**analysis, "clusters": clusters},
        )


# ─────────────────────────────────────────────────────────────
# Unified Market Intelligence Hub
# ─────────────────────────────────────────────────────────────

class MarketIntelligenceHub:
    """Orchestrates all 9 market intelligence models."""

    def __init__(self):
        self.alt_data = AlternativeDataFusion()
        self.regime = RegimeDetector()
        self.crowding = CrowdingRiskDetector()
        self.liquidity = LiquidityForecaster()
        self.arbitrage = CrossMarketArbitrage()
        self.sentiment_decay = SentimentDecayModel()
        self.cascade = InformationCascadeDetector()
        self.reflexivity = ReflexivityModel()
        self.dark_pool = DarkPoolAnalyzer()

    def full_scan(self, asset: str) -> Dict[str, IntelSignal]:
        """Run all intelligence models for an asset."""
        return {
            "alternative_data": self.alt_data.generate_signal(asset),
            "regime": self.regime.generate_signal(asset),
            "crowding_risk": self.crowding.generate_signal(asset),
            "liquidity": self.liquidity.generate_signal(asset),
            "arbitrage": self.arbitrage.generate_signal(asset),
            "sentiment_decay": self.sentiment_decay.generate_signal(asset),
            "information_cascade": self.cascade.generate_signal(asset),
            "reflexivity": self.reflexivity.generate_signal(asset),
            "dark_pool": self.dark_pool.generate_signal(asset),
        }

    def risk_summary(self, asset: str) -> Dict[str, Any]:
        """High-level risk summary from all models."""
        signals = self.full_scan(asset)
        high_severity = [s for s in signals.values() if s.severity > 0.5]
        warning_signals = [s for s in signals.values() if s.severity > 0.3]

        overall_risk = statistics.mean(
            [s.severity for s in signals.values()]
        ) if signals else 0

        return {
            "overall_risk": overall_risk,
            "risk_level": ("critical" if overall_risk > 0.7 else
                           "elevated" if overall_risk > 0.4 else
                           "moderate" if overall_risk > 0.2 else "normal"),
            "high_severity_count": len(high_severity),
            "warning_count": len(warning_signals),
            "key_warnings": [
                {"source": s.source, "type": s.signal_type, "severity": s.severity,
                 "description": s.description}
                for s in sorted(signals.values(), key=lambda x: x.severity, reverse=True)[:5]
            ],
        }
