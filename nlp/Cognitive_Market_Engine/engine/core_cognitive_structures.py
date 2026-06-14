"""
CORE COGNITIVE STRUCTURES

This module defines the atomic data structures for cognitive market simulation.
NOT sentiment. NOT opinion. Cognitive shock, belief vectors, and expectation states.

This is the foundation that makes the entire system unique.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from enum import Enum
from datetime import datetime
import json

# Import canonical types from shared (single source of truth)
from shared import ParticipantType


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================


class TemporalFocus(Enum):
    """What timeframe does this news impact?"""
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"
    AMBIGUOUS = "ambiguous"


class NarrativeShift(Enum):
    """How much did the narrative change?"""
    NONE = "none"
    WEAK = "weak"
    STRONG = "strong"
    REGIME_CHANGE = "regime_change"


class LatencyClass(Enum):
    """Participant reaction time characteristic"""
    INSTANT = "instant"  # HFT: microseconds
    FAST = "fast"  # Minutes (HFT, retail FOMO)
    MEDIUM = "medium"  # 5-30 minutes (hedge funds)
    SLOW = "slow"  # Hours (banks, large positions)
    VERY_SLOW = "very_slow"  # Days (structural)


class CapitalScale(Enum):
    """Size of participant"""
    RETAIL = "retail"  # < $1M
    INSTITUTIONAL = "institutional"  # $1M - $1B
    MEGA = "mega"  # > $1B


# ============================================================================
# 1.1 LINGUISTIC SHOCK VECTOR (LSV)
# ============================================================================

@dataclass
class LinguisticShockVector:
    """
    What changed in language space?
    
    This replaces sentiment analysis.
    It captures structural properties of the news itself.
    
    Range: [0,1] for all metrics
    """
    
    surprise_level: float  # How unexpected was this?
    ambiguity_level: float  # How uncertain is the statement?
    certainty_level: float  # How definite/confident?
    authority_strength: float  # How credible is the source?
    novelty_score: float  # How new is this information?
    
    temporal_focus: TemporalFocus  # Past/Present/Future
    narrative_shift: NarrativeShift  # How much did story change?
    
    # Domain specificity
    is_macro: bool  # Affects entire market?
    is_asset_specific: bool  # Affects specific asset?
    
    # Metadata
    source_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    raw_text_preview: str = ""  # First 200 chars
    
    def to_dict(self) -> dict:
        return {
            "surprise_level": self.surprise_level,
            "ambiguity_level": self.ambiguity_level,
            "certainty_level": self.certainty_level,
            "authority_strength": self.authority_strength,
            "novelty_score": self.novelty_score,
            "temporal_focus": self.temporal_focus.value,
            "narrative_shift": self.narrative_shift.value,
            "is_macro": self.is_macro,
            "is_asset_specific": self.is_asset_specific,
        }
    
    def __str__(self) -> str:
        return (
            f"LSV(surprise={self.surprise_level:.2f}, "
            f"ambiguity={self.ambiguity_level:.2f}, "
            f"authority={self.authority_strength:.2f}, "
            f"novelty={self.novelty_score:.2f}, "
            f"shift={self.narrative_shift.value})"
        )


# ============================================================================
# 1.2 COGNITIVE STATE (PER PARTICIPANT)
# ============================================================================

@dataclass
class CognitiveState:
    """
    The internal mental/computational state of a participant after observing news.
    
    This is NOT sentiment. This is belief + expectation shift.
    """
    
    # Core cognitive metrics [0,1]
    belief_shift: float  # How much did my belief change?
    risk_perception: float  # How dangerous do I think this is?
    confidence: float  # How confident in my interpretation?
    urgency: float  # How soon do I need to act?
    uncertainty: float  # How much don't I know?
    
    # Action orientation (NOT action itself)
    action_bias: float  # Tendency to act (0=passive, 1=aggressive)
    
    # Information processing
    information_latency: float  # How long to fully process? (seconds)
    
    # Credibility of source
    source_credibility: float  # Do I believe this source?
    
    # Meta
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_strong_signal(self, threshold: float = 0.7) -> bool:
        """Is this a strong cognitive state?"""
        return self.belief_shift > threshold or self.uncertainty > threshold
    
    def to_dict(self) -> dict:
        return {
            "belief_shift": self.belief_shift,
            "risk_perception": self.risk_perception,
            "confidence": self.confidence,
            "urgency": self.urgency,
            "uncertainty": self.uncertainty,
            "action_bias": self.action_bias,
            "information_latency": self.information_latency,
            "source_credibility": self.source_credibility,
        }


# ============================================================================
# 1.3 EXPECTATION VECTOR
# ============================================================================

@dataclass
class ExpectationVector:
    """
    What does this participant expect the market to do?
    
    Notably: direction_bias is LOW weight. We care more about structure.
    """
    
    # Market structure expectations
    volatility_expectation: float  # Vol spike magnitude [0,1]
    liquidity_expectation: float  # How much liquidity available? [0,1]
    spread_expectation: float  # Expected spread widening [0,1]
    
    # Price + volume expectations
    direction_bias: float  # Weak directional signal [-1,1] (-1=down, 0=neutral, 1=up)
    volume_expectation: float  # Expected volume change [0,1]
    
    # Risk expectations
    tail_risk_awareness: float  # How worried about tail events? [0,1]
    correlation_expectation: float  # Cross-asset correlation [0,1]
    
    # Time expectations
    time_horizon: float  # Expected duration (minutes) [1,1440]
    peak_impact_time: float  # When will impact peak? (minutes) [0,time_horizon]
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "volatility_expectation": self.volatility_expectation,
            "liquidity_expectation": self.liquidity_expectation,
            "spread_expectation": self.spread_expectation,
            "direction_bias": self.direction_bias,
            "volume_expectation": self.volume_expectation,
            "tail_risk_awareness": self.tail_risk_awareness,
            "correlation_expectation": self.correlation_expectation,
            "time_horizon": self.time_horizon,
            "peak_impact_time": self.peak_impact_time,
        }


# ============================================================================
# 1.4 BEHAVIOR INTENTION (NOT ACTION)
# ============================================================================

@dataclass
class BehaviorIntention:
    """
    What is this participant INTENDING to do? (Not actual execution)
    
    Still no trades. Just behavioral vectors.
    """
    
    # Execution style
    aggressiveness: float  # [0,1]: passive to aggressive
    patience: float  # [0,1]: willing to wait vs immediate
    size_preference: float  # [0,1]: small retail to large institutional
    
    # Execution method
    execution_style: Literal["passive", "algorithmic", "aggressive", "predatory"]
    
    # Reaction timing
    reaction_delay_seconds: float  # How long before acting?
    is_mechanical: bool  # Is this decision automated?
    
    # Risk management
    uses_stops: bool
    stop_loss_distance: float  # How wide? [0,1] (normalized to vol)
    takes_profits: bool
    profit_target_distance: float
    
    # Meta
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "aggressiveness": self.aggressiveness,
            "patience": self.patience,
            "size_preference": self.size_preference,
            "execution_style": self.execution_style,
            "reaction_delay_seconds": self.reaction_delay_seconds,
            "is_mechanical": self.is_mechanical,
            "uses_stops": self.uses_stops,
            "stop_loss_distance": self.stop_loss_distance,
            "takes_profits": self.takes_profits,
            "profit_target_distance": self.profit_target_distance,
        }


# ============================================================================
# 1.5 PARTICIPANT PROFILE (STATIC)
# ============================================================================

@dataclass
class ParticipantProfile:
    """
    Static profile of a market participant type.
    
    This defines how they think, not what they do in any specific moment.
    """
    
    type: ParticipantType
    latency_class: LatencyClass
    capital_scale: CapitalScale
    
    # Regulatory/structural constraints
    max_position_pct: float  # Max % of AUM in one position
    leverage_limit: float  # Max leverage allowed
    
    # Historical + characteristic behavior
    historical_reliability: float  # [0,1]: How often are they right?
    overreaction_tendency: float  # [0,1]: Do they overreact?
    reversal_tendency: float  # [0,1]: Do they reverse quickly?
    
    # Information processing
    uses_sentiment: bool  # Do they care about sentiment?
    uses_technicals: bool  # Do they use charts?
    uses_fundamentals: bool  # Do they research?
    
    # Liquidity provision
    provides_liquidity: bool
    consumes_liquidity: bool
    
    # Description
    name: str = ""
    description: str = ""
    
    def __str__(self) -> str:
        return f"{self.type.value} ({self.latency_class.value}, {self.capital_scale.value})"


# ============================================================================
# 1.6 PARTICIPANT RESPONSE (ATOMIC UNIT)
# ============================================================================

@dataclass
class ParticipantResponse:
    """
    Complete state snapshot of a participant responding to a news event.
    
    This is the atomic unit of the cognitive system.
    """
    
    # Who is responding?
    profile: ParticipantProfile
    
    # News that triggered this response
    news_event_id: str
    linguistic_shock: LinguisticShockVector
    
    # How did they think?
    cognitive_state: CognitiveState
    expectation_vector: ExpectationVector
    behavior_intention: BehaviorIntention
    
    # Timing
    stimulus_time: datetime = field(default_factory=datetime.now)
    response_time: datetime = field(default_factory=datetime.now)
    
    @property
    def reaction_latency_seconds(self) -> float:
        """How long to respond to stimulus?"""
        return (self.response_time - self.stimulus_time).total_seconds()
    
    @property
    def will_act(self) -> bool:
        """Will this participant actually take action?"""
        return (
            self.cognitive_state.urgency > 0.5 and
            self.cognitive_state.action_bias > 0.3
        )
    
    @property
    def action_magnitude(self) -> float:
        """If they act, how aggressively? [0,1]"""
        return (
            self.behavior_intention.aggressiveness * 0.4 +
            self.cognitive_state.urgency * 0.3 +
            self.cognitive_state.belief_shift * 0.3
        )
    
    def to_dict(self) -> dict:
        return {
            "profile": {
                "type": self.profile.type.value,
                "latency_class": self.profile.latency_class.value,
                "capital_scale": self.profile.capital_scale.value,
            },
            "news_event_id": self.news_event_id,
            "linguistic_shock": self.linguistic_shock.to_dict(),
            "cognitive_state": self.cognitive_state.to_dict(),
            "expectation_vector": self.expectation_vector.to_dict(),
            "behavior_intention": self.behavior_intention.to_dict(),
            "will_act": self.will_act,
            "action_magnitude": self.action_magnitude,
            "reaction_latency_seconds": self.reaction_latency_seconds,
        }


# ============================================================================
# 1.7 NEWS EVENT (UPDATED FOR NEW SYSTEM)
# ============================================================================

@dataclass
class NewsEvent:
    """
    News event with linguistic properties but NO sentiment.
    """
    
    event_id: str
    timestamp: datetime
    source_id: str
    raw_text: str
    
    # What markets/assets affected?
    asset_scope: List[str]  # ["AAPL", "SPY"] etc
    macro_scope: List[str]  # ["rates", "inflation"] etc
    
    # Linguistic properties
    linguistic_shock: LinguisticShockVector
    
    # Who responded?
    participant_responses: Dict[str, ParticipantResponse] = field(default_factory=dict)
    
    def add_response(self, response: ParticipantResponse):
        """Register a participant response"""
        self.participant_responses[response.profile.type.value] = response
    
    def get_responses_by_type(self, participant_type: ParticipantType) -> List[ParticipantResponse]:
        """Get all responses of a specific type"""
        return [r for r in self.participant_responses.values() 
                if r.profile.type == participant_type]
    
    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source_id": self.source_id,
            "raw_text": self.raw_text[:200],  # Preview
            "asset_scope": self.asset_scope,
            "macro_scope": self.macro_scope,
            "linguistic_shock": self.linguistic_shock.to_dict(),
            "participant_responses": {
                k: v.to_dict() for k, v in self.participant_responses.items()
            }
        }


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "ParticipantType",
    "TemporalFocus",
    "NarrativeShift",
    "LatencyClass",
    "CapitalScale",
    "LinguisticShockVector",
    "CognitiveState",
    "ExpectationVector",
    "BehaviorIntention",
    "ParticipantProfile",
    "ParticipantResponse",
    "NewsEvent",
]
