"""
STREAMING PIPELINE — Real-time event processing pipeline

Orchestrates the full cognitive processing flow:
1. News ingestion → NLP parsing → Entity extraction
2. Participant cognitive modeling
3. Market behavior prediction
4. Impact assessment → DecisionEngine signal synthesis
5. Reality validation → ExecutionNexus order execution
6. Hidden truth analysis
7. Multi-asset correlation

All connected via EventBus for real-time streaming.
"""

import threading
import time
from datetime import datetime
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass

try:
    from config.logging_config import get_logger
    _log = get_logger("streaming.pipeline")
except Exception:
    import logging
    _log = logging.getLogger(__name__)

from .event_bus import EventBus, Event, EventTypes

# Decision system imports (graceful)
try:
    from decision_system.decision_engine import (
        DecisionEngine, SignalInput, SignalSource, DecisionAction
    )
    _HAS_DECISION = True
except ImportError:
    _HAS_DECISION = False

# Execution imports (graceful)
try:
    from execution.execution_nexus import ExecutionNexus, ApprovedSignal
    _HAS_EXECUTION = True
except ImportError:
    _HAS_EXECUTION = False


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics."""
    events_processed: int = 0
    avg_latency_ms: float = 0.0
    errors: int = 0
    last_processed: str = ""
    pipeline_status: str = "idle"
    
    def to_dict(self) -> Dict:
        return {
            "events_processed": self.events_processed,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "errors": self.errors,
            "last_processed": self.last_processed,
            "pipeline_status": self.pipeline_status,
        }


class StreamingPipeline:
    """
    Real-time streaming pipeline for the Cognitive Market Engine.
    
    Connects all modules together via an event bus and processes
    news events through the full cognitive pipeline.
    """
    
    def __init__(self, event_bus: EventBus = None,
                 nlp_engine=None,
                 cognitive_system=None,
                 scenario_engine=None,
                 hidden_truth=None,
                 storage=None,
                 multi_asset=None,
                 feedback_loop=None,
                 execution_engine=None,
                 decision_engine=None):
        """
        Initialize StreamingPipeline.
        
        Args:
            event_bus: EventBus instance (created if None)
            nlp_engine: NLP engine for parsing
            cognitive_system: CognitiveMarketSystem for full pipeline
            scenario_engine: ScenarioGenerator
            hidden_truth: Hidden truth detection modules (dict)
            storage: DatabaseManager for persistence
            multi_asset: Multi-asset analysis modules (dict)
            feedback_loop: FeedbackLoop for learning
            execution_engine: ExecutionNexus for order execution
            decision_engine: DecisionEngine for signal synthesis
        """
        self.event_bus = event_bus or EventBus()
        self.nlp_engine = nlp_engine
        self.cognitive_system = cognitive_system
        self.scenario_engine = scenario_engine
        self.hidden_truth = hidden_truth
        self.storage = storage
        self.multi_asset = multi_asset
        self.feedback_loop = feedback_loop
        self.execution_engine = execution_engine
        
        # Initialize DecisionEngine (use provided or create default)
        if decision_engine:
            self.decision_engine = decision_engine
        elif _HAS_DECISION:
            self.decision_engine = DecisionEngine()
        else:
            self.decision_engine = None
        
        self.metrics = PipelineMetrics()
        self._latencies = []
        self._running = False
        self._stages = {}
        
        # Register pipeline stages
        self._register_stages()
        
        print("[PIPELINE] Streaming pipeline initialized")
    
    def _register_stages(self):
        """Register event handlers for each pipeline stage."""
        # Stage 1: Raw news → Parsed
        self.event_bus.subscribe(
            EventTypes.NEWS_RAW,
            self._stage_parse
        )
        
        # Stage 2: Parsed → Cognitive processing
        self.event_bus.subscribe(
            EventTypes.NEWS_PARSED,
            self._stage_cognitive
        )
        
        # Stage 3: Interpretation → Scenario generation
        self.event_bus.subscribe(
            EventTypes.INTERPRETATION_READY,
            self._stage_scenario
        )
        
        # Stage 4: Impact → Signal generation
        self.event_bus.subscribe(
            EventTypes.IMPACT_COMPUTED,
            self._stage_signal
        )
        
        # Stage 5: Signal → Validation
        self.event_bus.subscribe(
            EventTypes.SIGNAL_GENERATED,
            self._stage_validate
        )
        
        # Stage 6: Hidden truth analysis (runs on parsed news)
        self.event_bus.subscribe(
            EventTypes.NEWS_PARSED,
            self._stage_hidden_truth
        )
        
        # Stage 7: Multi-asset correlation (runs on interpretation)
        self.event_bus.subscribe(
            EventTypes.INTERPRETATION_READY,
            self._stage_multi_asset
        )
        
        # Storage: persist all major events
        self.event_bus.subscribe("*", self._stage_persist)
    
    def start(self):
        """Start the streaming pipeline."""
        self._running = True
        self.metrics.pipeline_status = "running"
        self.event_bus.start()
        print("[PIPELINE] Started")
    
    def stop(self):
        """Stop the streaming pipeline."""
        self._running = False
        self.metrics.pipeline_status = "stopped"
        self.event_bus.stop()
        print("[PIPELINE] Stopped")
    
    def process_news(self, text: str, source: str = "manual",
                     metadata: Dict = None) -> Dict:
        """
        Process a news event through the full pipeline.
        
        This is the main entry point for feeding news into the system.
        
        Args:
            text: Raw news text
            source: Source of the news
            metadata: Additional metadata
            
        Returns:
            Processing result with event_id
        """
        start_time = time.time()
        
        event = self.event_bus.emit(
            EventTypes.NEWS_RAW,
            payload={
                "raw_text": text,
                "source": source,
                "metadata": metadata or {},
                "ingested_at": datetime.now().isoformat(),
            },
            source="pipeline",
            priority=3,
        )
        
        # Track metrics
        latency = (time.time() - start_time) * 1000
        self._latencies.append(latency)
        if len(self._latencies) > 100:
            self._latencies = self._latencies[-100:]
        
        self.metrics.events_processed += 1
        self.metrics.avg_latency_ms = sum(self._latencies) / len(self._latencies)
        self.metrics.last_processed = datetime.now().isoformat()
        
        return {
            "event_id": event.event_id,
            "status": "processing",
            "latency_ms": round(latency, 2),
        }
    
    def process_batch(self, articles: List[Dict]) -> List[Dict]:
        """Process multiple articles."""
        results = []
        for article in articles:
            result = self.process_news(
                text=article.get("text", ""),
                source=article.get("source", "batch"),
                metadata=article.get("metadata"),
            )
            results.append(result)
        return results
    
    # ================================================================
    # PIPELINE STAGES
    # ================================================================
    
    def _stage_parse(self, event: Event):
        """Stage 1: Parse raw news with NLP."""
        try:
            raw_text = event.payload.get("raw_text", "")
            
            if self.nlp_engine:
                parse_result = self.nlp_engine.parse(raw_text)
                parsed_data = {
                    "raw_text": raw_text,
                    "source": event.payload.get("source", ""),
                    "sentences": getattr(parse_result, "sentences", []),
                    "entities": getattr(parse_result, "entities", []),
                    "triples": getattr(parse_result, "triples", []),
                    "ambiguity_score": getattr(parse_result, "ambiguity_score", 0.5),
                    "certainty_score": getattr(parse_result, "certainty_score", 0.5),
                    "complexity_score": getattr(parse_result, "complexity_score", 0.5),
                }
            else:
                parsed_data = {
                    "raw_text": raw_text,
                    "source": event.payload.get("source", ""),
                    "ambiguity_score": 0.5,
                    "certainty_score": 0.5,
                    "complexity_score": 0.5,
                }
            
            self.event_bus.emit(
                EventTypes.NEWS_PARSED,
                payload=parsed_data,
                source="pipeline.parse",
            )
        except Exception as e:
            self.metrics.errors += 1
            self.event_bus.emit(
                EventTypes.SYSTEM_ERROR,
                payload={"stage": "parse", "error": str(e)},
                source="pipeline",
            )
    
    def _stage_cognitive(self, event: Event):
        """Stage 2: Run through cognitive market system."""
        try:
            if self.cognitive_system:
                signal = self.cognitive_system.process_news_event(
                    source_id=event.payload.get("source", "pipeline"),
                    raw_text=event.payload.get("raw_text", ""),
                    asset_scope=event.payload.get("asset_scope", ["BTC"]),
                    macro_scope=event.payload.get("macro_scope", ["general"]),
                )
                
                signal_data = signal.to_dict() if hasattr(signal, "to_dict") else {}
                
                self.event_bus.emit(
                    EventTypes.INTERPRETATION_READY,
                    payload={
                        "parsed": event.payload,
                        "cognitive_result": signal_data,
                        "signal": signal_data,
                    },
                    source="pipeline.cognitive",
                )
            else:
                # Pass through if no cognitive system
                self.event_bus.emit(
                    EventTypes.INTERPRETATION_READY,
                    payload={"parsed": event.payload},
                    source="pipeline.cognitive",
                )
        except Exception as e:
            self.metrics.errors += 1
            self.event_bus.emit(
                EventTypes.SYSTEM_ERROR,
                payload={"stage": "cognitive", "error": str(e)},
                source="pipeline",
            )
    
    def _stage_scenario(self, event: Event):
        """Stage 3: Generate scenarios from interpreted data."""
        try:
            if self.scenario_engine:
                parsed = event.payload.get("parsed", {})
                cognitive_result = event.payload.get("cognitive_result", {})
                
                # Build event data for scenario generator
                event_data = {
                    "raw_text": parsed.get("raw_text", ""),
                    "certainty_score": parsed.get("certainty_score", 0.5),
                    "ambiguity_score": parsed.get("ambiguity_score", 0.5),
                    "narrative_types": parsed.get("narrative_types", []),
                    "event_id": event.event_id,
                }
                
                tree = self.scenario_engine.generate(event_data)
                
                tree_data = tree.to_dict() if hasattr(tree, "to_dict") else {}
                
                # Persist scenario to storage
                if self.storage and hasattr(self.storage, "store_scenario"):
                    try:
                        self.storage.store_scenario(event.event_id, tree_data)
                    except Exception:
                        pass
                
                self.event_bus.emit(
                    EventTypes.SCENARIO_GENERATED,
                    payload={
                        "scenario_tree": tree_data,
                        "expected_direction": getattr(tree, "expected_direction", "neutral"),
                        "tail_risk": getattr(tree, "tail_risk_probability", 0.0),
                    },
                    source="pipeline.scenario",
                )
        except Exception as e:
            self.metrics.errors += 1
    
    def _stage_signal(self, event: Event):
        """Stage 4: Generate trading signal via DecisionEngine."""
        try:
            impact_data = event.payload or {}
            decision_result = None

            if self.decision_engine and _HAS_DECISION:
                # Build SignalInput objects from upstream data
                signals = []

                # NLP analysis signal
                parsed = impact_data.get("parsed", impact_data)
                certainty = parsed.get("certainty_score", 0.5)
                ambiguity = parsed.get("ambiguity_score", 0.5)
                signals.append(SignalInput(
                    source=SignalSource.NLP_ANALYSIS,
                    direction="bullish" if certainty > 0.6 else "bearish" if certainty < 0.4 else "neutral",
                    strength=abs(certainty - 0.5) * 2,
                    confidence=1.0 - ambiguity,
                    urgency=0.5,
                    reasoning=f"NLP certainty={certainty:.2f}, ambiguity={ambiguity:.2f}",
                ))

                # Cognitive model signal (from engine output)
                cognitive_result = impact_data.get("cognitive_result", {})
                if cognitive_result:
                    cog_direction = cognitive_result.get("direction", "neutral")
                    cog_strength = cognitive_result.get("strength", 0.0)
                    cog_confidence = cognitive_result.get("confidence", 0.5)
                    if isinstance(cog_confidence, str):
                        cog_confidence = {"high": 0.85, "medium": 0.6, "low": 0.3}.get(cog_confidence.lower(), 0.5)
                    signals.append(SignalInput(
                        source=SignalSource.COGNITIVE_MODELS,
                        direction=cog_direction if cog_direction in ("bullish", "bearish") else "neutral",
                        strength=float(cog_strength) if isinstance(cog_strength, (int, float)) else 0.0,
                        confidence=float(cog_confidence),
                        urgency=0.6,
                        reasoning=f"Cognitive engine: {cog_direction} strength={cog_strength}",
                    ))

                # Scenario signal (if scenario data present)
                scenario_data = impact_data.get("scenario_tree", {})
                if scenario_data:
                    exp_dir = scenario_data.get("expected_direction", "neutral")
                    tail_risk = scenario_data.get("tail_risk_probability", 0.0)
                    signals.append(SignalInput(
                        source=SignalSource.SCENARIO_ENGINE,
                        direction="bearish" if tail_risk > 0.3 else ("bullish" if exp_dir == "up" else "neutral"),
                        strength=max(0.3, tail_risk) if tail_risk > 0.1 else 0.3,
                        confidence=0.6,
                        urgency=0.7 if tail_risk > 0.3 else 0.4,
                        reasoning=f"Scenario: direction={exp_dir}, tail_risk={tail_risk:.2f}",
                    ))

                # Impact signal (market stress from impact computation)
                stress = impact_data.get("overall_stress", 0.0)
                if stress > 0:
                    signals.append(SignalInput(
                        source=SignalSource.MARKET_IMPACT,
                        direction="bearish" if stress > 0.5 else "neutral",
                        strength=stress,
                        confidence=0.65,
                        urgency=min(1.0, stress * 1.5),
                        reasoning=f"Market stress={stress:.2f}",
                    ))

                # Run DecisionEngine
                decision_packet = self.decision_engine.decide(signals)
                decision_result = decision_packet.to_dict()

                _log.info(
                    "DecisionEngine: action=%s direction=%s confidence=%.2f",
                    decision_packet.action.value,
                    decision_packet.direction,
                    decision_packet.overall_confidence,
                )

            self.event_bus.emit(
                EventTypes.SIGNAL_GENERATED,
                payload={
                    "impact": impact_data,
                    "decision": decision_result,
                    "generated_at": datetime.now().isoformat(),
                },
                source="pipeline.signal",
            )
        except Exception as e:
            self.metrics.errors += 1
            _log.error("Stage signal error: %s", e)
    
    def _stage_validate(self, event: Event):
        """Stage 5: Validate signal and route to execution."""
        try:
            signal_payload = event.payload or {}
            decision = signal_payload.get("decision", {})
            execution_result = None

            # Execute if decision says to act and execution engine is available
            if decision and self.execution_engine and _HAS_EXECUTION:
                action = decision.get("action", "hold")
                confidence = decision.get("overall_confidence", 0.0)

                if action in ("buy", "sell", "emergency_exit") and confidence > 0.3:
                    # Build ApprovedSignal for ExecutionNexus
                    direction = "BUY" if action in ("buy",) else "SELL"
                    strength = decision.get("suggested_position_pct", 0.0) * 10  # Normalize
                    strength = min(1.0, max(0.1, strength))

                    approved = ApprovedSignal(
                        signal_id=decision.get("decision_id", f"SIG-{datetime.now().timestamp()}"),
                        timestamp=datetime.now(),
                        direction=direction,
                        strength=strength,
                        volatility_impact="MEDIUM",
                        trust_score=confidence,
                        reaction_horizon="SHORT_TERM",
                        participant_weights={"nlp": 0.6, "cognitive": 0.4},
                        source_news_ids=[event.event_id],
                        expiration_timestamp=datetime.now(),
                    )

                    # Execute via ExecutionNexus
                    current_price = signal_payload.get("market_price", 50000.0)
                    order = self.execution_engine.execute_signal(
                        signal=approved,
                        current_price=current_price,
                        current_time=datetime.now(),
                    )

                    if order:
                        execution_result = {
                            "order_id": order.order_id,
                            "direction": order.direction,
                            "size": order.order_size,
                            "price": order.entry_price,
                            "status": order.status.value,
                        }
                        _log.info("ExecutionNexus: %s %s @ %.2f", direction, order.order_size, current_price)
                    else:
                        execution_result = {"status": "blocked_by_risk"}
                        _log.info("ExecutionNexus: blocked by risk gates")
                else:
                    execution_result = {"status": "hold", "action": action}

            self.event_bus.emit(
                EventTypes.VALIDATION_COMPLETE,
                payload={
                    "signal": signal_payload,
                    "execution": execution_result,
                    "validated_at": datetime.now().isoformat(),
                },
                source="pipeline.validate",
            )
        except Exception as e:
            self.metrics.errors += 1
            _log.error("Stage validate error: %s", e)
    
    def _stage_persist(self, event: Event):
        """Persist events to storage."""
        if not self.storage:
            return
        
        try:
            if event.event_type == EventTypes.NEWS_PARSED:
                self.storage.store_news_event({
                    "event_id": event.event_id,
                    **event.payload,
                })
            elif event.event_type == EventTypes.SIGNAL_GENERATED:
                self.storage.store_signal({
                    "signal_id": event.event_id,
                    **event.payload,
                })
        except Exception:
            pass  # Don't let persistence failures break the pipeline
    
    def _stage_hidden_truth(self, event: Event):
        """Stage 6: Run hidden-truth analysis on parsed news."""
        if not self.hidden_truth:
            return
        
        try:
            raw_text = event.payload.get("raw_text", "")
            source = event.payload.get("source", "")
            alerts = []
            
            # Cross-source verification
            cross_src = self.hidden_truth.get("crosssource")
            if cross_src and hasattr(cross_src, "analyze"):
                try:
                    result = cross_src.analyze(raw_text, source=source)
                    if result:
                        alerts.append({"type": "cross_source", "data": result})
                except Exception:
                    pass
            
            # Omission detection
            omission = self.hidden_truth.get("omission")
            if omission and hasattr(omission, "detect"):
                try:
                    result = omission.detect(raw_text)
                    if result:
                        alerts.append({"type": "omission", "data": result})
                except Exception:
                    pass
            
            # Timing analysis
            timing = self.hidden_truth.get("timing")
            if timing and hasattr(timing, "analyze"):
                try:
                    result = timing.analyze(raw_text, source=source)
                    if result:
                        alerts.append({"type": "timing", "data": result})
                except Exception:
                    pass
            
            if alerts:
                self.event_bus.emit(
                    "hidden_truth_alert",
                    payload={"alerts": alerts, "source_text": raw_text[:200]},
                    source="pipeline.hidden_truth",
                )
        except Exception:
            pass
    
    def _stage_multi_asset(self, event: Event):
        """Stage 7: Multi-asset correlation analysis."""
        if not self.multi_asset:
            return
        
        try:
            signal_data = event.payload.get("signal", {})
            
            # Correlation engine
            corr = (self.multi_asset if isinstance(self.multi_asset, dict)
                    else {}).get("correlation")
            if corr and hasattr(corr, "update"):
                try:
                    corr.update(signal_data)
                except Exception:
                    pass
            
            # Contagion model
            contagion = (self.multi_asset if isinstance(self.multi_asset, dict)
                         else {}).get("contagion")
            if contagion and hasattr(contagion, "assess"):
                try:
                    result = contagion.assess(signal_data)
                    if result:
                        self.event_bus.emit(
                            "contagion_alert",
                            payload={"contagion": result},
                            source="pipeline.multi_asset",
                        )
                except Exception:
                    pass
        except Exception:
            pass
    
    # ================================================================
    # MONITORING
    # ================================================================
    
    def get_metrics(self) -> Dict:
        """Get pipeline metrics."""
        return {
            **self.metrics.to_dict(),
            "event_bus": self.event_bus.get_stats(),
        }
    
    def add_stage(self, name: str, event_type: str, handler: Callable):
        """
        Add a custom pipeline stage.
        
        Args:
            name: Stage name
            event_type: Event type to subscribe to
            handler: Handler function(event: Event)
        """
        self._stages[name] = {"event_type": event_type, "handler": handler}
        self.event_bus.subscribe(event_type, handler)
        print(f"[PIPELINE] Added stage: {name} -> {event_type}")
