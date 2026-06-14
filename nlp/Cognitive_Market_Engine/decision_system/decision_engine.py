"""
DECISION ENGINE — Multi-Factor Signal Synthesis & Risk-Aware Decision Making

The Decision Engine is the central intelligence that:
1. Receives signals from ALL upstream modules
2. Weighs them against each other
3. Applies risk gates and portfolio constraints
4. Produces a single, unified decision with full reasoning trace

Core Principles:
- NO signal is trusted alone — everything is cross-validated
- Risk gates are HARD — they override any signal strength
- Decisions are EXPLAINED — full reasoning chain is preserved
- Portfolio-aware — considers existing positions and correlations
- Regime-adaptive — different logic for different market states

Architecture:
    SignalCollector → FactorScorer → RiskGateCheck → PortfolioAdjust → DecisionPacket
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime
import math


# ============================================================
# ENUMS & DATA STRUCTURES
# ============================================================

class DecisionAction(str, Enum):
    """Possible decision outcomes."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"               # Do nothing
    REDUCE = "reduce"           # Reduce existing position
    HEDGE = "hedge"             # Add protective hedge
    WATCH = "watch"             # Not actionable yet, monitor
    EMERGENCY_EXIT = "emergency_exit"  # Immediate position closure


class MarketRegime(str, Enum):
    """Current market regime affects decision logic."""
    CALM = "calm"               # Low vol, normal correlations
    TRENDING = "trending"       # Directional momentum
    VOLATILE = "volatile"       # High vol, wide spreads
    CRISIS = "crisis"           # Extreme stress, correlation breakdown
    TRANSITIONING = "transitioning"  # Regime is changing


class SignalSource(str, Enum):
    """Where a signal originates from."""
    NLP_ANALYSIS = "nlp_analysis"
    COGNITIVE_MODELS = "cognitive_models"  
    BEHAVIOR_TRANSLATION = "behavior_translation"
    MARKET_IMPACT = "market_impact"
    SCENARIO_ENGINE = "scenario_engine"
    HIDDEN_TRUTH = "hidden_truth"
    REALITY_VALIDATION = "reality_validation"
    CROSS_ASSET = "cross_asset"


@dataclass
class SignalInput:
    """A single signal from any upstream module."""
    source: SignalSource
    direction: str = "neutral"      # bullish, bearish, neutral
    strength: float = 0.0           # 0.0 to 1.0
    confidence: float = 0.5         # 0.0 to 1.0
    urgency: float = 0.5            # 0.0 to 1.0
    reasoning: str = ""
    metadata: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RiskGate:
    """A hard risk constraint that can block or force decisions."""
    name: str
    triggered: bool = False
    severity: str = "warning"       # warning, block, emergency
    message: str = ""
    
    # Configurable thresholds
    max_position_pct: float = 0.15          # Max 15% of portfolio in one position
    max_portfolio_drawdown_pct: float = 0.10  # Max 10% drawdown
    max_correlation_exposure: float = 0.80   # Max correlation to existing positions
    max_daily_trades: int = 10               # Max trades per day
    min_signal_confidence: float = 0.55      # Min confidence to act
    

@dataclass
class PortfolioState:
    """Current portfolio state for position-aware decisions."""
    total_capital: float = 100000.0
    cash_available: float = 100000.0
    positions: Dict[str, Dict] = field(default_factory=dict)  
    # positions format: {"BTC": {"size": 0.5, "entry": 45000, "current": 46000, "pnl_pct": 2.2}}
    daily_pnl: float = 0.0
    daily_trades: int = 0
    max_drawdown_today: float = 0.0
    gross_exposure: float = 0.0     # Sum of absolute position values
    net_exposure: float = 0.0       # Sum of signed position values


