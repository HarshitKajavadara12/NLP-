"""
Phase 4: Behavior → Market Impact Modeling

Maps aggregated behavioral profiles to observable market impacts.

Core Principle: Market Impact ≠ Direction

Market impact describes measurable changes in market microstructure:
- Liquidity impacts (depth, concentration, asymmetry, vacuum)
- Volatility impacts (instant spike, sustained, clustering, suppression)
- Spread impacts (widening, instability, asymmetry)
- Order flow impacts (aggressive, passive, one-sided, fragmented)
- Price dynamics (jump risk, drift, mean reversion, range expansion)
- Regime impacts (transition probability, instability, dislocation)

Direction (up/down) emerges from aggregated impacts, not predicted directly.

Key Features:
- Time structure (onset, peak, decay, persistence) for each impact
- Non-linearity (threshold breach, saturation, feedback loops)
- Weighted aggregation (speed, role, market share, timing overlap)
- No prices, no trades, no direction prediction
- Observable market state changes only
"""

from .market_impact_models import (
    LiquidityImpactType,
    VolatilityImpactType,
    SpreadImpactType,
    OrderFlowImpactType,
    PriceDynamicsType,
    RegimeImpactType,
    ImpactTiming,
    ImpactMeasurement,
    MarketImpactProfile,
    AggregatedBehavior,
    BehaviorAggregator,
    ImpactTranslator,
)

__all__ = [
    'LiquidityImpactType',
    'VolatilityImpactType',
    'SpreadImpactType',
    'OrderFlowImpactType',
    'PriceDynamicsType',
    'RegimeImpactType',
    'ImpactTiming',
    'ImpactMeasurement',
    'MarketImpactProfile',
    'AggregatedBehavior',
    'BehaviorAggregator',
    'ImpactTranslator',
]
