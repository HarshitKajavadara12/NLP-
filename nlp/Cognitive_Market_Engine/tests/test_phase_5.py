"""
PHASE 5 TESTS: Market Reality Validation (Research Core)

Tests validate that the validation system itself works correctly:
1. Can accept predictions from Phases 1-4
2. Can compare against market reality
3. Produces meaningful credibility scores
4. Detects failure patterns
5. Is research-only (no trading signals)

All tests are about validation quality, not market prediction.
"""

import sys
from pathlib import Path
import pytest
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from reality_validation import (
    NewsEventType,
    DirectionType,
    RegimeType,
    ValidityScore,
    NewsUnderstanding,
    ParticipantExpectation,
    PredictedMarketState,
    OHLCV,
    MarketSnapshot,
    MarketReality,
    DirectionalValidity,
    VolatilityValidity,
    TimingValidity,
    ParticipationValidity,
    RegimeValidity,
    ValidationRecord,
    ModelCredibility,
    CredibilityDataset,
    FailurePattern,
    FailureAnalysis,
    RealityValidator,
)


# ============================================================
# TEST 01-03: Core Structure Tests
# ============================================================

def test_01_validator_exists():
    """Test that RealityValidator class exists."""
    print("\nTEST 01: RealityValidator Exists")
    validator = RealityValidator()
    assert validator is not None
    assert hasattr(validator, 'credibility_dataset')
    assert hasattr(validator, 'failure_analysis')
    print("    RealityValidator instantiated successfully")


def test_02_input_structures_exist():
    """Test that Phase 1-4 input structures exist."""
    print("\nTEST 02: Input Structures from Phases 1-4 Exist")
    
    # Phase 1: News Understanding
    news = NewsUnderstanding(
        event_id="TEST_001",
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        event_type=NewsEventType.EARNINGS,
        entity="Company XYZ",
        polarity=0.7,
        intensity=0.8,
        ambiguity=0.2
    )
    assert news.polarity == 0.7
    
    # Phase 2: Participant Expectation
    expectation = ParticipantExpectation(
        participant_type="bank",
        sentiment=-0.6,
        confidence=0.8,
        expected_direction=DirectionType.DOWN,
        expected_reaction_time=timedelta(seconds=5),
        vol_expectation=0.6,
        liquidity_expectation=0.4
    )
    assert expectation.sentiment == -0.6
    
    # Phase 4: Predicted Market State
    prediction = PredictedMarketState(
        event_id="TEST_001",
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        expected_direction=DirectionType.DOWN,
        expected_magnitude=2.5,
        expected_regime_shift=RegimeType.PANIC,
        expected_vol_expansion=0.7,
        expected_vol_duration=timedelta(hours=2),
        expected_volume_spike=3.5,
        expected_order_imbalance=-0.8,
        expected_spread_widening=0.6,
        shock_onset=timedelta(seconds=2),
        peak_impact_window=timedelta(minutes=10),
        recovery_time=timedelta(hours=1),
        persistence=timedelta(hours=4)
    )
    assert prediction.expected_magnitude == 2.5
    
    print("    All input structures (Phase 1, 2, 4) work")


def test_03_market_reality_structures_exist():
    """Test that market reality structures exist."""
    print("\nTEST 03: Market Reality Structures Exist")
    
    # Single snapshot
    snapshot = MarketSnapshot(
        timestamp=datetime(2026, 1, 10, 14, 31, 0),
        price=100.5,
        bid=100.45,
        ask=100.55,
        spread=0.1,
        volume_cumulative=10000,
        order_book_imbalance=-0.3,
        realized_volatility=0.25,
        regime=RegimeType.TRENDING
    )
    assert snapshot.price == 100.5
    
    # Market reality with time windows
    reality = MarketReality(
        event_id="TEST_001",
        news_timestamp=datetime(2026, 1, 10, 14, 30, 0),
        pre_news_baseline=[snapshot],
        shock_period=[snapshot],
        hft_digestion=[snapshot],
        institutional_reaction=[snapshot],
        structural_reposition=[snapshot],
        actual_direction=DirectionType.DOWN,
        actual_magnitude=2.0,
        actual_vol_expansion=0.6,
        actual_regime_shift=RegimeType.PANIC,
        peak_price_time=datetime(2026, 1, 10, 14, 32, 0),
        peak_vol_time=datetime(2026, 1, 10, 14, 35, 0),
        recovery_time=datetime(2026, 1, 10, 15, 30, 0),
        hft_participation_marker=True,
        institutional_participation_marker=True,
        retail_panic_marker=False
    )
    assert reality.actual_magnitude == 2.0
    
    print("    Market reality structures work")


