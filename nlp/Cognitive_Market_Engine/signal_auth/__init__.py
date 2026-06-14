"""
Phase 6: Signal Authorization & Trust Weighting

Public exports for integration with other phases.
"""

from .signal_authorization import (
    # Enums
    SignalDirection,
    VolatilityImpact,
    SignalSource,
    SignalStatus,
    ReactionHorizon,
    
    # Input structures (from Phase 5)
    ValidationMetrics,
    NewsMetadata,
    PredictionFromPhase4,
    
    # Core structures
    TrustWeightHistory,
    ParticipantWeights,
    SignalRecord,
    NormalizedSignal,
    
    # Main engine
    SignalAuthorizer,
)

__all__ = [
    # Enums
    "SignalDirection",
    "VolatilityImpact",
    "SignalSource",
    "SignalStatus",
    "ReactionHorizon",
    
    # Input structures
    "ValidationMetrics",
    "NewsMetadata",
    "PredictionFromPhase4",
    
    # Core structures
    "TrustWeightHistory",
    "ParticipantWeights",
    "SignalRecord",
    "NormalizedSignal",
    
    # Main engine
    "SignalAuthorizer",
]
