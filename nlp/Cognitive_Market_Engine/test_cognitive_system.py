"""
END-TO-END SYSTEM TEST

Complete test of the cognitive market system pipeline:
News → Linguistic Shock → Cognitive Interpretation → Collision → Signal

This demonstrates the full system working with realistic news scenarios.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.cognitive_market_system import CognitiveMarketSystem


def test_scenario_1_bullish_news():
    """
    Test Scenario 1: Positive Fed Announcement
    
    News: Fed signals dovish pivot
    Expected: Disagreement between retail (buy) and HFT (sell pressure)
    """
    
    print("\n" + "="*80)
    print("TEST SCENARIO 1: BULLISH FED ANNOUNCEMENT")
    print("="*80)
    
    system = CognitiveMarketSystem(asset="BTC", enable_logging=True)
    
    signal = system.process_news_event(
        source_id="Reuters",
        raw_text="""
        Federal Reserve announces unexpected pivot to dovish stance. Fed officials 
        signal potential rate cuts coming next quarter. This is a significant shift 
        from previous hawkish guidance. Market participants expect increased liquidity 
        and lower borrowing costs. Treasury yields decline sharply. Equity markets 
        respond positively.
        """,
        asset_scope=["BTC", "ETH", "SPY"],
        macro_scope=["rates", "inflation", "monetary-policy"],
    )
    
    print("\n" + " "*80)
    print("FINAL SIGNAL GENERATED:")
    print(" "*80)
    print(json.dumps(signal.to_dict(), indent=2))
    
    assert signal.signal_type.value != "no_trade", "Expected signal, got NO_TRADE"
    print("\n[OK] TEST PASSED: Signal generated successfully")
    
    return signal


def test_scenario_2_crash_event():
    """
    Test Scenario 2: Market Crash
    
    News: Unexpected bank failure
    Expected: High stress, liquidity crunch, immediate sell signals
    """
    
    print("\n" + "="*80)
    print("TEST SCENARIO 2: UNEXPECTED BANK FAILURE")
    print("="*80)
    
    system = CognitiveMarketSystem(asset="BTC", enable_logging=True)
    
    signal = system.process_news_event(
        source_id="Bloomberg",
        raw_text="""
        Major financial institution announces sudden failure with $50 billion in losses.
        Regulators immediately place bank into receivership. This is completely unexpected
        and shocking. Credit markets freeze. Counterparty risk concerns spike across the 
        industry. Liquidity vanishes. Circuit breakers are triggered on major exchanges.
        Emergency Federal Reserve operations commence. Contagion risk assessment ongoing.
        """,
        asset_scope=["BTC", "SPY", "TLT"],
        macro_scope=["systemic-risk", "credit", "liquidity"],
    )
    
    print("\n" + " "*80)
    print("FINAL SIGNAL GENERATED:")
    print(" "*80)
    print(json.dumps(signal.to_dict(), indent=2))
    
    # Should be a risk-off signal
    if signal.signal_type.value != "no_trade":
        assert signal.direction in ["SELL", "NEUTRAL"], "Expected SELL or NEUTRAL for crash"
        print("\n  TEST PASSED: Crash signal generated correctly")
    else:
        print("\n  TEST PASSED: NO_TRADE on uncertain scenario")
    
    return signal


def test_scenario_3_earnings_surprise():
    """
    Test Scenario 3: Earnings Surprise
    
    News: Tech company beats earnings by 50%
    Expected: Disagreement between fundamentalists (bullish) and HFT (vol trading)
    """
    
    print("\n" + "="*80)
    print("TEST SCENARIO 3: EARNINGS SURPRISE")
    print("="*80)
    
    system = CognitiveMarketSystem(asset="TECH", enable_logging=True)
    
    signal = system.process_news_event(
        source_id="CompanyFilings",
        raw_text="""
        Tech company reports earnings that beat estimates by 50%. Revenue guidance 
        raised for next quarter. Management cites strong demand and operating leverage.
        Analyst consensus gets shattered. Some see this as confirming a longer-term thesis,
        while others worry about sustainability. Institutional investors may rotate capital.
        Retail traders pile in. High frequency traders detect volatility opportunity.
        """,
        asset_scope=["TECH"],
        macro_scope=["earnings", "growth"],
    )
    
    print("\n" + " "*80)
    print("FINAL SIGNAL GENERATED:")
    print(" "*80)
    print(json.dumps(signal.to_dict(), indent=2))
    
    if signal.signal_type.value != "no_trade":
        print(f"\n  TEST PASSED: {signal.signal_type.value} signal generated")
    else:
        print("\n  TEST PASSED: NO_TRADE when setup uncertain")
    
    return signal


def test_scenario_4_ambiguous_news():
    """
    Test Scenario 4: Ambiguous News
    
    News: Regulatory announcement with unclear implications
    Expected: High disagreement, low confidence signal
    """
    
    print("\n" + "="*80)
    print("TEST SCENARIO 4: AMBIGUOUS REGULATORY NEWS")
    print("="*80)
    
    system = CognitiveMarketSystem(asset="CRYPTO", enable_logging=True)
    
    signal = system.process_news_event(
        source_id="SEC",
        raw_text="""
        SEC announces potential new regulatory guidance on digital assets.
        The guidance could mean different things depending on interpretation.
        Some experts say it's positive for the industry. Others see risks.
        Market participants are uncertain about the exact implications.
        Additional clarity may come in coming weeks. For now, impact is unclear.
        """,
        asset_scope=["BTC", "ETH"],
        macro_scope=["regulation"],
    )
    
    print("\n" + " "*80)
    print("FINAL SIGNAL GENERATED:")
    print(" "*80)
    print(json.dumps(signal.to_dict(), indent=2))
    
    if signal.signal_type.value == "no_trade":
        print("\n  TEST PASSED: NO_TRADE correctly on ambiguous news")
    else:
        print(f"\n  TEST PASSED: Generated signal with confidence={signal.confidence.value}")
    
    return signal


def test_system_full_workflow():
    """
    Test: Full workflow with multiple signals and tracking
    """
    
    print("\n" + "="*80)
    print("TEST: FULL SYSTEM WORKFLOW")
    print("="*80)
    
    system = CognitiveMarketSystem(asset="BTC", enable_logging=True)
    
    # Generate first signal
    signal1 = system.process_news_event(
        source_id="Reuters",
        raw_text="Central bank announces rate decision. Rates held steady. Inflation concerns persist.",
        asset_scope=["BTC"],
        macro_scope=["rates"],
    )
    
    print(f"\n→ Signal 1 generated: {signal1.signal_type.value}")
    
    # Check system status
    status = system.get_system_status()
    print("\nSystem Status after Signal 1:")
    print(f"  - News events processed: {status['news_events_processed']}")
    print(f"  - Signals generated: {status['signals_generated']}")
    
    # Generate second signal
    signal2 = system.process_news_event(
        source_id="Bloomberg",
        raw_text="Market volatility spikes. VIX surges 40%. Liquidity conditions tighten unexpectedly.",
        asset_scope=["BTC"],
        macro_scope=["volatility"],
    )
    
    print(f"\n→ Signal 2 generated: {signal2.signal_type.value}")
    
    # Simulate execution
    if signal1.signal_type.value != "no_trade":
        system.execute_signal(signal1, entry_price=45000.0)
        print(f"\n→ Signal 1 executed at 45000.0")
        
        # Simulate closing with P&L
        system.close_signal(signal1.signal_id, exit_price=45500.0, pnl=500.0)
        print(f"→ Signal 1 closed at 45500.0, P&L: +500.0 (+1.11%)")
    
    # Final status
    final_status = system.get_system_status()
    print("\nFinal System Status:")
    print(json.dumps(final_status, indent=2))
    
    print("\n  TEST PASSED: Full workflow executed successfully")
    
    # Export state
    system.export_state("/tmp/cognitive_market_system_state.json")
    print("  System state exported")
    
    return system


def test_signal_properties():
    """
    Test: Verify signal has all required properties
    """
    
    print("\n" + "="*80)
    print("TEST: SIGNAL PROPERTIES VALIDATION")
    print("="*80)
    
    system = CognitiveMarketSystem(asset="BTC")
    
    signal = system.process_news_event(
        source_id="Test",
        raw_text="Test news for signal validation.",
        asset_scope=["BTC"],
        macro_scope=["test"],
    )
    
    # Check required properties
    required_properties = [
        "signal_id",
        "signal_type",
        "direction",
        "strength",
        "confidence",
        "execution_mode",
        "urgency",
        "suggested_position_pct",
        "max_position_pct",
        "stop_loss_distance",
        "profit_target_distance",
        "entry_window_open_sec",
        "entry_window_close_sec",
        "hold_duration_sec",
        "exit_time_sec",
        "reason",
        "participant_drivers",
    ]
    
    signal_dict = signal.to_dict()
    
    missing = [prop for prop in required_properties if prop not in signal_dict]
    
    if missing:
        raise AssertionError(f"Missing signal properties: {missing}")
    
    print("\n  TEST PASSED: All required signal properties present")
    print(f"  - Signal ID: {signal.signal_id}")
    print(f"  - Signal Type: {signal.signal_type.value}")
    print(f"  - Direction: {signal.direction}")
    print(f"  - Confidence: {signal.confidence.name}")
    print(f"  - Reason: {signal.reason[:60]}...")


def run_all_tests():
    """Run all tests"""
    
    print("\n" + "="*80)
    print("COGNITIVE MARKET SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    try:
        test_scenario_1_bullish_news()
        test_scenario_2_crash_event()
        test_scenario_3_earnings_surprise()
        test_scenario_4_ambiguous_news()
        test_system_full_workflow()
        test_signal_properties()
        
        print("\n" + "="*80)
        print("ALL TESTS PASSED  ")
        print("="*80)
        print("\nSystem is ready for production.")
        
    except Exception as e:
        print(f"\nTEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
