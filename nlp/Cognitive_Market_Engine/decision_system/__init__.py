"""
Phase 4: Decision System — Multi-Factor Signal Synthesis

This module is the BRAIN of the Cognitive Market Engine.
It synthesizes ALL upstream analysis into unified, risk-aware trading decisions.

Input Sources:
1. NLP Analysis (Phase 1) → Linguistic shock, sentiment, entities
2. Cognitive Interpretations (Phase 2) → 5 participant perspectives  
3. Behavior Translation (Phase 3) → Behavioral postures
4. Market Impact (Phase 4a) → 6-dimensional impact assessment
5. Scenario Engine → Probability-weighted outcome distribution
6. Hidden Truth → Cross-source verification, omission alerts
7. Reality Validation → Model credibility scores

Decision Framework:
- Multi-factor scoring (weighted combination of all inputs)
- Portfolio awareness (existing positions, correlation, sizing)
- Regime adaptation (different rules for different market states)
- Risk gates (hard limits that override signals)
- Confidence calibration (how sure are we?)

Output: DecisionPacket with action, sizing, confidence, reasoning
"""

from .decision_engine import (
    DecisionEngine,
    DecisionPacket,
    DecisionAction,
    RiskGate,
    PortfolioState,
)

__all__ = [
    'DecisionEngine',
    'DecisionPacket',
    'DecisionAction',
    'RiskGate',
    'PortfolioState',
]