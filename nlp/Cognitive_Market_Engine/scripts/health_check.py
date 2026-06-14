"""
HEALTH CHECK — End-to-End System Validation

Tests every module imports, pipeline wiring, and runs a full
News → NLP → Cognitive → Decision → Execution pipeline.

Usage:
    python scripts/health_check.py
"""

import os
import sys
import time
import traceback

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"

results = {"passed": 0, "failed": 0, "warned": 0}


def check(label, fn):
    """Run a check and print result."""
    try:
        ok = fn()
        if ok:
            print(f"  {PASS} {label}")
            results["passed"] += 1
        else:
            print(f"  {WARN} {label} (returned False)")
            results["warned"] += 1
    except Exception as e:
        print(f"  {FAIL} {label}: {e}")
        results["failed"] += 1
        return False
    return True


def main():
    print("\n" + "=" * 70)
    print("  COGNITIVE MARKET ENGINE — Health Check")
    print("=" * 70)

    # ================================================================
    # SECTION 1: Module Imports (all 24 packages)
    # ================================================================
    print("\n--- Section 1: Module Imports ---")
    
    modules = [
        # Core Engine
        ("engine.cognitive_market_system", "CognitiveMarketSystem"),
        ("engine.core_cognitive_structures", None),
        ("engine.expectation_collision_engine", None),
        ("engine.tradable_signal_translator", None),
        
        # NLP
        ("nlp_engine.deep_nlp_parser", "DeepNLPParser"),
        ("nlp_engine.entity_extraction", None),
        ("nlp_engine.advanced_nlp", None),
        ("nlp_engine.contradiction_detector", None),
        ("nlp_engine.intent_detector", None),
        
        # News Model
        ("news_model.parser", "NewsEventParser"),
        ("news_model.news_event", None),
        
        # Participant Cognition
        ("participant_cognition.participant_models", "Participant"),
        
        # Market Response
        ("market_response.behavior_models", "BehaviorTranslator"),
        
        # Market Impact
        ("market_impact.market_impact_models", "MarketImpactCalculator"),
        
        # Reality Validation
        ("reality_validation.market_reality", "RealityValidator"),
        
        # Signal Authorization
        ("signal_auth.signal_authorization", "SignalAuthorizer"),
        
        # Decision System
        ("decision_system.decision_engine", "DecisionEngine"),
        
        # Execution
        ("execution.execution_nexus", "ExecutionNexus"),
        
        # Scenario Engine
        ("scenario_engine.scenario_generator", "ScenarioGenerator"),
        
        # Hidden Truth
        ("hidden_truth.cross_source_analyzer", "CrossSourceAnalyzer"),
        ("hidden_truth.omission_detector", "OmissionDetector"),
        ("hidden_truth.timing_analyzer", "TimingAnalyzer"),
        ("hidden_truth.narrative_tracker", "NarrativeTracker"),
        
        # Multi-Asset
        ("multi_asset.correlation_engine", "CorrelationEngine"),
        ("multi_asset.contagion_model", "ContagionModel"),
        
        # Streaming
        ("streaming.event_bus", "EventBus"),
        ("streaming.pipeline", "StreamingPipeline"),
        
        # Storage
        ("storage.database", "DatabaseManager"),
        ("storage.knowledge_graph", "KnowledgeGraph"),
        
        # Learning
        ("learning.feedback_loop", "FeedbackLoop"),
        
        # News Ingestion
        ("news_ingestion.news_aggregator", "NewsAggregator"),
        ("news_ingestion.rss_reader", None),
        ("news_ingestion.gdelt_client", None),
        ("news_ingestion.news_api_client", None),
        
        # Config
        ("config.logging_config", "setup_logging"),
        
        # Pipeline Bridge
        ("pipeline_bridge", "PipelineBridge"),
        
        # Market Data
        ("data.market_data_feed", "MarketDataFeed"),
        
        # Dashboard
        ("dashboard.app", None),
    ]
    
    for mod_path, cls_name in modules:
        label = f"import {mod_path}"
        if cls_name:
            label += f".{cls_name}"
        
        def _import(mp=mod_path, cn=cls_name):
            mod = __import__(mp, fromlist=[cn] if cn else [""])
            if cn:
                assert hasattr(mod, cn), f"{cn} not found in {mp}"
            return True
        
        check(label, _import)

    # ================================================================
    # SECTION 2: Component Instantiation
    # ================================================================
    print("\n--- Section 2: Component Instantiation ---")
    
    components = {}
    
    def _create_decision():
        from decision_system.decision_engine import DecisionEngine
        components["decision"] = DecisionEngine()
        return True
    check("DecisionEngine()", _create_decision)
    
    def _create_execution():
        from execution.execution_nexus import ExecutionNexus
        components["execution"] = ExecutionNexus()
        return True
    check("ExecutionNexus()", _create_execution)
    
    def _create_market_data():
        from data.market_data_feed import MarketDataFeed
        components["market_data"] = MarketDataFeed(use_live=False)
        return True
    check("MarketDataFeed()", _create_market_data)
    
    def _create_pipeline_bridge():
        from pipeline_bridge import PipelineBridge
        components["bridge"] = PipelineBridge(mode="hybrid")
        return True
    check("PipelineBridge(hybrid)", _create_pipeline_bridge)

    # ================================================================
    # SECTION 3: Pipeline Wiring Tests
    # ================================================================
    print("\n--- Section 3: Pipeline Wiring ---")
    
    def _test_decision_engine():
        from decision_system.decision_engine import (
            DecisionEngine, SignalInput, SignalSource
        )
        engine = components.get("decision") or DecisionEngine()
        signals = [
            SignalInput(
                source=SignalSource.NLP_ANALYSIS,
                direction="bullish",
                strength=0.7,
                confidence=0.8,
                urgency=0.5,
                reasoning="Test NLP signal",
            ),
            SignalInput(
                source=SignalSource.COGNITIVE_MODELS,
                direction="bullish",
                strength=0.6,
                confidence=0.75,
                urgency=0.6,
                reasoning="Test cognitive signal",
            ),
        ]
        packet = engine.decide(signals)
        assert packet.action is not None, "No action produced"
        assert packet.decision_id, "No decision ID"
        assert len(packet.reasoning_chain) > 0, "No reasoning chain"
        return True
    check("DecisionEngine.decide() → DecisionPacket", _test_decision_engine)
    
    def _test_execution():
        from execution.execution_nexus import ExecutionNexus, ApprovedSignal
        from datetime import datetime
        nexus = components.get("execution") or ExecutionNexus()
        signal = ApprovedSignal(
            signal_id="TEST-001",
            timestamp=datetime.now(),
            direction="BUY",
            strength=0.8,
            volatility_impact="MEDIUM",
            trust_score=0.75,
            reaction_horizon="SHORT_TERM",
            participant_weights={"test": 1.0},
            source_news_ids=["test"],
            expiration_timestamp=datetime.now(),
        )
        order = nexus.execute_signal(
            signal=signal, current_price=50000.0, current_time=datetime.now()
        )
        assert order is not None, "No order created"
        assert order.status.value == "filled", f"Unexpected status: {order.status}"
        return True
    check("ExecutionNexus.execute_signal() → ExecutedOrder", _test_execution)
    
    def _test_market_data():
        md = components.get("market_data")
        if not md:
            from data.market_data_feed import MarketDataFeed
            md = MarketDataFeed(use_live=False)
        snap = md.get_market_snapshot("BTC")
        assert snap.price > 0, "Invalid price"
        assert snap.asset == "BTC", "Wrong asset"
        return True
    check("MarketDataFeed.get_market_snapshot(BTC)", _test_market_data)
    
    def _test_bridge_process():
        bridge = components.get("bridge")
        if not bridge:
            from pipeline_bridge import PipelineBridge
            bridge = PipelineBridge(mode="hybrid")
        result = bridge.process(
            "Federal Reserve raises interest rates by 50 basis points",
            source="test",
            market_price=50000.0,
        )
        assert result is not None, "No result"
        assert len(result.reasoning) > 0, "No reasoning chain"
        return True
    check("PipelineBridge.process() end-to-end", _test_bridge_process)

    # ================================================================
    # SECTION 4: Full Bootstrap
    # ================================================================
    print("\n--- Section 4: Full Bootstrap ---")
    
    def _test_bootstrap():
        import os
        os.environ["TRANSFORMERS_OFFLINE"] = "1"  # Prevent model downloads
        from main import bootstrap
        comps = bootstrap(asset="BTC", verbose=False)
        loaded = sum(1 for v in comps.values() if v is not None and v != {})
        assert loaded >= 8, f"Only {loaded} modules loaded (need at least 8)"
        assert comps.get("engine") is not None, "Core engine not loaded"
        assert comps.get("decision") is not None, "DecisionEngine not loaded"
        assert comps.get("execution") is not None, "ExecutionNexus not loaded"
        assert comps.get("pipeline") is not None, "Pipeline not loaded"
        del os.environ["TRANSFORMERS_OFFLINE"]
        return True
    check("bootstrap() loads all modules", _test_bootstrap)

    # ================================================================
    # SUMMARY
    # ================================================================
    total = results["passed"] + results["failed"] + results["warned"]
    print("\n" + "=" * 70)
    print(f"  RESULTS: {results['passed']}/{total} passed, "
          f"{results['failed']} failed, {results['warned']} warnings")
    print("=" * 70)
    
    if results["failed"] == 0:
        print(f"\n  {PASS} ALL CHECKS PASSED — System is fully wired end-to-end")
    else:
        print(f"\n  {FAIL} {results['failed']} checks failed — see above for details")
    
    return results["failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
