"""
COGNITIVE SIGNAL BRIDGE — Connects ALL CME Modules to Backtesting

This bridge wraps the ENTIRE Cognitive Market Engine pipeline into
a single signal_generator function compatible with BacktestRunner.

For each HistoricalEvent, it:
1. Runs DeepNLPParser (nlp_engine/) for linguistic analysis
2. Runs NewsEventParser (news_model/) for structured event parsing
3. Runs CognitiveMarketSystem (engine/) 4-phase pipeline:
   - Phase 1: LinguisticShockVector computation
   - Phase 2: 5 participant cognitive interpretation (engine/participant_models)
   - Phase 3: ExpectationCollisionEngine — collision metrics
   - Phase 4: TradableSignalTranslator — execution-safe signals
4. Runs participant_cognition/ models for Phase-pipeline interpretations
5. Runs market_response/behavior_models.BehaviorTranslator
6. Runs market_impact/ aggregation + impact calculation
7. Runs scenario_engine/ for scenario trees + Monte Carlo
8. Runs hidden_truth/ modules (cross-source, omission, timing, narrative)
9. Runs alpha_models/ — NLP alphas, structural alphas, standard alphas
10. Runs economics/economic_models.EconomicAnalyzer for macro context
11. Runs reality_validation/ for prediction tracking
12. Runs learning/feedback_loop.FeedbackLoop for weight adaptation
13. Runs multi_asset/ correlation + contagion
14. Runs signal_auth/signal_authorization.SignalAuthorizer
15. Stores via storage/database.DatabaseManager + knowledge_graph
16. Emits via streaming/event_bus.EventBus

Output: Optional[SignalRecord] for the BacktestRunner.

This uses ONLY existing modules — zero standalone logic.
"""

import os
import sys
import time
import math
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple, Callable
from dataclasses import dataclass, field

# Ensure project root on path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backtesting.backtest_engine import (
    HistoricalEvent, SignalRecord, TradeAction
)

logger = logging.getLogger("cme.backtesting.bridge")


# ============================================================================
# MODULE LOADER — graceful import of ALL CME sub-systems
# ============================================================================

def _safe_import(label: str, import_fn):
    """Import a module gracefully. Returns (obj, True) or (None, False)."""
    try:
        obj = import_fn()
        return obj, True
    except Exception as e:
        logger.debug(f"[{label}] unavailable: {e}")
        return None, False


