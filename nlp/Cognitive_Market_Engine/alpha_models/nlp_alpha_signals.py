"""
NLP-Based Alpha Signals — Categories 9.2, 9.3, 9.4, 9.5, 9.6
==============================================================
9.2  News Velocity Alpha — rate of news flow acceleration as momentum signal
9.3  Narrative Shift Alpha — detect when media tone shifts from the consensus
9.4  Hidden Truth Alpha — trade opposite when manipulation is flagged
9.5  Event Surprise Alpha — fuse implied vol + positioning + actual outcome
9.6  Cross-Source Divergence Alpha — trade the direction of the most credible
     source when sources disagree
"""
import time
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque

logger = logging.getLogger("cme.alpha_models.nlp_alpha")


@dataclass
class AlphaSignal:
    """Standardized alpha signal output."""
    name: str
    asset: str
    direction: str              # long / short / neutral
    strength: float             # -1.0 to 1.0
    confidence: float           # 0-1
    decay_hours: float          # expected half-life
    reasoning: List[str]
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

    @property
    def is_actionable(self) -> bool:
        return abs(self.strength) > 0.2 and self.confidence > 0.3

    @property
    def position_scalar(self) -> float:
        """Suggested position size scalar based on signal strength × confidence."""
        return self.strength * self.confidence


# ---------------------------------------------------------------------------
#  9.2  News Velocity Alpha
# ---------------------------------------------------------------------------

