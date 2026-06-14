"""
PHASE 5: MARKET REALITY VALIDATION (RESEARCH CORE)

Purpose:
Validates whether cognitive models predict actual market behavior.
NOT for trading, signal generation, or execution.
This is scientific truth-verification.

Key Principle:
 Did the market actually behave the way our models predicted,
or are we fooling ourselves? 

This phase answers:
1. Did price move in predicted direction? (Directional Validity)
2. Did volatility expand/contract as expected? (Volatility Validity)
3. Did reactions occur in expected time windows? (Timing Validity)
4. Which participant models aligned with reality? (Participation Match)
5. Did news cause temporary noise or regime change? (Regime Shift Detection)

Output: Reality alignment scores (0.0-1.0), NOT trading signals.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics
import math
import json
import os


class NewsEventType(str, Enum):
    """Types of news events that drive market behavior."""
    EARNINGS = "earnings"
    RATE_DECISION = "rate_decision"
    MACRO_DATA = "macro_data"
    GEOPOLITICAL = "geopolitical"
    REGULATORY = "regulatory"
    CREDIT_EVENT = "credit_event"
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"


class DirectionType(str, Enum):
    """Predicted and observed price direction."""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"


class RegimeType(str, Enum):
    """Market regimes."""
    TRENDING = "trending"
    CHOPPY = "choppy"
    PANIC = "panic"
    QUIET = "quiet"
    DISLOCATION = "dislocation"


class ValidityScore(str, Enum):
    """Validation outcome categories."""
    ACCURATE = "accurate"
    PARTIALLY_ACCURATE = "partially_accurate"
    INACCURATE = "inaccurate"
    NOISY = "noisy"


# ============================================================
# INPUT STRUCTURES: Predictions from Phases 1-4
# ============================================================

@dataclass
class NewsUnderstanding:
    """Input from Phase 1: Parsed news event."""
    event_id: str
    timestamp_utc: datetime
    event_type: NewsEventType
    entity: str  # Company, sector, macro indicator
    polarity: float  # -1.0 (negative) to +1.0 (positive)
    intensity: float  # 0.0 to 1.0 (shock level)
    ambiguity: float  # 0.0 to 1.0 (clarity of signal)


@dataclass
class ParticipantExpectation:
    """Input from Phase 2: One participant's interpretation."""
    participant_type: str  # "bank", "hft", "hedge_fund", "market_maker", "retail"
    sentiment: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    expected_direction: DirectionType
    expected_reaction_time: timedelta  # How fast will they react?
    vol_expectation: float  # 0.0 to 1.0 (volatility expansion)
    liquidity_expectation: float  # 0.0 to 1.0 (0=less liquid, 1=more)


@dataclass
class PredictedMarketState:
    """Input from Phase 4: Predicted market behavior."""
    event_id: str
    timestamp_utc: datetime
    
    # Predicted price behavior
    expected_direction: DirectionType
    expected_magnitude: float  # In standard deviations or bps
    expected_regime_shift: Optional[RegimeType]
    
    # Predicted volatility
    expected_vol_expansion: float  # 0.0 to 1.0
    expected_vol_duration: timedelta
    
    # Predicted volume / order flow
    expected_volume_spike: float  # Multiplier on baseline
    expected_order_imbalance: float  # -1.0 to 1.0 (buy vs sell pressure)
    
    # Predicted spread behavior
    expected_spread_widening: float  # 0.0 to 1.0
    
    # Time structure (from Phase 4)
    shock_onset: timedelta  # When does shock hit?
    peak_impact_window: timedelta  # When is maximum?
    recovery_time: timedelta  # How long to recover?
    persistence: timedelta  # How long does effect linger?


# ============================================================
# MARKET REALITY: Actual observed data
# ============================================================

