"""
COGNITIVE MARKET ENGINE — Unified Entry Point

Bootstraps all modules and wires them together:
  Engine (NLP → Cognitive → Collision → Signal) +
  Storage + Feedback + Scenarios + Hidden Truth +
  Multi-Asset + Streaming Pipeline + Dashboard

Usage:
    python main.py                       # Interactive demo
    python main.py --live                # Live monitoring
    python main.py --dashboard           # Start dashboard
    python main.py --test                # Run validation suite
    python main.py --news "Breaking..."  # Process single news
"""

import os
import sys
import argparse
from datetime import datetime

# Ensure project root is on path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(ROOT_DIR, ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv not installed — rely on system env vars

# Setup centralized logging early
from config.logging_config import setup_logging, get_logger

_log = get_logger("main")


# ============================================================================
# LAZY MODULE LOADING (graceful — every module is optional)
# ============================================================================

def _try_import(label, import_fn):
    """Import a module silently, return (module, True) or (None, False)."""
    try:
        mod = import_fn()
        return mod, True
    except Exception as e:
        print(f"  [{label}] unavailable: {e}")
        return None, False


def bootstrap(asset="BTC", enable_logging=False, verbose=True):
    """
    Create and wire every sub-system.

    Returns:
        dict with keys: engine, nlp, aggregator, storage, feedback,
             scenario, hidden_truth, multi_asset, pipeline, event_bus
    """
    components = {}

    # Initialize logging
    log_level = "DEBUG" if verbose else "INFO"
    log_file = os.path.join(ROOT_DIR, "data", "logs", "engine.log") if enable_logging else None
    setup_logging(level=log_level, log_file=log_file)
    _log.info("Bootstrap started (asset=%s)", asset)

    if verbose:
        print("\n" + "=" * 70)
        print("  COGNITIVE MARKET ENGINE — Bootstrap")
        print("=" * 70)

    # ---- 1. NLP Engine ---------------------------------------------------
    nlp_parser = None
    DeepNLPParser, ok = _try_import("NLP", lambda: __import__(
        "nlp_engine.deep_nlp_parser", fromlist=["DeepNLPParser"]).DeepNLPParser)
    if ok:
        try:
            nlp_parser = DeepNLPParser(use_transformers=False)
            if verbose:
                print("  [OK] NLP Engine loaded (DeepNLPParser)")
        except Exception as e:
            if verbose:
                print(f"  [--] NLP Engine init failed: {e}")
    components["nlp"] = nlp_parser

    # ---- 2. Storage -------------------------------------------------------
    storage = None
    DatabaseManager, ok = _try_import("Storage", lambda: __import__(
        "storage.database", fromlist=["DatabaseManager"]).DatabaseManager)
    if ok:
        try:
            storage = DatabaseManager()
            if verbose:
                print("  [OK] Storage connected (SQLite)")
        except Exception as e:
            if verbose:
                print(f"  [--] Storage init failed: {e}")
    components["storage"] = storage

    # ---- 3. Feedback Loop --------------------------------------------------
    feedback = None
    FeedbackLoop, ok = _try_import("Feedback", lambda: __import__(
        "learning.feedback_loop", fromlist=["FeedbackLoop"]).FeedbackLoop)
    if ok:
        try:
            feedback = FeedbackLoop(storage=storage)
            if verbose:
                print("  [OK] Feedback loop active")
        except Exception as e:
            if verbose:
                print(f"  [--] Feedback init failed: {e}")
    components["feedback"] = feedback

    # ---- 4. Core Cognitive Engine -----------------------------------------
    from engine.cognitive_market_system import CognitiveMarketSystem
    engine = CognitiveMarketSystem(
        asset=asset,
        enable_logging=enable_logging,
        nlp_parser=nlp_parser,
        storage=storage,
        feedback_loop=feedback,
    )
    if verbose:
        print(f"  [OK] Cognitive Engine initialized (asset={asset})")
    components["engine"] = engine

    # ---- 5. Scenario Engine -----------------------------------------------
    scenario = None
    ScenarioGenerator, ok = _try_import("Scenario", lambda: __import__(
        "scenario_engine.scenario_generator", fromlist=["ScenarioGenerator"]).ScenarioGenerator)
    if ok:
        try:
            kg = None
            try:
                from storage.knowledge_graph import KnowledgeGraph
                kg = KnowledgeGraph()
            except Exception:
                pass
            scenario = ScenarioGenerator(knowledge_graph=kg)
            if verbose:
                print("  [OK] Scenario Engine ready")
        except Exception as e:
            if verbose:
                print(f"  [--] Scenario init failed: {e}")
    components["scenario"] = scenario

    # ---- 6. Hidden Truth --------------------------------------------------
    hidden_truth = {}
    for name, path, cls_name in [
        ("CrossSource", "hidden_truth.cross_source_analyzer", "CrossSourceAnalyzer"),
        ("Omission", "hidden_truth.omission_detector", "OmissionDetector"),
        ("Timing", "hidden_truth.timing_analyzer", "TimingAnalyzer"),
        ("Narrative", "hidden_truth.narrative_tracker", "NarrativeTracker"),
    ]:
        cls, ok = _try_import(name, lambda p=path, c=cls_name: getattr(
            __import__(p, fromlist=[c]), c))
        if ok:
            try:
                hidden_truth[name.lower()] = cls()
            except Exception:
                pass
    if hidden_truth and verbose:
        print(f"  [OK] Hidden Truth modules: {list(hidden_truth.keys())}")
    components["hidden_truth"] = hidden_truth or None

    # ---- 7. Multi-Asset ----------------------------------------------------
    multi_asset = {}
    for name, path, cls_name in [
        ("Correlation", "multi_asset.correlation_engine", "CorrelationEngine"),
        ("Contagion", "multi_asset.contagion_model", "ContagionModel"),
    ]:
        cls, ok = _try_import(name, lambda p=path, c=cls_name: getattr(
            __import__(p, fromlist=[c]), c))
        if ok:
            try:
                multi_asset[name.lower()] = cls()
            except Exception:
                pass
    if multi_asset and verbose:
        print(f"  [OK] Multi-Asset modules: {list(multi_asset.keys())}")
    components["multi_asset"] = multi_asset or None

    # ---- 8. News Aggregator ------------------------------------------------
    aggregator = None
    NewsAggregator, ok = _try_import("Aggregator", lambda: __import__(
        "news_ingestion.news_aggregator", fromlist=["NewsAggregator"]).NewsAggregator)
    if ok:
        try:
            api_key = os.environ.get("NEWSAPI_KEY", "")
            aggregator = NewsAggregator(
                newsapi_key=api_key if api_key else None,
                enable_newsapi=bool(api_key),
                enable_gdelt=True,
                enable_rss=True,
            )
            if verbose:
                print("  [OK] NewsAggregator ready")
        except Exception as e:
            if verbose:
                print(f"  [--] Aggregator init failed: {e}")
    components["aggregator"] = aggregator

    # ---- 9. Execution Engine (loaded before pipeline so pipeline can use it)
    execution = None
    try:
        from execution.execution_nexus import ExecutionNexus
        execution = ExecutionNexus()
        if verbose:
            print("  [OK] Execution Engine ready")
    except Exception as e:
        if verbose:
            print(f"  [--] Execution init failed: {e}")
    components["execution"] = execution

    # ---- 10. Market Data Feed ---------------------------------------------
    market_data = None
    try:
        from data.market_data_feed import MarketDataFeed
        market_data = MarketDataFeed(use_live=True, cache_ttl_seconds=30)
        if verbose:
            print("  [OK] Market Data Feed connected")
    except Exception as e:
        if verbose:
            print(f"  [--] Market Data Feed init failed: {e}")
    components["market_data"] = market_data

    # ---- 11. Streaming Pipeline + EventBus + DecisionEngine ----------------
    event_bus = None
    pipeline = None
    decision = None
    try:
        from streaming.event_bus import EventBus
        from streaming.pipeline import StreamingPipeline

        # Initialize DecisionEngine
        try:
            from decision_system.decision_engine import DecisionEngine
            decision = DecisionEngine(asset=asset)
            if verbose:
                print("  [OK] DecisionEngine initialized")
        except Exception as e:
            if verbose:
                print(f"  [--] DecisionEngine init failed: {e}")

        event_bus = EventBus()
        pipeline = StreamingPipeline(
            event_bus=event_bus,
            nlp_engine=nlp_parser,
            cognitive_system=engine,
            scenario_engine=scenario,
            hidden_truth=hidden_truth or None,
            storage=storage,
            execution_engine=execution,
            decision_engine=decision,
        )
        if verbose:
            print("  [OK] Streaming Pipeline & EventBus wired (Decision + Execution connected)")
    except Exception as e:
        if verbose:
            print(f"  [--] Pipeline init failed: {e}")
    components["event_bus"] = event_bus
    components["pipeline"] = pipeline
    components["decision"] = decision

    if verbose:
        ok_count = sum(1 for v in components.values()
                       if v is not None and v != {})
        print(f"\n  Bootstrap complete: {ok_count}/{len(components)} modules loaded")
        print("=" * 70 + "\n")

    return components


