"""
COGNITIVE MARKET SYSTEM - MAIN ORCHESTRATOR

This is the end-to-end pipeline that brings all 4 components together:

1. Linguistic Shock Detection (news parsing)
2. Cognitive State Formation (participant interpretation)
3. Expectation Collision Analysis (where alpha is)
4. Tradable Signal Translation (execution-safe signals)

This is a Cognitive Market Simulator, not a sentiment bot.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import json

try:
    from config.logging_config import get_logger
    _log = get_logger("engine.cognitive")
except Exception:
    import logging
    _log = logging.getLogger(__name__)

from .core_cognitive_structures import (
    NewsEvent, LinguisticShockVector, TemporalFocus, NarrativeShift,
    ParticipantType
)
from .participant_models import (
    interpret_news_with_all_participants, PARTICIPANT_MODELS
)
from .expectation_collision_engine import (
    ExpectationCollisionEngine, ExpectationCollisionMetrics, MarketStressVector
)
from .tradable_signal_translator import (
    TradableSignalTranslator, TradableSignal, SignalType
)

# Try importing the deep NLP parser — falls back to keyword heuristics if unavailable
try:
    from nlp_engine.deep_nlp_parser import DeepNLPParser
    _NLP_AVAILABLE = True
except ImportError:
    _NLP_AVAILABLE = False


# ============================================================================
# PIPELINE STATE MANAGEMENT
# ============================================================================

class CognitiveMarketSystem:
    """
    Complete cognitive market simulation system
    
    This system:
    1. Takes raw news
    2. Creates linguistic shock vectors
    3. Simulates 5 participant cognitive states
    4. Computes expectation collisions
    5. Translates to tradable signals
    6. Tracks results
    """
    
    def __init__(self, asset: str = "BTC", enable_logging: bool = True,
                 nlp_parser=None, storage=None, feedback_loop=None):
        self.asset = asset
        self.enable_logging = enable_logging
        
        # Core components
        self.collision_engine = ExpectationCollisionEngine()
        self.signal_translator = TradableSignalTranslator(asset=asset)
        
        # Deep NLP parser (replaces keyword heuristics)
        if nlp_parser is not None:
            self.nlp_parser = nlp_parser
        elif _NLP_AVAILABLE:
            try:
                self.nlp_parser = DeepNLPParser(use_transformers=False)
            except Exception:
                self.nlp_parser = None
        else:
            self.nlp_parser = None
        
        # Optional integrations
        self.storage = storage
        self.feedback_loop = feedback_loop
        
        # State tracking
        self.news_events: Dict[str, NewsEvent] = {}
        self.collision_metrics: Dict[str, ExpectationCollisionMetrics] = {}
        self.market_stress_vectors: Dict[str, MarketStressVector] = {}
        self.tradable_signals: Dict[str, TradableSignal] = {}
        
        # Execution tracking
        self.executed_signals: Dict[str, TradableSignal] = {}
        self.signal_performance: Dict[str, Dict] = {}
        
        self.log("System initialized", extra={
            "asset": asset,
            "participants": [t.value for t in ParticipantType]
        })
    
    # =====================================================================
    # PHASE 1: NEWS INGESTION & LINGUISTIC SHOCK
    # =====================================================================
    
    def ingest_news(
        self,
        source_id: str,
        raw_text: str,
        asset_scope: List[str],
        macro_scope: List[str],
    ) -> NewsEvent:
        """
        Ingest raw news and compute linguistic shock vector
        
        This replaces sentiment analysis with structural linguistic analysis.
        """
        
        event_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # =====================================================
        # Compute Linguistic Shock Vector
        # =====================================================
        
        lsv = self._compute_linguistic_shock(raw_text)
        
        # =====================================================
        # Create NewsEvent
        # =====================================================
        
        news_event = NewsEvent(
            event_id=event_id,
            timestamp=timestamp,
            source_id=source_id,
            raw_text=raw_text,
            asset_scope=asset_scope,
            macro_scope=macro_scope,
            linguistic_shock=lsv,
        )
        
        # Store
        self.news_events[event_id] = news_event
        
        self.log("News ingested", extra={
            "event_id": event_id,
            "source": source_id,
            "linguistic_shock": lsv.to_dict(),
        })
        
        return news_event
    
    def _compute_linguistic_shock(self, text: str) -> LinguisticShockVector:
        """
        Compute linguistic shock from raw text.
        
        Uses DeepNLPParser when available for real NLP analysis.
        Falls back to keyword heuristics otherwise.
        """
        
        # =====================================================
        # PATH A: Deep NLP Parser (production)
        # =====================================================
        if self.nlp_parser is not None:
            try:
                parse_result = self.nlp_parser.parse(text)
                
                # Map DeepParseResult → LinguisticShockVector
                surprise_level = 1.0 - parse_result.overall_certainty
                ambiguity_level = parse_result.overall_subjectivity
                certainty_level = parse_result.overall_certainty
                
                # Authority from entity density and source types
                authority_entities = [e for e in parse_result.all_entities
                                     if e.label in ("ORG", "PERSON", "GPE")]
                authority_strength = min(1.0, 0.4 + len(authority_entities) * 0.1)
                
                # Novelty from complexity + intent
                novelty_score = parse_result.complexity_score
                
                # Determine intent-based adjustments
                intent = parse_result.detected_intent
                intent_name = intent.value if hasattr(intent, 'value') else str(intent)
                if intent_name in ("warn", "crisis_manage"):
                    surprise_level = max(surprise_level, 0.6)
                elif intent_name in ("reassure", "deflect"):
                    certainty_level = max(certainty_level, 0.5)
                
                # Temporal focus from sentence tenses
                tenses = [s.tense for s in parse_result.sentences if hasattr(s, 'tense')]
                future_count = tenses.count("future") if tenses else 0
                past_count = tenses.count("past") if tenses else 0
                if future_count > past_count:
                    temporal_focus = TemporalFocus.FUTURE
                elif past_count > future_count:
                    temporal_focus = TemporalFocus.PAST
                else:
                    temporal_focus = TemporalFocus.PRESENT
                
                # Narrative shift from intent + certainty gap
                if surprise_level > 0.6 and ambiguity_level < 0.3:
                    narrative_shift = NarrativeShift.REGIME_CHANGE
                elif surprise_level > 0.4:
                    narrative_shift = NarrativeShift.STRONG
                elif surprise_level > 0.2:
                    narrative_shift = NarrativeShift.WEAK
                else:
                    narrative_shift = NarrativeShift.NONE
                
                # Domain specificity
                text_lower = text.lower()
                is_macro = any(w in text_lower for w in
                               ["fed", "rates", "inflation", "economy", "gdp",
                                "monetary", "fiscal", "central bank"])
                is_asset_specific = self.asset.lower() in text_lower
                
                return LinguisticShockVector(
                    surprise_level=surprise_level,
                    ambiguity_level=ambiguity_level,
                    certainty_level=certainty_level,
                    authority_strength=authority_strength,
                    novelty_score=novelty_score,
                    temporal_focus=temporal_focus,
                    narrative_shift=narrative_shift,
                    is_macro=is_macro,
                    is_asset_specific=is_asset_specific,
                    source_id="",
                    raw_text_preview=text[:200],
                )
            except Exception as e:
                self.log(f"NLP parser failed, falling back to heuristics: {e}")
        
        # =====================================================
        # PATH B: Keyword heuristics (fallback)
        # =====================================================
        return self._compute_linguistic_shock_fallback(text)
    
    def _compute_linguistic_shock_fallback(self, text: str) -> LinguisticShockVector:
        """Keyword-based fallback for linguistic shock computation."""
        
        text_lower = text.lower()
        
        # Surprise level: presence of unexpected words
        surprise_words = ["shock", "unexpected", "crash", "surge", "plunge", "soar"]
        surprise_level = min(1.0, sum(1 for word in surprise_words if word in text_lower) * 0.2)
        
        # Ambiguity: presence of uncertainty language
        ambiguity_words = ["may", "might", "could", "possibly", "uncertain", "unclear"]
        ambiguity_level = min(1.0, sum(1 for word in ambiguity_words if word in text_lower) * 0.15)
        
        # Certainty: presence of confident language
        certainty_words = ["definitely", "certainly", "confirmed", "official", "clear"]
        certainty_level = min(1.0, 0.3 + sum(1 for word in certainty_words if word in text_lower) * 0.15)
        
        # Authority strength: presence of authoritative sources
        authority_sources = ["federal reserve", "fed", "sec", "ecb", "bank of england"]
        authority_strength = min(1.0, 0.4 + sum(1 for source in authority_sources if source in text_lower) * 0.2)
        
        # Novelty: presence of first-mention words
        novelty_words = ["first", "new", "novel", "breakthrough", "unprecedented"]
        novelty_score = min(1.0, sum(1 for word in novelty_words if word in text_lower) * 0.2)
        
        # Temporal focus
        if any(word in text_lower for word in ["will", "expected", "forecast", "next"]):
            temporal_focus = TemporalFocus.FUTURE
        elif any(word in text_lower for word in ["just", "today", "now", "announced"]):
            temporal_focus = TemporalFocus.PRESENT
        else:
            temporal_focus = TemporalFocus.PAST
        
        # Narrative shift
        if surprise_level > 0.6 and ambiguity_level < 0.3:
            narrative_shift = NarrativeShift.REGIME_CHANGE
        elif surprise_level > 0.4:
            narrative_shift = NarrativeShift.STRONG
        elif surprise_level > 0.2:
            narrative_shift = NarrativeShift.WEAK
        else:
            narrative_shift = NarrativeShift.NONE
        
        # Domain specificity
        is_macro = any(word in text_lower for word in ["fed", "rates", "inflation", "economy", "gdp"])
        is_asset_specific = any(self.asset.lower() in text_lower for _ in [self.asset])
        
        return LinguisticShockVector(
            surprise_level=surprise_level,
            ambiguity_level=ambiguity_level,
            certainty_level=certainty_level,
            authority_strength=authority_strength,
            novelty_score=novelty_score,
            temporal_focus=temporal_focus,
            narrative_shift=narrative_shift,
            is_macro=is_macro,
            is_asset_specific=is_asset_specific,
            source_id="",
            raw_text_preview=text[:200],
        )
    
    # =====================================================================
    # PHASE 2: COGNITIVE INTERPRETATION
    # =====================================================================
    
    def interpret_cognitively(self, news_event: NewsEvent) -> NewsEvent:
        """
        Have all 5 participants interpret the news
        
        This creates the cognitive divergence map.
        """
        
        # All participants interpret
        news_event = interpret_news_with_all_participants(news_event)
        
        self.log("Cognitive interpretation complete", extra={
            "event_id": news_event.event_id,
            "participants_responded": len(news_event.participant_responses),
            "responses": {
                ptype: r.to_dict() for ptype, r in news_event.participant_responses.items()
            }
        })
        
        return news_event
    
    # =====================================================================
    # PHASE 3: EXPECTATION COLLISION
    # =====================================================================
    
    def compute_collision(self, news_event: NewsEvent) -> Tuple[ExpectationCollisionMetrics, MarketStressVector]:
        """
        Compute where expectations collide
        
        This is where alpha is hiding.
        """
        
        collision_metrics, market_stress = self.collision_engine.compute_collision(news_event)
        
        # Store
        self.collision_metrics[news_event.event_id] = collision_metrics
        self.market_stress_vectors[news_event.event_id] = market_stress
        
        self.log("Expectation collision computed", extra={
            "event_id": news_event.event_id,
            "collision_metrics": collision_metrics.to_dict(),
            "market_stress": market_stress.to_dict(),
        })
        
        return collision_metrics, market_stress
    
    # =====================================================================
    # PHASE 4: TRADABLE SIGNAL TRANSLATION
    # =====================================================================
    
    def translate_to_signal(self, market_stress: MarketStressVector) -> TradableSignal:
        """
        Translate market stress into an execution-safe trading signal
        """
        
        signal = self.signal_translator.translate(market_stress)
        
        # Store
        self.tradable_signals[signal.signal_id] = signal
        
        self.log("Trading signal generated", extra={
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type.value,
            "direction": signal.direction,
            "strength": signal.strength,
            "confidence": signal.confidence.name,
            "suggested_position_pct": signal.suggested_position_pct,
            "reason": signal.reason,
        })
        
        return signal
    
    # =====================================================================
    # END-TO-END PIPELINE
    # =====================================================================
    
    def process_news_event(
        self,
        source_id: str,
        raw_text: str,
        asset_scope: List[str],
        macro_scope: List[str],
    ) -> TradableSignal:
        """
        Complete end-to-end pipeline: News → Signal
        
        This is the main entry point.
        """
        
        self.log("\n" + "="*80, extra={"stage": "NEW EVENT"})
        
        # PHASE 1: Linguistic shock
        news_event = self.ingest_news(
            source_id=source_id,
            raw_text=raw_text,
            asset_scope=asset_scope,
            macro_scope=macro_scope,
        )
        
        # PHASE 2: Cognitive interpretation
        news_event = self.interpret_cognitively(news_event)
        
        # PHASE 3: Expectation collision
        collision_metrics, market_stress = self.compute_collision(news_event)
        
        # PHASE 4: Tradable signal
        signal = self.translate_to_signal(market_stress)
        
        self.log("END-TO-END PIPELINE COMPLETE", extra={
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type.value,
        })
        
        # Auto-persist to storage if available
        self._persist_event(news_event, signal)
        
        # Record prediction in feedback loop if available
        self._record_prediction(news_event, signal)
        
        return signal
    
    # =====================================================================
    # PERSISTENCE & FEEDBACK INTEGRATION
    # =====================================================================
    
    def _persist_event(self, news_event: NewsEvent, signal: TradableSignal):
        """Persist news event and signal to storage."""
        if not self.storage:
            return
        try:
            self.storage.store_news_event({
                "event_id": news_event.event_id,
                "timestamp_utc": news_event.timestamp.isoformat(),
                "source": news_event.source_id,
                "raw_text": news_event.raw_text,
                "ambiguity_score": news_event.linguistic_shock.ambiguity_level,
                "certainty_score": news_event.linguistic_shock.certainty_level,
            })
            self.storage.store_signal({
                "signal_id": signal.signal_id,
                "event_id": news_event.event_id,
                "direction": signal.direction,
                "strength": signal.strength,
                "signal_type": signal.signal_type.value,
                "status": "generated",
                "execution_mode": signal.execution_mode.value if hasattr(signal.execution_mode, 'value') else str(signal.execution_mode),
                "detail": signal.to_dict(),
            })
        except Exception as e:
            self.log(f"Storage persistence failed: {e}")
    
    def _record_prediction(self, news_event: NewsEvent, signal: TradableSignal):
        """Record prediction in feedback loop for later validation."""
        if not self.feedback_loop:
            return
        try:
            direction = "bullish" if signal.direction == "BUY" else (
                "bearish" if signal.direction == "SELL" else "neutral"
            )
            self.feedback_loop.record_prediction(
                prediction_id=signal.signal_id,
                event_type=news_event.macro_scope[0] if news_event.macro_scope else "general",
                participant_type="cognitive_system",
                asset=self.asset,
                predicted_direction=direction,
                predicted_magnitude=signal.strength,
                confidence=0.5,
            )
        except Exception as e:
            self.log(f"Feedback recording failed: {e}")
    
    # =====================================================================
    # SIGNAL EXECUTION & TRACKING
    # =====================================================================
    
    def execute_signal(self, signal: TradableSignal, entry_price: float) -> TradableSignal:
        """
        Mark signal as executed and track performance
        """
        
        signal.entry_price = entry_price
        signal.execution_status = "filled"
        signal.is_active = True
        
        self.executed_signals[signal.signal_id] = signal
        
        self.log("Signal executed", extra={
            "signal_id": signal.signal_id,
            "entry_price": entry_price,
        })
        
        return signal
    
    def close_signal(self, signal_id: str, exit_price: float, pnl: float) -> Dict:
        """
        Close a signal and record P&L
        """
        
        signal = self.executed_signals.get(signal_id)
        if not signal:
            raise ValueError(f"Signal not found: {signal_id}")
        
        signal.exit_price = exit_price
        signal.execution_status = "cancelled"
        signal.is_active = False
        
        performance = {
            "signal_id": signal_id,
            "entry_price": signal.entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_pct": (pnl / signal.entry_price) * 100,
            "execution_time_sec": (signal.exit_price - signal.entry_price) if signal.entry_price else 0,
        }
        
        self.signal_performance[signal_id] = performance
        
        self.log("Signal closed", extra=performance)
        
        return performance
    
    # =====================================================================
    # REPORTING & LOGGING
    # =====================================================================
    
    def log(self, message: str, extra: Dict = None):
        """Log with context — uses both legacy print and centralized logger."""
        _log.debug("%s %s", message, extra or "")
        if self.enable_logging:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "message": message,
            }
            if extra:
                log_entry["data"] = extra
            
            print(json.dumps(log_entry, indent=2))
    
    def get_system_status(self) -> Dict:
        """Get complete system status"""
        return {
            "asset": self.asset,
            "news_events_processed": len(self.news_events),
            "signals_generated": len(self.tradable_signals),
            "signals_executed": len(self.executed_signals),
            "signals_with_performance": len(self.signal_performance),
            "avg_signal_performance": (
                sum(p["pnl"] for p in self.signal_performance.values()) / len(self.signal_performance)
                if self.signal_performance else 0
            ),
            "collision_history_length": len(self.collision_engine.collision_history),
        }
    
    def get_last_signal(self) -> Optional[TradableSignal]:
        """Get the most recently generated signal"""
        if not self.tradable_signals:
            return None
        return list(self.tradable_signals.values())[-1]
    
    def export_state(self, filepath: str):
        """Export complete system state to JSON"""
        state = {
            "system_config": {
                "asset": self.asset,
                "timestamp": datetime.now().isoformat(),
            },
            "news_events": {
                eid: event.to_dict() for eid, event in self.news_events.items()
            },
            "collision_metrics": {
                eid: m.to_dict() for eid, m in self.collision_metrics.items()
            },
            "market_stress_vectors": {
                eid: m.to_dict() for eid, m in self.market_stress_vectors.items()
            },
            "tradable_signals": {
                sid: s.to_dict() for sid, s in self.tradable_signals.items()
            },
            "executed_signals": {
                sid: s.to_dict() for sid, s in self.executed_signals.items()
            },
            "performance": self.signal_performance,
        }
        
        with open(filepath, "w") as f:
            json.dump(state, f, indent=2, default=str)
        
        self.log(f"State exported to {filepath}")


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "CognitiveMarketSystem",
]