@dataclass
class DecisionPacket:
    """Final output: a complete, explained trading decision."""
    decision_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Decision
    action: DecisionAction = DecisionAction.HOLD
    asset: str = "BTC-USD"
    direction: str = "neutral"
    
    # Sizing
    suggested_position_pct: float = 0.0     # % of portfolio
    max_position_pct: float = 0.0
    
    # Confidence
    overall_confidence: float = 0.0         # 0.0 to 1.0
    signal_agreement: float = 0.0           # How aligned are signals (0=conflicting, 1=agreement)
    
    # Risk
    stop_loss_pct: float = 0.0
    take_profit_pct: float = 0.0
    max_risk_pct: float = 0.0              # Max loss if wrong
    risk_reward_ratio: float = 0.0
    
    # Context
    market_regime: MarketRegime = MarketRegime.CALM
    risk_gates_triggered: List[str] = field(default_factory=list)
    
    # Reasoning (full trace)
    factor_scores: Dict[str, float] = field(default_factory=dict)
    reasoning_chain: List[str] = field(default_factory=list)
    dissenting_signals: List[str] = field(default_factory=list)
    
    # Hidden truth alerts
    hidden_truth_flags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "action": self.action.value,
            "asset": self.asset,
            "direction": self.direction,
            "suggested_position_pct": round(self.suggested_position_pct, 4),
            "overall_confidence": round(self.overall_confidence, 3),
            "signal_agreement": round(self.signal_agreement, 3),
            "stop_loss_pct": round(self.stop_loss_pct, 4),
            "take_profit_pct": round(self.take_profit_pct, 4),
            "risk_reward_ratio": round(self.risk_reward_ratio, 2),
            "market_regime": self.market_regime.value,
            "risk_gates_triggered": self.risk_gates_triggered,
            "factor_scores": {k: round(v, 3) for k, v in self.factor_scores.items()},
            "reasoning_chain": self.reasoning_chain,
            "dissenting_signals": self.dissenting_signals,
            "hidden_truth_flags": self.hidden_truth_flags,
        }


# ============================================================
# FACTOR WEIGHTS — How much each signal source matters
# ============================================================

DEFAULT_FACTOR_WEIGHTS = {
    SignalSource.NLP_ANALYSIS: 0.10,
    SignalSource.COGNITIVE_MODELS: 0.20,
    SignalSource.BEHAVIOR_TRANSLATION: 0.15,
    SignalSource.MARKET_IMPACT: 0.15,
    SignalSource.SCENARIO_ENGINE: 0.15,
    SignalSource.HIDDEN_TRUTH: 0.10,
    SignalSource.REALITY_VALIDATION: 0.10,
    SignalSource.CROSS_ASSET: 0.05,
}

# Regime-adjusted weights (in crisis, impact and scenario matter more)
CRISIS_FACTOR_WEIGHTS = {
    SignalSource.NLP_ANALYSIS: 0.05,
    SignalSource.COGNITIVE_MODELS: 0.15,
    SignalSource.BEHAVIOR_TRANSLATION: 0.10,
    SignalSource.MARKET_IMPACT: 0.25,
    SignalSource.SCENARIO_ENGINE: 0.20,
    SignalSource.HIDDEN_TRUTH: 0.10,
    SignalSource.REALITY_VALIDATION: 0.10,
    SignalSource.CROSS_ASSET: 0.05,
}


# ============================================================
# DECISION ENGINE
# ============================================================