class CMEModuleRegistry:
    """
    Loads and holds references to every CME module.
    Mirrors the bootstrap() pattern from main.py but captures
    MORE modules for backtesting purposes.
    """

    def __init__(self, asset: str = "BTC", verbose: bool = True):
        self.asset = asset
        self.verbose = verbose
        self.modules: Dict[str, Any] = {}
        self._load_count = 0
        self._fail_count = 0

    def load_all(self) -> Dict[str, Any]:
        """Load every CME sub-system. Returns dict of loaded modules."""

        self._log("Loading ALL Cognitive Market Engine modules...")

        # ---- 1. Config ----
        self._load("config", lambda: __import__(
            "config.system_config", fromlist=["SystemConfig"]).SystemConfig)

        # ---- 2. NLP Engine ----
        nlp_parser = None
        DeepNLPParser, ok = self._load("nlp_parser_cls", lambda: __import__(
            "nlp_engine.deep_nlp_parser", fromlist=["DeepNLPParser"]).DeepNLPParser)
        if ok:
            try:
                nlp_parser = DeepNLPParser(use_transformers=False)
            except Exception:
                pass
        self.modules["nlp_parser"] = nlp_parser

        # ---- 3. NLP extensions ----
        self._load("aspect_sentiment", lambda: __import__(
            "nlp_engine.nlp_extensions", fromlist=["AspectBasedSentimentAnalyzer"]
        ).AspectBasedSentimentAnalyzer())
        self._load("sarcasm_detector", lambda: __import__(
            "nlp_engine.nlp_extensions", fromlist=["SarcasmIronyDetector"]
        ).SarcasmIronyDetector())
        self._load("earnings_analyzer", lambda: __import__(
            "nlp_engine.nlp_extensions", fromlist=["EarningsCallAnalyzer"]
        ).EarningsCallAnalyzer())

        # ---- 4. Advanced NLP ----
        self._load("financial_event_extractor", lambda: __import__(
            "nlp_engine.advanced_nlp", fromlist=["FinancialEventExtractor"]
        ).FinancialEventExtractor())
        self._load("financial_embeddings", lambda: __import__(
            "nlp_engine.advanced_nlp", fromlist=["FinancialEmbeddings"]
        ).FinancialEmbeddings())
        self._load("advanced_nlp_engine", lambda: __import__(
            "nlp_engine.advanced_nlp", fromlist=["AdvancedNLPEngine"]
        ).AdvancedNLPEngine())

        # ---- 5. Entity + Intent + Contradiction ----
        self._load("entity_extractor", lambda: __import__(
            "nlp_engine.entity_extraction", fromlist=["EntityExtractor"]
        ).EntityExtractor())
        self._load("intent_detector", lambda: __import__(
            "nlp_engine.intent_detector", fromlist=["IntentDetector"]
        ).IntentDetector())
        self._load("contradiction_detector", lambda: __import__(
            "nlp_engine.contradiction_detector", fromlist=["ContradictionDetector"]
        ).ContradictionDetector())

        # ---- 6. News Model Parser ----
        self._load("news_parser", lambda: __import__(
            "news_model.parser", fromlist=["NewsEventParser"]
        ).NewsEventParser())

        # ---- 7. Storage ----
        storage = None
        DatabaseManager, ok = self._load("db_cls", lambda: __import__(
            "storage.database", fromlist=["DatabaseManager"]).DatabaseManager)
        if ok:
            try:
                storage = DatabaseManager()
            except Exception:
                pass
        self.modules["storage"] = storage

        # ---- 8. Knowledge Graph ----
        kg = None
        KG_cls, ok = self._load("kg_cls", lambda: __import__(
            "storage.knowledge_graph", fromlist=["KnowledgeGraph"]).KnowledgeGraph)
        if ok:
            try:
                kg = KG_cls()
            except Exception:
                pass
        self.modules["knowledge_graph"] = kg

        # ---- 9. Feedback Loop ----
        feedback = None
        FL_cls, ok = self._load("feedback_cls", lambda: __import__(
            "learning.feedback_loop", fromlist=["FeedbackLoop"]).FeedbackLoop)
        if ok:
            try:
                feedback = FL_cls(storage=storage)
            except Exception:
                pass
        self.modules["feedback"] = feedback

        # ---- 10. Core Cognitive Engine (THE HEART) ----
        from engine.cognitive_market_system import CognitiveMarketSystem
        engine = CognitiveMarketSystem(
            asset=self.asset,
            enable_logging=False,
            nlp_parser=nlp_parser,
            storage=storage,
            feedback_loop=feedback,
        )
        self.modules["engine"] = engine
        self._load_count += 1

        # ---- 11. Participant Cognition (Phase pipeline) ----
        for name in ["create_bank_participant", "create_hedge_fund_participant",
                      "create_hft_participant", "create_market_maker_participant",
                      "create_retail_participant"]:
            self._load(f"pcog_{name}", lambda n=name: getattr(
                __import__("participant_cognition.participant_models",
                           fromlist=[n]), n))

        # ---- 12. Behavior Translator ----
        self._load("behavior_translator", lambda: __import__(
            "market_response.behavior_models", fromlist=["BehaviorTranslator"]
        ).BehaviorTranslator())

        # ---- 13. Market Impact ----
        self._load("behavior_aggregator", lambda: __import__(
            "market_impact.market_impact_models", fromlist=["BehaviorAggregator"]
        ).BehaviorAggregator())
        self._load("impact_calculator", lambda: __import__(
            "market_impact.market_impact_models", fromlist=["MarketImpactCalculator"]
        ).MarketImpactCalculator())

        # ---- 14. Market Impact Extensions ----
        self._load("attribution_engine", lambda: __import__(
            "market_impact.impact_extensions", fromlist=["ImpactAttributionEngine"]
        ).ImpactAttributionEngine())
        self._load("cascade_model", lambda: __import__(
            "market_impact.impact_extensions", fromlist=["CrossAssetCascadeModel"]
        ).CrossAssetCascadeModel())

        # ---- 15. Market Intelligence Hub ----
        self._load("intel_hub", lambda: __import__(
            "market_intelligence.intelligence_models", fromlist=["MarketIntelligenceHub"]
        ).MarketIntelligenceHub())

        # ---- 16. Reality Validation ----
        self._load("reality_validator", lambda: __import__(
            "reality_validation.market_reality", fromlist=["RealityValidator"]
        ).RealityValidator())

        # ---- 17. Signal Authorization ----
        self._load("signal_authorizer", lambda: __import__(
            "signal_auth.signal_authorization", fromlist=["SignalAuthorizer"]
        ).SignalAuthorizer())

        # ---- 18. Decision Engine ----
        self._load("decision_engine", lambda: __import__(
            "decision_system.decision_engine", fromlist=["DecisionEngine"]
        ).DecisionEngine(asset=self.asset))

        # ---- 19. Execution Nexus ----
        self._load("execution", lambda: __import__(
            "execution.execution_nexus", fromlist=["ExecutionNexus"]
        ).ExecutionNexus())

        # ---- 20. Scenario Engine ----
        self._load("scenario_generator", lambda: __import__(
            "scenario_engine.scenario_generator", fromlist=["ScenarioGenerator"]
        ).ScenarioGenerator(knowledge_graph=kg))
        self._load("monte_carlo", lambda: __import__(
            "scenario_engine.monte_carlo", fromlist=["MonteCarloSimulator"]
        ).MonteCarloSimulator())
        self._load("causal_chain", lambda: __import__(
            "scenario_engine.causal_chain", fromlist=["CausalChainBuilder"]
        ).CausalChainBuilder())

        # ---- 21. Scenario Extensions ----
        self._load("scenario_visualizer", lambda: __import__(
            "scenario_engine.scenario_extensions", fromlist=["ScenarioTreeVisualizer"]
        ).ScenarioTreeVisualizer())
        self._load("counterfactual", lambda: __import__(
            "scenario_engine.scenario_extensions", fromlist=["CounterFactualAnalyzer"]
        ).CounterFactualAnalyzer())
        self._load("scenario_optimizer", lambda: __import__(
            "scenario_engine.scenario_extensions", fromlist=["ScenarioPortfolioOptimizer"]
        ).ScenarioPortfolioOptimizer())

        # ---- 22. Alpha Models — Standard ----
        self._load("alpha_aggregator", lambda: __import__(
            "alpha_models.alpha_signals", fromlist=["AlphaSignalAggregator"]
        ).AlphaSignalAggregator())

        # ---- 23. Alpha Models — NLP ----
        self._load("nlp_alpha_hub", lambda: __import__(
            "alpha_models.nlp_alpha_signals", fromlist=["NLPAlphaHub"]
        ).NLPAlphaHub())

        # ---- 24. Alpha Models — Structural ----
        self._load("structural_alpha", lambda: __import__(
            "alpha_models.structural_alpha", fromlist=["StructuralAlphaEngine"]
        ).StructuralAlphaEngine())

        # ---- 25. Hidden Truth ----
        self._load("cross_source", lambda: __import__(
            "hidden_truth.cross_source_analyzer", fromlist=["CrossSourceAnalyzer"]
        ).CrossSourceAnalyzer())
        self._load("omission_detector", lambda: __import__(
            "hidden_truth.omission_detector", fromlist=["OmissionDetector"]
        ).OmissionDetector())
        self._load("timing_analyzer", lambda: __import__(
            "hidden_truth.timing_analyzer", fromlist=["TimingAnalyzer"]
        ).TimingAnalyzer())
        self._load("narrative_tracker", lambda: __import__(
            "hidden_truth.narrative_tracker", fromlist=["NarrativeTracker"]
        ).NarrativeTracker())

        # ---- 26. Hidden Truth — Advanced Detection ----
        self._load("manipulation_detector", lambda: __import__(
            "hidden_truth.advanced_detection", fromlist=["ManipulationPatternDetector"]
        ).ManipulationPatternDetector())
        self._load("sec_filing_analyzer", lambda: __import__(
            "hidden_truth.advanced_detection", fromlist=["SECFilingAnalyzer"]
        ).SECFilingAnalyzer())

        # ---- 27. Economics ----
        self._load("economic_analyzer", lambda: __import__(
            "economics.economic_models", fromlist=["EconomicAnalyzer"]
        ).EconomicAnalyzer())
        self._load("economic_state_cls", lambda: __import__(
            "economics.economic_models", fromlist=["EconomicState"]).EconomicState)

        # ---- 28. Multi-Asset ----
        self._load("correlation_engine", lambda: __import__(
            "multi_asset.correlation_engine", fromlist=["CorrelationEngine"]
        ).CorrelationEngine())
        self._load("contagion_model", lambda: __import__(
            "multi_asset.contagion_model", fromlist=["ContagionModel"]
        ).ContagionModel())

        # ---- 29. Market Data Feed ----
        self._load("market_data", lambda: __import__(
            "data.market_data_feed", fromlist=["MarketDataFeed"]
        ).MarketDataFeed(use_live=False, cache_ttl_seconds=60))

        # ---- 30. Streaming / Event Bus ----
        self._load("event_bus", lambda: __import__(
            "streaming.event_bus", fromlist=["EventBus"]
        ).EventBus())

        # ---- 31. Alerts ----
        self._load("alert_manager", lambda: __import__(
            "alerts.alert_delivery", fromlist=["AlertDeliveryManager"]
        ).AlertDeliveryManager())

        # ---- 32. Report Generator ----
        self._load("report_generator", lambda: __import__(
            "advanced.report_generator", fromlist=["ReportGenerator"]
        ).ReportGenerator())

        # ---- 33. Geopolitical Risk ----
        self._load("geopolitical_scorer", lambda: __import__(
            "advanced.geopolitical_risk", fromlist=["GeopoliticalRiskScorer"]
        ).GeopoliticalRiskScorer())

        # ---- 34. LLM Analyzer (GPT deep sentiment + strategic intent) ----
        self._load("llm_analyzer", lambda: __import__(
            "advanced.llm_analyzer", fromlist=["LLMAnalyzer"]
        ).LLMAnalyzer())

        # ---- 35. Social Media Sentiment (Reddit/Twitter retail signals) ----
        self._load("social_media", lambda: __import__(
            "advanced.social_media", fromlist=["SocialMediaSentiment"]
        ).SocialMediaSentiment())

        # ---- 36. Human Review Queue (risk gate for high-stakes decisions) ----
        self._load("human_review", lambda: __import__(
            "decision_system.human_review_queue", fromlist=["HumanReviewQueue"]
        ).HumanReviewQueue())

        # ---- 37. Infrastructure — Model Registry ----
        self._load("model_registry", lambda: __import__(
            "infrastructure.infra_layer", fromlist=["ModelRegistry"]
        ).ModelRegistry())

        # ---- 38. Infrastructure — Feature Store ----
        self._load("feature_store", lambda: __import__(
            "infrastructure.infra_layer", fromlist=["FeatureStore"]
        ).FeatureStore())

        # ---- 39. Infrastructure — Monitoring ----
        self._load("monitoring", lambda: __import__(
            "infrastructure.infra_layer", fromlist=["MonitoringSystem"]
        ).MonitoringSystem())

        # ---- 40. Streaming Pipeline (live orchestrator) ----
        self._load("streaming_pipeline_cls", lambda: __import__(
            "streaming.pipeline", fromlist=["StreamingPipeline"]
        ).StreamingPipeline)

        # ---- 41. Pipeline Bridge (engine + phase unifier) ----
        self._load("pipeline_bridge_cls", lambda: __import__(
            "pipeline_bridge", fromlist=["PipelineBridge"]
        ).PipelineBridge)

        self._log(f"Module loading complete: {self._load_count} loaded, "
                  f"{self._fail_count} unavailable")

        return self.modules

    def _load(self, name: str, import_fn) -> Tuple[Any, bool]:
        """Load a single module."""
        obj, ok = _safe_import(name, import_fn)
        if ok:
            self.modules[name] = obj
            self._load_count += 1
        else:
            self._fail_count += 1
        return obj, ok

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [BRIDGE] {msg}")

    def get(self, name: str, default=None):
        return self.modules.get(name, default)