# ============================================================================
# DEMO / INTERACTIVE MODE
# ============================================================================

def interactive_demo(components):
    """Run an interactive demo processing sample news events."""
    engine = components["engine"]
    pipeline = components.get("pipeline")
    scenario = components.get("scenario")

    print("\n" + "=" * 70)
    print("  INTERACTIVE DEMO")
    print("=" * 70)

    sample_events = [
        {
            "source": "Reuters",
            "text": (
                "Federal Reserve signals unexpected dovish pivot in interest rate "
                "policy. Fed officials indicate potential rate cuts beginning next "
                "quarter due to moderating inflation pressures. Treasury yields "
                "decline sharply. Equity markets surge."
            ),
            "assets": ["BTC", "ETH", "SPY"],
            "macro": ["rates", "monetary-policy", "inflation"],
        },
        {
            "source": "Bloomberg",
            "text": (
                "Major financial institution announces sudden failure with $50 "
                "billion in losses. Regulators place bank into receivership. "
                "Credit markets freeze. Contagion risk assessment ongoing."
            ),
            "assets": ["BTC", "SPY"],
            "macro": ["systemic-risk", "credit"],
        },
        {
            "source": "CNBC",
            "text": (
                "SEC announces new regulatory framework for digital assets. "
                "The guidance could be positive or negative depending on "
                "interpretation. Industry experts are divided."
            ),
            "assets": ["BTC", "ETH"],
            "macro": ["regulation"],
        },
    ]

    signals = []
    for i, evt in enumerate(sample_events, 1):
        print(f"\n--- Event {i}: {evt['source']} ---")
        print(f"    {evt['text'][:80]}...")

        signal = engine.process_news_event(
            source_id=evt["source"],
            raw_text=evt["text"],
            asset_scope=evt["assets"],
            macro_scope=evt["macro"],
        )
        signals.append(signal)

        print(f"  -> Signal: {signal.signal_type.value} | "
              f"Direction: {signal.direction} | "
              f"Strength: {signal.strength:.2f} | "
              f"Confidence: {signal.confidence.name}")

        # Generate scenarios if available
        if scenario:
            tree = scenario.generate({
                "raw_text": evt["text"],
                "certainty_score": 0.5,
                "ambiguity_score": 0.3,
            })
            print(f"  -> Scenarios: {tree.expected_direction}, "
                  f"tail_risk={tree.tail_risk_probability:.2f}")

    print(f"\n[SUMMARY] Processed {len(sample_events)} events, "
          f"generated {len([s for s in signals if s.signal_type.value != 'no_trade'])} "
          f"tradable signals")

    status = engine.get_system_status()
    print(f"\n[STATUS]")
    for k, v in status.items():
        print(f"  {k}: {v}")


