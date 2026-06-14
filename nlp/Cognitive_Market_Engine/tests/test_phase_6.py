"""
Phase 6: Signal Authorization & Trust Weighting — Comprehensive Test Suite

14 core tests:
- Tests 01-03: Structure and instantiation
- Tests 04-08: Core logic (trust, filtering, weighting)
- Tests 09-11: Signal generation and normalization
- Tests 12-14: Execution gate and research bridge
"""

import sys
from pathlib import Path
import pytest
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from signal_auth import (
    SignalAuthorizer,
    SignalDirection,
    VolatilityImpact,
    SignalStatus,
    ReactionHorizon,
    ValidationMetrics,
    NewsMetadata,
    PredictionFromPhase4,
    SignalRecord,
    NormalizedSignal,
    TrustWeightHistory,
    ParticipantWeights,
)


# ============================================================================
# TESTS 01-03: Structure and Instantiation
# ============================================================================

def test_01_signal_authorizer_exists():
    """Test that SignalAuthorizer can be instantiated"""
    authorizer = SignalAuthorizer()
    assert authorizer is not None
    assert len(authorizer.approved_signals) == 0
    assert len(authorizer.filtered_signals) == 0


def test_02_input_structures_exist():
    """Test that Phase 5 input structures are available"""
    now = datetime.now()
    
    # ValidationMetrics from Phase 5
    validation = ValidationMetrics(
        event_id="TEST_001",
        timestamp=now,
        directional_accuracy=0.85,
        volatility_accuracy=0.78,
        timing_accuracy=0.82,
        hft_participation_accuracy=0.92,
        hedge_fund_participation_accuracy=0.80,
        retail_participation_accuracy=0.45,
        bank_participation_accuracy=0.75,
        market_maker_participation_accuracy=0.88,
        overall_credibility=0.82,
        regime_classification="ACCURATE",
    )
    assert validation.event_id == "TEST_001"
    assert validation.overall_credibility == 0.82
    
    # NewsMetadata
    news = NewsMetadata(
        event_id="TEST_001",
        timestamp=now,
        event_type="EARNINGS",
        entity="AAPL",
        polarity=0.75,
        intensity=0.85,
        ambiguity=0.2,
    )
    assert news.entity == "AAPL"
    assert news.polarity == 0.75
    
    # PredictionFromPhase4
    prediction = PredictionFromPhase4(
        event_id="TEST_001",
        expected_direction="UP",
        expected_magnitude=0.65,
        expected_vol_expansion=0.72,
        expected_volume_spike=0.55,
        shock_onset_seconds=2.5,
        peak_impact_seconds=45.0,
        recovery_seconds=480.0,
    )
    assert prediction.expected_direction == "UP"
    assert prediction.expected_magnitude == 0.65


def test_03_signal_record_structure():
    """Test that SignalRecord and related structures work"""
    now = datetime.now()
    
    signal = SignalRecord(
        signal_id="SIG_001",
        timestamp=now,
        direction=SignalDirection.BUY,
        strength=0.87,
        volatility_impact=VolatilityImpact.HIGH,
        trust_score=0.92,
        participant_weights={
            "hft": 0.95,
            "hedge_fund": 0.80,
            "retail": 0.40,
            "bank": 0.70,
            "market_maker": 0.85,
        },
        source_news_ids=["NEWS_001"],
        source_event_types=["EARNINGS"],
        expected_reaction_horizon=ReactionHorizon.IMMEDIATE,
        status=SignalStatus.APPROVED,
        approval_timestamp=now,
        expiration_timestamp=now + timedelta(hours=4),
    )
    
    assert signal.is_approved()
    assert not signal.is_expired()
    assert signal.get_effective_strength() == pytest.approx(0.87 * 0.92, abs=0.001)


# ============================================================================
# TESTS 04-08: Core Logic (Trust, Filtering, Weighting)
# ============================================================================

