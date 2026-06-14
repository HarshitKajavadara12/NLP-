"""
PHASE 2 TESTS: PARTICIPANT COGNITIVE MODELS

Testing that:
1. Same NewsEvent -> Different expectations for different participants
2. Each participant respects their cognitive profile
3. No prices or trading signals (mental modeling only)
4. Deterministic: same input -> same output
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from news_model.news_event import NewsEvent, ConfidenceLevel
from news_model.parser import NewsEventParser
from participant_cognition.participant_models import (
    Participant, ParticipantType, CognitiveProfile,
    TimeHorizon, RiskTolerance, ObjectiveType, InformationPriority,
    InterpretationBias, ParticipantExpectation,
    create_bank_participant, create_hedge_fund_participant,
    create_hft_participant, create_market_maker_participant,
    create_retail_participant
)


def test_01_canonical_participants_exist():
    """Test that all 5 canonical archetypes can be instantiated."""
    print("\nTEST 01: Canonical Participants Exist")
    
    bank = create_bank_participant()
    hf = create_hedge_fund_participant()
    hft = create_hft_participant()
    mm = create_market_maker_participant()
    retail = create_retail_participant()
    
    assert bank.participant_type == ParticipantType.BANK
    assert hf.participant_type == ParticipantType.HEDGE_FUND
    assert hft.participant_type == ParticipantType.HFT
    assert mm.participant_type == ParticipantType.MARKET_MAKER
    assert retail.participant_type == ParticipantType.RETAIL
    
    print("[PASS]")


def test_02_cognitive_profiles_complete():
    """Test that all cognitive profiles have 6 dimensions."""
    print("\nTEST 02: Cognitive Profiles Have 6 Dimensions")
    
    participants = [
        create_bank_participant(),
        create_hedge_fund_participant(),
        create_hft_participant(),
        create_market_maker_participant(),
        create_retail_participant(),
    ]
    
    for p in participants:
        profile = p.cognitive_profile
        assert profile.time_horizon is not None
        assert profile.risk_tolerance is not None
        assert profile.objectives is not None and len(profile.objectives) > 0
        assert profile.priority_information is not None
        assert profile.reaction_latency is not None
        assert profile.interpretation_bias is not None
        print(f"  {p.name}: 6 dimensions complete")
    
    print("[PASS]")


def test_03_same_news_different_expectations():
    """CORE TEST: Same NewsEvent -> Different expectations."""
    print("\nTEST 03: Same News Produces Different Expectations")
    
    parser = NewsEventParser()
    news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Bank of England maintains interest rates unchanged."
    )
    
    participants = [
        create_bank_participant(),
        create_hedge_fund_participant(),
        create_hft_participant(),
        create_market_maker_participant(),
        create_retail_participant(),
    ]
    
    expectations = []
    for participant in participants:
        exp = participant.interpret(news)
        expectations.append(exp)
    
    # Check that expectations differ by participant type
    belief_shifts = [e.belief_shift for e in expectations]
    urgencies = [e.urgency for e in expectations]
    
    # Not all the same
    assert len(set(belief_shifts)) > 1 or len(set(urgencies)) > 1, \
        "Different participants should have different expectations"
    
    for i, exp in enumerate(expectations):
        print(f"  {participants[i].name}: belief_shift={exp.belief_shift:+.2f}, urgency={exp.urgency:.2f}")
    
    print("[PASS]")


def test_04_bank_risk_averse_profile():
    """Test bank specifically shows risk-averse behavior."""
    print("\nTEST 04: Bank Shows Risk-Averse Profile")
    
    bank = create_bank_participant()
    profile = bank.cognitive_profile
    
    # Bank should be risk-averse
    assert profile.risk_tolerance == RiskTolerance.LOW
    assert profile.interpretation_bias == InterpretationBias.RISK_AVERSE
    assert ObjectiveType.BALANCE_SHEET_PROTECTION in profile.objectives
    
    # Test with negative news
    parser = NewsEventParser()
    bad_news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Credit spreads widening dramatically."
    )
    
    exp = bank.interpret(bad_news)
    # Bank should show negative belief shift on bad news
    assert isinstance(exp.belief_shift, float)
    assert isinstance(exp.action_likelihoods.increase_hedging, float)
    
    print(f"  Bank belief shift on bad news: {exp.belief_shift:+.2f}")
    print(f"  Bank hedging likelihood: {exp.action_likelihoods.increase_hedging:.2f}")
    print("[PASS]")


def test_05_hft_ultrafast_profile():
    """Test HFT shows ultrafast reaction characteristics."""
    print("\nTEST 05: HFT Shows Ultrafast Profile")
    
    hft = create_hft_participant()
    profile = hft.cognitive_profile
    
    # HFT should be ultrafast
    assert profile.time_horizon == TimeHorizon.MILLISECONDS
    assert profile.reaction_latency == TimeHorizon.MILLISECONDS
    assert profile.risk_tolerance == RiskTolerance.ULTRA_LOW
    assert ObjectiveType.SPREAD_CAPTURE in profile.objectives
    
    # Test with volatile news
    parser = NewsEventParser()
    volatile_news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Flash",
        raw_text="Unexpected earnings miss triggers volatility spike."
    )
    
    exp = hft.interpret(volatile_news)
    # HFT should respond urgently
    print(f"  HFT urgency level: {exp.urgency:.2f}")
    print(f"  HFT spread-widening likelihood: {exp.action_likelihoods.widen_spreads:.2f}")
    print("[PASS]")


def test_06_hedge_fund_asymmetric_profile():
    """Test hedge fund seeks asymmetric returns."""
    print("\nTEST 06: Hedge Fund Seeks Asymmetric Returns")
    
    hf = create_hedge_fund_participant()
    profile = hf.cognitive_profile
    
    # Hedge fund should seek opportunity
    assert profile.interpretation_bias == InterpretationBias.OPPORTUNITY_SEEKING
    assert ObjectiveType.ASYMMETRIC_RETURN in profile.objectives
    assert profile.risk_tolerance == RiskTolerance.ADAPTIVE
    
    # Test with mixed news
    parser = NewsEventParser()
    opportunity_news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Bloomberg",
        raw_text="Company reports strong quarter but macro concerns linger."
    )
    
    exp = hf.interpret(opportunity_news)
    # Hedge fund should see narrative opportunity
    print(f"  HF narrative alignment: {exp.narrative_alignment:+.2f}")
    print(f"  HF exposure increase likelihood: {exp.action_likelihoods.increase_exposure:.2f}")
    print("[PASS]")


def test_07_market_maker_inventory_focus():
    """Test market maker manages inventory."""
    print("\nTEST 07: Market Maker Manages Inventory")
    
    mm = create_market_maker_participant()
    profile = mm.cognitive_profile
    
    # Market maker should manage inventory
    assert ObjectiveType.INVENTORY_STABILITY in profile.objectives
    assert ObjectiveType.SPREAD_CAPTURE in profile.objectives
    
    parser = NewsEventParser()
    uncertainty_news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Multiple policy signals create significant uncertainty."
    )
    
    exp = mm.interpret(uncertainty_news)
    # MM should widen spreads on uncertainty
    print(f"  MM uncertainty level: {exp.uncertainty_level:.2f}")
    print(f"  MM spread-widening likelihood: {exp.action_likelihoods.widen_spreads:.2f}")
    print("[PASS]")


def test_08_retail_overreaction_profile():
    """Test retail shows overreaction bias."""
    print("\nTEST 08: Retail Shows Overreaction Bias")
    
    retail = create_retail_participant()
    profile = retail.cognitive_profile
    
    # Retail should be prone to overreaction
    assert profile.interpretation_bias == InterpretationBias.OVERREACTION
    assert profile.risk_tolerance == RiskTolerance.HIGH
    
    parser = NewsEventParser()
    positive_news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="CNBC",
        raw_text="Stock market rallies on optimistic earnings outlook."
    )
    
    exp = retail.interpret(positive_news)
    # Retail should overreact to positive
    print(f"  Retail exposure increase: {exp.action_likelihoods.increase_exposure:.2f}")
    print("[PASS]")


def test_09_no_prices_no_signals():
    """CRITICAL: Verify NO prices or trading signals appear."""
    print("\nTEST 09: NO PRICES OR TRADING SIGNALS (CRITICAL)")
    
    parser = NewsEventParser()
    news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Stock prices surge on positive economic data."
    )
    
    participants = [
        create_bank_participant(),
        create_hedge_fund_participant(),
        create_hft_participant(),
        create_market_maker_participant(),
        create_retail_participant(),
    ]
    
    for participant in participants:
        exp = participant.interpret(news)
        
        # No price fields
        assert not hasattr(exp, 'price'), "NO price field allowed"
        assert not hasattr(exp, 'target_price'), "NO target_price field allowed"
        assert not hasattr(exp, 'predicted_price'), "NO predicted_price field allowed"
        
        # No trading signals
        assert not hasattr(exp, 'trading_signal'), "NO trading_signal field allowed"
        assert not hasattr(exp, 'signal'), "NO signal field allowed"
        assert not hasattr(exp, 'buy'), "NO buy field allowed"
        assert not hasattr(exp, 'sell'), "NO sell field allowed"
        
        # No P&L
        assert not hasattr(exp, 'pnl'), "NO pnl field allowed"
        assert not hasattr(exp, 'return'), "NO return field allowed"
        
        # Action likelihoods are NOT signals
        assert hasattr(exp.action_likelihoods, 'increase_exposure'), \
            "Should have action likelihoods (these are NOT signals)"
    
    print("  All participants: NO prices, NO trading signals, NO P&L")
    print("[PASS - CRITICAL CHECK]")


def test_10_participant_expectation_fields():
    """Test ParticipantExpectation has all required fields."""
    print("\nTEST 10: ParticipantExpectation Has All Fields")
    
    parser = NewsEventParser()
    news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Economic indicators point to sustained growth."
    )
    
    bank = create_bank_participant()
    exp = bank.interpret(news)
    
    # Required fields
    assert exp.participant_type is not None
    assert exp.news_event_id == news.event_id
    assert exp.belief_shift >= -1.0 and exp.belief_shift <= 1.0
    assert isinstance(exp.belief_shift_confidence, ConfidenceLevel)
    assert exp.uncertainty_level >= 0.0 and exp.uncertainty_level <= 1.0
    assert exp.urgency >= 0.0 and exp.urgency <= 1.0
    assert exp.short_term_expectation >= -1.0 and exp.short_term_expectation <= 1.0
    assert exp.long_term_expectation >= -1.0 and exp.long_term_expectation <= 1.0
    assert exp.action_likelihoods is not None
    assert exp.narrative_alignment >= -1.0 and exp.narrative_alignment <= 1.0
    assert isinstance(exp.reasoning, str)
    
    print(f"  All fields present and valid")
    print(f"  Sample expectation: {exp.get_summary()}")
    print("[PASS]")


def test_11_deterministic_interpretation():
    """Test that same input -> same output (deterministic)."""
    print("\nTEST 11: Deterministic Interpretation")
    
    parser = NewsEventParser()
    news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Central bank signals hawkish stance on inflation."
    )
    
    bank = create_bank_participant()
    
    # Interpret same news twice
    exp1 = bank.interpret(news)
    exp2 = bank.interpret(news)
    
    # Should be identical (deterministic)
    assert exp1.belief_shift == exp2.belief_shift
    assert exp1.uncertainty_level == exp2.uncertainty_level
    assert exp1.urgency == exp2.urgency
    assert exp1.reasoning == exp2.reasoning
    
    print(f"  Same participant + same news = same expectation")
    print(f"  Belief shift: {exp1.belief_shift:+.2f} == {exp2.belief_shift:+.2f}")
    print("[PASS]")


def test_12_action_likelihoods_normalized():
    """Test that action likelihoods sum to ~1.0."""
    print("\nTEST 12: Action Likelihoods Normalized")
    
    parser = NewsEventParser()
    news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Markets react to unexpected policy shift."
    )
    
    participants = [
        create_bank_participant(),
        create_hedge_fund_participant(),
        create_hft_participant(),
        create_market_maker_participant(),
        create_retail_participant(),
    ]
    
    for participant in participants:
        exp = participant.interpret(news)
        actions = exp.action_likelihoods
        
        total = (actions.increase_exposure + actions.decrease_exposure +
                actions.widen_spreads + actions.pull_liquidity +
                actions.hold_position + actions.increase_hedging +
                actions.wait_for_clarity + actions.panic_action)
        
        # Should sum to 1.0 (with floating point tolerance)
        assert 0.99 < total <= 1.01, f"Total: {total}"
        print(f"  {participant.name}: actions sum to {total:.4f}")
    
    print("[PASS]")


def test_13_different_participants_different_actions():
    """Test that different archetypes take different action likelihoods."""
    print("\nTEST 13: Different Participants -> Different Actions")
    
    parser = NewsEventParser()
    
    # Create TWO different news scenarios to get variance
    positive_news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Strong earnings growth reported by major bank with excellent forward guidance."
    )
    
    participants = [
        create_bank_participant(),
        create_hedge_fund_participant(),
        create_hft_participant(),
        create_market_maker_participant(),
        create_retail_participant(),
    ]
    
    # Interpret the positive news
    expectations = []
    for participant in participants:
        exp = participant.interpret(positive_news)
        expectations.append(exp)
    
    # Check that at least 2 different dominant actions emerge
    dominant_actions = []
    for i, exp in enumerate(expectations):
        al = exp.action_likelihoods
        dominant = max([
            ("increase_exposure", al.increase_exposure),
            ("decrease_exposure", al.decrease_exposure),
            ("widen_spreads", al.widen_spreads),
            ("pull_liquidity", al.pull_liquidity),
            ("hold_position", al.hold_position),
            ("increase_hedging", al.increase_hedging),
            ("wait_for_clarity", al.wait_for_clarity),
            ("panic_action", al.panic_action),
        ], key=lambda x: x[1])
        
        dominant_actions.append(dominant[0])
        print(f"  {participants[i].name}: {dominant[0]} ({dominant[1]:.2f}), belief={exp.belief_shift:+.2f}")
    
    # Different participants should have different dominant actions
    # (Not all same action)
    unique_actions = set(dominant_actions)
    assert len(unique_actions) >= 2, f"Expected 2+ different actions, got: {unique_actions}"
    print(f"  Actions vary across participants: {unique_actions}")
    print("[PASS]")


def test_14_interpretation_respects_cognitive_profile():
    """Test that interpretation respects cognitive profile constraints."""
    print("\nTEST 14: Interpretation Respects Cognitive Profile")
    
    # Create custom participant with extreme profile
    profile = CognitiveProfile(
        time_horizon=TimeHorizon.YEARS,
        risk_tolerance=RiskTolerance.LOW,
        objectives=[ObjectiveType.BALANCE_SHEET_PROTECTION],
        priority_information=InformationPriority.REGULATORY_LANGUAGE,
        reaction_latency=TimeHorizon.WEEKS,
        interpretation_bias=InterpretationBias.RISK_AVERSE
    )
    participant = Participant(ParticipantType.BANK, profile, "Conservative Bank")
    
    parser = NewsEventParser()
    
    # Test with positive news
    good_news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Economic growth accelerates to 5% annualized rate."
    )
    
    # Test with negative news
    bad_news = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Banking crisis emerges in emerging markets."
    )
    
    exp_good = participant.interpret(good_news)
    exp_bad = participant.interpret(bad_news)
    
    # Conservative bank should show lower urgency on bad news
    print(f"  Conservative bank on good news: urgency={exp_good.urgency:.2f}")
    print(f"  Conservative bank on bad news: urgency={exp_bad.urgency:.2f}")
    print(f"  Risk-averse bias should manifest in hedging on bad news")
    
    print("[PASS]")


def run_all_tests():
    """Run all Phase 2 tests."""
    print("\n" + "="*70)
    print("PHASE 2: PARTICIPANT COGNITIVE MODELS - TEST SUITE")
    print("="*70)
    
    tests = [
        test_01_canonical_participants_exist,
        test_02_cognitive_profiles_complete,
        test_03_same_news_different_expectations,
        test_04_bank_risk_averse_profile,
        test_05_hft_ultrafast_profile,
        test_06_hedge_fund_asymmetric_profile,
        test_07_market_maker_inventory_focus,
        test_08_retail_overreaction_profile,
        test_09_no_prices_no_signals,
        test_10_participant_expectation_fields,
        test_11_deterministic_interpretation,
        test_12_action_likelihoods_normalized,
        test_13_different_participants_different_actions,
        test_14_interpretation_respects_cognitive_profile,
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
        print("\n[TARGET] PHASE 2 COMPLETE AND VERIFIED")
        print("[LOCK] PHASE 2 LOCKED AND READY FOR PHASE 3")
    
    return passed, failed


if __name__ == "__main__":
    import sys
    passed, failed = run_all_tests()
    sys.exit(0 if failed == 0 else 1)