# ============================================================
# TEST 04-08: Validation Logic Tests
# ============================================================

def test_04_directional_validation():
    """Test directional accuracy validation."""
    print("\nTEST 04: Directional Validity")
    
    validator = RealityValidator()
    
    # Prediction correct
    correct = validator.validate_directional_accuracy(
        DirectionType.DOWN,
        DirectionType.DOWN
    )
    assert correct.matches == True
    assert correct.confidence == 1.0
    
    # Prediction wrong
    wrong = validator.validate_directional_accuracy(
        DirectionType.DOWN,
        DirectionType.UP
    )
    assert wrong.matches == False
    assert wrong.confidence == 0.0
    
    print(f"    Correct prediction confidence: {correct.confidence}")
    print(f"    Wrong prediction confidence: {wrong.confidence}")


def test_05_volatility_validation():
    """Test volatility accuracy validation."""
    print("\nTEST 05: Volatility Validity")
    
    validator = RealityValidator()
    
    # Perfect prediction
    perfect = validator.validate_volatility_accuracy(0.6, 0.6)
    assert perfect.accuracy == 1.0
    
    # Off by 0.1
    off = validator.validate_volatility_accuracy(0.6, 0.7)
    assert 0.0 <= off.accuracy < 1.0
    
    # Way off
    very_wrong = validator.validate_volatility_accuracy(0.2, 0.8)
    assert very_wrong.accuracy < off.accuracy
    
    print(f"    Perfect prediction accuracy: {perfect.accuracy}")
    print(f"    Off by 0.1 accuracy: {off.accuracy:.2f}")
    print(f"    Way off accuracy: {very_wrong.accuracy:.2f}")


def test_06_timing_validation():
    """Test timing accuracy validation."""
    print("\nTEST 06: Timing Validity")
    
    validator = RealityValidator()
    
    # Perfect timing
    perfect = validator.validate_timing_accuracy(
        expected_shock_onset=timedelta(seconds=2),
        actual_shock_onset=timedelta(seconds=2),
        expected_peak=timedelta(minutes=10),
        actual_peak=timedelta(minutes=10),
        expected_recovery=timedelta(hours=1),
        actual_recovery=timedelta(hours=1)
    )
    assert perfect.overall_timing_accuracy == 1.0
    
    # Some error
    off = validator.validate_timing_accuracy(
        expected_shock_onset=timedelta(seconds=2),
        actual_shock_onset=timedelta(seconds=5),
        expected_peak=timedelta(minutes=10),
        actual_peak=timedelta(minutes=12),
        expected_recovery=timedelta(hours=1),
        actual_recovery=timedelta(hours=1, minutes=10)
    )
    assert 0.0 <= off.overall_timing_accuracy < 1.0
    
    print(f"    Perfect timing accuracy: {perfect.overall_timing_accuracy}")
    print(f"    Off timing accuracy: {off.overall_timing_accuracy:.2f}")


def test_07_participation_validation():
    """Test participant model validation."""
    print("\nTEST 07: Participation Validity")
    
    validator = RealityValidator()
    
    # HFT was predicted and observed
    hft = validator.validate_participation_match(
        participant_type="hft",
        predicted_sentiment=0.2,
        predicted_speed=timedelta(milliseconds=500),
        observed_in_market=True,
        timing_match=0.9,
        direction_match=0.8
    )
    assert abs(hft.overall_accuracy - 0.85) < 0.001  # (0.9 + 0.8) / 2
    
    # Bank was predicted but not observed
    bank = validator.validate_participation_match(
        participant_type="bank",
        predicted_sentiment=-0.6,
        predicted_speed=timedelta(seconds=30),
        observed_in_market=False,
        timing_match=0.3,
        direction_match=0.5
    )
    assert abs(bank.overall_accuracy - 0.4) < 0.001  # (0.3 + 0.5) / 2
    
    print(f"    HFT participation accuracy: {hft.overall_accuracy}")
    print(f"    Bank participation accuracy: {bank.overall_accuracy}")