class NewsVelocityAlpha:
    """
    Alpha from the RATE of news flow, not content.
    
    Intuition:
    - Sudden spike in article count → something is happening before price reacts
    - Acceleration of news (articles per hour increasing) → event building
    - News vacuum (sudden drop after high activity) → resolution / exhaustion
    
    Signal:
    - velocity > 2σ above normal → go with the sentiment direction
    - velocity > 3σ → potentially too late / crowded
    - velocity drops after spike → mean reversion opportunity
    """

    def __init__(self, baseline_window_hours: int = 168):  # 7 days
        self.baseline_window = baseline_window_hours
        # asset -> deque of (timestamp, sentiment)
        self._article_stream: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._baseline_rates: Dict[str, float] = {}  # asset -> avg articles/hour

    def ingest_article(self, asset: str, timestamp: float, sentiment: float = 0.0) -> None:
        """Record an article arrival."""
        self._article_stream[asset].append((timestamp, sentiment))

    def compute_signal(self, asset: str, now: Optional[float] = None) -> AlphaSignal:
        """Compute news velocity alpha for an asset."""
        now = now or time.time()
        stream = self._article_stream.get(asset, deque())

        if len(stream) < 10:
            return AlphaSignal(
                name="news_velocity", asset=asset, direction="neutral",
                strength=0.0, confidence=0.0, decay_hours=24,
                reasoning=["Insufficient data"],
            )

        # Current rate (last 2 hours)
        two_hours_ago = now - 7200
        recent = [(t, s) for t, s in stream if t > two_hours_ago]
        current_rate = len(recent) / 2.0  # articles per hour

        # Baseline rate (prior 7 days, excluding last 2 hours)
        baseline_start = now - self.baseline_window * 3600
        baseline = [(t, s) for t, s in stream if baseline_start < t <= two_hours_ago]
        baseline_hours = max(1, (two_hours_ago - baseline_start) / 3600)
        baseline_rate = len(baseline) / baseline_hours

        if baseline_rate == 0:
            baseline_rate = 0.1  # avoid division by zero

        # Z-score of current velocity
        # Estimate std from baseline
        hourly_counts = defaultdict(int)
        for t, _ in baseline:
            hour_bucket = int(t // 3600)
            hourly_counts[hour_bucket] += 1
        counts = list(hourly_counts.values()) or [0]
        mean_bl = sum(counts) / len(counts)
        std_bl = math.sqrt(sum((c - mean_bl) ** 2 for c in counts) / max(1, len(counts)))
        std_bl = max(0.1, std_bl)

        z_score = (current_rate - baseline_rate) / std_bl

        # Acceleration: compare last 1hr vs prior 1hr
        one_hour_ago = now - 3600
        last_hour = len([t for t, _ in stream if t > one_hour_ago])
        prev_hour = len([t for t, _ in stream if one_hour_ago - 3600 < t <= one_hour_ago])
        acceleration = last_hour - prev_hour

        # Average sentiment of recent articles
        if recent:
            avg_sentiment = sum(s for _, s in recent) / len(recent)
        else:
            avg_sentiment = 0.0

        # Signal logic
        reasoning = []
        strength = 0.0

        if z_score > 3.0:
            # Too late / crowded
            strength = -0.3 * (1 if avg_sentiment > 0 else -1)
            reasoning.append(f"News velocity extremely high (z={z_score:.1f}), likely crowded")
            reasoning.append("Contrarian signal: event may be priced in")
        elif z_score > 2.0:
            # Strong signal: go with sentiment
            strength = 0.6 * (1 if avg_sentiment > 0 else -1)
            reasoning.append(f"News velocity spiking (z={z_score:.1f})")
            reasoning.append(f"Average sentiment of spike: {avg_sentiment:+.2f}")
        elif z_score > 1.0:
            strength = 0.3 * (1 if avg_sentiment > 0 else -1)
            reasoning.append(f"News velocity elevated (z={z_score:.1f})")
        elif z_score < -1.0 and len(stream) > 50:
            # News vacuum after activity → mean reversion
            strength = -0.2 * (1 if avg_sentiment > 0 else -1)
            reasoning.append(f"News vacuum after prior activity (z={z_score:.1f})")
            reasoning.append("Post-event exhaustion — potential mean reversion")

        if acceleration > 3:
            strength *= 1.2
            reasoning.append(f"News accelerating: +{acceleration} articles in last hour vs prior")

        direction = "long" if strength > 0 else "short" if strength < 0 else "neutral"
        confidence = min(1.0, abs(z_score) / 4 * 0.5 + min(len(recent), 20) / 20 * 0.5)

        return AlphaSignal(
            name="news_velocity",
            asset=asset,
            direction=direction,
            strength=round(max(-1, min(1, strength)), 3),
            confidence=round(confidence, 3),
            decay_hours=6,
            reasoning=reasoning,
            metadata={
                "current_rate": round(current_rate, 2),
                "baseline_rate": round(baseline_rate, 2),
                "z_score": round(z_score, 2),
                "acceleration": acceleration,
                "avg_sentiment": round(avg_sentiment, 3),
            },
        )


# ---------------------------------------------------------------------------
#  9.3  Narrative Shift Alpha
# ---------------------------------------------------------------------------

class NarrativeShiftAlpha:
    """
    Detect when the media narrative is shifting from the consensus.
    
    Intuition:
    - If the dominant narrative has been "AAPL is growing" but articles start
      saying "growth slowing", the narrative shift is a leading indicator
    - The transition period (before consensus updates) is the alpha window
    
    Mechanics:
    - Track rolling sentiment by topic/asset over time windows
    - Detect inflection points (2nd derivative of sentiment)
    - Compare short-term vs long-term narrative
    """

    def __init__(self, short_window_hours: int = 48, long_window_hours: int = 336):
        self.short_window = short_window_hours
        self.long_window = long_window_hours
        self._sentiment_stream: Dict[str, deque] = defaultdict(lambda: deque(maxlen=5000))

    def ingest_sentiment(self, asset: str, timestamp: float, sentiment: float,
                          source: str = "", headline: str = "") -> None:
        self._sentiment_stream[asset].append({
            "timestamp": timestamp,
            "sentiment": sentiment,
            "source": source,
            "headline": headline,
        })

    def compute_signal(self, asset: str, now: Optional[float] = None) -> AlphaSignal:
        """Detect narrative shift and generate alpha signal."""
        now = now or time.time()
        stream = self._sentiment_stream.get(asset, deque())

        if len(stream) < 20:
            return AlphaSignal(
                name="narrative_shift", asset=asset, direction="neutral",
                strength=0.0, confidence=0.0, decay_hours=48,
                reasoning=["Insufficient sentiment history"],
            )

        # Short-term sentiment
        short_cutoff = now - self.short_window * 3600
        short_items = [s for s in stream if s["timestamp"] > short_cutoff]
        short_sent = (sum(s["sentiment"] for s in short_items) / len(short_items)
                      if short_items else 0)

        # Long-term sentiment
        long_cutoff = now - self.long_window * 3600
        long_items = [s for s in stream if s["timestamp"] > long_cutoff]
        long_sent = (sum(s["sentiment"] for s in long_items) / len(long_items)
                     if long_items else 0)

        # Narrative delta
        delta = short_sent - long_sent

        # Rate of change (sentiment acceleration)
        # Compare last 12hrs vs prior 12hrs
        t12 = now - 43200
        t24 = now - 86400
        last_12 = [s for s in stream if s["timestamp"] > t12]
        prev_12 = [s for s in stream if t24 < s["timestamp"] <= t12]

        if last_12 and prev_12:
            last_12_avg = sum(s["sentiment"] for s in last_12) / len(last_12)
            prev_12_avg = sum(s["sentiment"] for s in prev_12) / len(prev_12)
            acceleration = last_12_avg - prev_12_avg
        else:
            acceleration = 0

        reasoning = []
        strength = 0.0

        # Detect narrative shift
        if abs(delta) > 0.3:
            # Strong shift
            strength = delta * 0.8  # go with the new narrative direction
            reasoning.append(
                f"Strong narrative shift: short-term sentiment ({short_sent:+.2f}) "
                f"diverging from consensus ({long_sent:+.2f})"
            )
            if delta > 0:
                reasoning.append("Media turning more positive ahead of consensus update")
            else:
                reasoning.append("Media turning more negative ahead of consensus update")
        elif abs(delta) > 0.15:
            strength = delta * 0.4
            reasoning.append(
                f"Moderate narrative shift detected (delta={delta:+.2f})"
            )

        if abs(acceleration) > 0.2:
            strength *= 1.3
            reasoning.append(
                f"Sentiment accelerating (accel={acceleration:+.2f}/12h)"
            )

        # Source diversity check
        recent_sources = set(s.get("source", "") for s in short_items if s.get("source"))
        if len(recent_sources) >= 3:
            reasoning.append(f"Shift confirmed across {len(recent_sources)} sources")
            strength *= 1.1

        direction = "long" if strength > 0 else "short" if strength < 0 else "neutral"
        confidence = min(1.0, abs(delta) / 0.5 * 0.4 + len(short_items) / 30 * 0.3 +
                         len(recent_sources) / 5 * 0.3)

        return AlphaSignal(
            name="narrative_shift",
            asset=asset,
            direction=direction,
            strength=round(max(-1, min(1, strength)), 3),
            confidence=round(confidence, 3),
            decay_hours=48,
            reasoning=reasoning,
            metadata={
                "short_sentiment": round(short_sent, 3),
                "long_sentiment": round(long_sent, 3),
                "delta": round(delta, 3),
                "acceleration": round(acceleration, 3),
                "source_diversity": len(recent_sources),
            },
        )


# ---------------------------------------------------------------------------
#  9.4  Hidden Truth Alpha
# ---------------------------------------------------------------------------

class HiddenTruthAlpha:
    """
    Trade opposite when manipulation is flagged.
    
    Intuition:
    - If hidden truth detection flags pump-and-dump → short
    - If omission detector finds suppressed bad news → short
    - If positive divergence between filing and PR → wait for filing truth to emerge
    
    Must cross-reference with confidence and position sizing.
    """

    def __init__(self, min_manipulation_confidence: float = 0.5):
        self.min_confidence = min_manipulation_confidence
        self._manipulations: Dict[str, List[Dict]] = defaultdict(list)

    def ingest_manipulation_flag(self, asset: str, flag: Dict) -> None:
        """
        flag: {
            type: "pump_and_dump" | "wash_trading" | "narrative_manipulation",
            confidence: 0.8,
            detected_direction: "bullish" | "bearish",
            evidence: [...]
        }
        """
        self._manipulations[asset].append({**flag, "timestamp": time.time()})

    def compute_signal(self, asset: str, current_sentiment: float = 0.0,
                        now: Optional[float] = None) -> AlphaSignal:
        """Generate contrarian alpha from manipulation detection."""
        now = now or time.time()
        flags = self._manipulations.get(asset, [])

        # Only consider recent flags (last 48 hours)
        recent = [f for f in flags if now - f.get("timestamp", 0) < 172800]

        if not recent:
            return AlphaSignal(
                name="hidden_truth", asset=asset, direction="neutral",
                strength=0.0, confidence=0.0, decay_hours=24,
                reasoning=["No active manipulation flags"],
            )

        # Aggregate signals
        high_conf = [f for f in recent if f.get("confidence", 0) >= self.min_confidence]

        if not high_conf:
            return AlphaSignal(
                name="hidden_truth", asset=asset, direction="neutral",
                strength=0.0, confidence=0.0, decay_hours=24,
                reasoning=[f"Flags exist but confidence below {self.min_confidence}"],
            )

        reasoning = []
        strength = 0.0

        for flag in high_conf:
            manipulation_type = flag.get("type", "unknown")
            detected_dir = flag.get("detected_direction", "")
            conf = flag.get("confidence", 0)

            if manipulation_type == "pump_and_dump":
                # Counter the pump
                strength -= 0.7 * conf
                reasoning.append(
                    f"Pump-and-dump detected (conf={conf:.2f}). Shorting the pump."
                )
            elif manipulation_type == "wash_trading":
                # Volume is fake, don't trust momentum
                strength -= 0.3 * conf * (1 if current_sentiment > 0 else -1)
                reasoning.append(
                    f"Wash trading detected (conf={conf:.2f}). Volume unreliable."
                )
            elif manipulation_type == "narrative_manipulation":
                # Counter the narrative
                if detected_dir == "bullish":
                    strength -= 0.5 * conf
                    reasoning.append("Bullish narrative manipulation → contrarian short")
                elif detected_dir == "bearish":
                    strength += 0.5 * conf
                    reasoning.append("Bearish narrative manipulation → contrarian long")
            elif manipulation_type == "pr_filing_divergence":
                # PR positive but filing negative → trust filing
                strength -= 0.4 * conf
                reasoning.append(
                    "PR/filing divergence: filing language more cautious than PR"
                )

        # Cap strength
        strength = max(-1, min(1, strength))
        avg_conf = sum(f.get("confidence", 0) for f in high_conf) / len(high_conf)
        direction = "long" if strength > 0 else "short" if strength < 0 else "neutral"

        return AlphaSignal(
            name="hidden_truth",
            asset=asset,
            direction=direction,
            strength=round(strength, 3),
            confidence=round(avg_conf, 3),
            decay_hours=24,
            reasoning=reasoning,
            metadata={
                "active_flags": len(high_conf),
                "flag_types": list(set(f.get("type", "") for f in high_conf)),
            },
        )


# ---------------------------------------------------------------------------
#  9.5  Event Surprise Alpha
# ---------------------------------------------------------------------------

class EventSurpriseAlpha:
    """
    Fuse implied volatility, positioning, and actual event outcome
    to generate alpha from surprise magnitude.
    
    Intuition:
    - Large earnings surprise + low implied vol = big move opportunity
    - Positioning heavily one way + surprise in opposite direction = squeeze
    - Actual outcome magnitude vs consensus estimate spread
    """

    def __init__(self):
        pass

    def compute_signal(self, asset: str,
                        actual_value: float,
                        consensus_estimate: float,
                        estimate_std: float,
                        implied_vol: float,
                        realized_vol: float,
                        positioning: float,  # -1 (max short) to +1 (max long)
                        event_type: str = "earnings") -> AlphaSignal:
        """
        actual_value: EPS / revenue actual
        consensus_estimate: street estimate
        estimate_std: standard deviation of estimates
        implied_vol: pre-event IV (annualized)
        realized_vol: recent realized vol
        positioning: net positioning (-1=short, +1=long)
        """
        reasoning = []

        # Surprise magnitude (in standard deviations)
        if estimate_std > 0:
            surprise_z = (actual_value - consensus_estimate) / estimate_std
        else:
            surprise_z = 0 if actual_value == consensus_estimate else (
                3 if actual_value > consensus_estimate else -3
            )

        # Vol surprise (how much more/less volatile than expected)
        vol_ratio = realized_vol / max(0.01, implied_vol)
        vol_mispriced = vol_ratio < 0.5 or vol_ratio > 2.0

        # Positioning squeeze potential
        squeeze = False
        if surprise_z > 1.5 and positioning < -0.3:
            squeeze = True
            reasoning.append(
                f"Short squeeze potential: surprise={surprise_z:+.1f}σ, "
                f"positioning={positioning:+.2f} (net short)"
            )
        elif surprise_z < -1.5 and positioning > 0.3:
            squeeze = True
            reasoning.append(
                f"Long squeeze potential: surprise={surprise_z:+.1f}σ, "
                f"positioning={positioning:+.2f} (net long)"
            )

        # Signal strength
        surprise_component = min(1.0, abs(surprise_z) / 3)
        direction_sign = 1 if surprise_z > 0 else -1

        strength = direction_sign * surprise_component * 0.6

        # Adjust for vol mispricing
        if vol_mispriced and abs(surprise_z) > 1:
            strength *= 1.3
            reasoning.append(
                f"Vol mispriced: IV={implied_vol:.1%} vs RV={realized_vol:.1%}"
            )

        # Adjust for squeeze
        if squeeze:
            strength *= 1.4

        # Baseline reasoning
        if abs(surprise_z) > 2:
            reasoning.append(f"Major {event_type} surprise: {surprise_z:+.1f}σ")
        elif abs(surprise_z) > 1:
            reasoning.append(f"Moderate {event_type} surprise: {surprise_z:+.1f}σ")
        else:
            reasoning.append(f"Mild {event_type} surprise: {surprise_z:+.1f}σ")

        reasoning.append(
            f"Actual={actual_value:.2f} vs Consensus={consensus_estimate:.2f} "
            f"(±{estimate_std:.2f})"
        )

        strength = max(-1, min(1, strength))
        direction = "long" if strength > 0 else "short" if strength < 0 else "neutral"

        confidence = min(1.0,
                         0.3 * surprise_component +
                         0.3 * (1 if squeeze else 0.3) +
                         0.2 * (1 if vol_mispriced else 0.3) +
                         0.2 * 0.7)

        return AlphaSignal(
            name="event_surprise",
            asset=asset,
            direction=direction,
            strength=round(strength, 3),
            confidence=round(confidence, 3),
            decay_hours=12,
            reasoning=reasoning,
            metadata={
                "surprise_z": round(surprise_z, 2),
                "vol_ratio": round(vol_ratio, 2),
                "positioning": positioning,
                "squeeze": squeeze,
                "event_type": event_type,
            },
        )


# ---------------------------------------------------------------------------
#  9.6  Cross-Source Divergence Alpha
# ---------------------------------------------------------------------------

class CrossSourceDivergenceAlpha:
    """
    When different sources disagree on an asset, trade the direction
    of the most credible source.
    
    Intuition:
    - If Reuters says bearish, but Reddit says bullish → trust Reuters
    - If insiders are selling but analysts say "buy" → trust insiders
    - If EDGAR filing is cautious but CEO interview is optimistic → trust EDGAR
    
    Must be combined with credibility scores from source network analysis.
    """

    DEFAULT_CREDIBILITY = {
        "sec_filing": 0.95,
        "insider_transaction": 0.90,
        "institutional_flow": 0.85,
        "reuters": 0.80,
        "bloomberg": 0.80,
        "wsj": 0.75,
        "analyst_report": 0.70,
        "company_pr": 0.50,
        "financial_blog": 0.40,
        "reddit": 0.25,
        "twitter": 0.20,
        "unknown": 0.30,
    }

    def __init__(self, credibility_map: Optional[Dict[str, float]] = None):
        self.credibility = credibility_map or self.DEFAULT_CREDIBILITY

    def compute_signal(self, asset: str,
                        source_sentiments: Dict[str, float]) -> AlphaSignal:
        """
        source_sentiments: {source_type: sentiment_score}
        e.g. {"reuters": -0.6, "reddit": 0.8, "analyst_report": -0.3}
        """
        if not source_sentiments:
            return AlphaSignal(
                name="cross_source_divergence", asset=asset,
                direction="neutral", strength=0.0, confidence=0.0,
                decay_hours=24, reasoning=["No source data"],
            )

        # Calculate credibility-weighted sentiment
        weighted_sum = 0.0
        weight_total = 0.0
        source_details = []

        for source, sentiment in source_sentiments.items():
            cred = self.credibility.get(source, self.credibility["unknown"])
            weighted_sum += sentiment * cred
            weight_total += cred
            source_details.append((source, sentiment, cred))

        if weight_total == 0:
            return AlphaSignal(
                name="cross_source_divergence", asset=asset,
                direction="neutral", strength=0.0, confidence=0.0,
                decay_hours=24, reasoning=["Zero credibility weight"],
            )

        credibility_weighted_sentiment = weighted_sum / weight_total

        # Measure divergence: standard deviation of sentiments
        sents = list(source_sentiments.values())
        mean_sent = sum(sents) / len(sents)
        variance = sum((s - mean_sent) ** 2 for s in sents) / len(sents)
        divergence = math.sqrt(variance)

        reasoning = []

        # Find most credible source
        source_details.sort(key=lambda x: x[2], reverse=True)
        top_source = source_details[0]
        lowest_source = source_details[-1]

        if divergence > 0.4:
            reasoning.append(
                f"High divergence ({divergence:.2f}) between sources"
            )
            reasoning.append(
                f"Most credible: {top_source[0]} (cred={top_source[2]:.2f}, "
                f"sentiment={top_source[1]:+.2f})"
            )
            reasoning.append(
                f"Least credible: {lowest_source[0]} (cred={lowest_source[2]:.2f}, "
                f"sentiment={lowest_source[1]:+.2f})"
            )

            # Trade with credible source, against low-credibility noise
            strength = credibility_weighted_sentiment * min(1.0, divergence / 0.5)
        elif divergence > 0.2:
            reasoning.append(f"Moderate source divergence ({divergence:.2f})")
            strength = credibility_weighted_sentiment * 0.5
        else:
            reasoning.append(f"Sources largely agree ({divergence:.2f})")
            strength = credibility_weighted_sentiment * 0.3

        # Special case: insider/filing contradicts public sentiment
        insider_sent = source_sentiments.get("insider_transaction")
        filing_sent = source_sentiments.get("sec_filing")
        public_avg = sum(
            s for src, s in source_sentiments.items()
            if src in ("reddit", "twitter", "company_pr", "financial_blog")
        )

        if insider_sent is not None and abs(insider_sent - mean_sent) > 0.5:
            strength = insider_sent * 0.7
            reasoning.append(
                f"Insiders diverge strongly from consensus: "
                f"insider={insider_sent:+.2f} vs avg={mean_sent:+.2f}"
            )

        if filing_sent is not None and abs(filing_sent - mean_sent) > 0.4:
            strength = filing_sent * 0.6
            reasoning.append(
                f"SEC filing tone diverges from public narrative: "
                f"filing={filing_sent:+.2f} vs avg={mean_sent:+.2f}"
            )

        strength = max(-1, min(1, strength))
        direction = "long" if strength > 0 else "short" if strength < 0 else "neutral"

        confidence = min(1.0,
                         divergence / 0.5 * 0.4 +
                         top_source[2] * 0.3 +
                         len(source_sentiments) / 6 * 0.3)

        return AlphaSignal(
            name="cross_source_divergence",
            asset=asset,
            direction=direction,
            strength=round(strength, 3),
            confidence=round(confidence, 3),
            decay_hours=24,
            reasoning=reasoning,
            metadata={
                "divergence": round(divergence, 3),
                "credibility_weighted_sentiment": round(credibility_weighted_sentiment, 3),
                "source_count": len(source_sentiments),
                "top_source": top_source[0],
            },
        )


# ---------------------------------------------------------------------------
#  Composite: NLP Alpha Hub
# ---------------------------------------------------------------------------

class NLPAlphaHub:
    """
    Aggregates all NLP-based alpha signals into a unified interface.
    Generates a composite signal from all sub-models.
    """

    def __init__(self):
        self.news_velocity = NewsVelocityAlpha()
        self.narrative_shift = NarrativeShiftAlpha()
        self.hidden_truth = HiddenTruthAlpha()
        self.event_surprise = EventSurpriseAlpha()
        self.cross_source = CrossSourceDivergenceAlpha()

    def get_composite_signal(self, asset: str,
                               weights: Optional[Dict[str, float]] = None) -> AlphaSignal:
        """
        Generate composite signal from all active sub-signals.
        weights: {signal_name: weight}  (defaults to equal weight)
        """
        default_weights = {
            "news_velocity": 0.20,
            "narrative_shift": 0.25,
            "hidden_truth": 0.20,
            "event_surprise": 0.20,
            "cross_source_divergence": 0.15,
        }
        weights = weights or default_weights

        signals = [
            self.news_velocity.compute_signal(asset),
            self.narrative_shift.compute_signal(asset),
            self.hidden_truth.compute_signal(asset),
        ]

        weighted_strength = 0.0
        total_weight = 0.0
        all_reasoning = []
        active_signals = []

        for sig in signals:
            w = weights.get(sig.name, 0.2)
            if sig.is_actionable:
                weighted_strength += sig.strength * w * sig.confidence
                total_weight += w * sig.confidence
                active_signals.append(sig.name)
                all_reasoning.extend(
                    [f"[{sig.name}] {r}" for r in sig.reasoning[:2]]
                )

        if total_weight > 0:
            composite_strength = weighted_strength / total_weight
        else:
            composite_strength = 0.0

        direction = "long" if composite_strength > 0 else "short" if composite_strength < 0 else "neutral"
        confidence = min(1.0, total_weight)

        return AlphaSignal(
            name="nlp_composite",
            asset=asset,
            direction=direction,
            strength=round(max(-1, min(1, composite_strength)), 3),
            confidence=round(confidence, 3),
            decay_hours=24,
            reasoning=all_reasoning,
            metadata={"active_sub_signals": active_signals},
        )