class DecisionEngine:
    """
    Multi-factor decision synthesis engine.
    
    Workflow:
    1. Collect signals from all upstream modules
    2. Score each factor (direction, strength, confidence)
    3. Check risk gates (hard blockers)
    4. Apply portfolio constraints
    5. Generate decision with full reasoning trace
    """
    
    def __init__(
        self,
        portfolio: PortfolioState = None,
        factor_weights: Dict = None,
        risk_gates: List[RiskGate] = None,
        asset: str = "BTC-USD"
    ):
        self.portfolio = portfolio or PortfolioState()
        self.factor_weights = factor_weights or DEFAULT_FACTOR_WEIGHTS.copy()
        self.risk_gates = risk_gates or [RiskGate(name="default")]
        self.asset = asset
        self.decision_counter = 0
        self.decision_history: List[DecisionPacket] = []
        self.current_regime = MarketRegime.CALM
        
        print(f"[DECISION] Engine initialized for {asset}")
    
    def set_regime(self, regime: MarketRegime):
        """Update market regime — adjusts factor weights automatically."""
        self.current_regime = regime
        if regime == MarketRegime.CRISIS:
            self.factor_weights = CRISIS_FACTOR_WEIGHTS.copy()
        else:
            self.factor_weights = DEFAULT_FACTOR_WEIGHTS.copy()
    
    def decide(self, signals: List[SignalInput]) -> DecisionPacket:
        """
        Main decision method. Takes all signals and produces a decision.
        
        Args:
            signals: List of SignalInput objects from all upstream modules
            
        Returns:
            DecisionPacket with action, sizing, confidence, and reasoning
        """
        self.decision_counter += 1
        decision_id = f"DEC-{self.decision_counter:06d}"
        
        packet = DecisionPacket(
            decision_id=decision_id,
            asset=self.asset,
            market_regime=self.current_regime,
        )
        
        if not signals:
            packet.action = DecisionAction.HOLD
            packet.reasoning_chain.append("No signals received — holding")
            return packet
        
        # =====================================================
        # STEP 1: Score each factor
        # =====================================================
        factor_scores = self._score_factors(signals, packet)
        packet.factor_scores = factor_scores
        
        # =====================================================
        # STEP 2: Compute aggregate direction & strength
        # =====================================================
        agg_direction, agg_strength, agreement = self._aggregate_signals(signals, factor_scores)
        packet.direction = agg_direction
        packet.signal_agreement = agreement
        
        # =====================================================
        # STEP 3: Check risk gates
        # =====================================================
        gate_result = self._check_risk_gates(agg_direction, agg_strength, packet)
        if gate_result == "BLOCK":
            packet.action = DecisionAction.HOLD
            packet.reasoning_chain.append(
                f"BLOCKED by risk gates: {packet.risk_gates_triggered}"
            )
            return self._finalize(packet)
        elif gate_result == "EMERGENCY":
            packet.action = DecisionAction.EMERGENCY_EXIT
            packet.reasoning_chain.append(
                f"EMERGENCY EXIT triggered: {packet.risk_gates_triggered}"
            )
            return self._finalize(packet)
        
        # =====================================================
        # STEP 4: Check hidden truth flags
        # =====================================================
        hidden_truth_signals = [
            s for s in signals if s.source == SignalSource.HIDDEN_TRUTH
        ]
        for ht in hidden_truth_signals:
            if ht.metadata.get("manufactured_consensus"):
                packet.hidden_truth_flags.append("Manufactured consensus detected — reducing confidence")
                agg_strength *= 0.5
            if ht.metadata.get("omission_detected"):
                packet.hidden_truth_flags.append(f"Omission detected: {ht.metadata.get('omission_topic', 'unknown')}")
                agg_strength *= 0.7
            if ht.metadata.get("strategic_timing"):
                packet.hidden_truth_flags.append("Strategic timing detected — possible news dump")
                agg_strength *= 0.8
        
        # =====================================================
        # STEP 5: Determine action
        # =====================================================
        action = self._determine_action(agg_direction, agg_strength, agreement, packet)
        packet.action = action
        
        # =====================================================
        # STEP 6: Position sizing
        # =====================================================
        self._compute_sizing(packet, agg_strength, agreement)
        
        # =====================================================
        # STEP 7: Stop loss & take profit
        # =====================================================
        self._compute_risk_levels(packet, agg_strength)
        
        # =====================================================
        # STEP 8: Track dissenting signals
        # =====================================================
        for s in signals:
            if s.direction != agg_direction and s.strength > 0.5:
                packet.dissenting_signals.append(
                    f"{s.source.value}: {s.direction} (strength={s.strength:.2f}) — {s.reasoning}"
                )
        
        return self._finalize(packet)
    
    def _score_factors(
        self, signals: List[SignalInput], packet: DecisionPacket
    ) -> Dict[str, float]:
        """Score each signal source as a factor (0 to 1)."""
        scores = {}
        for s in signals:
            weight = self.factor_weights.get(s.source, 0.05)
            # Factor score = strength * confidence * weight
            factor_score = s.strength * s.confidence * weight
            source_key = s.source.value
            scores[source_key] = max(scores.get(source_key, 0), factor_score)
            
            packet.reasoning_chain.append(
                f"[{source_key}] direction={s.direction}, strength={s.strength:.2f}, "
                f"confidence={s.confidence:.2f}, weight={weight:.2f} → score={factor_score:.3f}"
            )
        
        return scores
    
    def _aggregate_signals(
        self, signals: List[SignalInput], factor_scores: Dict[str, float]
    ) -> Tuple[str, float, float]:
        """
        Aggregate all signals into a single direction and strength.
        
        Returns: (direction, strength, agreement)
        """
        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0
        
        for s in signals:
            weight = self.factor_weights.get(s.source, 0.05)
            weighted = s.strength * s.confidence * weight
            
            if s.direction == "bullish":
                bullish_score += weighted
            elif s.direction == "bearish":
                bearish_score += weighted
            # Neutral signals don't contribute to direction
            
            total_weight += weight
        
        if total_weight == 0:
            return "neutral", 0.0, 0.0
        
        # Direction is determined by which side has more weighted support
        if bullish_score > bearish_score * 1.2:  # Need 20% edge for conviction
            direction = "bullish"
            strength = (bullish_score - bearish_score) / total_weight
        elif bearish_score > bullish_score * 1.2:
            direction = "bearish"
            strength = (bearish_score - bullish_score) / total_weight
        else:
            direction = "neutral"
            strength = 0.0
        
        strength = min(1.0, max(0.0, strength))
        
        # Agreement: how much signals agree with each other
        # 1.0 = all signals same direction, 0.0 = perfectly split
        max_score = max(bullish_score, bearish_score)
        total_score = bullish_score + bearish_score
        agreement = (max_score / total_score) if total_score > 0 else 0.5
        
        return direction, strength, agreement
    
    def _check_risk_gates(
        self, direction: str, strength: float, packet: DecisionPacket
    ) -> str:
        """
        Check all risk gates. Returns 'PASS', 'BLOCK', or 'EMERGENCY'.
        """
        gate = self.risk_gates[0] if self.risk_gates else RiskGate(name="default")
        
        # Gate 1: Portfolio drawdown
        if self.portfolio.max_drawdown_today > gate.max_portfolio_drawdown_pct:
            packet.risk_gates_triggered.append(
                f"Portfolio drawdown {self.portfolio.max_drawdown_today:.1%} > {gate.max_portfolio_drawdown_pct:.1%}"
            )
            return "EMERGENCY"
        
        # Gate 2: Daily trade limit
        if self.portfolio.daily_trades >= gate.max_daily_trades:
            packet.risk_gates_triggered.append(
                f"Daily trade limit reached ({self.portfolio.daily_trades}/{gate.max_daily_trades})"
            )
            return "BLOCK"
        
        # Gate 3: Minimum confidence
        avg_confidence = strength  # Simplified
        if avg_confidence < gate.min_signal_confidence and direction != "neutral":
            packet.risk_gates_triggered.append(
                f"Signal confidence {avg_confidence:.2f} < minimum {gate.min_signal_confidence:.2f}"
            )
            return "BLOCK"
        
        # Gate 4: Existing position check
        existing = self.portfolio.positions.get(packet.asset, {})
        if existing:
            existing_pct = abs(existing.get("size", 0)) * existing.get("current", 0) / max(self.portfolio.total_capital, 1)
            if existing_pct > gate.max_position_pct:
                packet.risk_gates_triggered.append(
                    f"Existing position {existing_pct:.1%} > max {gate.max_position_pct:.1%}"
                )
                if direction == "neutral":
                    return "PASS"  # Allow hold/reduce decisions
                return "BLOCK"
        
        # Gate 5: Gross exposure check
        if self.portfolio.gross_exposure / max(self.portfolio.total_capital, 1) > 0.80:
            packet.risk_gates_triggered.append("Gross exposure > 80% of capital")
            return "BLOCK"
        
        return "PASS"
    
    def _determine_action(
        self, direction: str, strength: float, agreement: float,
        packet: DecisionPacket
    ) -> DecisionAction:
        """Determine the specific action to take."""
        
        existing = self.portfolio.positions.get(packet.asset, {})
        has_position = bool(existing and existing.get("size", 0) != 0)
        existing_direction = "long" if existing.get("size", 0) > 0 else "short" if existing.get("size", 0) < 0 else None
        
        # No conviction → hold or watch
        if direction == "neutral" or strength < 0.15:
            if has_position:
                packet.reasoning_chain.append("Neutral signal with existing position → HOLD")
                return DecisionAction.HOLD
            else:
                packet.reasoning_chain.append("Neutral signal, no position → WATCH")
                return DecisionAction.WATCH
        
        # Low agreement → watch (signals conflicting)
        if agreement < 0.55:
            packet.reasoning_chain.append(f"Low agreement ({agreement:.2f}) — signals conflicting → WATCH")
            return DecisionAction.WATCH
        
        # Strong signal, no position → enter
        if not has_position:
            if strength > 0.3:
                action = DecisionAction.BUY if direction == "bullish" else DecisionAction.SELL
                packet.reasoning_chain.append(
                    f"Strong {direction} signal (strength={strength:.2f}), "
                    f"no existing position → {action.value.upper()}"
                )
                return action
            else:
                packet.reasoning_chain.append(f"Weak signal (strength={strength:.2f}) → WATCH")
                return DecisionAction.WATCH
        
        # Has position, signal in same direction → hold
        if (existing_direction == "long" and direction == "bullish") or \
           (existing_direction == "short" and direction == "bearish"):
            packet.reasoning_chain.append(
                f"Signal aligns with existing {existing_direction} position → HOLD"
            )
            return DecisionAction.HOLD
        
        # Has position, signal in opposite direction → reduce or exit
        if (existing_direction == "long" and direction == "bearish") or \
           (existing_direction == "short" and direction == "bullish"):
            if strength > 0.6 and agreement > 0.7:
                packet.reasoning_chain.append(
                    f"Strong opposing signal (strength={strength:.2f}) → EMERGENCY_EXIT"
                )
                return DecisionAction.EMERGENCY_EXIT
            elif strength > 0.3:
                packet.reasoning_chain.append(
                    f"Moderate opposing signal (strength={strength:.2f}) → REDUCE"
                )
                return DecisionAction.REDUCE
            else:
                packet.reasoning_chain.append(
                    f"Weak opposing signal → HEDGE"
                )
                return DecisionAction.HEDGE
        
        return DecisionAction.HOLD
    
    def _compute_sizing(
        self, packet: DecisionPacket, strength: float, agreement: float
    ):
        """Compute position sizing based on strength, agreement, and regime."""
        if packet.action in (DecisionAction.HOLD, DecisionAction.WATCH):
            packet.suggested_position_pct = 0.0
            packet.max_position_pct = 0.0
            return
        
        # Base size: strength * agreement
        base_pct = strength * agreement * 0.10  # Max 10% at full conviction
        
        # Regime adjustment
        regime_multiplier = {
            MarketRegime.CALM: 1.0,
            MarketRegime.TRENDING: 1.2,
            MarketRegime.VOLATILE: 0.6,
            MarketRegime.CRISIS: 0.3,
            MarketRegime.TRANSITIONING: 0.5,
        }.get(self.current_regime, 1.0)
        
        suggested = base_pct * regime_multiplier
        
        # Apply Kelly-inspired constraint: never risk more than edge/odds
        edge = strength - 0.5  # Edge over random
        if edge > 0:
            kelly_fraction = edge / max(strength, 0.01)
            # Use half-Kelly for safety
            suggested = min(suggested, kelly_fraction * 0.5 * 0.15)
        
        packet.suggested_position_pct = max(0.005, min(0.15, suggested))  # 0.5% to 15%
        packet.max_position_pct = min(0.15, packet.suggested_position_pct * 1.5)
        packet.overall_confidence = min(1.0, strength * agreement)
        
        packet.reasoning_chain.append(
            f"Sizing: base={base_pct:.3f}, regime_mult={regime_multiplier}, "
            f"suggested={packet.suggested_position_pct:.3f}"
        )
    
    def _compute_risk_levels(self, packet: DecisionPacket, strength: float):
        """Compute stop loss, take profit, and risk/reward."""
        if packet.action in (DecisionAction.HOLD, DecisionAction.WATCH):
            return
        
        # Volatility-adjusted stops
        vol_mult = {
            MarketRegime.CALM: 1.0,
            MarketRegime.TRENDING: 0.8,
            MarketRegime.VOLATILE: 1.5,
            MarketRegime.CRISIS: 2.0,
            MarketRegime.TRANSITIONING: 1.3,
        }.get(self.current_regime, 1.0)
        
        # Base stop: 2-5% depending on conviction
        base_stop = 0.05 - (strength * 0.03)  # Higher conviction → tighter stop
        packet.stop_loss_pct = max(0.01, base_stop * vol_mult)
        
        # Take profit: 2x stop minimum
        packet.take_profit_pct = max(packet.stop_loss_pct * 2.0, strength * 0.08)
        
        # Risk/reward
        if packet.stop_loss_pct > 0:
            packet.risk_reward_ratio = packet.take_profit_pct / packet.stop_loss_pct
        
        # Max risk
        packet.max_risk_pct = packet.suggested_position_pct * packet.stop_loss_pct
        
        packet.reasoning_chain.append(
            f"Risk: stop={packet.stop_loss_pct:.2%}, target={packet.take_profit_pct:.2%}, "
            f"R:R={packet.risk_reward_ratio:.1f}, max_risk={packet.max_risk_pct:.3%}"
        )
    
    def _finalize(self, packet: DecisionPacket) -> DecisionPacket:
        """Finalize and store the decision."""
        self.decision_history.append(packet)
        
        # Keep only last 100 decisions in memory
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
        
        return packet
    
    def get_recent_decisions(self, n: int = 10) -> List[Dict]:
        """Get recent decision history."""
        return [d.to_dict() for d in self.decision_history[-n:]]
    
    def get_performance_summary(self) -> Dict:
        """Summarize decision engine performance."""
        if not self.decision_history:
            return {"total_decisions": 0}
        
        actions = [d.action.value for d in self.decision_history]
        confidences = [d.overall_confidence for d in self.decision_history]
        
        return {
            "total_decisions": len(self.decision_history),
            "action_distribution": {
                a: actions.count(a) for a in set(actions)
            },
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "risk_gate_triggers": sum(
                1 for d in self.decision_history if d.risk_gates_triggered
            ),
            "hidden_truth_flags": sum(
                1 for d in self.decision_history if d.hidden_truth_flags
            ),
        }
