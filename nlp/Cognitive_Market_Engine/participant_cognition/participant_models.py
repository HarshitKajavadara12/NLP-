"""
PHASE 2: PARTICIPANT COGNITIVE MODELS

A Participant is a decision-making agent with:
- Constraints (what they can/cannot do)
- Objectives (what they optimize)
- Interpretation rules (how they think)

That transforms a NewsEvent into ParticipantExpectations.

Same news -> Different expectations for different participants.
This is the CORE of cognitive market modeling.

Key principle: Participants see interpreted claims, not raw text.
No prices involved yet. This is mental modeling.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

from news_model.news_event import NewsEvent, ConfidenceLevel

# Import canonical types from shared (single source of truth)
from shared import ParticipantType, TimeHorizon, RiskTolerance


class ObjectiveType(str, Enum):
    """What a participant optimizes."""
    SPREAD_CAPTURE = "spread_capture"
    INVENTORY_STABILITY = "inventory_stability"
    BALANCE_SHEET_PROTECTION = "balance_sheet_protection"
    RISK_ADJUSTED_RETURN = "risk_adjusted_return"
    ASYMMETRIC_RETURN = "asymmetric_return"
    NARRATIVE_ALIGNMENT = "narrative_alignment"
    DIRECTIONAL_GAIN = "directional_gain"


class InformationPriority(str, Enum):
    """What information matters FIRST."""
    MACRO_POLICY = "macro_policy"
    LIQUIDITY_CONDITIONS = "liquidity_conditions"
    EARNINGS_GROWTH = "earnings_growth"
    VOLATILITY_REGIME = "volatility_regime"
    REGULATORY_LANGUAGE = "regulatory_language"
    HEADLINE_SENTIMENT = "headline_sentiment"


class InterpretationBias(str, Enum):
    """Built-in cognitive bias."""
    RISK_AVERSE = "risk_averse"
    TREND_CONFIRMATION = "trend_confirmation"
    MEAN_REVERSION = "mean_reversion"
    REGULATORY_FEAR = "regulatory_fear"
    OPPORTUNITY_SEEKING = "opportunity_seeking"
    LIQUIDITY_PRESERVATION = "liquidity_preservation"
    OVERREACTION = "overreaction"


@dataclass
class CognitiveProfile:
    """
    Immutable cognitive profile of a participant.
    
    These six dimensions completely define how a participant thinks.
    """
    
    # 1. Time Horizon: How far ahead do they care?
    time_horizon: TimeHorizon
    
    # 2. Risk Tolerance: How much uncertainty do they accept?
    risk_tolerance: RiskTolerance
    
    # 3. Objective Function: What do they optimize?
    objectives: List[ObjectiveType]
    
    # 4. Information Priority: What matters first?
    priority_information: InformationPriority
    
    # 5. Reaction Latency: How quickly do they respond?
    reaction_latency: TimeHorizon  # Same enum for consistency
    
    # 6. Interpretation Bias: What's their cognitive bias?
    interpretation_bias: InterpretationBias
    
    def get_summary(self) -> str:
        """Human-readable summary of cognitive profile."""
        objectives_str = ", ".join([o.value for o in self.objectives])
        return f"""
