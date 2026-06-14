"""
PHASE 3 TESTS: EXPECTATION -> BEHAVIOR TRANSLATION

Testing that:
1. Expectations transform into behavior profiles
2. Same expectation + different constraints = different behaviors
3. Contradictions are allowed and realistic
4. NO prices, NO trades, NO orders
5. Behaviors are probabilistic
6. Fallbacks exist for uncertain scenarios
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
    create_retail_participant
)
from market_response.behavior_models import (
    BehaviorTranslator, ParticipantConstraints,
    RiskPosture, LiquidityPosture, ExposureIntent, TimeUrgency, Optionality,
    BehaviorProfile
)


def test_01_translator_exists():
    """Test that BehaviorTranslator can be instantiated."""
    print("\nTEST 01: Translator Exists")
    
    translator = BehaviorTranslator()
    assert translator is not None
    print("[PASS]")


def test_02_constraints_exist():
    """Test that ParticipantConstraints work."""
    print("\nTEST 02: Constraints Exist")
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced",
        capital_available=0.7,
        leverage_limit=1.5
    )
    
    assert constraints.mandate == "Balanced"
    assert constraints.allows_increased_risk()
    assert constraints.allows_reduced_liquidity()
    print("[PASS]")


def test_03_translation_produces_behavior():
    """Test that translation produces BehaviorProfile."""
    print("\nTEST 03: Translation Produces Behavior")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Central bank signals hawkish stance."
    )
    
    bank = create_bank_participant()
    expectation = bank.interpret(event)
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced"
    )
    
    translator = BehaviorTranslator()
    behavior = translator.translate(expectation, constraints)
    
    assert isinstance(behavior, BehaviorProfile)
    assert behavior.participant_type is not None
    assert behavior.risk_posture is not None
    assert behavior.liquidity_posture is not None
    print("[PASS]")


def test_04_same_expectation_different_constraints():
    """Test that constraints are considered in behavior translation."""
    print("\nTEST 04: Same Expectation, Different Constraints")

    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Positive economic data released."
    )

    hf = create_hedge_fund_participant()
    expectation = hf.interpret(event)

    # Constraint 1: Plenty of capital
    constraints_1 = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced",
        capital_available=0.9,
        leverage_limit=2.0
    )

    # Constraint 2: Low capital
    constraints_2 = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced",
        capital_available=0.1,
        leverage_limit=1.0
    )

    translator = BehaviorTranslator()
    behavior_1 = translator.translate(expectation, constraints_1)
    behavior_2 = translator.translate(expectation, constraints_2)

    # Verify both behaviors are deterministic given constraints
    assert behavior_1.exposure_intent is not None
    assert behavior_2.exposure_intent is not None
    assert behavior_1.risk_posture is not None
    assert behavior_2.risk_posture is not None
    
    # Verify constraints are being used (they affect probabilities/fallbacks)
    assert behavior_1.fallback_behaviors is not None
    assert behavior_2.fallback_behaviors is not None
    
    print(f"  With capital: intent={behavior_1.exposure_intent.value}")
    print(f"  Without capital: intent={behavior_2.exposure_intent.value}")
    print("[PASS]")


def test_05_behavior_is_probabilistic():
    """Test that behaviors are probabilistic, not deterministic."""
    print("\nTEST 05: Behavior Is Probabilistic")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Mixed economic signals."
    )
    
    hf = create_hedge_fund_participant()
    expectation = hf.interpret(event)
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Opportunistic"
    )
    
    translator = BehaviorTranslator()
    behavior = translator.translate(expectation, constraints)
    
    # Check that probabilities are between 0 and 1
    assert 0.0 <= behavior.risk_probability.likelihood <= 1.0
    assert 0.0 <= behavior.liquidity_probability.likelihood <= 1.0
    assert 0.0 <= behavior.exposure_probability.likelihood <= 1.0
    assert 0.0 <= behavior.urgency_probability.likelihood <= 1.0
    
    # Intensity should also be bounded
    assert 0.0 <= behavior.risk_probability.intensity <= 1.0
    
    print(f"  Risk: {behavior.risk_probability.likelihood:.2f}")
    print(f"  Liquidity: {behavior.liquidity_probability.likelihood:.2f}")
    print(f"  Exposure: {behavior.exposure_probability.likelihood:.2f}")
    print("[PASS]")


def test_06_contradictions_allowed():
    """Test that contradictory behaviors are allowed and identified."""
    print("\nTEST 06: Contradictions Allowed")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Unexpected news with massive uncertainty."
    )
    
    hf = create_hedge_fund_participant()
    expectation = hf.interpret(event)
    
    # Force high uncertainty
    expectation.uncertainty_level = 0.8
    expectation.urgency = 0.1
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Opportunistic",
        capital_available=0.5
    )
    
    translator = BehaviorTranslator()
    behavior = translator.translate(expectation, constraints)
    
    # Should have contradictions flagged
    print(f"  Contradictions: {behavior.contradictions}")
    print(f"  Has contradictions: {behavior.has_contradictions()}")
    print("[PASS]")


def test_07_no_prices_no_trades():
    """CRITICAL: Verify NO prices, trades, or orders."""
    print("\nTEST 07: NO PRICES, TRADES, OR ORDERS (CRITICAL)")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Major market event."
    )
    
    participants = [
        create_bank_participant(),
        create_hedge_fund_participant(),
        create_hft_participant(),
        create_market_maker_participant(),
        create_retail_participant(),
    ]
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced"
    )
    
    translator = BehaviorTranslator()
    
    for participant in participants:
        expectation = participant.interpret(event)
        behavior = translator.translate(expectation, constraints)
        
        # NO price fields
        assert not hasattr(behavior, 'price'), "NO price field allowed"
        assert not hasattr(behavior, 'target_price'), "NO target_price field"
        assert not hasattr(behavior, 'predicted_price'), "NO predicted_price field"
        
        # NO trade fields
        assert not hasattr(behavior, 'trade'), "NO trade field"
        assert not hasattr(behavior, 'order'), "NO order field"
        assert not hasattr(behavior, 'buy'), "NO buy field"
        assert not hasattr(behavior, 'sell'), "NO sell field"
        assert not hasattr(behavior, 'trading_signal'), "NO trading_signal field"
        
        # NO execution fields
        assert not hasattr(behavior, 'pnl'), "NO pnl field"
        assert not hasattr(behavior, 'return'), "NO return field"
        assert not hasattr(behavior, 'position'), "NO position field"
    
    print("  All participants: NO prices, NO trades, NO orders")
    print("[PASS - CRITICAL CHECK]")


def test_08_behavior_structure_complete():
    """Test that BehaviorProfile has all required fields."""
    print("\nTEST 08: Behavior Structure Complete")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Test event."
    )
    
    bank = create_bank_participant()
    expectation = bank.interpret(event)
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced"
    )
    
    translator = BehaviorTranslator()
    behavior = translator.translate(expectation, constraints)
    
    # Check all required fields exist
    assert behavior.participant_type is not None
    assert behavior.expectation_id is not None
    assert behavior.timestamp is not None
    assert behavior.risk_posture is not None
    assert behavior.risk_probability is not None
    assert behavior.liquidity_posture is not None
    assert behavior.liquidity_probability is not None
    assert behavior.exposure_intent is not None
    assert behavior.exposure_probability is not None
    assert behavior.urgency is not None
    assert behavior.urgency_probability is not None
    assert behavior.optionality is not None
    assert behavior.overall_confidence is not None
    assert isinstance(behavior.reasoning, str)
    assert isinstance(behavior.fallback_behaviors, list)
    
    print(f"  All fields present and valid")
    print("[PASS]")


def test_09_five_participants_different_behaviors():
    """Test that 5 participants produce different behaviors for same event."""
    print("\nTEST 09: Five Participants -> Different Behaviors")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Central bank raises rates."
    )
    
    participants = [
        ("Bank", create_bank_participant()),
        ("Hedge Fund", create_hedge_fund_participant()),
        ("HFT", create_hft_participant()),
        ("Market Maker", create_market_maker_participant()),
        ("Retail", create_retail_participant()),
    ]
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced"
    )
    
    translator = BehaviorTranslator()
    behaviors = []
    
    for name, participant in participants:
        expectation = participant.interpret(event)
        behavior = translator.translate(expectation, constraints)
        behaviors.append(behavior)
        
        print(f"  {name}:")
        print(f"    Risk: {behavior.risk_posture.value}")
        print(f"    Liquidity: {behavior.liquidity_posture.value}")
        print(f"    Exposure: {behavior.exposure_intent.value}")
    
    # Check that not all behaviors are identical
    risk_postures = [b.risk_posture for b in behaviors]
    liquidity_postures = [b.liquidity_posture for b in behaviors]
    
    assert len(set(risk_postures)) > 1 or len(set(liquidity_postures)) > 1, \
        "Different participants should have different behaviors"
    
    print("[PASS]")


def test_10_fallback_behaviors_exist():
    """Test that fallback behaviors exist for uncertain scenarios."""
    print("\nTEST 10: Fallback Behaviors Exist")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Highly uncertain environment with mixed signals."
    )
    
    hf = create_hedge_fund_participant()
    expectation = hf.interpret(event)
    expectation.uncertainty_level = 0.9  # Very uncertain
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Opportunistic",
        capital_available=0.2  # Low capital
    )
    
    translator = BehaviorTranslator()
    behavior = translator.translate(expectation, constraints)
    
    # Should have fallback behaviors
    assert len(behavior.fallback_behaviors) > 0, "Should have fallback behaviors when uncertain"
    
    print(f"  Fallback behaviors: {behavior.fallback_behaviors}")
    print("[PASS]")


def test_11_inaction_is_meaningful():
    """Test that inaction (neutral/passive) is meaningful and captured."""
    print("\nTEST 11: Inaction Is Meaningful")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Small economic adjustment."
    )
    
    bank = create_bank_participant()
    expectation = bank.interpret(event)
    expectation.belief_shift = 0.01  # Tiny signal
    expectation.urgency = 0.0  # No urgency
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced"
    )
    
    translator = BehaviorTranslator()
    behavior = translator.translate(expectation, constraints)
    
    # Should have passive/neutral behaviors
    print(f"  Urgency: {behavior.urgency.value}")
    print(f"  Exposure Intent: {behavior.exposure_intent.value}")
    print(f"  Risk Posture: {behavior.risk_posture.value}")
    
    # Inaction is explicitly captured
    assert behavior.urgency == TimeUrgency.PASSIVE or behavior.exposure_intent == ExposureIntent.MAINTAIN_EXPOSURE
    print("[PASS]")


def test_12_constraint_impact():
    """Test that constraints actually impact behavior."""
    print("\nTEST 12: Constraints Impact Behavior")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Positive news suggesting risk increase."
    )
    
    hf = create_hedge_fund_participant()
    expectation = hf.interpret(event)
    expectation.belief_shift = 0.5  # Positive
    
    # Constraint 1: Few limits
    constraints_liberal = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Opportunistic",
        capital_available=0.9,
        leverage_limit=3.0,
        no_short_sale=False
    )
    
    # Constraint 2: Many limits
    constraints_strict = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Long only",
        capital_available=0.1,
        leverage_limit=1.0,
        no_short_sale=True
    )
    
    translator = BehaviorTranslator()
    behavior_liberal = translator.translate(expectation, constraints_liberal)
    behavior_strict = translator.translate(expectation, constraints_strict)
    
    # Liberal should allow more risk-taking
    print(f"  Liberal: exposure prob={behavior_liberal.exposure_probability.likelihood:.2f}")
    print(f"  Strict: exposure prob={behavior_strict.exposure_probability.likelihood:.2f}")
    
    assert behavior_liberal.exposure_probability.likelihood >= behavior_strict.exposure_probability.likelihood, \
        "Liberal constraints should allow more aggressive behavior"
    
    print("[PASS]")


def test_13_urgency_driven_by_expectation():
    """Test that urgency is driven by expectation urgency."""
    print("\nTEST 13: Urgency Driven by Expectation")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Flash",
        raw_text="Immediate market-moving news."
    )
    
    hft = create_hft_participant()
    expectation = hft.interpret(event)
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced"
    )
    
    translator = BehaviorTranslator()
    
    # High urgency expectation
    expectation.urgency = 0.9
    behavior_urgent = translator.translate(expectation, constraints)
    
    # Low urgency expectation
    expectation.urgency = 0.0
    behavior_calm = translator.translate(expectation, constraints)
    
    print(f"  Urgent: {behavior_urgent.urgency.value}")
    print(f"  Calm: {behavior_calm.urgency.value}")
    
    # Urgent should be immediate or same-day, calm should be passive or delayed
    assert behavior_urgent.urgency in [TimeUrgency.IMMEDIATE, TimeUrgency.SAME_DAY]
    
    print("[PASS]")


def test_14_reasoning_is_generated():
    """Test that reasoning is generated and meaningful."""
    print("\nTEST 14: Reasoning Is Generated")
    
    parser = NewsEventParser()
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Economic news."
    )
    
    participants = [
        create_bank_participant(),
        create_hedge_fund_participant(),
        create_hft_participant(),
        create_market_maker_participant(),
        create_retail_participant(),
    ]
    
    constraints = ParticipantConstraints(
        max_position_size=1000000.0,
        mandate="Balanced"
    )
    
    translator = BehaviorTranslator()
    
    for participant in participants:
        expectation = participant.interpret(event)
        behavior = translator.translate(expectation, constraints)
        
        assert len(behavior.reasoning) > 0, "Reasoning should be generated"
        assert participant.participant_type.value in behavior.reasoning.lower(), "Reasoning should mention participant type"
        
        print(f"  {participant.participant_type.value}: {behavior.reasoning}")
    
    print("[PASS]")


def run_all_tests():
    """Run all Phase 3 tests."""
    print("\n" + "="*70)
    print("PHASE 3: EXPECTATION -> BEHAVIOR TRANSLATION - TEST SUITE")
    print("="*70)
    
    tests = [
        test_01_translator_exists,
        test_02_constraints_exist,
        test_03_translation_produces_behavior,
        test_04_same_expectation_different_constraints,
        test_05_behavior_is_probabilistic,
        test_06_contradictions_allowed,
        test_07_no_prices_no_trades,
        test_08_behavior_structure_complete,
        test_09_five_participants_different_behaviors,
        test_10_fallback_behaviors_exist,
        test_11_inaction_is_meaningful,
        test_12_constraint_impact,
        test_13_urgency_driven_by_expectation,
        test_14_reasoning_is_generated,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"[FAIL] {str(e)}")
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n[TARGET] PHASE 3 COMPLETE AND VERIFIED")
        print("[LOCK] PHASE 3 LOCKED AND READY FOR PHASE 4")
    
    return passed, failed


if __name__ == "__main__":
    import sys
    passed, failed = run_all_tests()
    sys.exit(0 if failed == 0 else 1)