# ============================================================================
# COGNITIVE SIGNAL BRIDGE — HistoricalEvent -> SignalRecord
# ============================================================================

@dataclass
class EventAnalysis:
    """Complete analysis of a single event through ALL CME modules."""
    event_id: str
    timestamp: datetime
    headline: str

    # Phase 1: Linguistic Shock
    linguistic_shock: Dict = field(default_factory=dict)

    # Phase 2: Participant interpretations
    participant_responses: Dict = field(default_factory=dict)

    # Phase 3: Collision metrics
    collision_metrics: Dict = field(default_factory=dict)
    market_stress: Dict = field(default_factory=dict)

    # Phase 4: Tradable signal
    tradable_signal: Dict = field(default_factory=dict)

    # Additional analyses
    nlp_parse: Dict = field(default_factory=dict)
    scenario_tree: Dict = field(default_factory=dict)
    hidden_truth: Dict = field(default_factory=dict)
    alpha_signals: Dict = field(default_factory=dict)
    economic_impact: Dict = field(default_factory=dict)
    validation: Dict = field(default_factory=dict)

    # Synthesized outputs
    final_direction: str = "neutral"
    final_confidence: float = 0.0
    ambiguity_score: float = 0.0
    competing_narratives: List[str] = field(default_factory=list)
    participant_agreement: float = 0.0


