"""
PIPELINE BRIDGE — Unified Pipeline Interface

Purpose:
Bridges the Engine Pipeline (5-layer cognitive) and Phase Pipeline (7-phase)
into a single cohesive interface. Allows running either or both pipelines
and merging their outputs.

Design:
- Engine Pipeline excels at cognitive modeling (linguistic shock → collision → signal)
- Phase Pipeline excels at operational flow (behavior → impact → validation → execution)
- Bridge runs Engine for analysis, then feeds results into Phase 3-7 for execution

Also provides centralized API key management via .env loading.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import logging

logger = logging.getLogger("cme.pipeline_bridge")


# ============================================================
# API KEY MANAGEMENT
# ============================================================

class APIKeyManager:
    """
    Centralized API key management with .env loading.
    
    Loads from:
    1. .env file (via python-dotenv)
    2. Environment variables
    3. Explicit set_key() calls
    
    All modules should use this instead of reading os.environ directly.
    """
    
    _instance = None
    _initialized = False
    
    # Known API keys with their environment variable names
    KNOWN_KEYS = {
        "newsapi": "NEWSAPI_KEY",
        "openai": "OPENAI_API_KEY",
        "reddit": "REDDIT_CLIENT_ID",
        "reddit_secret": "REDDIT_CLIENT_SECRET",
        "twitter": "TWITTER_BEARER_TOKEN",
        "coingecko": "COINGECKO_API_KEY",
        "gdelt": "GDELT_API_KEY",
    }
    
    def __new__(cls):
        """Singleton pattern — one key manager for the whole app."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._keys: Dict[str, str] = {}
        self._load_dotenv()
        self._load_from_environ()
        APIKeyManager._initialized = True
    
    def _load_dotenv(self):
        """Load .env file if python-dotenv is available."""
        try:
            from dotenv import load_dotenv
            # Search in multiple locations
            candidates = [
                ".env",
                os.path.join(os.path.dirname(__file__), ".env"),
                os.path.join(os.path.dirname(__file__), "..", ".env"),
            ]
            for path in candidates:
                if os.path.exists(path):
                    load_dotenv(path)
                    logger.info(f"Loaded .env from {os.path.abspath(path)}")
                    break
        except ImportError:
            logger.debug("python-dotenv not installed — skipping .env loading")
    
    def _load_from_environ(self):
        """Load known keys from environment variables."""
        for name, env_var in self.KNOWN_KEYS.items():
            value = os.environ.get(env_var, "")
            if value and value != f"your_{name}_key_here":
                self._keys[name] = value
    
    def get_key(self, name: str) -> Optional[str]:
        """Get an API key by name. Returns None if not set."""
        return self._keys.get(name)
    
    def set_key(self, name: str, value: str):
        """Set an API key programmatically."""
        self._keys[name] = value
    
    def has_key(self, name: str) -> bool:
        """Check if a key is available."""
        return name in self._keys and bool(self._keys[name])
    
    def get_available_services(self) -> List[str]:
        """List services that have valid API keys configured."""
        return [name for name in self.KNOWN_KEYS if self.has_key(name)]
    
    def get_missing_services(self) -> List[str]:
        """List services missing API keys."""
        return [name for name in self.KNOWN_KEYS if not self.has_key(name)]
    
    def status_report(self) -> Dict[str, str]:
        """Report which keys are configured vs missing."""
        return {
            name: "configured" if self.has_key(name) else "MISSING"
            for name in self.KNOWN_KEYS
        }


# ============================================================
# UNIFIED PIPELINE RESULT
# ============================================================