CognitiveProfile:
  Time Horizon: {self.time_horizon.value}
  Risk Tolerance: {self.risk_tolerance.value}
  Objectives: {objectives_str}
  Information Priority: {self.priority_information.value}
  Reaction Latency: {self.reaction_latency.value}
  Interpretation Bias: {self.interpretation_bias.value}
        """


@dataclass
class ActionLikelihoods:
    """Probability of different types of actions."""
    increase_exposure: float = 0.0      # 0.0-1.0
    decrease_exposure: float = 0.0
    widen_spreads: float = 0.0
    pull_liquidity: float = 0.0
    hold_position: float = 0.5
    increase_hedging: float = 0.0
    wait_for_clarity: float = 0.0
    panic_action: float = 0.0
    
    def __post_init__(self):
        """Normalize probabilities to sum to 1.0."""
        total = (self.increase_exposure + self.decrease_exposure +
                self.widen_spreads + self.pull_liquidity +
                self.hold_position + self.increase_hedging +
                self.wait_for_clarity + self.panic_action)
        
        if total > 0:
            self.increase_exposure /= total
            self.decrease_exposure /= total
            self.widen_spreads /= total
            self.pull_liquidity /= total
            self.hold_position /= total
            self.increase_hedging /= total
            self.wait_for_clarity /= total
            self.panic_action /= total


@dataclass
class ParticipantExpectation:
    """
    Output of participant interpretation.
    
    What a participant expects to happen after news,
    based on their cognitive profile.
    
    NO prices or trading signals.
    This is mental modeling.
    """
    
    participant_type: ParticipantType
    news_event_id: str
    timestamp: datetime
    
    # Core expectations
    belief_shift: float  # -1.0 (bearish) to +1.0 (bullish)
    belief_shift_confidence: ConfidenceLevel
    
    # Uncertainty management
    uncertainty_level: float  # 0.0 (clear) to 1.0 (very unclear)
    
    # Urgency of response
    urgency: float  # 0.0 (no rush) to 1.0 (immediate action)
    
    # Time horizon effect
    short_term_expectation: float  # What happens now?
    long_term_expectation: float   # What happens over time?
    
    # Narrative alignment
    narrative_alignment: float  # -1.0 (contradicts) to +1.0 (reinforces)
    
    # Action likelihoods
    action_likelihoods: ActionLikelihoods = field(default_factory=ActionLikelihoods)
    
    # Mental reasoning
    reasoning: str = ""  # Why they think this way
    
    # What they're looking for next
    next_catalysts: List[str] = field(default_factory=list)
    
    def get_summary(self) -> str:
        """Human-readable summary of expectation."""
        return f"""