@dataclass
class OHLCV:
    """Standard OHLC + Volume data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class MarketSnapshot:
    """Actual market state at a point in time."""
    timestamp: datetime
    price: float
    bid: float
    ask: float
    spread: float  # ask - bid
    volume_cumulative: int
    order_book_imbalance: float  # -1.0 to 1.0 (buy vs sell pressure)
    realized_volatility: float  # Recent vol
    regime: RegimeType


@dataclass
class MarketReality:
    """Observed market behavior after news event."""
    event_id: str
    news_timestamp: datetime
    
    # Time windows of observation
    pre_news_baseline: List[MarketSnapshot]  # T-30m to T-1m
    shock_period: List[MarketSnapshot]  # T0 to T+1m
    hft_digestion: List[MarketSnapshot]  # T+1m to T+15m
    institutional_reaction: List[MarketSnapshot]  # T+15m to T+2h
    structural_reposition: List[MarketSnapshot]  # T+2h to T+1d
    
    # Aggregated metrics
    actual_direction: DirectionType
    actual_magnitude: float  # In standard deviations
    actual_vol_expansion: float
    actual_regime_shift: Optional[RegimeType]
    
    # Key observations
    peak_price_time: datetime  # When did price reach extreme?
    peak_vol_time: datetime  # When was vol highest?
    recovery_time: datetime  # When did price stabilize?
    
    # Participation indicators
    hft_participation_marker: bool  # Did we see HFT signature?
    institutional_participation_marker: bool  # Did we see large order flow?
    retail_panic_marker: bool  # Did we see retail liquidations?


# ============================================================
# VALIDATION SCORING: 5 Core Questions
# ============================================================

@dataclass
class DirectionalValidity:
    """Did price move in predicted direction?"""
    predicted_direction: DirectionType
    actual_direction: DirectionType
    matches: bool  # True if predicted == actual
    confidence: float  # 0.0 to 1.0
    reasoning: str


@dataclass
class VolatilityValidity:
    """Did volatility expand/contract as expected?"""
    predicted_vol_expansion: float
    actual_vol_expansion: float
    difference: float  # |predicted - actual|
    accuracy: float  # 0.0 to 1.0 (lower diff = higher accuracy)
    reasoning: str


@dataclass
class TimingValidity:
    """Did reactions occur in expected time windows?"""
    expected_shock_onset: timedelta
    actual_shock_onset: timedelta
    shock_timing_error: timedelta  # How far off?
    
    expected_peak_window: timedelta
    actual_peak_time: timedelta
    peak_timing_error: timedelta
    
    expected_recovery: timedelta
    actual_recovery: timedelta
    recovery_timing_error: timedelta
    
    overall_timing_accuracy: float  # 0.0 to 1.0
    reasoning: str


@dataclass
class ParticipationValidity:
    """Which participant models aligned with reality?"""
    participant_type: str
    predicted_sentiment: float
    predicted_reaction_speed: timedelta
    
    # Did we actually see this participant's fingerprints?
    observed_in_market: bool
    timing_match: float  # 0.0 to 1.0
    direction_match: float  # 0.0 to 1.0
    
    overall_accuracy: float  # 0.0 to 1.0
    reasoning: str


@dataclass
class RegimeValidity:
    """Did news cause temporary noise or regime change?"""
    predicted_regime_shift: Optional[RegimeType]
    actual_regime_shift: Optional[RegimeType]
    
    pre_news_regime: RegimeType
    post_news_regime: RegimeType
    regime_changed: bool
    
    # Classification
    event_classification: ValidityScore  # TEMPORARY vs STRUCTURAL
    persistence_days: int  # How long did new regime last?
    
    reasoning: str


# ============================================================
# OVERALL VALIDATION RECORD
# ============================================================

@dataclass
class ValidationRecord:
    """Complete validation of one news event."""
    event_id: str
    news_timestamp: datetime
    news_type: NewsEventType
    
    # All 5 validation dimensions
    directional: DirectionalValidity
    volatility: VolatilityValidity
    timing: TimingValidity
    participation: List[ParticipationValidity]  # One per participant type
    regime: RegimeValidity
    
    # Aggregate scores
    overall_accuracy: float  # 0.0 to 1.0 (weighted average)
    model_credibility: float  # How trustworthy are our models?
    
    # Failure analysis
    most_accurate_participant: str
    least_accurate_participant: str
    biggest_assumption_failure: str  # What did we get most wrong?
    
    # Research notes
    research_notes: str  # Narrative explanation of what happened


# ============================================================
# CREDIBILITY TRACKER
# ============================================================

@dataclass
class ModelCredibility:
    """Track credibility of each participant model over time."""
    participant_type: str
    event_count: int = 0
    
    # Per-dimension tracking
    directional_accuracy_history: List[float] = field(default_factory=list)
    timing_accuracy_history: List[float] = field(default_factory=list)
    vol_accuracy_history: List[float] = field(default_factory=list)
    
    # Aggregate
    mean_accuracy: float = 0.0
    std_dev_accuracy: float = 0.0
    latest_accuracy: float = 0.0
    
    # Status
    is_reliable: bool = False  # True if mean_accuracy > 0.65
    warning_level: str = "normal"  # "normal", "degraded", "unreliable"
    
    def update(self, directional: float, timing: float, vol: float):
        """Update credibility with new validation scores."""
        self.event_count += 1
        self.directional_accuracy_history.append(directional)
        self.timing_accuracy_history.append(timing)
        self.vol_accuracy_history.append(vol)
        
        all_scores = (
            self.directional_accuracy_history +
            self.timing_accuracy_history +
            self.vol_accuracy_history
        )
        
        self.mean_accuracy = statistics.mean(all_scores)
        if len(all_scores) > 1:
            self.std_dev_accuracy = statistics.stdev(all_scores)
        else:
            self.std_dev_accuracy = 0.0
        
        self.latest_accuracy = all_scores[-1]
        self.is_reliable = self.mean_accuracy > 0.65
        
        # Set warning level
        if self.mean_accuracy < 0.5:
            self.warning_level = "unreliable"
        elif self.mean_accuracy < 0.6:
            self.warning_level = "degraded"
        else:
            self.warning_level = "normal"


@dataclass
class CredibilityDataset:
    """Track all models' credibility over time."""
    bank_credibility: ModelCredibility = field(default_factory=lambda: ModelCredibility("bank"))
    hft_credibility: ModelCredibility = field(default_factory=lambda: ModelCredibility("hft"))
    hedge_fund_credibility: ModelCredibility = field(default_factory=lambda: ModelCredibility("hedge_fund"))
    market_maker_credibility: ModelCredibility = field(default_factory=lambda: ModelCredibility("market_maker"))
    retail_credibility: ModelCredibility = field(default_factory=lambda: ModelCredibility("retail"))
    
    validation_records: List[ValidationRecord] = field(default_factory=list)
    
    def get_credibility(self, participant_type: str) -> ModelCredibility:
        """Get credibility record for participant."""
        credibility_map = {
            "bank": self.bank_credibility,
            "hft": self.hft_credibility,
            "hedge_fund": self.hedge_fund_credibility,
            "market_maker": self.market_maker_credibility,
            "retail": self.retail_credibility,
        }
        return credibility_map.get(participant_type)
    
    def add_validation(self, record: ValidationRecord):
        """Add a new validation record and update credibilities."""
        self.validation_records.append(record)
        
        # Update each participant's credibility
        for participation in record.participation:
            credibility = self.get_credibility(participation.participant_type)
            if credibility:
                # Extract accuracy scores
                directional = participation.direction_match
                timing = participation.timing_match
                vol = 0.5  # Placeholder, would come from volatility dimension
                
                credibility.update(directional, timing, vol)