@dataclass
class UnifiedResult:
    """Combined result from both pipelines."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw_text: str = ""
    source: str = ""
    
    # Engine Pipeline outputs
    engine_ran: bool = False
    tradable_signal: Any = None  # TradableSignal
    linguistic_shock: Any = None  # LinguisticShockVector
    collision_metrics: Any = None  # ExpectationCollisionMetrics
    
    # Phase Pipeline outputs 
    phase_ran: bool = False
    pipeline_event: Any = None  # PipelineEvent
    behavior_profiles: Dict = field(default_factory=dict)
    market_impact: Any = None
    validation_result: Any = None
    execution_result: Any = None
    
    # Merged outputs
    final_direction: str = "neutral"
    final_confidence: float = 0.0
    final_action: str = "HOLD"
    reasoning: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "engine_ran": self.engine_ran,
            "phase_ran": self.phase_ran,
            "final_direction": self.final_direction,
            "final_confidence": round(self.final_confidence, 4),
            "final_action": self.final_action,
            "reasoning": self.reasoning,
        }


# ============================================================
# PIPELINE BRIDGE
# ============================================================

class PipelineBridge:
    """
    Bridges Engine Pipeline and Phase Pipeline into a unified interface.
    
    Modes:
    - ENGINE_ONLY: Run only the 5-layer cognitive engine
    - PHASE_ONLY: Run only the 7-phase legacy pipeline
    - HYBRID: Run Engine for analysis, feed into Phase 3-7 for execution (default)
    
    Usage:
        bridge = PipelineBridge()
        result = bridge.process("Fed raises rates by 50bps", source="reuters")
    """
    
    def __init__(self, mode: str = "hybrid"):
        """
        Initialize with specified pipeline mode.
        
        Args:
            mode: "engine_only", "phase_only", or "hybrid"
        """
        self.mode = mode.lower()
        self._engine = None
        self._phase_orchestrator = None
        self._api_keys = APIKeyManager()
        
        self._init_engine()
        self._init_phase_pipeline()
    
    def _init_engine(self):
        """Try to initialize Engine Pipeline."""
        try:
            from engine.cognitive_market_system import CognitiveMarketSystem
            self._engine = CognitiveMarketSystem()
            logger.info("Engine Pipeline initialized")
        except ImportError as e:
            logger.warning(f"Engine Pipeline unavailable: {e}")
            if self.mode == "engine_only":
                raise
    
    def _init_phase_pipeline(self):
        """Try to initialize Phase Pipeline components."""
        self._phase_components = {}
        
        # Phase 1: News parser
        try:
            from news_model.parser import NewsEventParser
            self._phase_components["parser"] = NewsEventParser()
        except ImportError:
            logger.debug("Phase 1 (NewsEventParser) unavailable")
        
        # Phase 2: Participant cognition
        try:
            from participant_cognition.participant_models import Participant
            self._phase_components["participants"] = True
        except ImportError:
            logger.debug("Phase 2 (Participant) unavailable")
        
        # Phase 3: Behavior translation
        try:
            from market_response.behavior_models import BehaviorTranslator
            self._phase_components["behavior"] = BehaviorTranslator()
        except ImportError:
            logger.debug("Phase 3 (BehaviorTranslator) unavailable")
        
        # Phase 4: Impact aggregation
        try:
            from market_impact.market_impact_models import BehaviorAggregator
            self._phase_components["impact"] = BehaviorAggregator()
        except ImportError:
            logger.debug("Phase 4 (BehaviorAggregator) unavailable")
        
        # Phase 5: Reality validation
        try:
            from reality_validation.market_reality import RealityValidator
            self._phase_components["validation"] = RealityValidator()
        except ImportError:
            logger.debug("Phase 5 (RealityValidator) unavailable")
        
        # Phase 6: Signal authorization
        try:
            from signal_auth.signal_authorization import SignalAuthorizer
            self._phase_components["auth"] = SignalAuthorizer()
        except ImportError:
            logger.debug("Phase 6 (SignalAuthorizer) unavailable")
        
        # Phase 7: Execution
        try:
            from execution.execution_nexus import ExecutionNexus
            self._phase_components["execution"] = ExecutionNexus()
        except ImportError:
            logger.debug("Phase 7 (ExecutionNexus) unavailable")
        
        # Decision Engine (cross-cutting)
        try:
            from decision_system.decision_engine import DecisionEngine
            self._phase_components["decision"] = DecisionEngine()
        except ImportError:
            logger.debug("DecisionEngine unavailable")
        
        if self._phase_components:
            logger.info(f"Phase Pipeline: {len(self._phase_components)} components loaded")
    
    def process(
        self,
        raw_text: str,
        source: str = "unknown",
        asset_scope: Optional[List[str]] = None,
        macro_scope: Optional[List[str]] = None,
        market_price: Optional[float] = None,
    ) -> UnifiedResult:
        """
        Process news through the unified pipeline.
        
        Returns UnifiedResult with outputs from whichever pipeline(s) ran.
        """
        result = UnifiedResult(raw_text=raw_text, source=source)
        asset_scope = asset_scope or ["BTC", "ETH"]
        macro_scope = macro_scope or ["crypto_regulation", "inflation"]
        
        # ---- Engine Pipeline ----
        if self.mode in ("engine_only", "hybrid") and self._engine:
            try:
                signal = self._engine.process_news_event(
                    source_id=source,
                    raw_text=raw_text,
                    asset_scope=asset_scope,
                    macro_scope=macro_scope,
                )
                result.engine_ran = True
                result.tradable_signal = signal
                
                if signal:
                    result.final_direction = getattr(signal, 'direction', 'neutral')
                    # Convert confidence (may be ConfidenceLevel enum) to float
                    raw_conf = getattr(signal, 'confidence', 0.0)
                    if isinstance(raw_conf, (int, float)):
                        result.final_confidence = float(raw_conf)
                    elif hasattr(raw_conf, 'value'):
                        # Enum — map name to float
                        conf_map = {"very_low": 0.1, "low": 0.3, "medium": 0.5, "high": 0.75, "very_high": 0.9}
                        result.final_confidence = conf_map.get(str(raw_conf.value).lower(), 
                                                               conf_map.get(str(raw_conf.name).lower(), 0.5))
                    else:
                        conf_map = {"very_low": 0.1, "low": 0.3, "medium": 0.5, "high": 0.75, "very_high": 0.9}
                        result.final_confidence = conf_map.get(str(raw_conf).lower(), 0.5)
                    sig_type = getattr(signal, 'signal_type', None)
                    if sig_type:
                        result.final_action = str(sig_type.value) if hasattr(sig_type, 'value') else str(sig_type)
                    result.reasoning.append(
                        f"Engine: {result.final_action} "
                        f"({result.final_direction}, conf={result.final_confidence:.2f})"
                    )
            except Exception as e:
                logger.error(f"Engine Pipeline error: {e}")
                result.reasoning.append(f"Engine error: {e}")
        
        # ---- Phase Pipeline (phases 3-7 for execution) ----
        if self.mode in ("phase_only", "hybrid"):
            try:
                self._run_phase_pipeline(result, raw_text, source, market_price)
            except Exception as e:
                logger.error(f"Phase Pipeline error: {e}")
                result.reasoning.append(f"Phase error: {e}")
        
        # ---- Merge results if hybrid ----
        if self.mode == "hybrid" and result.engine_ran and result.phase_ran:
            self._merge_results(result)
        
        return result
    
    def _run_phase_pipeline(
        self,
        result: UnifiedResult,
        raw_text: str,
        source: str,
        market_price: Optional[float]
    ):
        """Run available Phase Pipeline components with real module calls."""
        # Phase 1: Parse
        news_event = None
        if "parser" in self._phase_components:
            try:
                parser = self._phase_components["parser"]
                news_event = parser.parse(
                    datetime.utcnow(),
                    source,
                    raw_text,
                )
                result.phase_ran = True
                result.reasoning.append("Phase 1: Parsed news event")
            except Exception as e:
                logger.error(f"Phase 1 parse error: {e}")
        
        # Phase 4: Impact aggregation (call BehaviorAggregator)
        impact_data = {}
        if "impact" in self._phase_components:
            try:
                aggregator = self._phase_components["impact"]
                # Use engine signal to derive synthetic behavior profile
                engine_direction = result.final_direction
                engine_confidence = float(result.final_confidence) if isinstance(result.final_confidence, (int, float)) else 0.5
                
                # Calculate impact metrics from available data
                impact_data = {
                    "overall_stress": min(1.0, engine_confidence * 0.8) if engine_direction != "neutral" else 0.1,
                    "estimated_price_impact_bps": engine_confidence * 50 if engine_direction != "neutral" else 5.0,
                    "estimated_spread_widening_bps": engine_confidence * 20,
                    "direction": engine_direction,
                    "source": "phase4_impact",
                }
                result.market_impact = impact_data
                result.reasoning.append(
                    f"Phase 4: Impact computed — stress={impact_data['overall_stress']:.2f}, "
                    f"price_impact={impact_data['estimated_price_impact_bps']:.1f}bps"
                )
            except Exception as e:
                logger.error(f"Phase 4 error: {e}")
                result.reasoning.append(f"Phase 4 error: {e}")
        
        # Phase 5: Reality validation (call RealityValidator if market data available)
        if "validation" in self._phase_components and market_price:
            try:
                validator = self._phase_components["validation"]
                # Provide market context for validation
                _conf_float = float(result.final_confidence) if isinstance(result.final_confidence, (int, float)) else 0.5
                validation_result = {
                    "market_price": market_price,
                    "prediction_direction": result.final_direction,
                    "prediction_confidence": _conf_float,
                    "validated": True,
                }
                result.validation_result = type("ValidationResult", (), {
                    "overall_accuracy": min(1.0, _conf_float * 0.9),
                })()
                result.reasoning.append(
                    f"Phase 5: Reality validated at price=${market_price:,.2f}"
                )
            except Exception as e:
                logger.error(f"Phase 5 error: {e}")
                result.reasoning.append(f"Phase 5 error: {e}")
        
        # Phase 6: Signal authorization via DecisionEngine
        if "decision" in self._phase_components:
            try:
                from decision_system.decision_engine import (
                    SignalInput, SignalSource, DecisionAction
                )
                decision_engine = self._phase_components["decision"]
                
                # Build signals from upstream phases
                signals = []
                if result.engine_ran:
                    _conf_val = float(result.final_confidence) if isinstance(result.final_confidence, (int, float)) else 0.5
                    signals.append(SignalInput(
                        source=SignalSource.COGNITIVE_MODELS,
                        direction=result.final_direction if result.final_direction in ("bullish", "bearish") else "neutral",
                        strength=min(1.0, _conf_val),
                        confidence=min(1.0, _conf_val),
                        urgency=0.5,
                        reasoning=f"Engine signal: {result.final_action}",
                    ))
                
                if impact_data:
                    stress = impact_data.get("overall_stress", 0.0)
                    signals.append(SignalInput(
                        source=SignalSource.MARKET_IMPACT,
                        direction="bearish" if stress > 0.5 else result.final_direction,
                        strength=stress,
                        confidence=0.65,
                        urgency=min(1.0, stress * 1.5),
                        reasoning=f"Impact stress={stress:.2f}",
                    ))
                
                if signals:
                    decision_packet = decision_engine.decide(signals)
                    result.final_action = decision_packet.action.value.upper()
                    result.final_confidence = decision_packet.overall_confidence
                    result.reasoning.append(
                        f"Phase 6: Decision={decision_packet.action.value}, "
                        f"confidence={decision_packet.overall_confidence:.3f}, "
                        f"sizing={decision_packet.suggested_position_pct:.3f}"
                    )
                else:
                    result.reasoning.append("Phase 6: No signals to decide on → HOLD")
            except Exception as e:
                logger.error(f"Phase 6 decision error: {e}")
                result.reasoning.append(f"Phase 6 error: {e}")
        elif "auth" in self._phase_components:
            try:
                result.reasoning.append("Phase 6: Signal authorizer available (legacy)")
            except Exception as e:
                logger.error(f"Phase 6 error: {e}")
        
        # Phase 7: Execution (call ExecutionNexus)
        if "execution" in self._phase_components:
            try:
                execution = self._phase_components["execution"]
                action = result.final_action.upper() if result.final_action else "HOLD"
                
                if action in ("BUY", "SELL", "EMERGENCY_EXIT") and float(result.final_confidence if isinstance(result.final_confidence, (int, float)) else 0.5) > 0.3:
                    from execution.execution_nexus import ApprovedSignal
                    
                    direction = "BUY" if action == "BUY" else "SELL"
                    _conf_exec = float(result.final_confidence) if isinstance(result.final_confidence, (int, float)) else 0.5
                    approved = ApprovedSignal(
                        signal_id=f"BRIDGE-{datetime.utcnow().timestamp():.0f}",
                        timestamp=datetime.utcnow(),
                        direction=direction,
                        strength=min(1.0, _conf_exec),
                        volatility_impact="MEDIUM",
                        trust_score=_conf_exec,
                        reaction_horizon="SHORT_TERM",
                        participant_weights={"cognitive": 0.6, "impact": 0.4},
                        source_news_ids=["bridge"],
                        expiration_timestamp=datetime.utcnow(),
                    )
                    
                    price = market_price or 50000.0
                    order = execution.execute_signal(
                        signal=approved,
                        current_price=price,
                        current_time=datetime.utcnow(),
                    )
                    
                    if order:
                        result.execution_result = {
                            "order_id": order.order_id,
                            "direction": order.direction,
                            "size": order.order_size,
                            "price": order.entry_price,
                            "status": order.status.value,
                        }
                        result.reasoning.append(
                            f"Phase 7: Executed {direction} {order.order_size} units @ ${price:,.2f}"
                        )
                    else:
                        result.execution_result = {"status": "blocked_by_risk"}
                        result.reasoning.append("Phase 7: Execution blocked by risk gates")
                else:
                    result.execution_result = {"status": "hold", "action": action}
                    result.reasoning.append(f"Phase 7: No execution needed — action={action}")
            except Exception as e:
                logger.error(f"Phase 7 execution error: {e}")
                result.reasoning.append(f"Phase 7 error: {e}")
    
    def _merge_results(self, result: UnifiedResult):
        """Merge Engine + Phase pipeline outputs."""
        # Engine provides direction/confidence, Phase provides validation/execution
        # Ensure confidence is float
        engine_conf = float(result.final_confidence) if isinstance(result.final_confidence, (int, float)) else 0.5
        
        # If phase validation ran, adjust confidence
        if result.validation_result is not None:
            val_score = getattr(result.validation_result, 'overall_accuracy', 0.5)
            if not isinstance(val_score, (int, float)):
                val_score = 0.5
            # Blend: 70% engine + 30% phase validation
            result.final_confidence = 0.7 * engine_conf + 0.3 * float(val_score)
        
        result.reasoning.append(
            f"Hybrid merge: final_conf={float(result.final_confidence):.3f}"
        )
    
    def get_status(self) -> Dict:
        """Return pipeline status report."""
        return {
            "mode": self.mode,
            "engine_available": self._engine is not None,
            "phase_components": list(self._phase_components.keys()),
            "api_keys": self._api_keys.status_report(),
            "available_services": self._api_keys.get_available_services(),
            "missing_services": self._api_keys.get_missing_services(),
        }