ParticipantExpectation ({self.participant_type.value}):
  Belief Shift: {self.belief_shift:+.2f} (confidence: {self.belief_shift_confidence.value})
  Uncertainty Level: {self.uncertainty_level:.2f}
  Urgency: {self.urgency:.2f}
  Short-term: {self.short_term_expectation:+.2f}
  Long-term: {self.long_term_expectation:+.2f}
  Narrative Alignment: {self.narrative_alignment:+.2f}
  Reasoning: {self.reasoning}
        """


@dataclass
class Participant:
    """
    A market participant with a cognitive profile.
    
    Transforms NewsEvent -> ParticipantExpectation through
    their cognitive framework.
    """
    
    participant_type: ParticipantType
    cognitive_profile: CognitiveProfile
    name: str = ""
    
    def __post_init__(self):
        """Set default name if not provided."""
        if not self.name:
            self.name = f"{self.participant_type.value.title()} Participant"
    
    def interpret(self, news_event: NewsEvent) -> ParticipantExpectation:
        """
        Transform a NewsEvent into expectations based on cognitive profile.
        
        This is the CORE of Phase 2.
        Same news + Different cognitive profiles = Different expectations.
        """
        
        # Step 1: Extract what they care about
        relevant_claims = self._filter_relevant_claims(news_event)
        
        # Step 2: Apply interpretation bias
        interpreted_meaning = self._apply_bias(relevant_claims, news_event)
        
        # Step 3: Calculate belief shift
        belief_shift = self._calculate_belief_shift(interpreted_meaning, news_event)
        
        # Step 4: Assess uncertainty they tolerate
        uncertainty = self._assess_uncertainty(news_event)
        
        # Step 5: Determine urgency
        urgency = self._determine_urgency(news_event)
        
        # Step 6: Project expectations
        short_term = self._project_short_term(belief_shift, urgency)
        long_term = self._project_long_term(belief_shift, news_event)
        
        # Step 7: Calculate action likelihoods
        actions = self._calculate_actions(belief_shift, urgency, uncertainty)
        
        # Step 8: Narrative alignment
        narrative_alignment = self._calculate_narrative_alignment(news_event)
        
        # Create expectation
        expectation = ParticipantExpectation(
            participant_type=self.participant_type,
            news_event_id=news_event.event_id,
            timestamp=datetime.now(),
            belief_shift=belief_shift,
            belief_shift_confidence=self._confidence_from_belief(belief_shift),
            uncertainty_level=uncertainty,
            urgency=urgency,
            short_term_expectation=short_term,
            long_term_expectation=long_term,
            action_likelihoods=actions,
            narrative_alignment=narrative_alignment,
            reasoning=self._generate_reasoning(belief_shift, uncertainty)
        )
        
        return expectation
    
    def _filter_relevant_claims(self, news_event: NewsEvent) -> List[str]:
        """Filter to claims relevant to this participant's priority."""
        relevant = []
        
        priority = self.cognitive_profile.priority_information
        
        # Filter based on what they care about
        for claim in news_event.semantic_claims:
            # Bank cares about policy and regulation
            if (self.participant_type == ParticipantType.BANK and 
                priority == InformationPriority.REGULATORY_LANGUAGE):
                relevant.append(claim.action)
            
            # HFT cares about volatility and surprise
            elif (self.participant_type == ParticipantType.HFT):
                if news_event.ambiguity_score > 0.5:
                    relevant.append(claim.action)
            
            # Hedge fund cares about narrative shifts
            elif (self.participant_type == ParticipantType.HEDGE_FUND):
                if len(news_event.narrative_types) > 0:
                    relevant.append(claim.action)
            
            # Market maker cares about liquidity implications
            elif (self.participant_type == ParticipantType.MARKET_MAKER):
                if claim.confidence == ConfidenceLevel.HIGH:
                    relevant.append(claim.action)
            
            # Retail cares about headlines
            elif (self.participant_type == ParticipantType.RETAIL):
                relevant.append(claim.action)
        
        return relevant if relevant else ["no relevant claims"]
    
    def _apply_bias(self, claims: List[str], news_event: NewsEvent) -> Dict:
        """Apply interpretation bias to claims."""
        bias = self.cognitive_profile.interpretation_bias
        
        result = {
            "bias": bias.value,
            "intensity": 0.5
        }
        
        # Risk-averse bias: interpret negative implications strongly
        if bias == InterpretationBias.RISK_AVERSE:
            result["intensity"] = 0.8
            result["direction"] = "bearish"
        
        # Trend-confirmation bias: confirm existing trend
        elif bias == InterpretationBias.TREND_CONFIRMATION:
            result["intensity"] = 0.7
        
        # Opportunity-seeking: find upside
        elif bias == InterpretationBias.OPPORTUNITY_SEEKING:
            result["intensity"] = 0.7
            result["direction"] = "bullish"
        
        # Mean-reversion: expect reversal
        elif bias == InterpretationBias.MEAN_REVERSION:
            result["intensity"] = 0.6
        
        return result
    
    def _calculate_belief_shift(self, interpreted: Dict, news_event: NewsEvent) -> float:
        """Calculate how much their belief shifts (-1.0 to +1.0)."""
        base_shift = 0.0
        
        # Start with ambiguity effect
        if news_event.ambiguity_score > 0.7:
            # High ambiguity reduces conviction
            base_shift = 0.0
        else:
            # Clearer news produces stronger shift
            base_shift = 0.3 if news_event.confidence_level == ConfidenceLevel.HIGH else 0.1
        
        # Apply bias modifier
        if "direction" in interpreted:
            if interpreted["direction"] == "bullish":
                base_shift = abs(base_shift)
            elif interpreted["direction"] == "bearish":
                base_shift = -abs(base_shift)
        
        # Risk tolerance dampens shift for risk-averse
        if self.cognitive_profile.risk_tolerance == RiskTolerance.ULTRA_LOW:
            base_shift *= 0.5
        
        return max(-1.0, min(1.0, base_shift * interpreted.get("intensity", 0.5)))
    
    def _assess_uncertainty(self, news_event: NewsEvent) -> float:
        """How much uncertainty do they tolerate?"""
        # HFT has ultra-low tolerance
        if self.participant_type == ParticipantType.HFT:
            return min(0.5, news_event.ambiguity_score)
        
        # Hedge fund has high tolerance
        elif self.participant_type == ParticipantType.HEDGE_FUND:
            return news_event.ambiguity_score * 1.2
        
        # Bank has low tolerance
        elif self.participant_type == ParticipantType.BANK:
            return news_event.ambiguity_score * 0.8
        
        # Market maker has controlled tolerance
        elif self.participant_type == ParticipantType.MARKET_MAKER:
            return news_event.ambiguity_score
        
        # Retail: emotional variable
        else:
            return news_event.ambiguity_score
    
    def _determine_urgency(self, news_event: NewsEvent) -> float:
        """How urgent is the response?"""
        urgency = 0.0
        
        # Temporal markers affect urgency
        for marker in news_event.temporal_markers:
            if marker.temporal_type.value == "now":
                urgency += 0.8
            elif marker.temporal_type.value == "conditional":
                urgency += 0.3
        
        # Contradiction creates urgency
        if news_event.contradicts_prior_news:
            urgency += 0.4
        
        # Time horizon affects responsiveness
        if self.cognitive_profile.time_horizon == TimeHorizon.MICROSECONDS:
            urgency = min(1.0, urgency + 0.7)
        elif self.cognitive_profile.time_horizon == TimeHorizon.YEARS:
            urgency = max(0.0, urgency - 0.5)
        
        return min(1.0, urgency)
    
    def _project_short_term(self, belief_shift: float, urgency: float) -> float:
        """What do they expect in short term?"""
        # HFT: quick reaction
        if self.participant_type == ParticipantType.HFT:
            return belief_shift * urgency
        
        # Others: belief drives short-term
        return belief_shift * 0.5
    
    def _project_long_term(self, belief_shift: float, news_event: NewsEvent) -> float:
        """What do they expect long-term?"""
        # Long-term usually dampens volatility response
        return belief_shift * 0.3 if news_event.ambiguity_score > 0.5 else belief_shift * 0.7
    
    def _calculate_actions(self, belief_shift: float, urgency: float, 
                          uncertainty: float) -> ActionLikelihoods:
        """What actions are they likely to take?"""
        actions = ActionLikelihoods()
        
        if self.participant_type == ParticipantType.BANK:
            # Banks reduce risk on bad news
            if belief_shift < -0.3:
                actions.increase_hedging = 0.5
                actions.decrease_exposure = 0.2
                actions.hold_position = 0.3
            elif belief_shift < 0:
                actions.increase_hedging = 0.2
                actions.hold_position = 0.8
            else:
                actions.hold_position = 0.9
                actions.increase_exposure = 0.1
        
        elif self.participant_type == ParticipantType.HEDGE_FUND:
            # Hedge funds position on asymmetry
            if belief_shift > 0.3:
                actions.increase_exposure = 0.6
                actions.hold_position = 0.4
            elif belief_shift < -0.3:
                actions.decrease_exposure = 0.5
                actions.hold_position = 0.5
            else:
                actions.wait_for_clarity = 0.5
                actions.hold_position = 0.5
        
        elif self.participant_type == ParticipantType.HFT:
            # HFTs capture volatility dynamically
            if urgency > 0.7:
                actions.widen_spreads = 0.4
                actions.pull_liquidity = 0.3
                actions.hold_position = 0.3
            elif uncertainty > 0.5:
                actions.widen_spreads = 0.5
                actions.hold_position = 0.5
            else:
                actions.hold_position = 1.0
        
        elif self.participant_type == ParticipantType.MARKET_MAKER:
            # Market makers manage inventory carefully
            if uncertainty > 0.6:
                actions.widen_spreads = 0.6
                actions.pull_liquidity = 0.2
                actions.hold_position = 0.2
            elif uncertainty > 0.4:
                actions.widen_spreads = 0.3
                actions.hold_position = 0.7
            else:
                actions.hold_position = 1.0
        
        else:  # Retail
            # Retail overreacts emotionally
            if belief_shift > 0.3:
                actions.increase_exposure = 0.8
                actions.hold_position = 0.2
            elif belief_shift < -0.3:
                actions.panic_action = 0.6
                actions.decrease_exposure = 0.4
            else:
                actions.wait_for_clarity = 0.6
                actions.hold_position = 0.4
        
        # Normalize
        actions.__post_init__()
        return actions
    
    def _calculate_narrative_alignment(self, news_event: NewsEvent) -> float:
        """Does this news align with their narrative?"""
        # For now, if contradicts prior, alignment is negative
        if news_event.contradicts_prior_news:
            return -0.5
        else:
            return 0.7
    
    def _confidence_from_belief(self, belief_shift: float) -> ConfidenceLevel:
        """Confidence level based on belief shift magnitude."""
        magnitude = abs(belief_shift)
        if magnitude > 0.6:
            return ConfidenceLevel.HIGH
        elif magnitude > 0.3:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_reasoning(self, belief_shift: float, uncertainty: float) -> str:
        """Generate explanation for expectation."""
        direction = "bullish" if belief_shift > 0 else "bearish" if belief_shift < 0 else "neutral"
        confidence = "high" if uncertainty < 0.3 else "medium" if uncertainty < 0.7 else "low"
        
        return f"{self.participant_type.value.title()} sees {direction} signal with {confidence} confidence"