# ============================================================
# FAILURE PATTERN ANALYSIS
# ============================================================

@dataclass
class FailurePattern:
    """Identifies systematic failures in model predictions."""
    failure_type: str  # "overreaction", "underreaction", "wrong_timing", "wrong_direction"
    participant_type: str
    news_type: NewsEventType
    
    occurrence_count: int
    severity_avg: float  # 0.0 to 1.0
    
    example_event_ids: List[str] = field(default_factory=list)
    
    research_notes: str = ""


@dataclass
class FailureAnalysis:
    """Collection of failure patterns across all models."""
    patterns: List[FailurePattern] = field(default_factory=list)
    
    def add_pattern(self, pattern: FailurePattern):
        """Register a failure pattern."""
        self.patterns.append(pattern)
    
    def get_patterns_for_participant(self, participant_type: str) -> List[FailurePattern]:
        """Get all failure patterns for a specific participant."""
        return [p for p in self.patterns if p.participant_type == participant_type]
    
    def get_patterns_for_news_type(self, news_type: NewsEventType) -> List[FailurePattern]:
        """Get all failure patterns for a specific news type."""
        return [p for p in self.patterns if p.news_type == news_type]


# ============================================================
# MARKET DATA PROVIDER — Live/historical price data integration
# ============================================================

