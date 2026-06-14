"""
PHASE 1: NEWS EVENT DATA MODEL

A News Event is:
A time-stamped linguistic artifact that introduces new information, reinterpretation,
or confirmation about the world, capable of changing expectations of at least one
market participant.

This module defines the immutable structure of a news event.
Key principle: News ≠ Market Reaction. This layer only captures the news.

Rules (LOCKED):
1. News is linguistic, not market-related
2. Raw text is never altered
3. No sentiment, trading signals, or bullish/bearish labels
4. Ambiguity is preserved, never resolved
5. Can be re-interpreted by different models later
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
import uuid


class NarrativeType(str, Enum):
    """Types of narratives a news event can represent."""
    MACRO_POLICY = "macro_policy"
    LIQUIDITY = "liquidity"
    GROWTH = "growth"
    CREDIT_RISK = "credit_risk"
    GEOPOLITICAL = "geopolitical"
    TECHNOLOGICAL = "technological"
    CRISIS_SHOCK = "crisis_shock"
    NARRATIVE_REINFORCEMENT = "narrative_reinforcement"
    NARRATIVE_CONTRADICTION = "narrative_contradiction"


class TemporalType(str, Enum):
    """Temporal classification of claims."""
    NOW = "now"
    FUTURE = "future"
    CONDITIONAL = "conditional"
    PAST = "past"
    UNCERTAIN = "uncertain"


class ConfidenceLevel(str, Enum):
    """How assertive is the statement."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Sentence:
    """A single sentence extracted from raw text."""
    text: str
    index: int  # Position in document
    
    def __hash__(self):
        return hash((self.text, self.index))


@dataclass
class Clause:
    """A logical clause within the news text."""
    text: str
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object_: Optional[str] = None
    is_conditional: bool = False
    is_negated: bool = False
    parent_sentence_index: Optional[int] = None


@dataclass
class ModalityMarker:
    """Words that indicate certainty, uncertainty, or authority."""
    text: str
    marker_type: str  # "uncertainty", "certainty", "authority"
    strength: float  # 0.0 to 1.0


@dataclass
class TemporalMarker:
    """Indicates when something is claimed to happen."""
    temporal_type: TemporalType
    explicit_time: Optional[str] = None  # "next quarter", "today", etc.
    reference_text: Optional[str] = None  # The exact text that triggered this


@dataclass
class Actor:
    """An entity performing an action."""
    name: str
    category: str  # "central_bank", "company", "government", "source", etc.
    certainty: float = 1.0  # How certain is this actor identification?