# ============================================================================
# CANONICAL PARTICIPANT ARCHETYPES (Predefined)
# ============================================================================

def create_bank_participant() -> Participant:
    """Commercial/Investment bank cognitive profile."""
    profile = CognitiveProfile(
        time_horizon=TimeHorizon.MONTHS,
        risk_tolerance=RiskTolerance.LOW,
        objectives=[
            ObjectiveType.BALANCE_SHEET_PROTECTION,
            ObjectiveType.INVENTORY_STABILITY
        ],
        priority_information=InformationPriority.REGULATORY_LANGUAGE,
        reaction_latency=TimeHorizon.DAYS,
        interpretation_bias=InterpretationBias.RISK_AVERSE
    )
    return Participant(ParticipantType.BANK, profile, "Bank")


def create_hedge_fund_participant() -> Participant:
    """Hedge fund cognitive profile."""
    profile = CognitiveProfile(
        time_horizon=TimeHorizon.DAYS,
        risk_tolerance=RiskTolerance.ADAPTIVE,
        objectives=[
            ObjectiveType.ASYMMETRIC_RETURN,
            ObjectiveType.NARRATIVE_ALIGNMENT
        ],
        priority_information=InformationPriority.MACRO_POLICY,
        reaction_latency=TimeHorizon.HOURS,
        interpretation_bias=InterpretationBias.OPPORTUNITY_SEEKING
    )
    return Participant(ParticipantType.HEDGE_FUND, profile, "Hedge Fund")