def test_08_regime_validation():
    """Test regime shift validation."""
    print("\nTEST 08: Regime Validity")
    
    validator = RealityValidator()
    
    # Regime DID shift, persisted long
    structural = validator.validate_regime_shift(
        predicted_regime=RegimeType.PANIC,
        actual_pre_regime=RegimeType.TRENDING,
        actual_post_regime=RegimeType.PANIC,
        persistence_days=10
    )
    assert structural.regime_changed == True
    assert structural.event_classification == ValidityScore.ACCURATE
    
    # Regime changed but only temporarily
    temporary = validator.validate_regime_shift(
        predicted_regime=RegimeType.PANIC,
        actual_pre_regime=RegimeType.TRENDING,
        actual_post_regime=RegimeType.CHOPPY,
        persistence_days=0.5  # Half day
    )
    assert temporary.regime_changed == True
    assert temporary.event_classification == ValidityScore.NOISY
    
    # Regime didn't change
    no_change = validator.validate_regime_shift(
        predicted_regime=RegimeType.PANIC,
        actual_pre_regime=RegimeType.TRENDING,
        actual_post_regime=RegimeType.TRENDING,
        persistence_days=0
    )
    assert no_change.regime_changed == False
    assert no_change.event_classification == ValidityScore.INACCURATE
    
    print(f"    Structural shift classification: {structural.event_classification}")
    print(f"    Temporary shift classification: {temporary.event_classification}")
    print(f"    No shift classification: {no_change.event_classification}")


# ============================================================
# TEST 09-11: Validation Record Assembly
# ============================================================

def test_09_validation_record_creation():
    """Test creating a complete validation record."""
    print("\nTEST 09: Validation Record Creation")
    
    validator = RealityValidator()
    
    # Create all 5 validation dimensions
    directional = validator.validate_directional_accuracy(DirectionType.DOWN, DirectionType.DOWN)
    volatility = validator.validate_volatility_accuracy(0.6, 0.6)
    timing = validator.validate_timing_accuracy(
        timedelta(seconds=2), timedelta(seconds=2),
        timedelta(minutes=10), timedelta(minutes=10),
        timedelta(hours=1), timedelta(hours=1)
    )
    participation = [
        validator.validate_participation_match("hft", 0.2, timedelta(milliseconds=500), True, 0.9, 0.8)
    ]
    regime = validator.validate_regime_shift(
        RegimeType.PANIC, RegimeType.TRENDING, RegimeType.PANIC, 5
    )
    
    # Create record
    record = validator.create_validation_record(
        event_id="TEST_001",
        news_timestamp=datetime(2026, 1, 10, 14, 30, 0),
        news_type=NewsEventType.EARNINGS,
        directional=directional,
        volatility=volatility,
        timing=timing,
        participation_list=participation,
        regime=regime
    )
    
    assert record.overall_accuracy > 0.0
    assert record.model_credibility > 0.0
    assert record.most_accurate_participant == "hft"
    
    print(f"    Record created with accuracy: {record.overall_accuracy:.2f}")
    print(f"    Model credibility: {record.model_credibility:.2f}")
    print(f"    Most accurate: {record.most_accurate_participant}")


def test_10_credibility_tracking():
    """Test model credibility tracking over time."""
    print("\nTEST 10: Credibility Tracking")
    
    credibility = ModelCredibility("hft")
    
    # Start with no validations
    assert credibility.event_count == 0
    assert credibility.is_reliable == False
    
    # Add validations
    credibility.update(0.9, 0.85, 0.8)  # Good
    assert credibility.event_count == 1
    assert credibility.latest_accuracy > 0.0
    
    # Add more
    credibility.update(0.8, 0.75, 0.85)  # Still good
    assert credibility.event_count == 2
    assert credibility.mean_accuracy > 0.75
    
    # Add bad ones
    credibility.update(0.3, 0.4, 0.2)  # Bad
    assert credibility.event_count == 3
    
    # Check reliability status
    if credibility.mean_accuracy > 0.65:
        assert credibility.is_reliable == True
    
    print(f"    Event count: {credibility.event_count}")
    print(f"    Mean accuracy: {credibility.mean_accuracy:.2f}")
    print(f"    Latest accuracy: {credibility.latest_accuracy:.2f}")
    print(f"    Is reliable: {credibility.is_reliable}")


