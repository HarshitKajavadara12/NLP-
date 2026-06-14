"""
Phase 5: Market Reality Validation (Research Core)

This module validates whether cognitive models predict actual market behavior.
NOT for trading, signal generation, or execution.
This is scientific truth-verification.

Key exports:
- NewsUnderstanding: Parsed news from Phase 1
- ParticipantExpectation: Interpretation from Phase 2
- PredictedMarketState: Prediction from Phase 4
- MarketReality: Observed market data
- ValidationRecord: Complete validation of one news event
- RealityValidator: Core validation engine
- CredibilityDataset: Track model credibility over time
"""

from .market_reality import (
    # Enums
    NewsEventType,
    DirectionType,
    RegimeType,
    ValidityScore,
    
    # Input structures (from Phases 1-4)
    NewsUnderstanding,
    ParticipantExpectation,
    PredictedMarketState,
    
    # Market reality
    OHLCV,
    MarketSnapshot,
    MarketReality,
    
    # Validation scoring
    DirectionalValidity,
    VolatilityValidity,
    TimingValidity,
    ParticipationValidity,
    RegimeValidity,
    ValidationRecord,
    
    # Credibility tracking
    ModelCredibility,
    CredibilityDataset,
    
    # Failure analysis
    FailurePattern,
    FailureAnalysis,
    
    # Core validator
    RealityValidator,
)

__all__ = [
    "NewsEventType",
    "DirectionType",
    "RegimeType",
    "ValidityScore",
    "NewsUnderstanding",
    "ParticipantExpectation",
    "PredictedMarketState",
    "OHLCV",
    "MarketSnapshot",
    "MarketReality",
    "DirectionalValidity",
    "VolatilityValidity",
    "TimingValidity",
    "ParticipationValidity",
    "RegimeValidity",
    "ValidationRecord",
    "ModelCredibility",
    "CredibilityDataset",
    "FailurePattern",
    "FailureAnalysis",
    "RealityValidator",
]