def process_single_news(components, text):
    """Process a single news string."""
    engine = components["engine"]
    signal = engine.process_news_event(
        source_id="CLI",
        raw_text=text,
        asset_scope=["BTC"],
        macro_scope=["general"],
    )
    print(f"\nSignal: {signal.signal_type.value}")
    print(f"Direction: {signal.direction}")
    print(f"Strength: {signal.strength:.3f}")
    print(f"Confidence: {signal.confidence.name}")
    print(f"Reason: {signal.reason}")


def run_tests(components):
    """Run the existing test suite."""
    print("\n[TEST] Running validation suite ...\n")
    try:
        from simple_test import main as simple_main
        simple_main()
    except Exception as e:
        print(f"[TEST] simple_test failed: {e}")

    try:
        from test_cognitive_system import run_all_tests
        run_all_tests()
    except Exception as e:
        print(f"[TEST] test_cognitive_system failed: {e}")


def launch_dashboard(components):
    """Launch the Streamlit dashboard."""
    try:
        from dashboard.app import create_dashboard
        create_dashboard(
            pipeline=components.get("pipeline"),
            feedback_loop=components.get("feedback"),
            correlation_engine=(components.get("multi_asset") or {}).get("correlation"),
            storage=components.get("storage"),
        )
    except ImportError:
        print("[DASHBOARD] Streamlit not installed. Run: pip install streamlit")
        print("            Then: streamlit run dashboard/app.py")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Cognitive Market Engine — unified entry point"
    )
    parser.add_argument("--live", action="store_true",
                        help="Start live market monitoring")
    parser.add_argument("--dashboard", action="store_true",
                        help="Launch Streamlit dashboard")
    parser.add_argument("--test", action="store_true",
                        help="Run validation suite")
    parser.add_argument("--news", type=str, default=None,
                        help="Process a single news string")
    parser.add_argument("--asset", type=str, default="BTC",
                        help="Target asset (default: BTC)")
    parser.add_argument("--verbose", action="store_true", default=True,
                        help="Verbose output")
    args = parser.parse_args()

    if args.live:
        # Delegate to run_live.py
        from run_live import main as live_main
        live_main()
        return

    if args.dashboard:
        components = bootstrap(asset=args.asset, verbose=args.verbose)
        launch_dashboard(components)
        return

    if args.test:
        components = bootstrap(asset=args.asset, verbose=False)
        run_tests(components)
        return

    if args.news:
        components = bootstrap(asset=args.asset, verbose=False)
        process_single_news(components, args.news)
        return

    # Default: interactive demo
    components = bootstrap(asset=args.asset, verbose=args.verbose)
    interactive_demo(components)


if __name__ == "__main__":
    main()
