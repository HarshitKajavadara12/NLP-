"""
PHASE 1 TEST SUITE

Tests that verify:
1. NewsEvent data model works correctly
2. Parser extracts linguistic structure
3. No trading signals are generated (this is news only, not market)
4. Raw text is preserved unchanged
5. Ambiguity and uncertainty are preserved
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from news_model.news_event import (
    NewsEvent, NarrativeType, TemporalType, ConfidenceLevel
)
from news_model.parser import NewsEventParser


def test_01_news_event_creation():
    """Test: Can we create a NewsEvent?"""
    print("\n" + "="*70)
    print("TEST 01: NewsEvent Creation")
    print("="*70)
    
    event = NewsEvent.create(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Federal Reserve announced a policy decision."
    )
    
    assert event.event_id is not None
    assert event.timestamp_utc == datetime(2026, 1, 10, 14, 30, 0)
    assert event.source == "Reuters"
    assert event.raw_text == "The Federal Reserve announced a policy decision."
    
    print(f"[OK] Event ID: {event.event_id}")
    print(f"[OK] Timestamp: {event.timestamp_utc}")
    print(f"[OK] Source: {event.source}")
    print(f"[OK] Raw text preserved: {event.raw_text[:50]}...")
    print("\nPASS: test_01\n")


def test_02_raw_text_never_altered():
    """Test: Raw text is never altered."""
    print("="*70)
    print("TEST 02: Raw Text Immutability")
    print("="*70)
    
    original_text = "   The Federal Reserve MAY raise rates IF inflation persists.   "
    
    event = NewsEvent.create(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text=original_text
    )
    
    assert event.raw_text == original_text, "Raw text must not be altered"
    
    print(f"[OK] Original: '{original_text}'")
    print(f"[OK] Stored:   '{event.raw_text}'")
    print(f"[OK] Identical: {event.raw_text == original_text}")
    print("\nPASS: test_02\n")


def test_03_parser_basic():
    """Test: Parser converts raw text to structured event."""
    print("="*70)
    print("TEST 03: Basic Parsing")
    print("="*70)
    
    parser = NewsEventParser()
    
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Federal Reserve signaled patience on rate cuts."
    )
    
    assert len(event.sentences) > 0, "Should extract sentences"
    assert len(event.actors) > 0, "Should identify actors"
    
    print(f"[OK] Sentences extracted: {len(event.sentences)}")
    print(f"[OK] Modality markers found: {len(event.modality_markers)}")
    print(f"[OK] Actors identified: {[a.name for a in event.actors]}")
    print("\nPASS: test_03\n")


def test_04_uncertainty_preserved():
    """Test: Uncertainty is extracted and preserved."""
    print("="*70)
    print("TEST 04: Uncertainty Preservation")
    print("="*70)
    
    parser = NewsEventParser()
    
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Fed MAY raise rates IF inflation persists."
    )
    
    uncertainty_markers = [m for m in event.modality_markers 
                          if m.marker_type == "uncertainty"]
    
    assert len(uncertainty_markers) > 0, "Should detect uncertainty"
    assert event.ambiguity_score > 0.4, "Should calculate high ambiguity"
    assert event.has_uncertainty(), "Should report has_uncertainty()"
    
    print(f"[OK] Uncertainty markers: {[m.text for m in uncertainty_markers]}")
    print(f"[OK] Ambiguity score: {event.ambiguity_score:.2f}")
    print(f"[OK] Confidence level: {event.confidence_level.value}")
    print("\nPASS: test_04\n")


def test_05_contradiction_detected():
    """Test: Contradictions with prior news are detected."""
    print("="*70)
    print("TEST 05: Contradiction Detection")
    print("="*70)
    
    parser = NewsEventParser()
    
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Fed REVERSED course, contrary to previous hawkish signals."
    )
    
    assert event.contradicts_prior_news, "Should detect contradiction"
    assert event.has_contradiction(), "Should report has_contradiction()"
    
    contradiction_markers = [m for m in event.modality_markers 
                            if m.marker_type == "contradiction"]
    assert len(contradiction_markers) > 0
    
    print(f"[OK] Contradiction markers: {[m.text for m in contradiction_markers]}")
    print(f"[OK] Contradicts prior: {event.contradicts_prior_news}")
    print(f"[OK] Narrative includes contradiction: {NarrativeType.NARRATIVE_CONTRADICTION in event.narrative_types}")
    print("\nPASS: test_05\n")


def test_06_temporal_markers():
    """Test: Temporal information is extracted."""
    print("="*70)
    print("TEST 06: Temporal Markers")
    print("="*70)
    
    parser = NewsEventParser()
    
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Fed will likely raise rates next quarter if inflation persists."
    )
    
    assert len(event.temporal_markers) > 0, "Should extract temporal markers"
    
    temporal_types = [m.temporal_type for m in event.temporal_markers]
    
    print(f"[OK] Temporal types: {[t.value for t in temporal_types]}")
    print(f"[OK] Has future marker: {TemporalType.FUTURE in temporal_types}")
    print(f"[OK] Has conditional: {TemporalType.CONDITIONAL in temporal_types}")
    print("\nPASS: test_06\n")


def test_07_semantic_claims():
    """Test: Semantic claims are extracted."""
    print("="*70)
    print("TEST 07: Semantic Claims")
    print("="*70)
    
    parser = NewsEventParser()
    
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Federal Reserve announced it may raise interest rates."
    )
    
    assert len(event.semantic_claims) > 0, "Should extract semantic claims"
    
    claim = event.semantic_claims[0]
    print(f"[OK] Actor: {claim.actor.name}")
    print(f"[OK] Action: {claim.action}")
    print(f"[OK] Object: {claim.object_}")
    print(f"[OK] Confidence: {claim.confidence.value}")
    print("\nPASS: test_07\n")


def test_08_narrative_classification():
    """Test: News is classified into narrative types."""
    print("="*70)
    print("TEST 08: Narrative Classification")
    print("="*70)
    
    parser = NewsEventParser()
    
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Fed policy decision affects credit spread widening."
    )
    
    assert len(event.narrative_types) > 0, "Should classify narratives"
    
    print(f"[OK] Narratives: {[n.value for n in event.narrative_types]}")
    print(f"[OK] Contains MACRO_POLICY: {NarrativeType.MACRO_POLICY in event.narrative_types}")
    print(f"[OK] Contains CREDIT_RISK: {NarrativeType.CREDIT_RISK in event.narrative_types}")
    print("\nPASS: test_08\n")


def test_09_no_trading_signals():
    """Test: CRITICAL - No trading signals in Phase 1."""
    print("="*70)
    print("TEST 09: NO TRADING SIGNALS (CRITICAL)")
    print("="*70)
    
    parser = NewsEventParser()
    
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="Fed signals rate cuts ahead."
    )
    
    # These should NOT exist:
    assert not hasattr(event, 'market_direction'), "Should NOT have market_direction"
    assert not hasattr(event, 'sentiment_score'), "Should NOT have sentiment_score"
    assert not hasattr(event, 'bullish_bearish'), "Should NOT have bullish_bearish"
    assert not hasattr(event, 'trading_signal'), "Should NOT have trading_signal"
    
    # Interpretations should be EMPTY
    assert len(event.participant_interpretations) == 0, "Interpretations must be empty"
    
    print(f"[OK] No market_direction field")
    print(f"[OK] No sentiment_score field")
    print(f"[OK] No trading_signal field")
    print(f"[OK] Participant interpretations empty: {event.participant_interpretations}")
    print(f"\nNote: Trading signals come from Phase 2 (participant cognitive models)")
    print("\nPASS: test_09\n")


def test_10_batch_parsing():
    """Test: Can we parse multiple news events?"""
    print("="*70)
    print("TEST 10: Batch Parsing")
    print("="*70)
    
    parser = NewsEventParser()
    
    news_items = [
        ("Reuters", "Fed signals patience on rates."),
        ("Bloomberg", "Company beats earnings expectations."),
        ("WSJ", "Credit spreads widen amid uncertainty."),
    ]
    
    events = []
    for source, text in news_items:
        event = parser.parse(
            timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
            source=source,
            raw_text=text
        )
        events.append(event)
    
    assert len(events) == 3, "Should parse all items"
    
    print(f"[OK] Parsed {len(events)} news events")
    print(f"[OK] Sources: {[e.source for e in events]}")
    print(f"[OK] All have unique IDs: {len(set(e.event_id for e in events)) == 3}")
    print("\nPASS: test_10\n")


def test_11_ambiguity_calculation():
    """Test: Ambiguity is calculated correctly."""
    print("="*70)
    print("TEST 11: Ambiguity Calculation")
    print("="*70)
    
    parser = NewsEventParser()
    
    # Certain statement
    certain_event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Fed officially announced it will raise rates."
    )
    
    # Uncertain statement
    uncertain_event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Fed may possibly raise rates if inflation persists."
    )
    
    print(f"[OK] Certain event ambiguity: {certain_event.ambiguity_score:.2f}")
    print(f"[OK] Uncertain event ambiguity: {uncertain_event.ambiguity_score:.2f}")
    print(f"[OK] Ambiguity difference: {uncertain_event.ambiguity_score > certain_event.ambiguity_score}")
    
    assert uncertain_event.ambiguity_score > certain_event.ambiguity_score, \
        "Uncertain event should have higher ambiguity"
    
    print("\nPASS: test_11\n")


def test_12_actor_extraction():
    """Test: Actors (entities) are correctly identified."""
    print("="*70)
    print("TEST 12: Actor Extraction")
    print("="*70)
    
    parser = NewsEventParser()
    
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="The Federal Reserve and ECB coordinated on policy."
    )
    
    actor_names = [a.name for a in event.actors]
    
    assert len(event.actors) > 0, "Should extract actors"
    print(f"[OK] Extracted actors: {actor_names}")
    
    # Check for central bank classification
    central_banks = [a for a in event.actors if a.category == "central_bank"]
    assert len(central_banks) > 0, "Should classify as central_bank"
    
    print(f"[OK] Central banks found: {[a.name for a in central_banks]}")
    print("\nPASS: test_12\n")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PHASE 1: NEWS EVENT DATA MODEL - COMPLETE TEST SUITE")
    print("="*70)
    
    tests = [
        test_01_news_event_creation,
        test_02_raw_text_never_altered,
        test_03_parser_basic,
        test_04_uncertainty_preserved,
        test_05_contradiction_detected,
        test_06_temporal_markers,
        test_07_semantic_claims,
        test_08_narrative_classification,
        test_09_no_trading_signals,
        test_10_batch_parsing,
        test_11_ambiguity_calculation,
        test_12_actor_extraction,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\nFAIL: {test_func.__name__}")
            print(f"   {e}\n")
            failed += 1
        except Exception as e:
            print(f"\nERROR: {test_func.__name__}")
            print(f"   {type(e).__name__}: {e}\n")
            failed += 1
    
    print("="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n[TARGET] PHASE 1 COMPLETE AND VERIFIED\n")
        print("What We Have:")
        print("   * NewsEvent data model (linguistic container)")
        print("   * NewsEventParser (raw text -> structured event)")
        print("   * Linguistic decomposition (sentences, clauses, modality)")
        print("   * Semantic extraction (actors, claims, narratives)")
        print("   * Uncertainty metrics (ambiguity, confidence)")
        print("   * Raw text preservation (immutable)\n")
        print("What We DON'T Have (and shouldn't):")
        print("   * No sentiment scores")
        print("   * No trading signals")
        print("   * No bullish/bearish labels")
        print("   * No market interpretation")
        print("   * No participant models yet (Phase 2)\n")
        print("[LOCK] PHASE 1 LOCKED AND READY FOR PHASE 2")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