def create_hft_participant() -> Participant:
    """HFT/Prop desk cognitive profile."""
    profile = CognitiveProfile(
        time_horizon=TimeHorizon.MILLISECONDS,
        risk_tolerance=RiskTolerance.ULTRA_LOW,
        objectives=[
            ObjectiveType.SPREAD_CAPTURE,
            ObjectiveType.INVENTORY_STABILITY
        ],
        priority_information=InformationPriority.VOLATILITY_REGIME,
        reaction_latency=TimeHorizon.MILLISECONDS,
        interpretation_bias=InterpretationBias.LIQUIDITY_PRESERVATION
    )
    return Participant(ParticipantType.HFT, profile, "HFT")


def create_market_maker_participant() -> Participant:
    """Market maker cognitive profile."""
    profile = CognitiveProfile(
        time_horizon=TimeHorizon.MINUTES,
        risk_tolerance=RiskTolerance.MEDIUM,
        objectives=[
            ObjectiveType.SPREAD_CAPTURE,
            ObjectiveType.INVENTORY_STABILITY
        ],
        priority_information=InformationPriority.LIQUIDITY_CONDITIONS,
        reaction_latency=TimeHorizon.SECONDS,
        interpretation_bias=InterpretationBias.LIQUIDITY_PRESERVATION
    )
    return Participant(ParticipantType.MARKET_MAKER, profile, "Market Maker")


def create_retail_participant() -> Participant:
    """Retail trader aggregate cognitive profile."""
    profile = CognitiveProfile(
        time_horizon=TimeHorizon.WEEKS,
        risk_tolerance=RiskTolerance.HIGH,
        objectives=[
            ObjectiveType.DIRECTIONAL_GAIN,
            ObjectiveType.NARRATIVE_ALIGNMENT
        ],
        priority_information=InformationPriority.HEADLINE_SENTIMENT,
        reaction_latency=TimeHorizon.HOURS,
        interpretation_bias=InterpretationBias.OVERREACTION
    )
    return Participant(ParticipantType.RETAIL, profile, "Retail")


if __name__ == "__main__":
    # Test the participant models
    from news_model.parser import NewsEventParser
    
    parser = NewsEventParser()
    
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Federal Reserve signaled patience on rate cuts."
    )
    
    # Create all canonical participants
    participants = [
        create_bank_participant(),
        create_hedge_fund_participant(),
        create_hft_participant(),
        create_market_maker_participant(),
        create_retail_participant(),
    ]
    
    print("="*70)
    print("PHASE 2: PARTICIPANT COGNITIVE MODELS - DEMO")
    print("="*70)
    print(f"\nNews Event: {event.title}")
    print(f"Raw Text: {event.raw_text[:50]}...")
    
    # Each participant interprets the same news differently
    for participant in participants:
        print("\n" + "-"*70)
        print(f"\nParticipant: {participant.name}")
        print(participant.cognitive_profile.get_summary())
        
        expectation = participant.interpret(event)
        print(expectation.get_summary())
