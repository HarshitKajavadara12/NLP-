"""
Phase 6: Signal Authorization & Trust Weighting

Bridge between validated research (Phase 5) and live trading execution.

Core Logic:
1. Trust Weight Assignment — Score news events by Phase 5 validation history
2. Signal Filtering — Gate: only trust > 0.6 moves forward
3. Signal Weighting — Translate credibility into numeric signal strength
4. Signal Normalization — Consolidate conflicting signals at same timestamp

Output: Market signals ready for live execution (Phase 7)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


# ============================================================================
# ENUMS: Signal Classification
# ============================================================================

class SignalDirection(Enum):
    """Trading direction derived from news + models"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"


class VolatilityImpact(Enum):
    """Expected volatility change from news"""
    LOW = "low"          # No vol spike expected
    MEDIUM = "medium"    # Moderate vol expansion
    HIGH = "high"        # Severe vol expansion
    EXTREME = "extreme"  # Dislocation expected


class SignalSource(Enum):
    """Which participant model generated the signal"""
    HFT = "hft"                    # High-frequency trader
    HEDGE_FUND = "hedge_fund"      # Hedge fund
    RETAIL = "retail"              # Retail investor
    BANK = "bank"                  # Bank/dealer
    MARKET_MAKER = "market_maker"  # Market maker


class SignalStatus(Enum):
    """Signal approval status"""
    APPROVED = "approved"        # Trust > 0.6, ready for execution
    FILTERED = "filtered"        # Trust < 0.6, blocked
    PENDING_VALIDATION = "pending"
    CONFLICTED = "conflicted"    # Multiple signals contradict


class ReactionHorizon(Enum):
    """Expected timeframe for market reaction"""
    IMMEDIATE = "immediate"      # < 1 minute (HFT)
    SHORT_TERM = "short_term"    # 1-15 minutes
    MEDIUM_TERM = "medium_term"  # 15 minutes - 2 hours
    LONG_TERM = "long_term"      # > 2 hours


# ============================================================================
# INPUTS FROM PHASE 5: Validation Results
# ============================================================================

@dataclass
class ValidationMetrics:
    """Phase 5 outputs: validation scores for a news event"""
    event_id: str
    timestamp: datetime
    
    # From Phase 5 validation
    directional_accuracy: float      # 0.0-1.0: did direction prediction match?
    volatility_accuracy: float       # 0.0-1.0: did volatility prediction match?
    timing_accuracy: float           # 0.0-1.0: were reaction times correct?
    
    # Per-participant accuracy
    hft_participation_accuracy: float           # 0.0-1.0
    hedge_fund_participation_accuracy: float    # 0.0-1.0
    retail_participation_accuracy: float        # 0.0-1.0
    bank_participation_accuracy: float          # 0.0-1.0
    market_maker_participation_accuracy: float  # 0.0-1.0
    
    # Overall credibility
    overall_credibility: float       # 0.0-1.0: mean of all validations
    
    # Regime assessment
    regime_classification: str       # ACCURATE, PARTIALLY_ACCURATE, NOISY, INACCURATE


@dataclass
class NewsMetadata:
    """News event information for signal weighting"""
    event_id: str
    timestamp: datetime
    event_type: str              # EARNINGS, RATE_DECISION, etc.
    entity: str                  # Company or economic indicator
    polarity: float              # -1.0 (bearish) to 1.0 (bullish)
    intensity: float             # 0.0-1.0: magnitude of news
    ambiguity: float             # 0.0-1.0: clarity of interpretation
    

@dataclass
class PredictionFromPhase4:
    """Market impact prediction from Phase 4"""
    event_id: str
    expected_direction: str          # UP, DOWN, NEUTRAL
    expected_magnitude: float        # 0.0-1.0: expected move size
    expected_vol_expansion: float    # 0.0-1.0: volatility impact
    expected_volume_spike: float     # 0.0-1.0: liquidity impact
    shock_onset_seconds: float       # When impact starts
    peak_impact_seconds: float       # When peak occurs
    recovery_seconds: float          # When market stabilizes
    

# ============================================================================
# PHASE 6 CORE STRUCTURES: Trust & Signal Assignment
# ============================================================================