def test_04_trust_weight_assignment():
    """Test trust score assignment based on validation history"""
    authorizer = SignalAuthorizer()
    now = datetime.now()
    
    validation = ValidationMetrics(
        event_id="EARNINGS_001",
        timestamp=now,
        directional_accuracy=0.90,
        volatility_accuracy=0.85,
        timing_accuracy=0.88,
        hft_participation_accuracy=0.92,
        hedge_fund_participation_accuracy=0.80,
        retail_participation_accuracy=0.45,
        bank_participation_accuracy=0.75,
        market_maker_participation_accuracy=0.88,
        overall_credibility=0.86,
        regime_classification="ACCURATE",
    )
    
    news = NewsMetadata(
        event_id="EARNINGS_001",
        timestamp=now,
        event_type="EARNINGS",
        entity="AAPL",
        polarity=0.75,
        intensity=0.5,
        ambiguity=0.1,
    )
    
    # First event: mostly current validation
    trust1 = authorizer.assign_trust_score(news, validation)
    assert 0.0 <= trust1 <= 1.0
    assert trust1 > 0.65  # Should be reasonably high for good validation
    
    # Second event of same type: history should blend in
    trust2 = authorizer.assign_trust_score(news, validation)
    assert trust2 > 0.65  # Both should be solid
    # History now includes previous event


def test_05_signal_filtering_gate():
    """Test that signals below threshold are filtered"""
    authorizer = SignalAuthorizer()
    now = datetime.now()
    
    # High credibility - should pass
    good_validation = ValidationMetrics(
        event_id="GOOD_001",
        timestamp=now,
        directional_accuracy=0.85,
        volatility_accuracy=0.80,
        timing_accuracy=0.82,
        hft_participation_accuracy=0.90,
        hedge_fund_participation_accuracy=0.80,
        retail_participation_accuracy=0.50,
        bank_participation_accuracy=0.75,
        market_maker_participation_accuracy=0.85,
        overall_credibility=0.82,
        regime_classification="ACCURATE",
    )
    
    status_good = authorizer.filter_signal(0.85, good_validation, threshold=0.6)
    assert status_good == SignalStatus.APPROVED
    
    # Low credibility - should be filtered
    poor_validation = ValidationMetrics(
        event_id="POOR_001",
        timestamp=now,
        directional_accuracy=0.35,
        volatility_accuracy=0.30,
        timing_accuracy=0.25,
        hft_participation_accuracy=0.40,
        hedge_fund_participation_accuracy=0.35,
        retail_participation_accuracy=0.30,
        bank_participation_accuracy=0.25,
        market_maker_participation_accuracy=0.30,
        overall_credibility=0.32,
        regime_classification="INACCURATE",
    )
    
    status_poor = authorizer.filter_signal(0.55, poor_validation, threshold=0.6)
    assert status_poor == SignalStatus.FILTERED


def test_06_signal_weighting_strength():
    """Test signal strength calculation based on credibility and participants"""
    authorizer = SignalAuthorizer()
    now = datetime.now()
    
    validation = ValidationMetrics(
        event_id="WEIGHT_001",
        timestamp=now,
        directional_accuracy=0.88,
        volatility_accuracy=0.85,
        timing_accuracy=0.90,
        hft_participation_accuracy=0.95,      # HFT was very accurate
        hedge_fund_participation_accuracy=0.80,
        retail_participation_accuracy=0.40,   # Retail was poor
        bank_participation_accuracy=0.75,
        market_maker_participation_accuracy=0.90,
        overall_credibility=0.83,
        regime_classification="ACCURATE",
    )
    
    prediction = PredictionFromPhase4(
        event_id="WEIGHT_001",
        expected_direction="UP",
        expected_magnitude=0.75,
        expected_vol_expansion=0.70,
        expected_volume_spike=0.55,
        shock_onset_seconds=2.0,
        peak_impact_seconds=30.0,
        recovery_seconds=600.0,
    )
    
    news = NewsMetadata(
        event_id="WEIGHT_001",
        timestamp=now,
        event_type="EARNINGS",
        entity="MSFT",
        polarity=0.8,
        intensity=0.6,
        ambiguity=0.15,
    )
    
    trust = 0.87
    strength, weights = authorizer.weight_signal_strength(
        trust, validation, prediction, news
    )
    
    # Strength should be 0.0-1.0
    assert 0.0 <= strength <= 1.0
    # Should be reasonably high given good validation + HFT accuracy
    assert strength > 0.4
    
    # Check participant weights
    assert "hft" in weights
    assert "retail" in weights


