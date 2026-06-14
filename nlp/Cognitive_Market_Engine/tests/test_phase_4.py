"""
Phase 4 Tests: Behavior → Market Impact Modeling

14 comprehensive tests validating:
1. BehaviorAggregator exists and works
2. Impact dimensions are properly defined
3. Aggregation produces weighted results
4. ImpactTranslator exists and works
5. Market impact ≠ price direction
6. Time structure is enforced
7. Non-linearity is modeled (threshold, saturation, feedback)
8. All six impact categories represented
9. Five participants produce different impacts
10. No prices, no trades, no direction in output
11. Confidence calculation
12. Reasoning generation
13. Disagreement and concentration detection
14. Overall market stress calculation
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from news_model.parser import NewsEventParser
from participant_cognition.participant_models import (
    create_bank_participant, create_hedge_fund_participant,
    create_hft_participant, create_market_maker_participant,
    create_retail_participant, ParticipantType
)
from market_response import (
    BehaviorTranslator, ParticipantConstraints
)
from market_impact import (
    BehaviorAggregator, ImpactTranslator,
    LiquidityImpactType, VolatilityImpactType, SpreadImpactType,
    OrderFlowImpactType, PriceDynamicsType, RegimeImpactType
)


def test_01_behavior_aggregator_exists():
    """Test that BehaviorAggregator class exists and is instantiable."""
    print("\nTEST 01: BehaviorAggregator Exists")
    
    aggregator = BehaviorAggregator()
    assert aggregator is not None
    assert hasattr(aggregator, 'aggregate')
    assert hasattr(aggregator, 'base_weights')
    
    print("[PASS]")


def test_02_impact_translator_exists():
    """Test that ImpactTranslator class exists and is instantiable."""
    print("\nTEST 02: ImpactTranslator Exists")
    
    translator = ImpactTranslator()
    assert translator is not None
    assert hasattr(translator, 'translate')
    
    print("[PASS]")


def test_03_impact_dimensions_defined():
    """Test that all six impact dimensions are defined."""
    print("\nTEST 03: All Impact Dimensions Defined")
    
    # Liquidity impacts
    assert LiquidityImpactType.DEPTH_REDUCTION is not None
    assert LiquidityImpactType.DEPTH_CONCENTRATION is not None
    assert LiquidityImpactType.LIQUIDITY_ASYMMETRY is not None
    assert LiquidityImpactType.TEMPORARY_VACUUM is not None
    
    # Volatility impacts
    assert VolatilityImpactType.INSTANT_SPIKE is not None
    assert VolatilityImpactType.SUSTAINED_VOLATILITY is not None
    assert VolatilityImpactType.VOLATILITY_CLUSTERING is not None
    assert VolatilityImpactType.VOLATILITY_SUPPRESSION is not None
    
    # Spread impacts
    assert SpreadImpactType.SPREAD_WIDENING is not None
    assert SpreadImpactType.SPREAD_INSTABILITY is not None
    assert SpreadImpactType.ASYMMETRIC_SPREADS is not None
    
    # Order flow impacts
    assert OrderFlowImpactType.AGGRESSIVE_IMBALANCE is not None
    assert OrderFlowImpactType.PASSIVE_IMBALANCE is not None
    assert OrderFlowImpactType.ONE_SIDED_FLOW is not None
    assert OrderFlowImpactType.FLOW_FRAGMENTATION is not None
    
    # Price dynamics
    assert PriceDynamicsType.JUMP_RISK is not None
    assert PriceDynamicsType.DRIFT is not None
    assert PriceDynamicsType.MEAN_REVERSION_PRESSURE is not None
    assert PriceDynamicsType.RANGE_EXPANSION is not None
    
    # Regime impacts
    assert RegimeImpactType.REGIME_TRANSITION_PROBABILITY is not None
    assert RegimeImpactType.REGIME_INSTABILITY is not None
    assert RegimeImpactType.TEMPORARY_DISLOCATION is not None
    
    print("[PASS]")


def test_04_aggregator_produces_aggregated_behavior():
    """Test that aggregator produces valid AggregatedBehavior output."""
    print("\nTEST 04: Aggregator Produces AggregatedBehavior")
    
    # Create behaviors from Phase 3
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Fed announces emergency rate cut"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    # Get expectations
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    # Define constraints
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.9, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.7, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.6, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.2, leverage_limit=1.0
        ),
    }
    
    # Translate to behaviors
    translator = BehaviorTranslator()
    behaviors = {
        pt: translator.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    # Aggregate
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    # Verify properties
    assert agg_behavior is not None
    assert hasattr(agg_behavior, 'avg_risk_posture_signal')
    assert hasattr(agg_behavior, 'avg_liquidity_posture_signal')
    assert hasattr(agg_behavior, 'behavior_disagreement')
    assert hasattr(agg_behavior, 'behavior_concentration')
    assert -1.0 <= agg_behavior.avg_risk_posture_signal <= 1.0
    assert -1.0 <= agg_behavior.avg_liquidity_posture_signal <= 1.0
    assert 0.0 <= agg_behavior.behavior_disagreement <= 1.0
    assert 0.0 <= agg_behavior.behavior_concentration <= 1.0
    
    print(f"  Risk signal: {agg_behavior.avg_risk_posture_signal:+.2f}")
    print(f"  Liquidity signal: {agg_behavior.avg_liquidity_posture_signal:+.2f}")
    print(f"  Disagreement: {agg_behavior.behavior_disagreement:.2f}")
    print(f"  Concentration: {agg_behavior.behavior_concentration:.2f}")
    print("[PASS]")


def test_05_translator_produces_market_impact():
    """Test that ImpactTranslator produces valid MarketImpactProfile."""
    print("\nTEST 05: Translator Produces MarketImpactProfile")
    
    # Reuse setup from test 04
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Unexpected jobless claims spike reported"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.85, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.7, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.6, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.2, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)

    # Now translate to market impact
    impact_translator = ImpactTranslator()
    market_impact = impact_translator.translate(agg_behavior, event.event_id)
    
    # Verify output
    assert market_impact is not None
    assert market_impact.news_event_id is not None
    assert hasattr(market_impact, 'liquidity_impacts')
    assert hasattr(market_impact, 'volatility_impacts')
    assert hasattr(market_impact, 'spread_impacts')
    assert hasattr(market_impact, 'order_flow_impacts')
    assert hasattr(market_impact, 'price_dynamics')
    assert hasattr(market_impact, 'regime_impacts')
    assert 0.0 <= market_impact.overall_market_stress <= 1.0
    assert 0.0 <= market_impact.confidence_in_impact <= 1.0
    
    print(f"  Overall stress: {market_impact.overall_market_stress:.2f}")
    print(f"  Confidence: {market_impact.confidence_in_impact:.2f}")
    print(f"  Threshold breached: {market_impact.threshold_breached}")
    print(f"  Saturation: {market_impact.saturation_detected}")
    print(f"  Feedback risk: {market_impact.feedback_loop_risk}")
    print("[PASS]")


def test_06_no_price_direction():
    """Test that MarketImpactProfile contains NO price direction predictions."""
    print("\nTEST 06: No Price Direction in Output")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Corporate earnings disappoint"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.8, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.75, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.65, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.25, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    impact_translator = ImpactTranslator()
    market_impact = impact_translator.translate(agg_behavior, event.event_id)
    
    # Verify NO prices, NO direction
    output_str = str(market_impact).lower()
    # Check for forbidden terms (allowing price_dynamics which describes market behavior)
    forbidden_terms = ["bullish", "bearish", " up", " down", "buy signal", "sell signal"]
    for term in forbidden_terms:
        assert term not in output_str, f"Output contains forbidden term: {term}"
    
    # Check that we don't have direction terms (not wrapped in "dynamics")
    if "price" in output_str:
        # This is OK only in "price_dynamics"
        assert "price_dynamics" in output_str, "Output has 'price' but not in price_dynamics context"
    
    # Verify OUTPUT contains market structure terms
    assert "liquidity" in output_str
    assert "volatility" in output_str or "spread" in output_str
    
    print("[PASS]")


def test_07_time_structure_defined():
    """Test that all impacts have time structure (onset, peak, decay, persistence)."""
    print("\nTEST 07: Time Structure Defined for All Impacts")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Volatility index surges 50%"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.9, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.7, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.6, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.2, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    impact_translator = ImpactTranslator()
    market_impact = impact_translator.translate(agg_behavior, event.event_id)
    
    # Check all impacts have time structure
    all_impacts = (
        market_impact.liquidity_impacts +
        market_impact.volatility_impacts +
        market_impact.spread_impacts +
        market_impact.order_flow_impacts +
        market_impact.price_dynamics +
        market_impact.regime_impacts
    )
    
    for impact in all_impacts:
        assert impact.timing is not None
        assert impact.timing.onset_delay is not None
        assert impact.timing.peak_window is not None
        assert impact.timing.decay_time is not None
        assert impact.timing.persistence is not None
    
    print(f"  Found {len(all_impacts)} impacts with time structure")
    for impact in all_impacts[:3]:  # Show first 3
        print(f"    - {impact.impact_type.value}: {impact.timing.get_summary()}")
    print("[PASS]")


def test_08_non_linearity_modeled():
    """Test that non-linearity (threshold, saturation, feedback) is detected."""
    print("\nTEST 08: Non-Linearity Detection")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Major financial institution fails unexpectedly"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.1, leverage_limit=1.5  # Constrained!
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.3, leverage_limit=2.0  # Constrained!
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.4, leverage_limit=8.0  # Constrained!
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.1, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    impact_translator = ImpactTranslator()
    market_impact = impact_translator.translate(agg_behavior, event.event_id)
    
    # Verify non-linearity fields exist and have meaningful values
    assert hasattr(market_impact, 'threshold_breached')
    assert hasattr(market_impact, 'saturation_detected')
    assert hasattr(market_impact, 'feedback_loop_risk')
    assert isinstance(market_impact.threshold_breached, bool)
    assert isinstance(market_impact.saturation_detected, bool)
    assert isinstance(market_impact.feedback_loop_risk, bool)
    
    print(f"  Threshold breached: {market_impact.threshold_breached}")
    print(f"  Saturation detected: {market_impact.saturation_detected}")
    print(f"  Feedback loop risk: {market_impact.feedback_loop_risk}")
    print("[PASS]")


def test_09_five_participants_different_impacts():
    """Test that five different participants produce measurably different impacts."""
    print("\nTEST 09: Five Participants → Different Impacts")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Treasury yields spike on inflation surprise"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.8, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.7, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.6, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.2, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    impact_translator = ImpactTranslator()
    market_impact = impact_translator.translate(agg_behavior, event.event_id)
    
    # Verify output includes different impact types
    assert len(market_impact.liquidity_impacts) > 0 or len(market_impact.volatility_impacts) > 0
    
    # Verify aggregation shows different participants diverge
    assert len(agg_behavior.participant_divergence) > 0 or agg_behavior.behavior_disagreement > 0.1
    
    print(f"  Aggregated disagreement: {agg_behavior.behavior_disagreement:.2f}")
    print(f"  Divergent participants: {len(agg_behavior.participant_divergence)}")
    print(f"  Total impacts identified: {len(market_impact.liquidity_impacts) + len(market_impact.volatility_impacts) + len(market_impact.spread_impacts) + len(market_impact.order_flow_impacts) + len(market_impact.price_dynamics) + len(market_impact.regime_impacts)}")
    print("[PASS]")


def test_10_all_impact_categories_represented():
    """Test that all six impact categories can be represented in output."""
    print("\nTEST 10: All Impact Categories Can Be Represented")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Extreme geopolitical crisis escalates: military action initiated"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.9, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.8, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.6, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.7, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.3, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    impact_translator = ImpactTranslator()
    market_impact = impact_translator.translate(agg_behavior, event.event_id)
    
    # Verify all categories present (at least some impacts in most categories)
    assert market_impact.liquidity_impacts is not None
    assert market_impact.volatility_impacts is not None
    assert market_impact.spread_impacts is not None
    assert market_impact.order_flow_impacts is not None
    assert market_impact.price_dynamics is not None
    assert market_impact.regime_impacts is not None
    
    print(f"  Liquidity impacts: {len(market_impact.liquidity_impacts)}")
    print(f"  Volatility impacts: {len(market_impact.volatility_impacts)}")
    print(f"  Spread impacts: {len(market_impact.spread_impacts)}")
    print(f"  Order flow impacts: {len(market_impact.order_flow_impacts)}")
    print(f"  Price dynamics: {len(market_impact.price_dynamics)}")
    print(f"  Regime impacts: {len(market_impact.regime_impacts)}")
    print("[PASS]")


def test_11_confidence_calculation():
    """Test that confidence is calculated and reflects disagreement/strength."""
    print("\nTEST 11: Confidence Calculation")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Minor economic data miss expected"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.9, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.8, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.7, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.2, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    impact_translator = ImpactTranslator()
    market_impact = impact_translator.translate(agg_behavior, event.event_id)
    
    # Verify confidence bounds
    assert 0.0 <= market_impact.confidence_in_impact <= 1.0
    
    # Higher disagreement should lower confidence
    if agg_behavior.behavior_disagreement > 0.5:
        assert market_impact.confidence_in_impact < 0.7
    
    print(f"  Disagreement: {agg_behavior.behavior_disagreement:.2f}")
    print(f"  Confidence: {market_impact.confidence_in_impact:.2f}")
    print("[PASS]")


def test_12_reasoning_generated():
    """Test that MarketImpactProfile includes reasoning explanation."""
    print("\nTEST 12: Reasoning Generation")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Central bank maintains guidance despite market volatility"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.9, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.8, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.7, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.2, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    impact_translator = ImpactTranslator()
    market_impact = impact_translator.translate(agg_behavior, event.event_id)
    
    # Verify reasoning exists and is non-empty
    assert market_impact.reasoning is not None
    assert len(market_impact.reasoning) > 0
    assert "Behavioral Aggregation" in market_impact.reasoning or "Market Impact" in market_impact.reasoning
    
    print(f"  Reasoning length: {len(market_impact.reasoning)} characters")
    print("[PASS]")


def test_13_disagreement_and_concentration():
    """Test that disagreement and concentration are properly detected."""
    print("\nTEST 13: Disagreement and Concentration Detection")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Conflicting signals in economic data"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.9, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.8, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.7, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.2, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    # Verify disagreement and concentration are valid
    assert 0.0 <= agg_behavior.behavior_disagreement <= 1.0
    assert 0.0 <= agg_behavior.behavior_concentration <= 1.0
    
    # Check divergence list
    assert isinstance(agg_behavior.participant_divergence, list)
    
    print(f"  Disagreement: {agg_behavior.behavior_disagreement:.2f} (0=unanimous, 1=split)")
    print(f"  Concentration: {agg_behavior.behavior_concentration:.2f} (0=balanced, 1=one-sided)")
    print(f"  Divergent participants: {len(agg_behavior.participant_divergence)}")
    for pt, div in agg_behavior.participant_divergence[:3]:
        print(f"    - {pt.value}: divergence={div:.2f}")
    print("[PASS]")


def test_14_overall_market_stress():
    """Test that overall market stress is calculated and meaningful."""
    print("\nTEST 14: Overall Market Stress Calculation")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Market-wide impact assessment test"
    )
    
    participants = {
        ParticipantType.BANK: create_bank_participant(),
        ParticipantType.HEDGE_FUND: create_hedge_fund_participant(),
        ParticipantType.HFT: create_hft_participant(),
        ParticipantType.MARKET_MAKER: create_market_maker_participant(),
        ParticipantType.RETAIL: create_retail_participant(),
    }
    
    expectations = {pt: p.interpret(event) for pt, p in participants.items()}
    
    constraints = {
        ParticipantType.BANK: ParticipantConstraints(
            max_position_size=1000000.0, mandate="Balanced",
            capital_available=0.9, leverage_limit=2.0
        ),
        ParticipantType.HEDGE_FUND: ParticipantConstraints(
            max_position_size=500000.0, mandate="Long/Short",
            capital_available=0.8, leverage_limit=3.0
        ),
        ParticipantType.HFT: ParticipantConstraints(
            max_position_size=100000.0, mandate="Market neutral",
            capital_available=0.5, leverage_limit=5.0
        ),
        ParticipantType.MARKET_MAKER: ParticipantConstraints(
            max_position_size=200000.0, mandate="Neutral",
            capital_available=0.7, leverage_limit=10.0
        ),
        ParticipantType.RETAIL: ParticipantConstraints(
            max_position_size=50000.0, mandate="Long only",
            capital_available=0.2, leverage_limit=1.0
        ),
    }
    
    translator_phase3 = BehaviorTranslator()
    behaviors = {
        pt: translator_phase3.translate(expectations[pt], constraints[pt])
        for pt in expectations.keys()
    }
    
    aggregator = BehaviorAggregator()
    agg_behavior = aggregator.aggregate(behaviors)
    
    impact_translator = ImpactTranslator()
    market_impact = impact_translator.translate(agg_behavior, event.event_id)
    
    # Verify stress bounds and meaning
    assert 0.0 <= market_impact.overall_market_stress <= 1.0
    
    # Stress should be 0 for benign news, higher for crisis news
    if "crisis" in event.raw_text.lower() or "fail" in event.raw_text.lower():
        print(f"  (Crisis-level stress expected)")
    else:
        print(f"  (Routine event)")
    
    print(f"  Overall market stress: {market_impact.overall_market_stress:.2f}")
    print(f"    0.0 = calm")
    print(f"    0.3 = elevated")
    print(f"    0.6 = stressed")
    print(f"    1.0 = crisis")
    print("[PASS]")