@dataclass
class TrustWeightHistory:
    """Historical trust evolution for a news event type"""
    event_type: str                  # EARNINGS, RATE_DECISION, etc.
    event_count: int = 0            # Number of occurrences
    accuracy_history: List[float] = field(default_factory=list)  # [0.8, 0.75, 0.92, ...]
    mean_accuracy: float = 0.0      # Average historical accuracy
    std_dev: float = 0.0            # Volatility of accuracy
    
    def update(self, accuracy: float) -> None:
        """Add new accuracy observation"""
        self.accuracy_history.append(accuracy)
        self.event_count += 1
        self.mean_accuracy = sum(self.accuracy_history) / len(self.accuracy_history)
        
        if len(self.accuracy_history) > 1:
            variance = sum((x - self.mean_accuracy) ** 2 for x in self.accuracy_history) / len(self.accuracy_history)
            self.std_dev = variance ** 0.5
    
    def get_trust_score(self) -> float:
        """Return current trust score (0.0-1.0)"""
        if self.event_count == 0:
            return 0.5  # Default neutral trust
        return max(0.0, min(1.0, self.mean_accuracy))


@dataclass
class ParticipantWeights:
    """Dynamic trust weights for each participant model"""
    timestamp: datetime
    hft_weight: float                  # 0.0-1.0
    hedge_fund_weight: float           # 0.0-1.0
    retail_weight: float               # 0.0-1.0
    bank_weight: float                 # 0.0-1.0
    market_maker_weight: float         # 0.0-1.0
    
    def get_weight_for_participant(self, participant: str) -> float:
        """Retrieve weight for specific participant"""
        weights_map = {
            "hft": self.hft_weight,
            "hedge_fund": self.hedge_fund_weight,
            "retail": self.retail_weight,
            "bank": self.bank_weight,
            "market_maker": self.market_maker_weight,
        }
        return weights_map.get(participant, 0.5)
    
    def normalize_weights(self) -> "ParticipantWeights":
        """Normalize weights to sum to 1.0"""
        total = (self.hft_weight + self.hedge_fund_weight + 
                self.retail_weight + self.bank_weight + self.market_maker_weight)
        if total == 0:
            return self
        
        scale = 1.0 / total
        return ParticipantWeights(
            timestamp=self.timestamp,
            hft_weight=self.hft_weight * scale,
            hedge_fund_weight=self.hedge_fund_weight * scale,
            retail_weight=self.retail_weight * scale,
            bank_weight=self.bank_weight * scale,
            market_maker_weight=self.market_maker_weight * scale,
        )


@dataclass
class SignalRecord:
    """Individual trading signal authorized for live execution"""
    signal_id: str
    timestamp: datetime
    
    # Signal definition
    direction: SignalDirection      # BUY, SELL, NEUTRAL, UNCERTAIN
    strength: float                 # 0.0-1.0: signal confidence
    volatility_impact: VolatilityImpact
    
    # Trust & weighting
    trust_score: float              # 0.0-1.0: event credibility
    participant_weights: Dict[str, float]  # {hft: 0.95, hedge_fund: 0.80, ...}
    
    # Source information
    source_news_ids: List[str]      # Which news events triggered
    source_event_types: List[str]   # Event types (EARNINGS, RATE_DECISION, etc.)
    
    # Reaction window
    expected_reaction_horizon: ReactionHorizon
    
    # Status
    status: SignalStatus            # APPROVED, FILTERED, CONFLICTED
    
    # Execution parameters
    approval_timestamp: datetime
    expiration_timestamp: datetime  # Signal valid until this time
    
    def is_approved(self) -> bool:
        """Check if signal is approved for live execution"""
        return self.status == SignalStatus.APPROVED
    
    def is_expired(self, check_time: Optional[datetime] = None) -> bool:
        """Check if signal has expired"""
        now = check_time or datetime.now()
        return now > self.expiration_timestamp
    
    def get_effective_strength(self) -> float:
        """Calculate effective signal strength for execution"""
        if not self.is_approved():
            return 0.0
        if self.is_expired():
            return 0.0
        
        # Strength = trust_score × signal_strength
        return self.trust_score * self.strength


