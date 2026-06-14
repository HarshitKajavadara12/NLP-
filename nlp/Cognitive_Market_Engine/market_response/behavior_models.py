"""
PHASE 3: EXPECTATION -> BEHAVIOR TRANSLATION

A Behavior is: A probabilistic market posture adopted by a participant
in response to changed expectations.

NOT a trade. NOT an order. NOT a price action.

A behavior is a WILLINGNESS and POSTURE.

Same expectation from different participants = Different behaviors.
Same participant with different expectations = Different behaviors.

This phase answers:
"Given what they believe (Phase 2), what are they LIKELY to do?"

Not "will definitely do" - "are likely to do"
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime

try:
    from participant_cognition.participant_models import (
        ParticipantExpectation, ParticipantType, ConfidenceLevel
    )
except ImportError:
    # Fallback: import from shared types if participant_cognition not on PYTHONPATH
    try:
        from shared import ParticipantType
    except ImportError:
        from enum import Enum
        class ParticipantType(str, Enum):
            RETAIL = "retail"
            HFT = "hft"
            HEDGE_FUND = "hedge_fund"
            BANK = "bank"
            MARKET_MAKER = "market_maker"
    ParticipantExpectation = None
    ConfidenceLevel = None


class RiskPosture(str, Enum):
    """How do they manage risk?"""
    INCREASE_RISK = "increase_risk"
    DECREASE_RISK = "decrease_risk"
    NEUTRAL = "neutral"
    HEDGE = "hedge"


class LiquidityPosture(str, Enum):
    """How do they supply/demand liquidity?"""
    PROVIDE_LIQUIDITY = "provide_liquidity"
    REDUCE_LIQUIDITY = "reduce_liquidity"
    WITHDRAW_LIQUIDITY = "withdraw_liquidity"
    NEUTRAL = "neutral"


class ExposureIntent(str, Enum):
    """What do they want their exposure to be?"""
    INCREASE_EXPOSURE = "increase_exposure"
    DECREASE_EXPOSURE = "decrease_exposure"
    MAINTAIN_EXPOSURE = "maintain_exposure"
    CONVERT_EXPOSURE = "convert_exposure"  # Change type, not amount


class TimeUrgency(str, Enum):
    """How fast must they act?"""
    IMMEDIATE = "immediate"
    SAME_DAY = "same_day"
    DELAYED = "delayed"
    PASSIVE = "passive"


class Optionality(str, Enum):
    """What's their flexibility?"""
    HEDGE = "hedge"
    WAIT = "wait"
    REBALANCE = "rebalance"
    CONVERT = "convert"
    NOTHING = "nothing"


@dataclass
class BehaviorProbability:
    """Probability of a behavior with confidence."""
    likelihood: float  # 0.0 to 1.0
    intensity: float   # 0.0 (weak) to 1.0 (strong)
    confidence: ConfidenceLevel
    time_window: str = ""  # e.g., "within 1 hour"
    
    def is_dominant(self, threshold: float = 0.5) -> bool:
        """Is this behavior dominant (above threshold)?"""
        return self.likelihood > threshold
    
    def get_summary(self) -> str:
        return f"{self.likelihood:.2f} likelihood, {self.intensity:.2f} intensity ({self.confidence.value})"