def test_07_signal_direction_determination():
    """Test direction determination (BUY, SELL, NEUTRAL)"""
    authorizer = SignalAuthorizer()
    now = datetime.now()
    
    # Bullish scenario
    bullish_validation = ValidationMetrics(
        event_id="DIR_001",
        timestamp=now,
        directional_accuracy=0.90,
        volatility_accuracy=0.85,
        timing_accuracy=0.88,
        hft_participation_accuracy=0.92,
        hedge_fund_participation_accuracy=0.80,
        retail_participation_accuracy=0.45,
        bank_participation_accuracy=0.75,
        market_maker_participation_accuracy=0.88,
        overall_credibility=0.86,
        regime_classification="ACCURATE",
    )
    
    bullish_news = NewsMetadata(
        event_id="DIR_001",
        timestamp=now,
        event_type="EARNINGS",
        entity="GOOGL",
        polarity=0.85,  # Bullish
        intensity=0.6,
        ambiguity=0.1,
    )
    
    bullish_prediction = PredictionFromPhase4(
        event_id="DIR_001",
        expected_direction="UP",
        expected_magnitude=0.70,
        expected_vol_expansion=0.65,
        expected_volume_spike=0.50,
        shock_onset_seconds=2.0,
        peak_impact_seconds=40.0,
        recovery_seconds=480.0,
    )
    
    direction = authorizer.determine_signal_direction(
        bullish_validation, bullish_news, bullish_prediction
    )
    assert direction == SignalDirection.BUY
    
    # Bearish scenario
    bearish_news = NewsMetadata(
        event_id="DIR_002",
        timestamp=now,
        event_type="EARNINGS",
        entity="TSLA",
        polarity=-0.85,  # Bearish
        intensity=0.6,
        ambiguity=0.1,
    )
    
    bearish_prediction = PredictionFromPhase4(
        event_id="DIR_002",
        expected_direction="DOWN",
        expected_magnitude=0.70,
        expected_vol_expansion=0.65,
        expected_volume_spike=0.50,
        shock_onset_seconds=2.0,
        peak_impact_seconds=40.0,
        recovery_seconds=480.0,
    )
    
    direction = authorizer.determine_signal_direction(
        bullish_validation, bearish_news, bearish_prediction
    )
    assert direction == SignalDirection.SELL


def test_08_volatility_impact_assessment():
    """Test volatility impact determination"""
    authorizer = SignalAuthorizer()
    now = datetime.now()
    
    # High intensity, high vol prediction → HIGH impact
    validation = ValidationMetrics(
        event_id="VOL_001",
        timestamp=now,
        directional_accuracy=0.85,
        volatility_accuracy=0.88,
        timing_accuracy=0.82,
        hft_participation_accuracy=0.90,
        hedge_fund_participation_accuracy=0.80,
        retail_participation_accuracy=0.45,
        bank_participation_accuracy=0.75,
        market_maker_participation_accuracy=0.85,
        overall_credibility=0.83,
        regime_classification="ACCURATE",
    )
    
    news_high = NewsMetadata(
        event_id="VOL_001",
        timestamp=now,
        event_type="RATE_DECISION",
        entity="FED",
        polarity=0.5,
        intensity=0.85,  # High intensity
        ambiguity=0.2,
    )
    
    prediction_high = PredictionFromPhase4(
        event_id="VOL_001",
        expected_direction="UP",
        expected_magnitude=0.65,
        expected_vol_expansion=0.78,  # High vol prediction
        expected_volume_spike=0.60,
        shock_onset_seconds=1.0,
        peak_impact_seconds=15.0,
        recovery_seconds=300.0,
    )
    
    impact = authorizer.determine_volatility_impact(
        validation, prediction_high, news_high
    )
    assert impact in [VolatilityImpact.HIGH, VolatilityImpact.EXTREME]


# ============================================================================
# TESTS 09-11: Signal Generation and Normalization
# ============================================================================