@dataclass
class NormalizedSignal:
    """Consolidated signal combining multiple news events at same timestamp"""
    timestamp: datetime
    
    # Aggregated direction
    net_direction: SignalDirection
    net_strength: float             # 0.0-1.0
    
    # Components
    constituent_signals: List[SignalRecord]
    signal_count: int
    
    # Conflict assessment
    has_conflicts: bool             # Multiple contradicting signals?
    conflict_resolution: str        # How conflicts were resolved
    
    # Execution readiness
    ready_for_execution: bool
    confidence_level: str           # high, medium, low
    

# ============================================================================
# PHASE 6 CORE ENGINE: Signal Authorization
# ============================================================================

class SignalAuthorizer:
    """
    Converts validated research insights into executable trading signals.
    
    Pipeline:
    1. Trust Score Assignment — Historical validation → trust weight
    2. Signal Filtering — Trust > 0.6 → approved, else blocked
    3. Signal Weighting — Credibility × participant insights → strength
    4. Signal Normalization — Consolidate conflicting signals
    5. Execution Gate — Approved signals → live trading
    """
    
    def __init__(self):
        """Initialize signal authorization engine"""
        self.trust_history: Dict[str, TrustWeightHistory] = {}
        self.current_participant_weights: ParticipantWeights = ParticipantWeights(
            timestamp=datetime.now(),
            hft_weight=0.95,
            hedge_fund_weight=0.80,
            retail_weight=0.40,
            bank_weight=0.70,
            market_maker_weight=0.85,
        )
        self.approved_signals: List[SignalRecord] = []
        self.filtered_signals: List[SignalRecord] = []
        self.signal_counter = 0
    
    # ========================================================================
    # STEP 1: Trust Weight Assignment
    # ========================================================================
    
    def assign_trust_score(
        self,
        news_metadata: NewsMetadata,
        validation_metrics: ValidationMetrics
    ) -> float:
        """
        Assign trust score to news event based on Phase 5 validation history.
        
        Trust Score = Historical Accuracy × Current Validation
        
        Args:
            news_metadata: Event type, intensity, etc.
            validation_metrics: Phase 5 validation results
        
        Returns:
            trust_score (0.0-1.0): How much to trust this event
        """
        event_type = news_metadata.event_type
        
        # Initialize history if first occurrence
        if event_type not in self.trust_history:
            self.trust_history[event_type] = TrustWeightHistory(event_type=event_type)
        
        # Get historical accuracy for this event type
        history = self.trust_history[event_type]
        historical_accuracy = history.get_trust_score()
        
        # Current validation score
        current_accuracy = validation_metrics.overall_credibility
        
        # For first event of type, use 50% historical (neutral default)
        # For subsequent events, weight historical more heavily
        if history.event_count == 0:
            # First event: lean on current validation
            trust_score = (0.3 * 0.5) + (0.7 * current_accuracy)
        else:
            # Subsequent: blend historical + current
            trust_score = (0.6 * historical_accuracy) + (0.4 * current_accuracy)
        
        # Adjust for intensity: high-intensity events need higher proof
        if news_metadata.intensity > 0.8:
            # High intensity requires slightly more evidence
            trust_score *= 0.98
        
        # Adjust for ambiguity: unclear news is less trustworthy
        trust_score *= (1.0 - (0.15 * news_metadata.ambiguity))
        
        # Update historical record
        history.update(current_accuracy)
        
        return max(0.0, min(1.0, trust_score))
    
    # ========================================================================
    # STEP 2: Signal Filtering & Gating
    # ========================================================================
    
    def filter_signal(
        self,
        trust_score: float,
        validation_metrics: ValidationMetrics,
        threshold: float = 0.6
    ) -> SignalStatus:
        """
        Gate signal: only trust > threshold moves forward.
        
        Args:
            trust_score: Assigned trust from Step 1
            validation_metrics: Phase 5 results
            threshold: Minimum trust for approval (default 0.6)
        
        Returns:
            SignalStatus: APPROVED or FILTERED
        """
        if trust_score < threshold:
            return SignalStatus.FILTERED
        
        # Additional check: regime must be at least PARTIALLY_ACCURATE
        regime_acceptability = {
            "ACCURATE": True,
            "PARTIALLY_ACCURATE": True,
            "NOISY": False,
            "INACCURATE": False,
        }
        
        if not regime_acceptability.get(validation_metrics.regime_classification, False):
            return SignalStatus.FILTERED
        
        return SignalStatus.APPROVED
    
    # ========================================================================
    # STEP 3: Signal Weighting
    # ========================================================================
    
    def weight_signal_strength(
        self,
        trust_score: float,
        validation_metrics: ValidationMetrics,
        prediction: PredictionFromPhase4,
        news_metadata: NewsMetadata,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Translate credibility into numeric signal strength.
        
        Signal Strength = Trust × Participant Consensus × Prediction Magnitude
        
        Args:
            trust_score: Trust assigned in Step 1
            validation_metrics: Phase 5 validation results
            prediction: Expected market impact from Phase 4
            news_metadata: Event details
        
        Returns:
            (signal_strength, participant_weights_used): Both 0.0-1.0
        """
        # Get current participant weights
        weights = self.current_participant_weights.normalize_weights()
        
        # Extract per-participant accuracies
        participant_accuracies = {
            "hft": validation_metrics.hft_participation_accuracy,
            "hedge_fund": validation_metrics.hedge_fund_participation_accuracy,
            "retail": validation_metrics.retail_participation_accuracy,
            "bank": validation_metrics.bank_participation_accuracy,
            "market_maker": validation_metrics.market_maker_participation_accuracy,
        }
        
        # Calculate weighted participant consensus
        consensus = 0.0
        for participant, accuracy in participant_accuracies.items():
            participant_weight = weights.get_weight_for_participant(participant)
            # Only count participants that had measurable predictions
            if accuracy > 0:
                consensus += accuracy * participant_weight
        
        # Signal strength = Trust × Consensus × Prediction Magnitude
        signal_strength = (
            trust_score *
            consensus *
            prediction.expected_magnitude
        )
        
        # Convert weights to dict for output
        weights_dict = {
            "hft": weights.hft_weight,
            "hedge_fund": weights.hedge_fund_weight,
            "retail": weights.retail_weight,
            "bank": weights.bank_weight,
            "market_maker": weights.market_maker_weight,
        }
        
        return max(0.0, min(1.0, signal_strength)), weights_dict
    
    # ========================================================================
    # STEP 4: Signal Direction & Volatility
    # ========================================================================
    
    def determine_signal_direction(
        self,
        validation_metrics: ValidationMetrics,
        news_metadata: NewsMetadata,
        prediction: PredictionFromPhase4,
    ) -> SignalDirection:
        """
        Determine trading direction from validation + news + prediction.
        
        Args:
            validation_metrics: Phase 5 results
            news_metadata: Event polarity and type
            prediction: Expected direction from Phase 4
        
        Returns:
            SignalDirection: BUY, SELL, NEUTRAL, UNCERTAIN
        """
        # If directional accuracy < 0.3, direction is uncertain
        if validation_metrics.directional_accuracy < 0.3:
            return SignalDirection.UNCERTAIN
        
        # Map news polarity to direction
        if news_metadata.polarity > 0.3:
            if prediction.expected_direction == "UP":
                return SignalDirection.BUY
        elif news_metadata.polarity < -0.3:
            if prediction.expected_direction == "DOWN":
                return SignalDirection.SELL
        
        return SignalDirection.NEUTRAL
    
    def determine_volatility_impact(
        self,
        validation_metrics: ValidationMetrics,
        prediction: PredictionFromPhase4,
        news_metadata: NewsMetadata,
    ) -> VolatilityImpact:
        """
        Determine expected volatility impact.
        
        Args:
            validation_metrics: Phase 5 results
            prediction: Expected vol from Phase 4
            news_metadata: Event intensity
        
        Returns:
            VolatilityImpact: LOW, MEDIUM, HIGH, EXTREME
        """
        # Vol accuracy indicates how well we predict vol
        expected_vol = prediction.expected_vol_expansion
        vol_accuracy = validation_metrics.volatility_accuracy
        
        # High intensity + high vol prediction + high vol accuracy = HIGH vol impact
        if (news_metadata.intensity > 0.7 and 
            expected_vol > 0.6 and 
            vol_accuracy > 0.7):
            return VolatilityImpact.HIGH
        
        # Extreme cases: high intensity + very high vol prediction
        if news_metadata.intensity > 0.9 and expected_vol > 0.8:
            return VolatilityImpact.EXTREME
        
        # Moderate vol
        if expected_vol > 0.4:
            return VolatilityImpact.MEDIUM
        
        return VolatilityImpact.LOW
    
    def determine_reaction_horizon(
        self,
        validation_metrics: ValidationMetrics,
        prediction: PredictionFromPhase4,
    ) -> ReactionHorizon:
        """
        Determine expected timeframe for market reaction.
        
        Horizon depends on which participants validate:
        - HFT accurate → immediate
        - HF accurate → short-term
        - Retail accurate → long-term
        
        Args:
            validation_metrics: Participant accuracies
            prediction: Timing from Phase 4
        
        Returns:
            ReactionHorizon: IMMEDIATE, SHORT_TERM, MEDIUM_TERM, LONG_TERM
        """
        if validation_metrics.hft_participation_accuracy > 0.75:
            return ReactionHorizon.IMMEDIATE
        
        if validation_metrics.hedge_fund_participation_accuracy > 0.75:
            if prediction.peak_impact_seconds < 900:  # < 15 min
                return ReactionHorizon.SHORT_TERM
            else:
                return ReactionHorizon.MEDIUM_TERM
        
        return ReactionHorizon.LONG_TERM
    
    # ========================================================================
    # STEP 5: Signal Normalization
    # ========================================================================
    
    def normalize_signals(
        self,
        signals: List[SignalRecord],
        timestamp: datetime,
    ) -> NormalizedSignal:
        """
        Consolidate multiple signals at same timestamp.
        
        Handle conflicting directions by weighted vote.
        
        Args:
            signals: Individual approved signals
            timestamp: Time of consolidation
        
        Returns:
            NormalizedSignal: Consolidated for execution
        """
        if not signals:
            return NormalizedSignal(
                timestamp=timestamp,
                net_direction=SignalDirection.NEUTRAL,
                net_strength=0.0,
                constituent_signals=[],
                signal_count=0,
                has_conflicts=False,
                conflict_resolution="no_signals",
                ready_for_execution=False,
                confidence_level="low",
            )
        
        # Vote on direction (weighted by strength)
        direction_votes = {
            SignalDirection.BUY: 0.0,
            SignalDirection.SELL: 0.0,
            SignalDirection.NEUTRAL: 0.0,
        }
        
        total_strength = 0.0
        for signal in signals:
            if signal.direction != SignalDirection.UNCERTAIN:
                direction_votes[signal.direction] += signal.strength
                total_strength += signal.strength
        
        # Determine net direction
        if total_strength == 0:
            net_direction = SignalDirection.NEUTRAL
            net_strength = 0.0
        else:
            net_direction = max(direction_votes.items(), key=lambda x: x[1])[0]
            net_strength = direction_votes[net_direction] / total_strength
        
        # Check for conflicts: if no clear winner
        buy_pct = direction_votes[SignalDirection.BUY] / total_strength if total_strength > 0 else 0
        sell_pct = direction_votes[SignalDirection.SELL] / total_strength if total_strength > 0 else 0
        has_conflicts = (0.3 < buy_pct < 0.7) or (0.3 < sell_pct < 0.7)
        
        # Confidence level
        if net_strength > 0.75:
            confidence_level = "high"
            ready_for_execution = True
        elif net_strength > 0.5:
            confidence_level = "medium"
            ready_for_execution = True
        else:
            confidence_level = "low"
            ready_for_execution = False
        
        return NormalizedSignal(
            timestamp=timestamp,
            net_direction=net_direction,
            net_strength=net_strength,
            constituent_signals=signals,
            signal_count=len(signals),
            has_conflicts=has_conflicts,
            conflict_resolution="weighted_vote" if not has_conflicts else "conflict_detected",
            ready_for_execution=ready_for_execution,
            confidence_level=confidence_level,
        )
    
    # ========================================================================
    # MAIN PIPELINE: Create Authorized Signal
    # ========================================================================
    
    def authorize_signal(
        self,
        news_metadata: NewsMetadata,
        validation_metrics: ValidationMetrics,
        prediction: PredictionFromPhase4,
    ) -> SignalRecord:
        """
        Full pipeline: Trust → Filter → Weight → Signal → Return
        
        This is the main entry point for Phase 6.
        
        Args:
            news_metadata: Event information
            validation_metrics: Phase 5 validation
            prediction: Phase 4 market impact prediction
        
        Returns:
            SignalRecord: Authorized or filtered signal
        """
        # STEP 1: Assign trust score
        trust_score = self.assign_trust_score(news_metadata, validation_metrics)
        
        # STEP 2: Filter signal
        status = self.filter_signal(trust_score, validation_metrics, threshold=0.6)
        
        # STEP 3: Weight signal strength
        signal_strength, participant_weights = self.weight_signal_strength(
            trust_score,
            validation_metrics,
            prediction,
            news_metadata,
        )
        
        # STEP 4: Determine direction & volatility
        direction = self.determine_signal_direction(
            validation_metrics,
            news_metadata,
            prediction,
        )
        
        vol_impact = self.determine_volatility_impact(
            validation_metrics,
            prediction,
            news_metadata,
        )
        
        reaction_horizon = self.determine_reaction_horizon(
            validation_metrics,
            prediction,
        )
        
        # STEP 5: Create signal record
        self.signal_counter += 1
        now = datetime.now()
        
        signal = SignalRecord(
            signal_id=f"SIG_{now.timestamp()}_{self.signal_counter}",
            timestamp=now,
            direction=direction,
            strength=signal_strength,
            volatility_impact=vol_impact,
            trust_score=trust_score,
            participant_weights=participant_weights,
            source_news_ids=[news_metadata.event_id],
            source_event_types=[news_metadata.event_type],
            expected_reaction_horizon=reaction_horizon,
            status=status,
            approval_timestamp=now,
            expiration_timestamp=now + timedelta(hours=4),  # Signal valid for 4 hours
        )
        
        # Store in appropriate list
        if status == SignalStatus.APPROVED:
            self.approved_signals.append(signal)
        else:
            self.filtered_signals.append(signal)
        
        return signal
    
    # ========================================================================
    # EXECUTION GATE: Live Trading Interface
    # ========================================================================
    
    def get_approved_signals(self, check_time: Optional[datetime] = None) -> List[SignalRecord]:
        """
        Retrieve all approved, non-expired signals ready for live execution.
        
        Args:
            check_time: Time to check expiration against (default: now)
        
        Returns:
            List[SignalRecord]: Signals approved for execution
        """
        now = check_time or datetime.now()
        return [
            signal for signal in self.approved_signals
            if signal.is_approved() and not signal.is_expired(now)
        ]
    
    def update_participant_weights(
        self,
        hft_weight: float,
        hedge_fund_weight: float,
        retail_weight: float,
        bank_weight: float,
        market_maker_weight: float,
    ) -> None:
        """
        Update participant model weights (dynamic, based on Phase 5 feedback).
        
        Args:
            *_weight: New weights for each participant (0.0-1.0)
        """
        self.current_participant_weights = ParticipantWeights(
            timestamp=datetime.now(),
            hft_weight=hft_weight,
            hedge_fund_weight=hedge_fund_weight,
            retail_weight=retail_weight,
            bank_weight=bank_weight,
            market_maker_weight=market_maker_weight,
        )
    
    def get_signal_statistics(self) -> Dict:
        """Return statistics on signal authorization"""
        total = len(self.approved_signals) + len(self.filtered_signals)
        approved_count = len(self.approved_signals)
        
        return {
            "total_signals_processed": total,
            "approved_signals": approved_count,
            "filtered_signals": len(self.filtered_signals),
            "approval_rate": approved_count / total if total > 0 else 0.0,
            "event_types_tracked": len(self.trust_history),
            "active_participant_weights": {
                "hft": self.current_participant_weights.hft_weight,
                "hedge_fund": self.current_participant_weights.hedge_fund_weight,
                "retail": self.current_participant_weights.retail_weight,
                "bank": self.current_participant_weights.bank_weight,
                "market_maker": self.current_participant_weights.market_maker_weight,
            },
        }
