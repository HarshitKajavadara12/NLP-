"""
Phase 3: Expectation → Behavior Translation

This module translates participant expectations (from Phase 2) into behaviors.
The key insight: expectations don't become trades or prices, they become 
observable behavioral postures that the market can detect.

Core Principle: Behavior ≠ Trade
- Behavior describes participant postures (risk, liquidity, exposure, time, options)
- Behavior is probabilistic, not certain
- Behavior includes meaningful inaction
- No asset selection, no order sizing, no price predictions

Five Behavioral Dimensions:
1. Risk Posture: increase | decrease | neutral | hedge
2. Liquidity Posture: provide | reduce | withdraw | neutral
3. Exposure Intent: increase | decrease | maintain | convert
4. Time Urgency: immediate | same-day | delayed | passive
5. Optionality: hedge | wait | rebalance | convert | nothing

Constraints Layer:
Participants have hard limits that modify behavior:
- Capital constraints (max available to deploy)
- Mandate constraints (what they're allowed to do)
- Regulatory constraints (market rules)
- Inventory constraints (position limits)

These constraints mean the same expectation produces different behaviors
for different participants with different constraints.
"""

from .behavior_models import (
    RiskPosture,
    LiquidityPosture,
    ExposureIntent,
    TimeUrgency,
    Optionality,
    BehaviorProbability,
    BehaviorProfile,
    ParticipantConstraints,
    BehaviorTranslator,
)

__all__ = [
    'RiskPosture',
    'LiquidityPosture',
    'ExposureIntent',
    'TimeUrgency',
    'Optionality',
    'BehaviorProbability',
    'BehaviorProfile',
    'ParticipantConstraints',
    'BehaviorTranslator',
]