@dataclass
class SemanticClaim:
    """A factual claim extracted from the news."""
    actor: Actor
    action: str  # "raise", "cut", "announce", "investigate", etc.
    object_: str  # "rates", "guidance", "earnings", etc.
    conditions: List[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    raw_source: str = ""  # The exact text this came from


@dataclass
class NewsEvent:
    """
    Complete representation of a single news event.
    
    IMMUTABLE CORE IDENTITY:
    - event_id: Unique, permanent, never reused
    - timestamp_utc: When news became public (not when price moved)
    - source: Publisher/platform
    - raw_text: Exact text, never altered
    
    LINGUISTIC DECOMPOSITION (stored, not assumed):
    - sentences: Ordered segmentation
    - clauses: Logical structure
    - modality_markers: Uncertainty, certainty, authority
    - temporal_markers: Now/future/conditional/past
    
    SEMANTIC MEANING (interpreted claims):
    - actors: Who is acting?
    - actions: What are they doing?
    - objects: What is affected?
    - conditions: Under what conditions?
    
    NARRATIVE CONTEXT:
    - narrative_types: Why this news exists
    
    UNCERTAINTY METRICS:
    - ambiguity_score: Language-based vagueness
    - confidence_level: Assertiveness
    - contradiction_flags: Conflicts with prior news
    """
    
    # ========== IMMUTABLE CORE IDENTITY ==========
    event_id: str
    timestamp_utc: datetime
    source: str
    raw_text: str
    
    # ========== LINGUISTIC DECOMPOSITION ==========
    sentences: List[Sentence] = field(default_factory=list)
    clauses: List[Clause] = field(default_factory=list)
    modality_markers: List[ModalityMarker] = field(default_factory=list)
    temporal_markers: List[TemporalMarker] = field(default_factory=list)
    
    # ========== SEMANTIC MEANING ==========
    actors: List[Actor] = field(default_factory=list)
    semantic_claims: List[SemanticClaim] = field(default_factory=list)
    
    # ========== NARRATIVE CONTEXT ==========
    narrative_types: List[NarrativeType] = field(default_factory=list)
    
    # ========== UNCERTAINTY METRICS ==========
    ambiguity_score: float = 0.5  # 0.0 = clear, 1.0 = completely vague
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    contradicts_prior_news: bool = False
    
    # ========== INTERPRETATION PLACEHOLDER ==========
    # These will be populated in Phase 2 by participant models
    # NOT in Phase 1
    participant_interpretations: Dict[str, Dict] = field(default_factory=dict)
    
    @staticmethod
    def create(timestamp_utc: datetime, source: str, raw_text: str) -> 'NewsEvent':
        """
        Factory method to create a new NewsEvent with generated ID.
        
        Args:
            timestamp_utc: When the news became public
            source: Publisher/platform name
            raw_text: The exact, unaltered raw news text
        
        Returns:
            NewsEvent: A new event with generated event_id
        """
        return NewsEvent(
            event_id=str(uuid.uuid4()),
            timestamp_utc=timestamp_utc,
            source=source,
            raw_text=raw_text
        )
    
    def add_sentence(self, text: str) -> Sentence:
        """Add a sentence to the linguistic decomposition."""
        sentence = Sentence(text=text, index=len(self.sentences))
        self.sentences.append(sentence)
        return sentence
    
    def add_clause(self, text: str, subject: str = None, predicate: str = None,
                   object_: str = None, conditional: bool = False, 
                   negated: bool = False, parent_sentence_idx: int = None) -> Clause:
        """Add a clause to the linguistic decomposition."""
        clause = Clause(
            text=text,
            subject=subject,
            predicate=predicate,
            object_=object_,
            is_conditional=conditional,
            is_negated=negated,
            parent_sentence_index=parent_sentence_idx
        )
        self.clauses.append(clause)
        return clause
    
    def add_modality_marker(self, text: str, marker_type: str, strength: float = 0.7):
        """Add a modality marker (uncertainty, certainty, authority)."""
        marker = ModalityMarker(text=text, marker_type=marker_type, strength=strength)
        self.modality_markers.append(marker)
        return marker
    
    def add_temporal_marker(self, temporal_type: TemporalType, 
                           explicit_time: str = None, reference_text: str = None):
        """Add a temporal marker."""
        marker = TemporalMarker(
            temporal_type=temporal_type,
            explicit_time=explicit_time,
            reference_text=reference_text
        )
        self.temporal_markers.append(marker)
        return marker
    
    def add_actor(self, name: str, category: str, certainty: float = 1.0) -> Actor:
        """Add an identified actor."""
        actor = Actor(name=name, category=category, certainty=certainty)
        self.actors.append(actor)
        return actor
    
    def add_semantic_claim(self, actor: Actor, action: str, object_: str,
                          conditions: List[str] = None,
                          confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
                          raw_source: str = "") -> SemanticClaim:
        """Add a semantic claim (factual claim extracted from news)."""
        claim = SemanticClaim(
            actor=actor,
            action=action,
            object_=object_,
            conditions=conditions or [],
            confidence=confidence,
            raw_source=raw_source
        )
        self.semantic_claims.append(claim)
        return claim
    
    def add_narrative_type(self, narrative_type: NarrativeType):
        """Tag this event with a narrative type."""
        if narrative_type not in self.narrative_types:
            self.narrative_types.append(narrative_type)
    
    def has_uncertainty(self) -> bool:
        """Does this event contain linguistic uncertainty markers?"""
        return any(m.marker_type == "uncertainty" for m in self.modality_markers)
    
    def has_contradiction(self) -> bool:
        """Is this event contradictory (contains contradictions or contradicts prior)?"""
        return self.contradicts_prior_news
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the event."""
        actors_str = ", ".join([a.name for a in self.actors]) if self.actors else "Unknown"
        narratives_str = ", ".join([n.value for n in self.narrative_types]) if self.narrative_types else "Unclassified"
        
        return f"""
NewsEvent {self.event_id}
  Time: {self.timestamp_utc}
  Source: {self.source}
  Actors: {actors_str}
  Narratives: {narratives_str}
  Ambiguity: {self.ambiguity_score:.2f}
  Confidence: {self.confidence_level.value}
  Contradicts Prior: {self.contradicts_prior_news}
  Raw Text: {self.raw_text[:100]}...
        """


if __name__ == "__main__":
    # Test: Create a sample news event
    event = NewsEvent.create(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Federal Reserve signaled patience on interest rate cuts."
    )
    
    # Add linguistic decomposition
    event.add_sentence("The Federal Reserve signaled patience on interest rate cuts.")
    event.add_clause(
        "Federal Reserve signaled patience",
        subject="Federal Reserve",
        predicate="signaled",
        object_="patience"
    )
    
    # Add modality markers
    event.add_modality_marker("signaled", "uncertainty", 0.6)
    
    # Add temporal markers
    event.add_temporal_marker(TemporalType.FUTURE, explicit_time="next quarter")
    
    # Add actor and claims
    fed = event.add_actor("Federal Reserve", "central_bank")
    event.add_semantic_claim(
        actor=fed,
        action="signal patience",
        object_="interest rates",
        confidence=ConfidenceLevel.MEDIUM,
        raw_source="exact quote text"
    )
    
    # Add narrative type
    event.add_narrative_type(NarrativeType.MACRO_POLICY)
    
    # Set uncertainty metrics
    event.ambiguity_score = 0.4
    event.confidence_level = ConfidenceLevel.MEDIUM
    
    print(event.get_summary())
    print(f"\nHas uncertainty: {event.has_uncertainty()}")
    print(f"Number of claims: {len(event.semantic_claims)}")
