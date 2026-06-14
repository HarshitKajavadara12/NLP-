"""
PHASE 2: PARTICIPANT COGNITIVE MODELS

This module provides the cognitive framework for market participants.

Each participant has an immutable 6-dimensional cognitive profile:
1. Time Horizon: How far ahead do they care?
2. Risk Tolerance: How much uncertainty do they accept?
3. Objectives: What do they optimize?
4. Information Priority: What information matters first?
5. Reaction Latency: How quickly do they respond?
6. Interpretation Bias: What's their cognitive bias?

These six dimensions completely define how a participant interprets news
and generates expectations about market behavior.

The Participant class transforms NewsEvent -> ParticipantExpectation,
proving that the SAME news produces DIFFERENT interpretations
based on cognitive profile.

NO prices or trading signals. This is mental modeling.
"""

from participant_cognition.participant_models import (
    # Enums
    ParticipantType,
    TimeHorizon,
    RiskTolerance,
    ObjectiveType,
    InformationPriority,
    InterpretationBias,
    
    # Dataclasses
    CognitiveProfile,
    ActionLikelihoods,
    ParticipantExpectation,
    Participant,
    
    # Canonical archetypes
    create_bank_participant,
    create_hedge_fund_participant,
    create_hft_participant,
    create_market_maker_participant,
    create_retail_participant,
)

__all__ = [
    "ParticipantType",
    "TimeHorizon",
    "RiskTolerance",
    "ObjectiveType",
    "InformationPriority",
    "InterpretationBias",
    "CognitiveProfile",
    "ActionLikelihoods",
    "ParticipantExpectation",
    "Participant",
    "create_bank_participant",
    "create_hedge_fund_participant",
    "create_hft_participant",
    "create_market_maker_participant",
    "create_retail_participant",
]
