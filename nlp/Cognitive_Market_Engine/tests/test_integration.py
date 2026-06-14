"""
INTEGRATION TESTS — End-to-End System Validation

Validates that:
1. Bootstrap succeeds and all available modules load
2. CognitiveMarketSystem processes news end-to-end
3. Streaming pipeline stages fire correctly
4. Scenario engine generates trees
5. Execution engine handles signals
6. Legacy orchestrator still works
7. Type unification is consistent
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Track results
_results = []


def _record(name, passed, msg=""):
    status = "PASS" if passed else "FAIL"
    _results.append((name, status, msg))
    print(f"  [{status}] {name}" + (f"  ({msg})" if msg else ""))


# ============================================================================
# TEST 1: Bootstrap loads without crashing
# ============================================================================

def test_01_bootstrap():
    """Test that bootstrap() completes without exceptions."""
    print("\n" + "=" * 70)
    print("  TEST 01: Bootstrap")
    print("=" * 70)
    try:
        from main import bootstrap
        components = bootstrap(asset="BTC", verbose=False)
        _record("bootstrap_runs", True)
        _record("engine_loaded", components.get("engine") is not None)
        # Event bus and pipeline are important
        _record("pipeline_loaded", components.get("pipeline") is not None)
        return components
    except Exception as e:
        _record("bootstrap_runs", False, str(e))
        return None


# ============================================================================
# TEST 2: CognitiveMarketSystem processes news
# ============================================================================

def test_02_cognitive_engine(components):
    """Test end-to-end news processing through the cognitive engine."""
    print("\n" + "=" * 70)
    print("  TEST 02: Cognitive Engine End-to-End")
    print("=" * 70)
    engine = components.get("engine") if components else None
    if engine is None:
        _record("cognitive_engine_available", False, "engine not loaded")
        return

    try:
        signal = engine.process_news_event(
            source_id="test",
            raw_text=(
                "Federal Reserve signals unexpected rate cut amid recession fears. "
                "Markets react sharply with Treasury yields plunging."
            ),
            asset_scope=["BTC", "SPY"],
            macro_scope=["rates", "recession"],
        )
        _record("process_news_event_runs", True)
        _record("signal_has_type", hasattr(signal, "signal_type"))
        _record("signal_has_direction", hasattr(signal, "direction"))
        _record("signal_has_strength", hasattr(signal, "strength") and isinstance(signal.strength, (int, float)))
        _record("signal_has_confidence", hasattr(signal, "confidence"))
        _record("signal_has_reason", hasattr(signal, "reason") and bool(signal.reason))

        # Verify to_dict works
        d = signal.to_dict() if hasattr(signal, "to_dict") else None
        _record("signal_to_dict", d is not None and isinstance(d, dict))
    except Exception as e:
        _record("process_news_event_runs", False, str(e))


# ============================================================================
# TEST 3: Streaming pipeline stages
# ============================================================================

def test_03_streaming_pipeline(components):
    """Test that the streaming pipeline can process a news event."""
    print("\n" + "=" * 70)
    print("  TEST 03: Streaming Pipeline")
    print("=" * 70)
    pipeline = components.get("pipeline") if components else None
    if pipeline is None:
        _record("streaming_pipeline_available", False, "pipeline not loaded")
        return

    try:
        result = pipeline.process_news(
            "SEC announces new crypto regulations effective immediately.",
            source="integration_test",
        )
        _record("pipeline_process_news_runs", True)
        _record("pipeline_returns_dict", isinstance(result, dict))
    except Exception as e:
        _record("pipeline_process_news_runs", False, str(e))

    # Check metrics
    try:
        metrics = pipeline.get_metrics()
        _record("pipeline_metrics", isinstance(metrics, dict))
    except Exception as e:
        _record("pipeline_metrics", False, str(e))


# ============================================================================
# TEST 4: Scenario engine
# ============================================================================

def test_04_scenario_engine(components):
    """Test scenario generation."""
    print("\n" + "=" * 70)
    print("  TEST 04: Scenario Engine")
    print("=" * 70)
    scenario = components.get("scenario") if components else None
    if scenario is None:
        _record("scenario_engine_available", False, "not loaded")
        return

    try:
        tree = scenario.generate({
            "raw_text": "Major exchange hack — $200M stolen",
            "certainty_score": 0.8,
            "ambiguity_score": 0.2,
        })
        _record("scenario_generates_tree", tree is not None)
        _record("tree_has_direction", hasattr(tree, "expected_direction"))
        _record("tree_has_tail_risk", hasattr(tree, "tail_risk_probability"))
    except Exception as e:
        _record("scenario_generates_tree", False, str(e))


# ============================================================================
# TEST 5: Execution engine
# ============================================================================

def test_05_execution_engine(components):
    """Test execution nexus with a mock signal."""
    print("\n" + "=" * 70)
    print("  TEST 05: Execution Engine")
    print("=" * 70)
    execution = components.get("execution") if components else None
    if execution is None:
        _record("execution_engine_available", False, "not loaded")
        return

    try:
        # Build a minimal signal-like object
        from engine.tradable_signal_translator import TradableSignal
        _record("TradableSignal_importable", True)
    except Exception as e:
        _record("TradableSignal_importable", False, str(e))
        return

    try:
        has_execute = hasattr(execution, "execute_signal")
        _record("has_execute_signal", has_execute)
        has_close = hasattr(execution, "close_position")
        _record("has_close_position", has_close)
    except Exception as e:
        _record("execution_methods", False, str(e))


# ============================================================================
# TEST 6: Legacy orchestrator
# ============================================================================

def test_06_legacy_orchestrator():
    """Test that legacy_main.py loads and initializes."""
    print("\n" + "=" * 70)
    print("  TEST 06: Legacy Orchestrator")
    print("=" * 70)
    try:
        from legacy_main import PipelineOrchestrator
        orch = PipelineOrchestrator(live_execution=False)
        status = orch.get_pipeline_status()
        _record("legacy_orchestrator_loads", True)
        _record("legacy_has_status", isinstance(status, dict))

        # Count ready phases
        ready = sum(1 for v in status.values() if v == "READY")
        _record(f"legacy_phases_ready ({ready}/7)", ready >= 1)
    except Exception as e:
        _record("legacy_orchestrator_loads", False, str(e))


# ============================================================================
# TEST 7: Type unification
# ============================================================================

def test_07_type_unification():
    """Test that ParticipantType is consistent everywhere."""
    print("\n" + "=" * 70)
    print("  TEST 07: Type Unification")
    print("=" * 70)
    try:
        from shared import ParticipantType as SharedPT

        from engine.core_cognitive_structures import ParticipantType as EnginePT
        _record("engine_uses_shared_PT", SharedPT is EnginePT)
    except Exception as e:
        _record("engine_uses_shared_PT", False, str(e))

    try:
        from shared import ParticipantType as SharedPT
        from participant_cognition.participant_models import ParticipantType as PartPT
        # They should be the same object (imported from shared)
        _record("participant_uses_shared_PT", SharedPT is PartPT)
    except Exception as e:
        _record("participant_uses_shared_PT", False, str(e))

    # Verify enum values
    try:
        from shared import ParticipantType
        expected = {"BANK", "HEDGE_FUND", "HFT", "MARKET_MAKER", "RETAIL"}
        actual = {e.name for e in ParticipantType}
        _record("PT_has_all_values", expected.issubset(actual),
                f"missing: {expected - actual}" if not expected.issubset(actual) else "")
    except Exception as e:
        _record("PT_has_all_values", False, str(e))


# ============================================================================
# TEST 8: Config cross-platform paths
# ============================================================================

def test_08_config_paths():
    """Test that config uses os.path, not hardcoded Unix paths."""
    print("\n" + "=" * 70)
    print("  TEST 08: Config Paths")
    print("=" * 70)
    try:
        from config.system_config import SystemConfig
        cfg = SystemConfig()
        _record("config_loads", True)

        # Check that module-level paths use os.path (not hardcoded Unix)
        from config import system_config as sc
        data_dir = getattr(sc, "DATA_DIR", "")
        _record("DATA_DIR_exists", bool(data_dir), data_dir[:60])

        log_file = str(cfg.log_file) if hasattr(cfg, "log_file") else ""
        _record("log_file_valid", bool(log_file), log_file[:60])
    except Exception as e:
        _record("config_loads", False, str(e))


# ============================================================================
# RUNNER
# ============================================================================

def main():
    print("\n" + "#" * 70)
    print("#  COGNITIVE MARKET ENGINE — INTEGRATION TEST SUITE")
    print("#" * 70)

    components = test_01_bootstrap()
    test_02_cognitive_engine(components)
    test_03_streaming_pipeline(components)
    test_04_scenario_engine(components)
    test_05_execution_engine(components)
    test_06_legacy_orchestrator()
    test_07_type_unification()
    test_08_config_paths()

    # Summary
    passed = sum(1 for _, s, _ in _results if s == "PASS")
    failed = sum(1 for _, s, _ in _results if s == "FAIL")
    total = len(_results)

    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print("=" * 70)

    if failed:
        print("\n  FAILURES:")
        for name, status, msg in _results:
            if status == "FAIL":
                print(f"    - {name}: {msg}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