@dataclass
class BehaviorProfile:
    """
    The behavior posture adopted by a participant
    in response to their expectations.
    
    This is NOT a trade.
    This is a willingness and posture.
    """
    
    participant_type: ParticipantType
    expectation_id: str  # Links to Phase 2 ParticipantExpectation
    timestamp: datetime
    
    # Risk Management
    risk_posture: RiskPosture
    risk_probability: BehaviorProbability
    
    # Liquidity Supply/Demand
    liquidity_posture: LiquidityPosture
    liquidity_probability: BehaviorProbability
    
    # Exposure
    exposure_intent: ExposureIntent
    exposure_probability: BehaviorProbability
    
    # Time Sensitivity
    urgency: TimeUrgency
    urgency_probability: BehaviorProbability
    
    # Flexibility
    optionality: Optionality
    optionality_probability: BehaviorProbability = field(default_factory=lambda: BehaviorProbability(0.5, 0.5, ConfidenceLevel.MEDIUM))
    
    # Contradictions Allowed (realistic)
    contradictions: List[str] = field(default_factory=list)
    
    # Confidence in entire posture
    overall_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    
    # Reasoning
    reasoning: str = ""
    
    # Alternative behaviors (in case primary doesn't execute)
    fallback_behaviors: List[tuple] = field(default_factory=list)  # [(posture, probability)]
    
    def get_summary(self) -> str:
        """Human-readable summary of behavior."""
        return f"""
BehaviorProfile ({self.participant_type.value}):
  Risk Posture: {self.risk_posture.value} ({self.risk_probability.get_summary()})
  Liquidity Posture: {self.liquidity_posture.value} ({self.liquidity_probability.get_summary()})
  Exposure Intent: {self.exposure_intent.value} ({self.exposure_probability.get_summary()})
  Urgency: {self.urgency.value} ({self.urgency_probability.get_summary()})
  Optionality: {self.optionality.value}
  Overall Confidence: {self.overall_confidence.value}
  Reasoning: {self.reasoning}
        """
    
    def has_contradictions(self) -> bool:
        """Are there contradictory behaviors?"""
        return len(self.contradictions) > 0
    
    def get_dominant_behaviors(self, threshold: float = 0.5) -> List[str]:
        """Get list of dominant behaviors above threshold."""
        dominants = []
        if self.risk_probability.is_dominant(threshold):
            dominants.append(f"Risk: {self.risk_posture.value}")
        if self.liquidity_probability.is_dominant(threshold):
            dominants.append(f"Liquidity: {self.liquidity_posture.value}")
        if self.exposure_probability.is_dominant(threshold):
            dominants.append(f"Exposure: {self.exposure_intent.value}")
        if self.urgency_probability.is_dominant(threshold):
            dominants.append(f"Urgency: {self.urgency.value}")
        return dominants


@dataclass
class ParticipantConstraints:
    """
    Real-world constraints that shape behavior.
    
    These are NOT cognitive - they're hard limits.
    """
    
    max_position_size: float  # Absolute maximum
    mandate: str  # "Long only", "Hedged", "Balanced", "Opportunistic"
    regulatory_limits: List[str] = field(default_factory=list)
    capital_available: float = 1.0  # 0.0 to 1.0 (normalized)
    leverage_limit: float = 1.0  # 1.0 = no leverage, 3.0 = 3x max
    liquidity_constraints: str = "normal"  # "tight", "normal", "abundant"
    end_of_day_rebalance_required: bool = False
    no_short_sale: bool = False
    
    def allows_increased_risk(self) -> bool:
        """Can they actually increase risk given constraints?"""
        return self.capital_available > 0.3 and self.leverage_limit > 1.0
    
    def allows_reduced_liquidity(self) -> bool:
        """Can they reduce liquidity given constraints?"""
        return self.liquidity_constraints != "tight"
    
    def get_summary(self) -> str:
        return f"""
ParticipantConstraints:
  Mandate: {self.mandate}
  Capital Available: {self.capital_available:.0%}
  Leverage Limit: {self.leverage_limit:.1f}x
  Liquidity: {self.liquidity_constraints}
  Max Position: {self.max_position_size:.1f}
        """