def test_11_credibility_dataset():
    """Test tracking credibility for all participants."""
    print("\nTEST 11: Credibility Dataset (All Participants)")
    
    dataset = CredibilityDataset()
    
    # All 5 participants should exist
    assert dataset.bank_credibility is not None
    assert dataset.hft_credibility is not None
    assert dataset.hedge_fund_credibility is not None
    assert dataset.market_maker_credibility is not None
    assert dataset.retail_credibility is not None
    
    # Get credibility should work
    hft = dataset.get_credibility("hft")
    assert hft is not None
    assert hft.participant_type == "hft"
    
    print("    All 5 participant credibilities exist")
    print("    Can retrieve by participant type")


# ============================================================
# TEST 12-14: Research-Only (No Trading Signals)
# ============================================================

def test_12_no_trading_signals():
    """Test that Phase 5 produces NO trading signals."""
    print("\nTEST 12: NO Trading Signals (Research-Only)")
    
    validator = RealityValidator()
    
    # Create a validation record
    directional = validator.validate_directional_accuracy(DirectionType.UP, DirectionType.UP)
    volatility = validator.validate_volatility_accuracy(0.7, 0.7)
    timing = validator.validate_timing_accuracy(
        timedelta(seconds=2), timedelta(seconds=1),
        timedelta(minutes=10), timedelta(minutes=9),
        timedelta(hours=1), timedelta(hours=1)
    )
    participation = []
    regime = validator.validate_regime_shift(
        RegimeType.PANIC, RegimeType.TRENDING, RegimeType.PANIC, 3
    )
    
    record = validator.create_validation_record(
        "TEST_001",
        datetime(2026, 1, 10, 14, 30, 0),
        NewsEventType.MACRO_DATA,
        directional,
        volatility,
        timing,
        participation,
        regime
    )
    
    # Verify NO trading-related fields
    assert not hasattr(record, "signal")
    assert not hasattr(record, "position_size")
    assert not hasattr(record, "entry_price")
    assert not hasattr(record, "profit_target")
    assert not hasattr(record, "stop_loss")
    assert not hasattr(record, "expected_pnl")
    
    # Verify only research fields
    assert hasattr(record, "overall_accuracy")
    assert hasattr(record, "model_credibility")
    assert hasattr(record, "research_notes")
    
    print("    No trading signal fields present")
    print("    Only research/credibility fields present")


def test_13_failure_pattern_detection():
    """Test failure pattern detection."""
    print("\nTEST 13: Failure Pattern Detection")
    
    analysis = FailureAnalysis()
    
    # Add a failure pattern
    pattern = FailurePattern(
        failure_type="overreaction",
        participant_type="retail",
        news_type=NewsEventType.EARNINGS,
        occurrence_count=5,
        severity_avg=0.7,
        example_event_ids=["EVENT_001", "EVENT_002"],
        research_notes="Retail tends to panic-sell after earnings misses"
    )
    
    analysis.add_pattern(pattern)
    
    # Query patterns
    retail_failures = analysis.get_patterns_for_participant("retail")
    assert len(retail_failures) == 1
    
    earnings_failures = analysis.get_patterns_for_news_type(NewsEventType.EARNINGS)
    assert len(earnings_failures) == 1
    
    print(f"    Failure patterns tracked for: {pattern.participant_type}")
    print(f"    Occurrences: {pattern.occurrence_count}")
    print(f"    Can query by participant and news type")


def test_14_overall_credibility_report():
    """Test generating overall credibility report."""
    print("\nTEST 14: Overall Credibility Report")
    
    validator = RealityValidator()
    
    # Add some validations
    dataset = validator.credibility_dataset
    dataset.hft_credibility.update(0.9, 0.8, 0.85)
    dataset.retail_credibility.update(0.4, 0.5, 0.3)
    dataset.bank_credibility.update(0.7, 0.75, 0.6)
    
    # Get report
    report = validator.get_credibility_report()
    
    # All 5 participants in report
    assert "bank" in report
    assert "hft" in report
    assert "hedge_fund" in report
    assert "market_maker" in report
    assert "retail" in report
    
    # HFT should be more credible than retail
    assert report["hft"] > report["retail"]
    
    # All scores 0.0-1.0
    for name, score in report.items():
        assert 0.0 <= score <= 1.0
    
    print("    Credibility report for all 5 participants:")
    for name, score in report.items():
        print(f"    - {name}: {score:.2f}")


# ============================================================
# HELPER FUNCTION
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