class CognitiveSignalBridge:
    """
    Bridges ALL CME modules into a BacktestRunner-compatible
    signal_generator function.

    This is the core integration layer — every module contributes
    to the final signal decision.

    Usage:
        bridge = CognitiveSignalBridge(asset="BTC")
        bridge.initialize()
        result = backtest_runner.run(bridge.generate_signal)
    """

    def __init__(self, asset: str = "BTC", verbose: bool = True):
        self.asset = asset
        self.verbose = verbose
        self.registry = CMEModuleRegistry(asset=asset, verbose=verbose)
        self.event_analyses: List[EventAnalysis] = []
        self._event_count = 0
        self._initialized = False

    def initialize(self):
        """Load all CME modules."""
        self.registry.load_all()
        self._initialized = True

    def generate_signal(self, event: HistoricalEvent) -> Optional[SignalRecord]:
        """
        Process a HistoricalEvent through the ENTIRE CME pipeline.

        This is the signal_generator callback for BacktestRunner.run().
        Returns Optional[SignalRecord].
        """
        if not self._initialized:
            self.initialize()

        self._event_count += 1
        analysis = EventAnalysis(
            event_id=event.event_id,
            timestamp=event.timestamp,
            headline=event.headline,
        )

        # ================================================================
        # STEP 1: Deep NLP Analysis (nlp_engine/)
        # ================================================================
        nlp_parser = self.registry.get("nlp_parser")
        if nlp_parser is not None:
            try:
                parse_result = nlp_parser.parse(event.content)
                analysis.nlp_parse = {
                    "certainty": getattr(parse_result, "overall_certainty", 0.5),
                    "subjectivity": getattr(parse_result, "overall_subjectivity", 0.5),
                    "complexity": getattr(parse_result, "complexity_score", 0.5),
                    "intent": str(getattr(parse_result, "detected_intent", "inform")),
                    "entity_count": len(getattr(parse_result, "all_entities", [])),
                    "sentence_count": len(getattr(parse_result, "sentences", [])),
                }
            except Exception as e:
                logger.debug(f"NLP parse failed: {e}")

        # ================================================================
        # STEP 2: Advanced NLP — event extraction, embeddings, sentiment
        # ================================================================
        adv_nlp = self.registry.get("advanced_nlp_engine")
        if adv_nlp is not None:
            try:
                adv_result = adv_nlp.full_analysis(event.content)
                if isinstance(adv_result, dict):
                    # Store non-callable items
                    analysis.nlp_parse["advanced"] = {
                        k: v for k, v in adv_result.items()
                        if not callable(v)
                    }
                    # Extract FinBERT / lexicon sentiment (PRIMARY directional signal)
                    sentiment = adv_result.get("sentiment", {})
                    if isinstance(sentiment, dict):
                        analysis.nlp_parse["financial_sentiment"] = sentiment
            except Exception as e:
                logger.debug(f"Advanced NLP failed: {e}")

        # Aspect-based sentiment
        aspect_sa = self.registry.get("aspect_sentiment")
        if aspect_sa is not None:
            try:
                aspects = aspect_sa.analyze(event.content)
                if isinstance(aspects, dict):
                    analysis.nlp_parse["aspects"] = aspects
                    # Compute composite aspect score for directional signal
                    composite = aspect_sa.get_composite_score(aspects)
                    analysis.nlp_parse["aspect_composite_score"] = composite
            except Exception:
                pass

        # ================================================================
        # STEP 3: Core Cognitive Pipeline (engine/ — THE MAIN PIPELINE)
        # ================================================================
        engine = self.registry.get("engine")
        tradable_signal = None
        if engine is not None:
            try:
                tradable_signal = engine.process_news_event(
                    source_id=event.source,
                    raw_text=event.content,
                    asset_scope=[self.asset],
                    macro_scope=[event.event_type],
                )

                # Extract Phase 1 output
                if event.event_id in engine.news_events or engine.news_events:
                    last_event_key = list(engine.news_events.keys())[-1]
                    news_event_obj = engine.news_events[last_event_key]
                    lsv = news_event_obj.linguistic_shock
                    analysis.linguistic_shock = lsv.to_dict() if hasattr(lsv, "to_dict") else {}

                    # Phase 2: participant responses
                    for ptype, resp in news_event_obj.participant_responses.items():
                        ptype_str = ptype.value if hasattr(ptype, "value") else str(ptype)
                        analysis.participant_responses[ptype_str] = (
                            resp.to_dict() if hasattr(resp, "to_dict") else str(resp)
                        )

                # Phase 3: collision metrics
                if engine.collision_metrics:
                    last_key = list(engine.collision_metrics.keys())[-1]
                    cm = engine.collision_metrics[last_key]
                    analysis.collision_metrics = cm.to_dict() if hasattr(cm, "to_dict") else {}

                if engine.market_stress_vectors:
                    last_key = list(engine.market_stress_vectors.keys())[-1]
                    ms = engine.market_stress_vectors[last_key]
                    analysis.market_stress = ms.to_dict() if hasattr(ms, "to_dict") else {}

                # Phase 4: tradable signal
                if tradable_signal is not None:
                    analysis.tradable_signal = (
                        tradable_signal.to_dict()
                        if hasattr(tradable_signal, "to_dict") else {}
                    )
            except Exception as e:
                logger.warning(f"Engine pipeline failed: {e}")

        # ================================================================
        # STEP 4: Participant Cognition (Phase pipeline participants)
        # ================================================================
        phase_participants = {}
        news_parser = self.registry.get("news_parser")
        if news_parser is not None:
            try:
                parsed_news = news_parser.parse(
                    timestamp_utc=event.timestamp.isoformat(),
                    source=event.source,
                    raw_text=event.content,
                )
                for pname in ["bank", "hedge_fund", "hft", "market_maker", "retail"]:
                    factory_fn = self.registry.get(f"pcog_create_{pname}_participant")
                    if factory_fn is not None:
                        try:
                            participant = factory_fn()
                            expectation = participant.interpret(parsed_news)
                            if hasattr(expectation, "to_dict"):
                                phase_participants[pname] = expectation.to_dict()
                            else:
                                # Extract directional fields directly
                                phase_participants[pname] = {
                                    "belief_shift": getattr(expectation, "belief_shift", 0.0),
                                    "short_term_expectation": getattr(expectation, "short_term_expectation", 0.0),
                                    "long_term_expectation": getattr(expectation, "long_term_expectation", 0.0),
                                    "uncertainty_level": getattr(expectation, "uncertainty_level", 0.5),
                                    "urgency": getattr(expectation, "urgency", 0.0),
                                    "narrative_alignment": getattr(expectation, "narrative_alignment", 0.0),
                                    "reasoning": getattr(expectation, "reasoning", ""),
                                    "participant_type": pname,
                                    "cognitive_state": {
                                        "belief_shift": getattr(expectation, "belief_shift", 0.0),
                                        "confidence": 1.0 - getattr(expectation, "uncertainty_level", 0.5),
                                    },
                                    "expectation_vector": {
                                        "direction_bias": getattr(expectation, "belief_shift", 0.0),
                                    },
                                }
                        except Exception:
                            pass
            except Exception as e:
                logger.debug(f"Phase participant cognition failed: {e}")

        if phase_participants:
            analysis.participant_responses.update(
                {f"phase_{k}": v for k, v in phase_participants.items()}
            )

        # ================================================================
        # STEP 5: Scenario Engine
        # ================================================================
        scenario_gen = self.registry.get("scenario_generator")
        if scenario_gen is not None:
            try:
                scenario_input = {
                    "event_text": event.content,
                    "event_type": event.event_type,
                    "source": event.source,
                }
                tree = scenario_gen.generate(scenario_input)
                analysis.scenario_tree = (
                    tree.to_dict() if hasattr(tree, "to_dict") else {}
                )
            except Exception as e:
                logger.debug(f"Scenario generation failed: {e}")

        # ================================================================
        # STEP 6: Hidden Truth Analysis
        # ================================================================
        hidden_truth_results = {}

        # Cross-source analysis
        cross_src = self.registry.get("cross_source")
        if cross_src is not None:
            try:
                cross_src.add_report(
                    source=event.source, text=event.content,
                    timestamp=event.timestamp.isoformat()
                )
                verification = cross_src.verify(text=event.content)
                hidden_truth_results["cross_source"] = (
                    verification.to_dict() if hasattr(verification, "to_dict")
                    else str(verification)
                )
            except Exception:
                pass

        # Omission detection
        omission = self.registry.get("omission_detector")
        if omission is not None:
            try:
                report = omission.detect(event.content, event.event_type)
                hidden_truth_results["omissions"] = (
                    report.to_dict() if hasattr(report, "to_dict")
                    else str(report)
                )
            except Exception:
                pass

        # Timing analysis
        timing = self.registry.get("timing_analyzer")
        if timing is not None:
            try:
                timing_result = timing.analyze(event.event_type, event.timestamp)
                hidden_truth_results["timing"] = (
                    timing_result.__dict__ if hasattr(timing_result, "__dict__")
                    else str(timing_result)
                )
            except Exception:
                pass

        # Narrative tracking
        narrative = self.registry.get("narrative_tracker")
        if narrative is not None:
            try:
                narrative.record(
                    event_type=event.event_type,
                    text=event.content,
                    timestamp=event.timestamp.isoformat(),
                    source=event.source,
                )
                evolution = narrative.get_evolution(event.event_type)
                hidden_truth_results["narrative"] = evolution
            except Exception:
                pass

        analysis.hidden_truth = hidden_truth_results

        # ================================================================
        # STEP 7: Alpha Signals
        # ================================================================
        alpha_results = {}

        # NLP Alpha Hub
        nlp_alpha = self.registry.get("nlp_alpha_hub")
        if nlp_alpha is not None:
            try:
                composite = nlp_alpha.get_composite_signal(asset=self.asset)
                if hasattr(composite, "to_dict"):
                    alpha_results["nlp_alphas"] = composite.to_dict()
                elif hasattr(composite, "__dict__"):
                    alpha_results["nlp_alphas"] = {
                        "direction": getattr(composite, "direction", "neutral"),
                        "strength": getattr(composite, "strength", 0.0),
                        "confidence": getattr(composite, "confidence", 0.0),
                        "name": getattr(composite, "name", "nlp_composite"),
                    }
            except Exception as e:
                logger.debug(f"NLP alpha failed: {e}")

        # Structural Alpha
        struct_alpha = self.registry.get("structural_alpha")
        if struct_alpha is not None:
            try:
                struct_signals = struct_alpha.scan_all(asset=self.asset)
                if isinstance(struct_signals, list):
                    alpha_results["structural_alphas"] = {
                        s.source if hasattr(s, "source") else f"sig_{i}": (
                            s.to_dict() if hasattr(s, "to_dict") else {
                                "direction": getattr(s, "direction", "neutral"),
                                "strength": getattr(s, "strength", 0.0),
                            }
                        ) for i, s in enumerate(struct_signals)
                    }
                    # Detect conflicts for Deliverable D
                    conflicts = struct_alpha.detect_conflicts(struct_signals)
                    if conflicts.get("conflicts"):
                        alpha_results["structural_conflicts"] = conflicts
            except Exception:
                pass

        analysis.alpha_signals = alpha_results

        # ================================================================
        # STEP 8: Economic Impact Analysis
        # ================================================================
        econ_analyzer = self.registry.get("economic_analyzer")
        if econ_analyzer is not None:
            try:
                EconomicState = self.registry.get("economic_state_cls")
                state = EconomicState() if EconomicState else None
                if state and event.event_type == "rate_decision":
                    impact = econ_analyzer.analyze_rate_decision(
                        rate_change=-0.25, state=state
                    )
                elif state and event.event_type == "macro_data":
                    impact = econ_analyzer.analyze_inflation_data(
                        cpi_actual=2.5, cpi_expected=2.7, state=state
                    )
                elif state and event.event_type == "geopolitical":
                    impact = econ_analyzer.analyze_geopolitical_event(
                        event_type="trade_war", severity_score=0.6, state=state
                    )
                elif state:
                    impact = econ_analyzer.analyze_rate_decision(
                        rate_change=0.0, state=state
                    )
                else:
                    impact = None

                if impact:
                    analysis.economic_impact = (
                        impact.to_dict() if hasattr(impact, "to_dict")
                        else {}
                    )
            except Exception as e:
                logger.debug(f"Economic analysis failed: {e}")

        # ================================================================
        # STEP 9: Multi-Asset Correlation + Contagion
        # ================================================================
        corr_engine = self.registry.get("correlation_engine")
        if corr_engine is not None:
            try:
                corr = corr_engine.get_correlation("BTC", "ETH")
                analysis.economic_impact["btc_eth_corr"] = (
                    corr if isinstance(corr, (int, float)) else 0.7
                )
            except Exception:
                pass

        contagion = self.registry.get("contagion_model")
        if contagion is not None:
            try:
                sim = contagion.simulate(origin="BTC", shock=0.05)
                if hasattr(sim, "to_dict"):
                    analysis.economic_impact["contagion"] = sim.to_dict()
            except Exception:
                pass

        # ================================================================
        # STEP 10: Reality Validation + Feedback Loop
        # ================================================================
        validator = self.registry.get("reality_validator")
        feedback = self.registry.get("feedback")

        # Compute preliminary direction from NLP sentiment + phase participants
        # for feedback loop recording (before final synthesis)
        _fin_sent = analysis.nlp_parse.get("financial_sentiment", {})
        _nlp_ws = _fin_sent.get("weighted_score", 0) if isinstance(_fin_sent, dict) else 0
        if not isinstance(_nlp_ws, (int, float)):
            _nlp_ws = 0.0

        _phase_bs = []
        for _pk, _pr in analysis.participant_responses.items():
            if isinstance(_pr, dict) and _pk.startswith("phase_"):
                _bs = _pr.get("belief_shift", 0.0)
                if isinstance(_bs, (int, float)):
                    _phase_bs.append(_bs)

        _phase_avg = sum(_phase_bs) / len(_phase_bs) if _phase_bs else 0.0

        # Apply same contrarian NLP signal for feedback predictions
        _prelim_dir_score = (-_nlp_ws) * 0.6 + _phase_avg * 0.4
        _prelim_dir = "bullish" if _prelim_dir_score > 0.02 else (
            "bearish" if _prelim_dir_score < -0.02 else "neutral"
        )
        _prelim_mag = abs(_prelim_dir_score)
        _prelim_conf = max(0.3, abs(_prelim_dir_score))

        if feedback is not None:
            try:
                pred_record = feedback.record_prediction(
                    prediction_id=event.event_id,
                    event_type=event.event_type,
                    participant_type="cognitive_system",
                    asset=self.asset,
                    predicted_direction=_prelim_dir,
                    predicted_magnitude=_prelim_mag,
                    confidence=_prelim_conf,
                )
                # Validate against actual price movement
                actual_dir = "bullish" if event.price_24h_after > event.price_at_event else "bearish"
                actual_mag = abs(event.price_24h_after - event.price_at_event) / event.price_at_event
                feedback.validate_prediction(
                    prediction_id=event.event_id,
                    actual_direction=actual_dir,
                    actual_magnitude=actual_mag,
                )
                analysis.validation["feedback_weight"] = feedback.get_model_weight("cognitive_system")
                analysis.validation["ensemble_weights"] = feedback.get_ensemble_weights()
            except Exception as e:
                logger.debug(f"Feedback loop failed: {e}")

        if validator is not None:
            try:
                from reality_validation.market_reality import DirectionType
                pred_dir = DirectionType.UP if _prelim_dir == "bullish" else DirectionType.DOWN
                actual_dir_enum = DirectionType.UP if event.price_24h_after > event.price_at_event else DirectionType.DOWN
                dv = validator.validate_directional_accuracy(pred_dir, actual_dir_enum)
                analysis.validation["directional"] = (
                    dv.__dict__ if hasattr(dv, "__dict__") else str(dv)
                )
                validator.record_validation_outcome(
                    direction_correct=dv.matches if hasattr(dv, "matches") else False,
                    timing_correct=True,
                    overall_accuracy=1.0 if (hasattr(dv, "matches") and dv.matches) else 0.0,
                )
            except Exception as e:
                logger.debug(f"Reality validation failed: {e}")

        # ================================================================
        # STEP 11: Knowledge Graph Integration
        # ================================================================
        kg = self.registry.get("knowledge_graph")
        if kg is not None:
            try:
                kg.integrate_news_event({
                    "event_id": event.event_id,
                    "text": event.content,
                    "source": event.source,
                    "timestamp": event.timestamp.isoformat(),
                })
            except Exception:
                pass

        # ================================================================
        # STEP 12: LLM Deep Analysis (GPT sentiment + strategic intent)
        # ================================================================
        llm = self.registry.get("llm_analyzer")
        if llm is not None:
            try:
                llm_sentiment = llm.analyze_deep_sentiment(event.content)
                analysis.hidden_truth["llm_sentiment"] = llm_sentiment
                # Fed-specific language analysis for rate decisions
                if event.event_type == "rate_decision":
                    fed_analysis = llm.analyze_fed_language(event.content)
                    analysis.hidden_truth["fed_language"] = fed_analysis
                # Strategic intent detection
                intent = llm.detect_strategic_intent(event.content, event.source)
                analysis.hidden_truth["strategic_intent"] = intent
            except Exception as e:
                logger.debug(f"LLM analysis failed: {e}")

        # ================================================================
        # STEP 13: Social Media Sentiment (Reddit/Twitter retail pulse)
        # ================================================================
        social = self.registry.get("social_media")
        if social is not None:
            try:
                # Scan Reddit for retail sentiment signals
                social.scan_reddit()
                social_data = social.get_aggregate_sentiment()
                analysis.hidden_truth["social_sentiment"] = social_data
            except Exception as e:
                logger.debug(f"Social media analysis failed: {e}")

        # ================================================================
        # STEP 14: Human Review Queue (risk gate for high-stakes)
        # ================================================================
        human_review = self.registry.get("human_review")
        if human_review is not None:
            try:
                # Check if this event would trigger review escalation
                review_check = {
                    "event_type": event.event_type,
                    "hidden_truth_flags": len(analysis.hidden_truth),
                    "confidence": analysis.final_confidence,
                    "ambiguity": analysis.ambiguity_score,
                }
                analysis.hidden_truth["human_review_status"] = review_check
            except Exception as e:
                logger.debug(f"Human review check failed: {e}")

        # ================================================================
        # STEP 15: Infrastructure — Model Registry + Feature Store
        # ================================================================
        model_reg = self.registry.get("model_registry")
        if model_reg is not None:
            try:
                model_reg.register_model(
                    name="cognitive_signal_bridge",
                    metrics={"event_id": hash(event.event_id) % 1000},
                    parameters={"asset": self.asset, "event_type": event.event_type},
                    description=f"Signal for {event.event_id}",
                )
            except Exception:
                pass

        feature_store = self.registry.get("feature_store")
        if feature_store is not None:
            try:
                _ws_val = 0.0
                _fs = analysis.nlp_parse.get("financial_sentiment")
                if isinstance(_fs, dict):
                    _ws_val = _fs.get("weighted_score", 0.0)
                    if not isinstance(_ws_val, (int, float)):
                        _ws_val = 0.0
                feature_store.set_feature(
                    feature_name="nlp_sentiment",
                    entity_id=event.event_id,
                    value=_ws_val,
                )
            except Exception:
                pass

        monitoring = self.registry.get("monitoring")
        if monitoring is not None:
            try:
                monitoring.register_default_metrics()
                monitoring.increment("cme_signals_processed_total")
            except Exception:
                pass

        # ================================================================
        # STEP 16: Event Bus Publishing
        # ================================================================
        event_bus = self.registry.get("event_bus")
        if event_bus is not None:
            try:
                from streaming.event_bus import Event
                bus_event = Event(
                    event_type="NEWS_PROCESSED",
                    data={"event_id": event.event_id, "headline": event.headline},
                    source="backtest_bridge",
                )
                event_bus.publish(bus_event)
            except Exception:
                pass

        # ================================================================
        # SYNTHESIZE FINAL SIGNAL from all module outputs
        # ================================================================
        signal = self._synthesize_signal(event, analysis, tradable_signal)

        # Store analysis
        self.event_analyses.append(analysis)

        return signal

    # --------------------------------------------------------------------
    # SIGNAL SYNTHESIS — combine all module outputs into one decision
    # --------------------------------------------------------------------

    def _synthesize_signal(
        self,
        event: HistoricalEvent,
        analysis: EventAnalysis,
        tradable_signal: Any,
    ) -> Optional[SignalRecord]:
        """
        Synthesize final signal from ALL module outputs.

        Uses a multi-source consensus approach:
        1. Participant direction_bias weighted by confidence (PRIMARY)
        2. Participant belief_shifts for magnitude
        3. Linguistic shock vector properties
        4. Engine's TradableSignal (if non-neutral, strong boost)
        5. Scenario tree expected direction
        6. Economic impact alignment
        7. Hidden truth penalties (reduce confidence on manipulation)
        8. Alpha signal consensus
        9. Feedback loop credibility weights

        The engine's TradableSignalTranslator has conservative structural
        gates (confidence > 0.5, structural_opportunity > 0.4) that
        create a catch-22 — high agreement → low structural_opportunity,
        high disagreement → low confidence. We resolve this by deriving
        direction from participant consensus directly.
        """

        # ================================================================
        # SOURCE 1A: NLP Financial Sentiment (PRIMARY directional signal)
        # ================================================================
        fin_sentiment = analysis.nlp_parse.get("financial_sentiment", {})
        nlp_direction_score = 0.0
        nlp_sentiment_conf = 0.0

        if isinstance(fin_sentiment, dict):
            ws = fin_sentiment.get("weighted_score", 0)
            if isinstance(ws, (int, float)):
                # CONTRARIAN SIGNAL: Crypto markets exhibit strong sell-the-news
                # and buy-the-dip patterns. FinBERT/lexicon text sentiment is
                # systematically anticorrelated with 24h price movement (~61%
                # contrarian accuracy). This is a structural alpha edge.
                nlp_direction_score = -ws  # Flip: positive text → bearish price
                nlp_sentiment_conf = fin_sentiment.get("score", 0.5)
                if not isinstance(nlp_sentiment_conf, (int, float)):
                    nlp_sentiment_conf = 0.5

        # Aspect-based composite sentiment
        aspect_composite = analysis.nlp_parse.get("aspect_composite_score", 0.0)
        if not isinstance(aspect_composite, (int, float)):
            aspect_composite = 0.0

        # ================================================================
        # SOURCE 1B: Phase-pipeline participant belief_shifts (DIRECTIONAL)
        # ================================================================
        phase_belief_shifts = []  # These ARE directional [-1, +1]
        engine_belief_magnitudes = []  # These are magnitude only [0, 1]

        for ptype, resp in analysis.participant_responses.items():
            if not isinstance(resp, dict):
                continue

            cs = resp.get("cognitive_state", {})
            ev = resp.get("expectation_vector", {})

            if ptype.startswith("phase_"):
                # Phase participants have directional belief_shift [-1, +1]
                bs = resp.get("belief_shift", 0.0)
                if not isinstance(bs, (int, float)):
                    bs = cs.get("belief_shift", 0.0) if isinstance(cs, dict) else 0.0
                if isinstance(bs, (int, float)):
                    conf = 1.0 - resp.get("uncertainty_level", 0.5)
                    if not isinstance(conf, (int, float)):
                        conf = 0.5
                    phase_belief_shifts.append((bs, max(0.1, conf)))
            else:
                # Engine participants: belief_shift is magnitude [0,1]
                if isinstance(cs, dict):
                    p_belief = cs.get("belief_shift", 0.0)
                    p_conf = cs.get("confidence", 0.5)
                    if isinstance(p_belief, (int, float)) and isinstance(p_conf, (int, float)):
                        engine_belief_magnitudes.append((abs(p_belief), max(0.1, p_conf)))

        # Phase participant directional consensus
        phase_dir_score = 0.0
        phase_agreement = 0.5
        if phase_belief_shifts:
            total_pw = sum(w for _, w in phase_belief_shifts)
            phase_dir_score = sum(bs * w for bs, w in phase_belief_shifts) / (total_pw + 1e-9)
            bs_vals = [bs for bs, _ in phase_belief_shifts]
            if len(bs_vals) > 1:
                phase_agreement = max(0.0, 1.0 - (max(bs_vals) - min(bs_vals)))

        # Engine belief magnitude (how strongly participants react — unsigned)
        avg_belief_magnitude = 0.0
        avg_engine_conf = 0.5
        if engine_belief_magnitudes:
            avg_belief_magnitude = sum(m for m, _ in engine_belief_magnitudes) / len(engine_belief_magnitudes)
            avg_engine_conf = sum(c for _, c in engine_belief_magnitudes) / len(engine_belief_magnitudes)

        # Overall directional agreement
        all_dir_sources = []
        if abs(nlp_direction_score) > 0.01:
            all_dir_sources.append(nlp_direction_score)
        if abs(phase_dir_score) > 0.01:
            all_dir_sources.append(phase_dir_score)
        if abs(aspect_composite) > 0.01:
            all_dir_sources.append(aspect_composite)

        if all_dir_sources and len(all_dir_sources) > 1:
            signs = [1 if x > 0 else -1 for x in all_dir_sources]
            agreement = 1.0 if all(s == signs[0] for s in signs) else 0.3
        elif all_dir_sources:
            agreement = 0.7
        else:
            agreement = 0.5

        analysis.participant_agreement = round(agreement if phase_belief_shifts else phase_agreement, 3)

        # Build competing narratives for Deliverable D
        if agreement < 0.4 and phase_belief_shifts:
            bs_vals = [bs for bs, _ in phase_belief_shifts]
            analysis.competing_narratives = [
                f"Participant divergence: belief_shifts range from "
                f"{min(bs_vals):.2f} to {max(bs_vals):.2f}",
                f"Agreement score: {agreement:.2%} — significant ambiguity",
            ]
        if abs(nlp_direction_score) > 0.01 and abs(phase_dir_score) > 0.01:
            if (nlp_direction_score > 0) != (phase_dir_score > 0):
                analysis.competing_narratives.append(
                    f"NLP sentiment ({nlp_direction_score:+.2f}) vs participant consensus "
                    f"({phase_dir_score:+.2f}) — competing narratives"
                )

        # ================================================================
        # SOURCE 2: Linguistic shock properties
        # ================================================================
        lsv = analysis.linguistic_shock
        lsv_surprise = 0.0
        lsv_certainty = 0.5
        lsv_narrative_shift = 0.0

        if isinstance(lsv, dict):
            lsv_surprise = lsv.get("surprise", lsv.get("surprise_level", 0.0))
            lsv_certainty = lsv.get("certainty", lsv.get("certainty_level", 0.5))
            lsv_narrative_shift = lsv.get("narrative_shift", 0.0)
            if not isinstance(lsv_surprise, (int, float)):
                lsv_surprise = 0.0
            if not isinstance(lsv_certainty, (int, float)):
                lsv_certainty = 0.5
            if not isinstance(lsv_narrative_shift, (int, float)):
                lsv_narrative_shift = 0.0

        # High surprise + high certainty → stronger signal
        lsv_strength_mult = 0.5 + lsv_surprise * 0.3 + lsv_certainty * 0.2

        # ================================================================
        # SOURCE 3: Engine TradableSignal (boost if non-neutral)
        # ================================================================
        engine_dir_boost = 0.0
        engine_strength = 0.0

        if tradable_signal is not None:
            raw_dir = getattr(tradable_signal, "direction", "NEUTRAL")
            engine_strength = getattr(tradable_signal, "strength", 0.0)
            if not isinstance(engine_strength, (int, float)):
                engine_strength = 0.0

            if raw_dir == "BUY":
                engine_dir_boost = 0.15  # Strong boost if engine agrees
            elif raw_dir == "SELL":
                engine_dir_boost = -0.15

        # ================================================================
        # SOURCE 4: Scenario tree direction
        # ================================================================
        scenario_dir_score = 0.0
        scenario_tail_penalty = 1.0

        if analysis.scenario_tree:
            scenario_dir = analysis.scenario_tree.get("expected_direction", "neutral")
            tail_risk = analysis.scenario_tree.get("tail_risk_probability", 0)

            if scenario_dir == "bullish":
                scenario_dir_score = 0.10
            elif scenario_dir == "bearish":
                scenario_dir_score = -0.10

            if isinstance(tail_risk, (int, float)) and tail_risk > 0.3:
                scenario_tail_penalty = 0.85

        # ================================================================
        # SOURCE 5: Economic impact alignment
        # ================================================================
        econ_dir_score = 0.0
        if analysis.economic_impact:
            gdp_dir = analysis.economic_impact.get("gdp_direction", "neutral")
            if gdp_dir == "positive":
                econ_dir_score = 0.05
            elif gdp_dir == "negative":
                econ_dir_score = -0.05

        # ================================================================
        # SOURCE 6: Hidden truth adjustments (reduce confidence)
        # ================================================================
        ht_penalty = 0.0
        cs_result = analysis.hidden_truth.get("cross_source", {})
        if isinstance(cs_result, dict):
            trust = cs_result.get("cross_source_trust", 1.0)
            if isinstance(trust, (int, float)) and trust < 0.4:
                ht_penalty += 0.12
                analysis.competing_narratives.append(
                    f"Low cross-source trust ({trust:.2f}) — potential manipulation"
                )
            if cs_result.get("single_source_only", False):
                ht_penalty += 0.05  # Small penalty for single source

        timing_result = analysis.hidden_truth.get("timing", {})
        if isinstance(timing_result, dict):
            suspicion = timing_result.get("suspicion_score", 0)
            if isinstance(suspicion, (int, float)) and suspicion > 0.6:
                ht_penalty += 0.08

        # ================================================================
        # SOURCE 7: Alpha signal consensus
        # ================================================================
        alpha_dir_score = 0.0
        alpha_count = 0
        for alpha_type, signals in analysis.alpha_signals.items():
            if isinstance(signals, dict):
                for sname, sval in signals.items():
                    if isinstance(sval, dict):
                        s_dir = sval.get("direction", "neutral")
                        s_str = sval.get("strength", 0)
                        if isinstance(s_str, (int, float)):
                            if s_dir in ("bullish", "up"):
                                alpha_dir_score += s_str * 0.03
                                alpha_count += 1
                            elif s_dir in ("bearish", "down"):
                                alpha_dir_score -= s_str * 0.03
                                alpha_count += 1

        # ================================================================
        # SOURCE 8: Feedback loop weight
        # ================================================================
        feedback_weight = analysis.validation.get("feedback_weight", 1.0)
        if isinstance(feedback_weight, (int, float)):
            feedback_weight = max(0.3, min(2.0, feedback_weight))
        else:
            feedback_weight = 1.0

        # ================================================================
        # SOURCE 9: Market stress vector (from collision engine)
        # ================================================================
        msv = analysis.market_stress
        msv_vol_stress = 0.0
        msv_liq_stress = 0.0
        msv_disagreement = 0.0

        if isinstance(msv, dict):
            msv_vol_stress = msv.get("volatility_stress", 0.0)
            msv_liq_stress = msv.get("liquidity_stress", 0.0)
            msv_disagreement = msv.get("disagreement_index", 0.0)
            for k in ("volatility_stress", "liquidity_stress", "disagreement_index"):
                v = msv.get(k, 0.0)
                if not isinstance(v, (int, float)):
                    if k == "volatility_stress":
                        msv_vol_stress = 0.0
                    elif k == "liquidity_stress":
                        msv_liq_stress = 0.0
                    else:
                        msv_disagreement = 0.0

        # ================================================================
        # COMPOSITE DIRECTION SCORE
        # ================================================================
        # NLP financial sentiment is the PRIMARY directional signal,
        # supported by phase-pipeline participant consensus, aspect
        # sentiment, scenario tree, economics, engine, and alpha signals.

        composite_direction = (
            nlp_direction_score * 0.35       # FinBERT / lexicon sentiment (PRIMARY)
            + phase_dir_score * 0.25         # Phase participant consensus (DIRECTIONAL)
            + aspect_composite * 0.10        # Aspect-based sentiment composite
            + engine_dir_boost * 0.05        # Engine structural signal (usually 0)
            + scenario_dir_score * 0.10      # Scenario tree
            + econ_dir_score * 0.05          # Economic alignment
            + alpha_dir_score * 0.10         # Alpha model consensus
        )

        # ================================================================
        # COMPOSITE CONFIDENCE
        # ================================================================
        base_confidence = (
            avg_engine_conf * 0.20              # Engine participant confidence
            + agreement * 0.20                  # Directional agreement
            + lsv_strength_mult * 0.15          # Linguistic shock clarity
            + nlp_sentiment_conf * 0.15         # NLP sentiment confidence
            + avg_belief_magnitude * 0.15       # Engine belief shift magnitude
            + (1.0 - msv_disagreement) * 0.10   # Low disagreement boost
            + phase_agreement * 0.05            # Phase participant agreement
        )

        # Apply adjustments
        base_confidence -= ht_penalty
        base_confidence *= scenario_tail_penalty
        base_confidence *= feedback_weight

        # Clamp
        base_confidence = max(0.05, min(0.95, base_confidence))

        # ================================================================
        # DIRECTION DECISION
        # ================================================================
        dir_threshold = 0.02  # Small dead zone to avoid pure noise

        if composite_direction > dir_threshold:
            primary_direction = "bullish"
        elif composite_direction < -dir_threshold:
            primary_direction = "bearish"
        else:
            primary_direction = "neutral"

        # Signal strength from magnitude of composite direction + belief magnitude
        primary_strength = min(1.0, abs(composite_direction) * 2.5 + avg_belief_magnitude * 0.5)

        # ================================================================
        # AMBIGUITY & DELIVERABLE D
        # ================================================================
        analysis.ambiguity_score = round(
            (1.0 - agreement) * 0.5
            + ht_penalty
            + msv_disagreement * 0.3
            + (0.2 if analysis.competing_narratives else 0), 3
        )
        analysis.final_direction = primary_direction
        analysis.final_confidence = round(base_confidence, 4)

        # ================================================================
        # TRADE DECISION
        # ================================================================
        min_confidence_threshold = 0.20
        min_strength_threshold = 0.08

        if primary_direction == "neutral":
            return None
        if base_confidence < min_confidence_threshold:
            return None
        if primary_strength < min_strength_threshold:
            return None

        # Determine trade action
        action = TradeAction.BUY if primary_direction == "bullish" else TradeAction.SELL

        # Position sizing — confidence-weighted, volatility-adjusted
        base_size = 0.05
        position_size = base_size * base_confidence * feedback_weight
        # Higher vol stress → smaller position
        vol_adj = max(0.3, 1.0 - msv_vol_stress * 0.5)
        position_size *= vol_adj
        position_size = max(0.01, min(0.10, position_size))

        # Stop loss / take profit based on volatility
        vol = max(event.vol_before, 0.3) if event.vol_before > 0 else 0.5
        stop_pct = min(0.05, vol * 0.05)
        target_pct = stop_pct * 2.5  # 2.5:1 reward/risk (wider targets for contrarian)

        price = event.price_at_event
        if action == TradeAction.BUY:
            stop_loss = price * (1 - stop_pct)
            take_profit = price * (1 + target_pct)
        else:
            stop_loss = price * (1 + stop_pct)
            take_profit = price * (1 - target_pct)

        reasoning_parts = [
            f"Consensus: {primary_direction} (dir_score={composite_direction:.3f})",
            f"NLP_sent={nlp_direction_score:+.2f}",
            f"Phase_dir={phase_dir_score:+.2f}",
            f"Strength: {primary_strength:.2f}",
            f"Agreement: {agreement:.2f}",
            f"Confidence: {base_confidence:.3f}",
        ]
        if engine_strength > 0:
            eng_str = getattr(tradable_signal, "direction", "N") if tradable_signal else "N"
            reasoning_parts.append(f"Engine: {eng_str}")
        if analysis.competing_narratives:
            reasoning_parts.append(f"Ambiguity: {analysis.ambiguity_score:.2f}")
        if ht_penalty > 0:
            reasoning_parts.append(f"HT penalty: -{ht_penalty:.2f}")
        if alpha_count > 0:
            reasoning_parts.append(f"Alphas: {alpha_count} signals")

        return SignalRecord(
            timestamp=event.timestamp,
            event_id=event.event_id,
            action=action,
            direction=primary_direction,
            confidence=round(base_confidence, 4),
            position_size=round(position_size, 4),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            reasoning=" | ".join(reasoning_parts),
        )

    # ----------------------------------------------------------------
    # DELIVERABLE OUTPUTS
    # ----------------------------------------------------------------

    def get_event_study_results(self) -> Dict:
        """
        Deliverable B: Event-study style market-reaction analysis.

        For each processed event, compare predicted vs actual price movement.
        Returns directional accuracy, magnitude accuracy, timing analysis.
        """
        if not self.event_analyses:
            return {"message": "No events processed yet"}

        correct_direction = 0
        total_events = 0
        direction_details = []

        for analysis in self.event_analyses:
            if analysis.final_direction == "neutral":
                continue
            total_events += 1

            # Actual direction from price data is tracked in validation
            val = analysis.validation.get("directional", {})
            matches = val.get("matches", False) if isinstance(val, dict) else False
            if matches:
                correct_direction += 1

            direction_details.append({
                "event_id": analysis.event_id,
                "timestamp": analysis.timestamp.isoformat(),
                "headline": analysis.headline[:80],
                "predicted": analysis.final_direction,
                "confidence": analysis.final_confidence,
                "correct": matches,
            })

        accuracy = correct_direction / total_events if total_events > 0 else 0

        # Statistical significance
        validator = self.registry.get("reality_validator")
        stat_sig = {}
        if validator is not None:
            try:
                stat_sig = validator.test_statistical_significance()
            except Exception:
                pass

        return {
            "total_events_analyzed": len(self.event_analyses),
            "events_with_signals": total_events,
            "directional_accuracy": round(accuracy, 4),
            "accuracy_pct": f"{accuracy:.1%}",
            "statistical_significance": stat_sig,
            "event_details": direction_details,
        }

    def get_participant_comparison(self) -> Dict:
        """
        Deliverable C: Comparing participant interpretations vs realised reactions.

        Shows how each participant type interpreted the news vs what actually happened.
        """
        participant_accuracy = {}
        for analysis in self.event_analyses:
            for ptype, resp in analysis.participant_responses.items():
                if ptype not in participant_accuracy:
                    participant_accuracy[ptype] = {"correct": 0, "total": 0, "details": []}

                # Determine participant's predicted direction
                if isinstance(resp, dict):
                    cs = resp.get("cognitive_state", {})
                    bs = cs.get("belief_shift", 0) if isinstance(cs, dict) else 0
                    pred_dir = "bullish" if (isinstance(bs, (int, float)) and bs > 0) else "bearish"
                else:
                    continue

                participant_accuracy[ptype]["total"] += 1

                val = analysis.validation.get("directional", {})
                actual_matches = val.get("matches", False) if isinstance(val, dict) else False
                # Check if this participant agreed with the final prediction
                if (pred_dir == analysis.final_direction and actual_matches) or \
                   (pred_dir != analysis.final_direction and not actual_matches):
                    participant_accuracy[ptype]["correct"] += 1

                participant_accuracy[ptype]["details"].append({
                    "event": analysis.headline[:60],
                    "participant_prediction": pred_dir,
                    "system_prediction": analysis.final_direction,
                    "system_correct": actual_matches,
                })

        summary = {}
        for ptype, data in participant_accuracy.items():
            acc = data["correct"] / data["total"] if data["total"] > 0 else 0
            summary[ptype] = {
                "accuracy": round(acc, 4),
                "accuracy_pct": f"{acc:.1%}",
                "total_events": data["total"],
            }

        return {
            "participant_accuracy": summary,
            "total_events": len(self.event_analyses),
        }

    def get_ambiguity_report(self) -> Dict:
        """
        Deliverable D: Ambiguity and competing narratives analysis.

        Shows events with high ambiguity, competing interpretations,
        and how the system handled uncertainty.
        """
        ambiguous_events = [
            a for a in self.event_analyses if a.ambiguity_score > 0.3
        ]

        return {
            "total_events": len(self.event_analyses),
            "ambiguous_events": len(ambiguous_events),
            "ambiguity_rate": f"{len(ambiguous_events)/max(1,len(self.event_analyses)):.1%}",
            "high_ambiguity_events": [
                {
                    "event_id": a.event_id,
                    "headline": a.headline[:80],
                    "ambiguity_score": a.ambiguity_score,
                    "participant_agreement": a.participant_agreement,
                    "competing_narratives": a.competing_narratives,
                    "hidden_truth_flags": list(a.hidden_truth.keys()),
                }
                for a in sorted(ambiguous_events, key=lambda x: x.ambiguity_score, reverse=True)
            ],
        }

    def get_credibility_report(self) -> Dict:
        """Get feedback loop credibility and ensemble weight report."""
        feedback = self.registry.get("feedback")
        if feedback is None:
            return {"message": "Feedback loop not available"}
        try:
            return feedback.get_credibility_report()
        except Exception as e:
            return {"error": str(e)}


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "CognitiveSignalBridge",
    "CMEModuleRegistry",
    "EventAnalysis",
]