class MarketDataProvider:
    """
    Provides actual market data for reality validation.
    
    Supports multiple backends:
    - CoinGecko API (free, crypto)
    - Yahoo Finance (via yfinance, if available)
    - Local CSV/JSON files for backtesting
    
    Falls back gracefully: API → local cache → None
    """
    
    def __init__(self, cache_dir: str = None):
        self._cache_dir = cache_dir or os.path.join(
            os.path.dirname(__file__), "..", "data", "market_cache"
        )
        os.makedirs(self._cache_dir, exist_ok=True)
        
        # Try import yfinance
        self._yf = None
        try:
            import yfinance as yf
            self._yf = yf
        except ImportError:
            pass
        
        # Try import requests for CoinGecko
        self._requests = None
        try:
            import requests
            self._requests = requests
        except ImportError:
            pass
        
        print(f"[MARKET_DATA] Provider initialized "
              f"(yfinance={'yes' if self._yf else 'no'}, "
              f"requests={'yes' if self._requests else 'no'})")
    
    def get_price_around_event(
        self,
        symbol: str,
        event_time: datetime,
        window_before: timedelta = timedelta(minutes=30),
        window_after: timedelta = timedelta(hours=2)
    ) -> Optional[Dict]:
        """
        Get price data around a news event for validation.
        
        Returns dict with:
        - pre_event_price: Price before event
        - post_event_price: Price after event
        - peak_price: Max price in window
        - trough_price: Min price in window
        - direction: 'up' or 'down'
        - magnitude_pct: Percentage move
        - volatility: Realized volatility in window
        """
        # Try CoinGecko first (for BTC/crypto)
        if symbol.upper() in ("BTC", "BITCOIN", "BTC-USD"):
            data = self._fetch_coingecko(event_time, window_before, window_after)
            if data:
                return data
        
        # Try yfinance
        if self._yf:
            data = self._fetch_yfinance(symbol, event_time, window_before, window_after)
            if data:
                return data
        
        # Try local cache
        data = self._fetch_from_cache(symbol, event_time)
        if data:
            return data
        
        return None
    
    def _fetch_coingecko(self, event_time, before, after) -> Optional[Dict]:
        """Fetch BTC price from CoinGecko."""
        if not self._requests:
            return None
        try:
            start_ts = int((event_time - before).timestamp())
            end_ts = int((event_time + after).timestamp())
            url = (
                f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
                f"?vs_currency=usd&from={start_ts}&to={end_ts}"
            )
            resp = self._requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                prices = data.get("prices", [])
                if len(prices) >= 2:
                    pre_prices = [p[1] for p in prices if p[0]/1000 < event_time.timestamp()]
                    post_prices = [p[1] for p in prices if p[0]/1000 >= event_time.timestamp()]
                    if pre_prices and post_prices:
                        pre = pre_prices[-1]
                        post = post_prices[-1] if len(post_prices) > 1 else post_prices[0]
                        all_p = [p[1] for p in prices]
                        return {
                            "pre_event_price": pre,
                            "post_event_price": post,
                            "peak_price": max(all_p),
                            "trough_price": min(all_p),
                            "direction": "up" if post > pre else "down",
                            "magnitude_pct": abs(post - pre) / pre * 100,
                            "volatility": statistics.stdev(
                                [(all_p[i] - all_p[i-1]) / all_p[i-1] 
                                 for i in range(1, len(all_p))]
                            ) if len(all_p) > 2 else 0.0,
                            "source": "coingecko",
                        }
        except Exception:
            pass
        return None
    
    def _fetch_yfinance(self, symbol, event_time, before, after) -> Optional[Dict]:
        """Fetch price from Yahoo Finance."""
        if not self._yf:
            return None
        try:
            start = (event_time - before).strftime("%Y-%m-%d")
            end = (event_time + after + timedelta(days=1)).strftime("%Y-%m-%d")
            ticker = self._yf.Ticker(symbol)
            hist = ticker.history(start=start, end=end, interval="5m")
            if not hist.empty:
                pre = hist['Close'].iloc[0]
                post = hist['Close'].iloc[-1]
                return {
                    "pre_event_price": float(pre),
                    "post_event_price": float(post),
                    "peak_price": float(hist['High'].max()),
                    "trough_price": float(hist['Low'].min()),
                    "direction": "up" if post > pre else "down",
                    "magnitude_pct": abs(float(post) - float(pre)) / float(pre) * 100,
                    "volatility": float(hist['Close'].pct_change().std()),
                    "source": "yfinance",
                }
        except Exception:
            pass
        return None
    
    def _fetch_from_cache(self, symbol, event_time) -> Optional[Dict]:
        """Try to load from local JSON cache."""
        cache_file = os.path.join(self._cache_dir, f"{symbol.lower()}_cache.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                # Find closest cached entry
                event_ts = event_time.timestamp()
                closest = min(cache, key=lambda x: abs(x.get("timestamp", 0) - event_ts))
                if abs(closest.get("timestamp", 0) - event_ts) < 86400:  # Within 1 day
                    return closest
            except Exception:
                pass
        return None
    
    def build_market_reality(
        self,
        event_id: str,
        news_timestamp: datetime,
        symbol: str = "BTC-USD"
    ) -> Optional['MarketReality']:
        """
        Build a MarketReality object from live data for validation.
        
        Returns None if data is unavailable.
        """
        price_data = self.get_price_around_event(symbol, news_timestamp)
        if price_data is None:
            return None
        
        direction = (
            DirectionType.BULLISH if price_data["direction"] == "up" 
            else DirectionType.BEARISH
        )
        
        return MarketReality(
            event_id=event_id,
            news_timestamp=news_timestamp,
            pre_news_baseline=[],  # Full snapshot data requires tick-level feed
            shock_period=[],
            hft_digestion=[],
            institutional_reaction=[],
            structural_reposition=[],
            actual_direction=direction,
            actual_magnitude=price_data["magnitude_pct"] / 100.0,
            actual_vol_expansion=price_data["volatility"],
            actual_regime_shift=None,
            peak_price_time=news_timestamp,  # Approximation without tick data
            peak_vol_time=news_timestamp,
            recovery_time=news_timestamp + timedelta(hours=1),
            hft_participation_marker=False,
            institutional_participation_marker=False,
            retail_panic_marker=price_data["magnitude_pct"] > 5.0,
        )


# ============================================================
# REALITY VALIDATOR
# ============================================================

class RealityValidator:
    """
    Core validation engine.
    Compares predictions (Phases 1-4) against market reality.
    
    Integrates with MarketDataProvider for live/historical price data.
    This is research-only, not for trading.
    """
    
    def __init__(self, data_provider=None, timing_tolerances: Optional[Dict[str, int]] = None):
        self.credibility_dataset = CredibilityDataset()
        self.failure_analysis = FailureAnalysis()
        self.data_provider = data_provider or MarketDataProvider()
        
        # Configurable timing tolerances (wired from RealityValidationConfig)
        self._timing_tolerances = timing_tolerances or {
            "shock": 30, "peak": 300, "recovery": 900
        }
        
        # Track validation history for statistical significance testing
        self._validation_history: List[Dict] = []
        self._direction_hits: List[bool] = []
        self._timing_hits: List[bool] = []
    
    def validate_directional_accuracy(
        self,
        predicted: DirectionType,
        actual: DirectionType,
        magnitude_match: float = 0.5
    ) -> DirectionalValidity:
        """
        Did price move in predicted direction?
        
        Returns:
            DirectionalValidity with accuracy score
        """
        matches = predicted == actual
        
        if matches:
            confidence = 1.0
            reasoning = f"Prediction '{predicted}' matched market reality '{actual}'"
        else:
            confidence = 0.0
            reasoning = f"Prediction '{predicted}' contradicted market reality '{actual}'"
        
        return DirectionalValidity(
            predicted_direction=predicted,
            actual_direction=actual,
            matches=matches,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def validate_volatility_accuracy(
        self,
        predicted_vol: float,
        actual_vol: float
    ) -> VolatilityValidity:
        """
        Did volatility expand/contract as expected?
        
        Returns:
            VolatilityValidity with accuracy score (0.0-1.0)
        """
        difference = abs(predicted_vol - actual_vol)
        # Accuracy: 1.0 if perfect match, decreases with difference
        accuracy = max(0.0, 1.0 - difference)
        
        reasoning = (
            f"Predicted vol expansion: {predicted_vol:.2f}, "
            f"Actual: {actual_vol:.2f}, "
            f"Difference: {difference:.2f}"
        )
        
        return VolatilityValidity(
            predicted_vol_expansion=predicted_vol,
            actual_vol_expansion=actual_vol,
            difference=difference,
            accuracy=accuracy,
            reasoning=reasoning
        )
    
    def validate_timing_accuracy(
        self,
        expected_shock_onset: timedelta,
        actual_shock_onset: timedelta,
        expected_peak: timedelta,
        actual_peak: timedelta,
        expected_recovery: timedelta,
        actual_recovery: timedelta
    ) -> TimingValidity:
        """
        Did reactions occur in expected time windows?
        
        Returns:
            TimingValidity with accuracy score
        """
        shock_error = abs(expected_shock_onset - actual_shock_onset).total_seconds()
        peak_error = abs(expected_peak - actual_peak).total_seconds()
        recovery_error = abs(expected_recovery - actual_recovery).total_seconds()
        
        # Normalize errors to 0.0-1.0 accuracy
        # Tolerance: 30 seconds for shock, 5min for peak, 15min for recovery
        shock_accuracy = max(0.0, 1.0 - shock_error / 30)
        peak_accuracy = max(0.0, 1.0 - peak_error / 300)
        recovery_accuracy = max(0.0, 1.0 - recovery_error / 900)
        
        overall = (shock_accuracy + peak_accuracy + recovery_accuracy) / 3.0
        
        reasoning = (
            f"Shock: expected {expected_shock_onset}, actual {actual_shock_onset}, "
            f"error {shock_error:.0f}s. "
            f"Peak: expected {expected_peak}, actual {actual_peak}, "
            f"error {peak_error:.0f}s. "
            f"Recovery: expected {expected_recovery}, actual {actual_recovery}, "
            f"error {recovery_error:.0f}s."
        )
        
        return TimingValidity(
            expected_shock_onset=expected_shock_onset,
            actual_shock_onset=actual_shock_onset,
            shock_timing_error=timedelta(seconds=shock_error),
            expected_peak_window=expected_peak,
            actual_peak_time=actual_peak,
            peak_timing_error=timedelta(seconds=peak_error),
            expected_recovery=expected_recovery,
            actual_recovery=actual_recovery,
            recovery_timing_error=timedelta(seconds=recovery_error),
            overall_timing_accuracy=overall,
            reasoning=reasoning
        )
    
    def validate_participation_match(
        self,
        participant_type: str,
        predicted_sentiment: float,
        predicted_speed: timedelta,
        observed_in_market: bool,
        timing_match: float,
        direction_match: float
    ) -> ParticipationValidity:
        """
        Which participant models aligned with reality?
        
        Returns:
            ParticipationValidity with accuracy score
        """
        overall = (timing_match + direction_match) / 2.0
        
        reasoning = (
            f"{participant_type}: observed={observed_in_market}, "
            f"timing_match={timing_match:.2f}, "
            f"direction_match={direction_match:.2f}"
        )
        
        return ParticipationValidity(
            participant_type=participant_type,
            predicted_sentiment=predicted_sentiment,
            predicted_reaction_speed=predicted_speed,
            observed_in_market=observed_in_market,
            timing_match=timing_match,
            direction_match=direction_match,
            overall_accuracy=overall,
            reasoning=reasoning
        )
    
    def validate_regime_shift(
        self,
        predicted_regime: Optional[RegimeType],
        actual_pre_regime: RegimeType,
        actual_post_regime: RegimeType,
        persistence_days: int
    ) -> RegimeValidity:
        """
        Did news cause temporary noise or structural regime change?
        
        Returns:
            RegimeValidity with classification
        """
        regime_changed = actual_pre_regime != actual_post_regime
        
        # Classify as temporary or structural
        if not regime_changed:
            classification = ValidityScore.INACCURATE
            reasoning = "Predicted regime change but market remained in same regime"
        elif persistence_days <= 1:
            classification = ValidityScore.NOISY
            reasoning = f"Regime change was temporary (lasted {persistence_days} day(s))"
        elif persistence_days <= 7:
            classification = ValidityScore.PARTIALLY_ACCURATE
            reasoning = f"Regime change was semi-persistent (lasted {persistence_days} days)"
        else:
            classification = ValidityScore.ACCURATE
            reasoning = f"Structural regime shift detected (persisted {persistence_days} days)"
        
        return RegimeValidity(
            predicted_regime_shift=predicted_regime,
            actual_regime_shift=actual_post_regime if regime_changed else None,
            pre_news_regime=actual_pre_regime,
            post_news_regime=actual_post_regime,
            regime_changed=regime_changed,
            event_classification=classification,
            persistence_days=persistence_days,
            reasoning=reasoning
        )
    
    def create_validation_record(
        self,
        event_id: str,
        news_timestamp: datetime,
        news_type: NewsEventType,
        directional: DirectionalValidity,
        volatility: VolatilityValidity,
        timing: TimingValidity,
        participation_list: List[ParticipationValidity],
        regime: RegimeValidity
    ) -> ValidationRecord:
        """
        Assemble all validations into a single record.
        """
        # Calculate weighted overall accuracy
        directional_weight = 0.3
        volatility_weight = 0.2
        timing_weight = 0.2
        participation_weight = 0.15
        regime_weight = 0.15
        
        participation_avg = (
            statistics.mean([p.overall_accuracy for p in participation_list])
            if participation_list
            else 0.5
        )
        
        overall_accuracy = (
            directional.confidence * directional_weight +
            volatility.accuracy * volatility_weight +
            timing.overall_timing_accuracy * timing_weight +
            participation_avg * participation_weight +
            (1.0 if regime.event_classification == ValidityScore.ACCURATE else 0.5) * regime_weight
        )
        
        # Model credibility: how much to trust our models?
        model_credibility = overall_accuracy  # 0.0 to 1.0
        
        # Find most/least accurate participants
        if participation_list:
            most_accurate = max(participation_list, key=lambda p: p.overall_accuracy)
            least_accurate = min(participation_list, key=lambda p: p.overall_accuracy)
            most_accurate_name = most_accurate.participant_type
            least_accurate_name = least_accurate.participant_type
        else:
            most_accurate_name = "N/A"
            least_accurate_name = "N/A"
        
        # Identify biggest failure
        if directional.confidence < 0.5:
            biggest_failure = f"Direction (predicted {directional.predicted_direction}, got {directional.actual_direction})"
        elif volatility.accuracy < 0.5:
            biggest_failure = f"Volatility (predicted {volatility.predicted_vol_expansion:.2f}, got {volatility.actual_vol_expansion:.2f})"
        elif timing.overall_timing_accuracy < 0.5:
            biggest_failure = "Timing accuracy"
        else:
            biggest_failure = "Unknown"
        
        return ValidationRecord(
            event_id=event_id,
            news_timestamp=news_timestamp,
            news_type=news_type,
            directional=directional,
            volatility=volatility,
            timing=timing,
            participation=participation_list,
            regime=regime,
            overall_accuracy=overall_accuracy,
            model_credibility=model_credibility,
            most_accurate_participant=most_accurate_name,
            least_accurate_participant=least_accurate_name,
            biggest_assumption_failure=biggest_failure,
            research_notes=f"Event {event_id}: Overall accuracy {overall_accuracy:.2f}, Credibility {model_credibility:.2f}"
        )
    
    def add_validation_record(self, record: ValidationRecord):
        """Add validation record and update credibilities."""
        self.credibility_dataset.add_validation(record)
    
    def get_credibility_report(self) -> Dict[str, float]:
        """Get credibility scores for all participant models."""
        return {
            "bank": self.credibility_dataset.bank_credibility.mean_accuracy,
            "hft": self.credibility_dataset.hft_credibility.mean_accuracy,
            "hedge_fund": self.credibility_dataset.hedge_fund_credibility.mean_accuracy,
            "market_maker": self.credibility_dataset.market_maker_credibility.mean_accuracy,
            "retail": self.credibility_dataset.retail_credibility.mean_accuracy,
        }
    
    # ================================================================
    # STATISTICAL SIGNIFICANCE TESTING
    # ================================================================
    
    def record_validation_outcome(
        self,
        direction_correct: bool,
        timing_correct: bool,
        overall_accuracy: float
    ):
        """Record a validation outcome for statistical significance analysis."""
        self._direction_hits.append(direction_correct)
        self._timing_hits.append(timing_correct)
        self._validation_history.append({
            "direction_correct": direction_correct,
            "timing_correct": timing_correct,
            "overall_accuracy": overall_accuracy,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def test_statistical_significance(
        self,
        null_probability: float = 0.5,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Test whether model accuracy is statistically better than random.
        
        Uses a one-sided binomial test:
        - H0: model accuracy = null_probability (e.g., 50% = coin flip)
        - H1: model accuracy > null_probability
        
        Returns significance results for directional and timing accuracy.
        """
        results = {}
        
        for name, hits in [
            ("directional", self._direction_hits),
            ("timing", self._timing_hits)
        ]:
            n = len(hits)
            if n < 5:
                results[name] = {
                    "n": n,
                    "status": "insufficient_data",
                    "message": f"Need ≥5 observations, have {n}",
                    "significant": False
                }
                continue
            
            k = sum(hits)  # successes
            observed_rate = k / n
            
            # Binomial test (one-sided): P(X >= k | n, p0)
            p_value = self._binomial_p_value(k, n, null_probability)
            
            # z-test approximation for large n
            se = math.sqrt(null_probability * (1 - null_probability) / n)
            z_score = (observed_rate - null_probability) / se if se > 0 else 0.0
            
            significant = p_value < (1 - confidence_level)
            
            results[name] = {
                "n": n,
                "successes": k,
                "observed_rate": round(observed_rate, 4),
                "null_probability": null_probability,
                "p_value": round(p_value, 6),
                "z_score": round(z_score, 3),
                "significant": significant,
                "confidence_level": confidence_level,
                "verdict": (
                    f"Model is significantly better than random (p={p_value:.4f})"
                    if significant
                    else f"Cannot reject H0 — model may not beat random (p={p_value:.4f})"
                )
            }
        
        # Overall assessment
        n_total = len(self._validation_history)
        if n_total >= 5:
            overall_scores = [v["overall_accuracy"] for v in self._validation_history]
            mean_acc = statistics.mean(overall_scores)
            std_acc = statistics.stdev(overall_scores) if n_total > 1 else 0.0
            
            # One-sample t-test: is mean accuracy > null_probability?
            t_stat = (mean_acc - null_probability) / (std_acc / math.sqrt(n_total)) if std_acc > 0 else 0.0
            
            results["overall"] = {
                "n": n_total,
                "mean_accuracy": round(mean_acc, 4),
                "std_accuracy": round(std_acc, 4),
                "t_statistic": round(t_stat, 3),
                "null_probability": null_probability,
                "verdict": (
                    f"Mean accuracy {mean_acc:.1%} vs random {null_probability:.1%} — "
                    f"{'significantly better' if t_stat > 1.645 else 'not significantly different'}"
                )
            }
        
        return results
    
    @staticmethod
    def _binomial_p_value(k: int, n: int, p: float) -> float:
        """
        Compute one-sided binomial p-value: P(X >= k | n, p).
        Uses normal approximation for large n, exact for small n.
        """
        if n > 30:
            # Normal approximation with continuity correction
            mean = n * p
            std = math.sqrt(n * p * (1 - p))
            if std == 0:
                return 0.0 if k > mean else 1.0
            z = (k - 0.5 - mean) / std
            # Approximate complementary CDF using error function
            return 0.5 * math.erfc(z / math.sqrt(2))
        else:
            # Exact binomial: sum P(X=i) for i=k..n
            p_val = 0.0
            for i in range(k, n + 1):
                # C(n, i) * p^i * (1-p)^(n-i)
                coeff = math.comb(n, i)
                p_val += coeff * (p ** i) * ((1 - p) ** (n - i))
            return min(1.0, p_val)