def test_09_signal_record_generation():
    """Test full signal record creation"""
    authorizer = SignalAuthorizer()
    now = datetime.now()
    
    validation = ValidationMetrics(
        event_id="SIG_GEN_001",
        timestamp=now,
        directional_accuracy=0.87,
        volatility_accuracy=0.84,
        timing_accuracy=0.86,
        hft_participation_accuracy=0.93,
        hedge_fund_participation_accuracy=0.79,
        retail_participation_accuracy=0.42,
        bank_participation_accuracy=0.74,
        market_maker_participation_accuracy=0.87,
        overall_credibility=0.83,
        regime_classification="ACCURATE",
    )
    
    news = NewsMetadata(
        event_id="SIG_GEN_001",
        timestamp=now,
        event_type="EARNINGS",
        entity="NVDA",
        polarity=0.80,
        intensity=0.70,
        ambiguity=0.12,
    )
    
    prediction = PredictionFromPhase4(
        event_id="SIG_GEN_001",
        expected_direction="UP",
        expected_magnitude=0.72,
        expected_vol_expansion=0.68,
        expected_volume_spike=0.52,
        shock_onset_seconds=2.5,
        peak_impact_seconds=45.0,
        recovery_seconds=600.0,
    )
    
    signal = authorizer.authorize_signal(news, validation, prediction)
    
    assert isinstance(signal, SignalRecord)
    assert signal.direction == SignalDirection.BUY
    # Signal should be approved due to high credibility (0.83)
    assert signal.status in [SignalStatus.APPROVED, SignalStatus.PENDING_VALIDATION]
    assert signal.trust_score > 0.6
    assert 0.0 <= signal.strength <= 1.0


def test_10_signal_expiration():
    """Test signal expiration logic"""
    now = datetime.now()
    
    # Create an expired signal
    signal_expired = SignalRecord(
        signal_id="EXPIRED_001",
        timestamp=now - timedelta(hours=5),
        direction=SignalDirection.BUY,
        strength=0.85,
        volatility_impact=VolatilityImpact.MEDIUM,
        trust_score=0.88,
        participant_weights={"hft": 0.95, "hedge_fund": 0.80, "retail": 0.40, "bank": 0.70, "market_maker": 0.85},
        source_news_ids=["NEWS_001"],
        source_event_types=["EARNINGS"],
        expected_reaction_horizon=ReactionHorizon.SHORT_TERM,
        status=SignalStatus.APPROVED,
        approval_timestamp=now - timedelta(hours=5),
        expiration_timestamp=now - timedelta(hours=1),  # Expired 1 hour ago
    )
    
    assert signal_expired.is_expired()
    assert signal_expired.get_effective_strength() == 0.0


def test_11_signal_normalization():
    """Test normalization of multiple conflicting signals"""
    now = datetime.now()
    
    # Create multiple signals with different directions
    buy_signal = SignalRecord(
        signal_id="SIG_BUY",
        timestamp=now,
        direction=SignalDirection.BUY,
        strength=0.85,
        volatility_impact=VolatilityImpact.MEDIUM,
        trust_score=0.90,
        participant_weights={"hft": 0.95, "hedge_fund": 0.80, "retail": 0.40, "bank": 0.70, "market_maker": 0.85},
        source_news_ids=["NEWS_001"],
        source_event_types=["EARNINGS"],
        expected_reaction_horizon=ReactionHorizon.SHORT_TERM,
        status=SignalStatus.APPROVED,
        approval_timestamp=now,
        expiration_timestamp=now + timedelta(hours=4),
    )
    
    sell_signal = SignalRecord(
        signal_id="SIG_SELL",
        timestamp=now,
        direction=SignalDirection.SELL,
        strength=0.50,  # Weaker
        volatility_impact=VolatilityImpact.LOW,
        trust_score=0.70,
        participant_weights={"hft": 0.95, "hedge_fund": 0.80, "retail": 0.40, "bank": 0.70, "market_maker": 0.85},
        source_news_ids=["NEWS_002"],
        source_event_types=["TECHNICAL"],
        expected_reaction_horizon=ReactionHorizon.LONG_TERM,
        status=SignalStatus.APPROVED,
        approval_timestamp=now,
        expiration_timestamp=now + timedelta(hours=4),
    )
    
    authorizer = SignalAuthorizer()
    normalized = authorizer.normalize_signals([buy_signal, sell_signal], now)
    
    # BUY signal is stronger, should win
    assert normalized.net_direction == SignalDirection.BUY
    assert normalized.signal_count == 2
    assert normalized.net_strength > 0.5