class BehaviorTranslator:
    """
    Translates ParticipantExpectation -> BehaviorProfile
    
    This is NOT deterministic (unlike Phase 2).
    Behavior is probabilistic because constraints matter.
    
    Same expectation + different constraints = different behaviors
    """
    
    def __init__(self):
        """Initialize translator with no state."""
        pass
    
    def translate(
        self,
        expectation: ParticipantExpectation,
        constraints: ParticipantConstraints
    ) -> BehaviorProfile:
        """
        Transform expectation into behavior profile.
        
        Process:
        1. Extract expectation signals (belief_shift, urgency, etc.)
        2. Evaluate constraints (can they actually do this?)
        3. Map to behavior postures
        4. Calculate probabilities
        5. Identify contradictions
        6. Generate reasoning
        """
        
        # Step 1: Extract signals
        belief_shift = expectation.belief_shift
        uncertainty = expectation.uncertainty_level
        urgency = expectation.urgency
        
        # Step 2: Risk Posture (belief-driven, constraint-limited)
        risk_posture, risk_prob = self._determine_risk_posture(
            belief_shift, constraints, expectation.participant_type
        )
        
        # Step 3: Liquidity Posture (uncertainty-driven, constraint-limited)
        liquidity_posture, liquidity_prob = self._determine_liquidity_posture(
            uncertainty, constraints, expectation.participant_type
        )
        
        # Step 4: Exposure Intent (belief-driven)
        exposure_intent, exposure_prob = self._determine_exposure_intent(
            belief_shift, constraints, expectation.participant_type
        )
        
        # Step 5: Time Urgency (urgency-driven)
        time_urgency, time_prob = self._determine_urgency(
            urgency, expectation.participant_type
        )
        
        # Step 6: Optionality (flexibility-driven)
        optionality, opt_prob = self._determine_optionality(
            uncertainty, belief_shift, expectation.participant_type
        )
        
        # Step 7: Identify contradictions
        contradictions = self._identify_contradictions(
            risk_posture, liquidity_posture, exposure_intent
        )
        
        # Step 8: Generate reasoning
        reasoning = self._generate_reasoning(
            expectation, risk_posture, liquidity_posture, exposure_intent
        )
        
        # Create behavior profile
        profile = BehaviorProfile(
            participant_type=expectation.participant_type,
            expectation_id=expectation.news_event_id,
            timestamp=datetime.now(),
            risk_posture=risk_posture,
            risk_probability=risk_prob,
            liquidity_posture=liquidity_posture,
            liquidity_probability=liquidity_prob,
            exposure_intent=exposure_intent,
            exposure_probability=exposure_prob,
            urgency=time_urgency,
            urgency_probability=time_prob,
            optionality=optionality,
            optionality_probability=opt_prob,
            contradictions=contradictions,
            overall_confidence=self._calculate_overall_confidence(expectation),
            reasoning=reasoning,
            fallback_behaviors=self._determine_fallbacks(
                expectation, constraints
            )
        )
        
        return profile
    
    def _determine_risk_posture(
        self, belief_shift: float, constraints: ParticipantConstraints,
        participant_type: ParticipantType
    ) -> tuple:
        """Determine risk posture from belief shift and constraints."""
        
        # Belief-driven baseline
        if belief_shift > 0.3:
            baseline_posture = RiskPosture.INCREASE_RISK
            baseline_prob = 0.7
        elif belief_shift < -0.3:
            baseline_posture = RiskPosture.DECREASE_RISK
            baseline_prob = 0.7
        else:
            baseline_posture = RiskPosture.NEUTRAL
            baseline_prob = 0.5
        
        # Constraint adjustment
        if not constraints.allows_increased_risk() and belief_shift > 0.3:
            # Can't increase risk due to constraints
            baseline_posture = RiskPosture.NEUTRAL
            baseline_prob *= 0.5
        
        # Participant-type adjustments
        if participant_type == ParticipantType.BANK and belief_shift < 0:
            baseline_posture = RiskPosture.HEDGE
            baseline_prob = 0.8
        
        elif participant_type == ParticipantType.HFT and belief_shift != 0:
            baseline_posture = RiskPosture.DECREASE_RISK
            baseline_prob = 0.6
        
        confidence = ConfidenceLevel.HIGH if baseline_prob > 0.6 else ConfidenceLevel.MEDIUM
        probability = BehaviorProbability(
            likelihood=min(1.0, baseline_prob),
            intensity=abs(belief_shift),
            confidence=confidence,
            time_window="immediate" if participant_type == ParticipantType.HFT else "within hours"
        )
        
        return baseline_posture, probability
    
    def _determine_liquidity_posture(
        self, uncertainty: float, constraints: ParticipantConstraints,
        participant_type: ParticipantType
    ) -> tuple:
        """Determine liquidity posture from uncertainty and constraints."""
        
        # Uncertainty-driven baseline
        if uncertainty > 0.7:
            baseline_posture = LiquidityPosture.REDUCE_LIQUIDITY
            baseline_prob = 0.8
        elif uncertainty > 0.4:
            baseline_posture = LiquidityPosture.NEUTRAL
            baseline_prob = 0.5
        else:
            baseline_posture = LiquidityPosture.PROVIDE_LIQUIDITY
            baseline_prob = 0.6
        
        # Constraint adjustment
        if not constraints.allows_reduced_liquidity() and uncertainty > 0.7:
            baseline_posture = LiquidityPosture.NEUTRAL
            baseline_prob *= 0.7
        
        # Participant-type adjustments
        if participant_type == ParticipantType.MARKET_MAKER and uncertainty > 0.5:
            baseline_posture = LiquidityPosture.REDUCE_LIQUIDITY
            baseline_prob = 0.8
        
        elif participant_type == ParticipantType.HFT and uncertainty > 0.5:
            baseline_posture = LiquidityPosture.WITHDRAW_LIQUIDITY
            baseline_prob = 0.9
        
        confidence = ConfidenceLevel.HIGH if baseline_prob > 0.6 else ConfidenceLevel.MEDIUM
        probability = BehaviorProbability(
            likelihood=min(1.0, baseline_prob),
            intensity=uncertainty,
            confidence=confidence
        )
        
        return baseline_posture, probability
    
    def _determine_exposure_intent(
        self, belief_shift: float, constraints: ParticipantConstraints,
        participant_type: ParticipantType
    ) -> tuple:
        """Determine exposure intent from belief shift and constraints."""
        
        # Belief-driven baseline
        if belief_shift > 0.2:
            baseline_intent = ExposureIntent.INCREASE_EXPOSURE
            baseline_prob = abs(belief_shift)
        elif belief_shift < -0.2:
            baseline_intent = ExposureIntent.DECREASE_EXPOSURE
            baseline_prob = abs(belief_shift)
        else:
            baseline_intent = ExposureIntent.MAINTAIN_EXPOSURE
            baseline_prob = 0.5
        
        # Constraint adjustment - CAPITAL AVAILABILITY MATTERS
        if baseline_intent == ExposureIntent.INCREASE_EXPOSURE:
            if constraints.capital_available < 0.3:
                baseline_intent = ExposureIntent.MAINTAIN_EXPOSURE
                baseline_prob = 0.2  # Low probability when capital-constrained
            elif constraints.capital_available < 0.5:
                baseline_prob *= 0.6  # Moderate reduction
            else:
                baseline_prob *= 0.9  # Slight increase with ample capital
        
        # Mandate constraint
        if constraints.mandate == "Long only" and belief_shift < 0:
            baseline_intent = ExposureIntent.MAINTAIN_EXPOSURE
            baseline_prob = 0.3
        
        confidence = ConfidenceLevel.HIGH if baseline_prob > 0.6 else ConfidenceLevel.MEDIUM
        probability = BehaviorProbability(
            likelihood=min(1.0, baseline_prob),
            intensity=abs(belief_shift),
            confidence=confidence
        )
        
        return baseline_intent, probability
    
    def _determine_urgency(
        self, urgency_signal: float,
        participant_type: ParticipantType
    ) -> tuple:
        """Determine time urgency from urgency signal and participant type."""
        
        # Base urgency from signal
        if urgency_signal > 0.7:
            baseline_urgency = TimeUrgency.IMMEDIATE
            baseline_prob = 0.8
        elif urgency_signal > 0.4:
            baseline_urgency = TimeUrgency.SAME_DAY
            baseline_prob = 0.6
        elif urgency_signal > 0.1:
            baseline_urgency = TimeUrgency.DELAYED
            baseline_prob = 0.4
        else:
            baseline_urgency = TimeUrgency.PASSIVE
            baseline_prob = 0.7
        
        # Participant-type override
        if participant_type == ParticipantType.HFT:
            baseline_urgency = TimeUrgency.IMMEDIATE if urgency_signal > 0.1 else TimeUrgency.PASSIVE
            baseline_prob = 0.9 if urgency_signal > 0.1 else 0.7
        
        elif participant_type == ParticipantType.BANK:
            if baseline_urgency == TimeUrgency.IMMEDIATE:
                baseline_urgency = TimeUrgency.SAME_DAY
                baseline_prob = 0.6
        
        confidence = ConfidenceLevel.HIGH if baseline_prob > 0.6 else ConfidenceLevel.MEDIUM
        probability = BehaviorProbability(
            likelihood=min(1.0, baseline_prob),
            intensity=urgency_signal,
            confidence=confidence
        )
        
        return baseline_urgency, probability
    
    def _determine_optionality(
        self, uncertainty: float, belief_shift: float,
        participant_type: ParticipantType
    ) -> tuple:
        """Determine optionality (hedging, waiting, etc.)."""
        
        # High uncertainty -> wait
        if uncertainty > 0.7:
            baseline_opt = Optionality.WAIT
            baseline_prob = 0.7
        # Conflicting signals -> hedge
        elif uncertainty > 0.4 and abs(belief_shift) > 0.2:
            baseline_opt = Optionality.HEDGE
            baseline_prob = 0.6
        # Clear signal -> act
        else:
            baseline_opt = Optionality.NOTHING
            baseline_prob = 0.5
        
        # Participant adjustments
        if participant_type == ParticipantType.BANK and belief_shift < 0:
            baseline_opt = Optionality.HEDGE
            baseline_prob = 0.8
        
        confidence = ConfidenceLevel.HIGH if baseline_prob > 0.6 else ConfidenceLevel.MEDIUM
        probability = BehaviorProbability(
            likelihood=min(1.0, baseline_prob),
            intensity=uncertainty,
            confidence=confidence
        )
        
        return baseline_opt, probability
    
    def _identify_contradictions(
        self, risk_posture: RiskPosture,
        liquidity_posture: LiquidityPosture,
        exposure_intent: ExposureIntent
    ) -> List[str]:
        """Identify realistic contradictions in behavior."""
        contradictions = []
        
        # Want to increase exposure but reduce liquidity
        if (exposure_intent == ExposureIntent.INCREASE_EXPOSURE and
            liquidity_posture == LiquidityPosture.REDUCE_LIQUIDITY):
            contradictions.append("Increase exposure despite reduced liquidity")
        
        # Want to increase risk but provide liquidity
        if (risk_posture == RiskPosture.INCREASE_RISK and
            liquidity_posture == LiquidityPosture.PROVIDE_LIQUIDITY):
            contradictions.append("Increase risk while providing liquidity")
        
        return contradictions
    
    def _generate_reasoning(
        self, expectation: ParticipantExpectation,
        risk_posture: RiskPosture, liquidity_posture: LiquidityPosture,
        exposure_intent: ExposureIntent
    ) -> str:
        """Generate explanation for behavior profile."""
        
        direction = "bullish" if expectation.belief_shift > 0 else "bearish" if expectation.belief_shift < 0 else "neutral"
        uncertainty_level = "high" if expectation.uncertainty_level > 0.6 else "moderate" if expectation.uncertainty_level > 0.3 else "low"
        
        return f"{expectation.participant_type.value.title()} sees {direction} signal with {uncertainty_level} uncertainty, " \
               f"adopting {risk_posture.value} risk and {liquidity_posture.value} liquidity postures"
    
    def _calculate_overall_confidence(
        self, expectation: ParticipantExpectation
    ) -> ConfidenceLevel:
        """Calculate overall confidence in behavior profile."""
        if expectation.belief_shift_confidence == ConfidenceLevel.HIGH:
            return ConfidenceLevel.HIGH
        elif expectation.belief_shift_confidence == ConfidenceLevel.MEDIUM:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _determine_fallbacks(
        self, expectation: ParticipantExpectation,
        constraints: ParticipantConstraints
    ) -> List[tuple]:
        """Determine fallback behaviors if primary doesn't execute."""
        fallbacks = []
        
        # If high uncertainty, might fallback to wait
        if expectation.uncertainty_level > 0.7:
            fallbacks.append(("Wait for clarity", 0.6))
        
        # If capital constrained, might fallback to reduce exposure
        if constraints.capital_available < 0.3:
            fallbacks.append(("Reduce exposure", 0.5))
        
        return fallbacks


def create_behavior_translator() -> BehaviorTranslator:
    """Factory function for translator."""
    return BehaviorTranslator()


if __name__ == "__main__":
    # Test behavior translation
    from participant_cognition.participant_models import create_bank_participant
    from news_model.parser import NewsEventParser
    from datetime import datetime
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Central bank signals hawkish policy stance."
    )
    
    bank = create_bank_participant()
    expectation = bank.interpret(event)
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced",
        capital_available=0.7,
        leverage_limit=1.5
    )
    
    translator = create_behavior_translator()
    behavior = translator.translate(expectation, constraints)
    
    print("="*70)
    print("PHASE 3: EXPECTATION -> BEHAVIOR TRANSLATION - DEMO")
    print("="*70)
    print(f"\nExpectation: {expectation.get_summary()}")
    print(f"\nConstraints: {constraints.get_summary()}")
    print(f"\nBehavior Profile: {behavior.get_summary()}")
    print(f"\nDominant Behaviors: {behavior.get_dominant_behaviors()}")