# ============================================================================
# TESTS 12-14: Execution Gate and Research Bridge
# ============================================================================

def test_12_approved_signals_only():
    """Test that only APPROVED signals reach execution gate"""
    authorizer = SignalAuthorizer()
    now = datetime.now()
    
    # Create one approved, one filtered
    approved = SignalRecord(
        signal_id="APPROVED_001",
        timestamp=now,
        direction=SignalDirection.BUY,
        strength=0.85,
        volatility_impact=VolatilityImpact.HIGH,
        trust_score=0.92,
        participant_weights={"hft": 0.95, "hedge_fund": 0.80, "retail": 0.40, "bank": 0.70, "market_maker": 0.85},
        source_news_ids=["NEWS_001"],
        source_event_types=["EARNINGS"],
        expected_reaction_horizon=ReactionHorizon.IMMEDIATE,
        status=SignalStatus.APPROVED,
        approval_timestamp=now,
        expiration_timestamp=now + timedelta(hours=4),
    )
    
    filtered = SignalRecord(
        signal_id="FILTERED_001",
        timestamp=now,
        direction=SignalDirection.NEUTRAL,
        strength=0.30,
        volatility_impact=VolatilityImpact.LOW,
        trust_score=0.45,
        participant_weights={"hft": 0.95, "hedge_fund": 0.80, "retail": 0.40, "bank": 0.70, "market_maker": 0.85},
        source_news_ids=["NEWS_002"],
        source_event_types=["TECHNICAL"],
        expected_reaction_horizon=ReactionHorizon.LONG_TERM,
        status=SignalStatus.FILTERED,
        approval_timestamp=now,
        expiration_timestamp=now + timedelta(hours=4),
    )
    
    authorizer.approved_signals.append(approved)
    authorizer.filtered_signals.append(filtered)
    
    # Get approved signals
    approved_list = authorizer.get_approved_signals()
    
    assert len(approved_list) == 1
    assert approved_list[0].signal_id == "APPROVED_001"
    assert approved_list[0].status == SignalStatus.APPROVED


def test_13_participant_weight_updates():
    """Test dynamic participant weight updates (feedback from Phase 5)"""
    authorizer = SignalAuthorizer()
    
    # Initial weights
    initial_weights = authorizer.current_participant_weights
    assert initial_weights.hft_weight == 0.95
    
    # Update based on Phase 5 feedback (e.g., HFT performance degraded)
    authorizer.update_participant_weights(
        hft_weight=0.85,           # Reduced from 0.95
        hedge_fund_weight=0.80,
        retail_weight=0.35,        # Down due to poor performance
        bank_weight=0.72,
        market_maker_weight=0.90,
    )
    
    updated_weights = authorizer.current_participant_weights
    assert updated_weights.hft_weight == 0.85
    assert updated_weights.retail_weight == 0.35


def test_14_signal_statistics_reporting():
    """Test statistics for research monitoring"""
    authorizer = SignalAuthorizer()
    now = datetime.now()
    
    # Add some signals
    for i in range(5):
        signal = SignalRecord(
            signal_id=f"SIG_{i}",
            timestamp=now,
            direction=SignalDirection.BUY if i < 3 else SignalDirection.SELL,
            strength=0.85,
            volatility_impact=VolatilityImpact.MEDIUM,
            trust_score=0.88,
            participant_weights={"hft": 0.95, "hedge_fund": 0.80, "retail": 0.40, "bank": 0.70, "market_maker": 0.85},
            source_news_ids=[f"NEWS_{i}"],
            source_event_types=["EARNINGS"],
            expected_reaction_horizon=ReactionHorizon.SHORT_TERM,
            status=SignalStatus.APPROVED if i < 3 else SignalStatus.FILTERED,
            approval_timestamp=now,
            expiration_timestamp=now + timedelta(hours=4),
        )
        if i < 3:
            authorizer.approved_signals.append(signal)
        else:
            authorizer.filtered_signals.append(signal)
    
    stats = authorizer.get_signal_statistics()
    
    assert stats["total_signals_processed"] == 5
    assert stats["approved_signals"] == 3
    assert stats["filtered_signals"] == 2
    assert stats["approval_rate"] == 0.6
    assert "hft" in stats["active_participant_weights"]
