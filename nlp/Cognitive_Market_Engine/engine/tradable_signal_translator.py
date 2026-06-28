"""
TRADABLE SIGNAL TRANSLATION

Converts MarketStressVector (cognitive assessment) into execution-safe trading signals.

This is carefully designed to prevent:
- Chasing noise
- Late entry to crowded trades
- Execution against superior liquidity users
- Regime mismatches

Signals are STRUCTURAL, not directional.
"""

from dataclasses import dataclass, field
from typing import List, Optional
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from enum import Enum
from datetime import datetime
import numpy as np

from .expectation_collision_engine import MarketStressVector
from .core_cognitive_structures import ParticipantType


# ============================================================================
# SIGNAL TYPES (WHAT WE CAN TRADE)
# ============================================================================

class SignalType(Enum):
    """Types of structural signals we can execute"""
    PASSIVE_ACCUMULATION = "passive_accumulation"  # Wait for liquidity stress, buy slowly
    PASSIVE_DISTRIBUTION = "passive_distribution"  # Wait for liquidity provision, sell slowly
    AGGRESSIVE_MEAN_REVERSION = "aggressive_mean_reversion"  # After retail panic, buy against
    LIQUIDITY_ARBITRAGE = "liquidity_arbitrage"  # Exploit spread differences
    VOLATILITY_CAPTURE = "volatility_capture"  # Trade the volatility spike
    LIQUIDITY_PROVISION = "liquidity_provision"  # Post spreads during stress
    REGIME_FADE = "regime_fade"  # Fade when regime shifts
    NO_TRADE = "no_trade"  # Insufficient setup


class ConfidenceLevel(Enum):
    """Confidence in the signal"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


class ExecutionMode(Enum):
    """How to execute the signal"""
    PASSIVE = "passive"  # Post orders, don't chase
    ALGORITHMIC = "algorithmic"  # VWAP/TWAP execution
    AGGRESSIVE = "aggressive"  # Market orders


# ============================================================================
# TRADABLE SIGNAL OBJECT
# ============================================================================

@dataclass
class TradableSignal:
    """
    A structural, execution-safe trading signal
    
    This is what can actually be traded without blowing up.
    """
    
    # Signal identity
    signal_id: str
    signal_type: SignalType
    direction: Literal["BUY", "SELL", "NEUTRAL"]
    strength: float  # [0,1]: How strong is this signal?
    confidence: ConfidenceLevel
    
    # Execution guidance
    execution_mode: ExecutionMode
    urgency: float  # [0,1]: How urgent is this?
    
    # Risk & sizing
    suggested_position_pct: float  # % of account to allocate [0.01, 0.10]
    max_position_pct: float  # Hard cap
    stop_loss_distance: float  # % below entry
    profit_target_distance: float  # % above entry
    
    # Time windows
    entry_window_open_sec: float  # When can we start?
    entry_window_close_sec: float  # When must we stop entering?
    hold_duration_sec: float  # How long to hold?
    exit_time_sec: float  # When to definitely exit?
    
    # Contextual reasoning
    reason: str  # Why are we trading this?
    
    # Defaults
    timestamp: datetime = field(default_factory=datetime.now)
    participant_drivers: List[ParticipantType] = field(default_factory=list)  # Who's driving?
    invalidation_conditions: List[str] = field(default_factory=list)  # Anti-patterns
    market_stress_snapshot: dict = field(default_factory=dict)  # Market state snapshot
    is_active: bool = True
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    execution_status: Literal["pending", "partial", "filled", "cancelled"] = "pending"
    
    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "direction": self.direction,
            "strength": self.strength,
            "confidence": self.confidence.name,
            "execution_mode": self.execution_mode.value,
            "urgency": self.urgency,
            "suggested_position_pct": self.suggested_position_pct,
            "max_position_pct": self.max_position_pct,
            "stop_loss_distance": self.stop_loss_distance,
            "profit_target_distance": self.profit_target_distance,
            "entry_window_open_sec": self.entry_window_open_sec,
            "entry_window_close_sec": self.entry_window_close_sec,
            "hold_duration_sec": self.hold_duration_sec,
            "exit_time_sec": self.exit_time_sec,
            "reason": self.reason,
            "participant_drivers": [p.value for p in self.participant_drivers],
            "is_active": self.is_active,
            "execution_status": self.execution_status,
        }


# ============================================================================
# SIGNAL TRANSLATOR
# ============================================================================

class TradableSignalTranslator:
    """
    Converts MarketStressVector → TradableSignal
    
    This is where we decide WHAT, WHERE, WHEN, and HOW to trade.
    
    The key: we only trade when structure is clear.
    """
    
    def __init__(self, asset: str = "BTC"):
        self.asset = asset
        self.signal_counter = 0
    
    def translate(self, market_stress_vector: MarketStressVector) -> TradableSignal:
        """
        Translate market stress into a tradable signal
        
        Process:
        1. Assess if trade is warranted (pass/fail gate)
        2. Identify the trade type
        3. Define execution parameters
        4. Set risk limits
        """
        
        msv = market_stress_vector
        self.signal_counter += 1
        signal_id = f"{self.asset}-{self.signal_counter:06d}"
        
        # =====================================================
        # GATE 1: Is there enough confidence?
        # =====================================================
        
        if msv.confidence_in_assessment < 0.5:
            return self._create_no_trade_signal(signal_id, "Low confidence in assessment")
        
        # =====================================================
        # GATE 2: Is structural opportunity present?
        # =====================================================
        
        if msv.structural_opportunity < 0.4:
            return self._create_no_trade_signal(signal_id, "Insufficient structural opportunity")
        
        # =====================================================
        # STEP 1: Identify signal type
        # =====================================================
        
        # Rule: High liquidity stress + high volatility = buying opportunity (after HFT sells)
        has_liquidity_stress = msv.liquidity_stress > 0.6
        has_volatility_spike = msv.volatility_stress > 0.7
        has_disagreement = msv.disagreement_index > 0.5
        has_retail_panic_window = msv.retail_panic_window[0] > 0
        
        # Detect signal type
        if has_liquidity_stress and has_volatility_spike and msv.immediate_impact_expected:
            # HFT volatility + stress = aggressive mean reversion opportunity
            signal_type = SignalType.AGGRESSIVE_MEAN_REVERSION
            direction = "BUY"  # Buy into stressed selling
            strength = min(1.0, msv.volatility_stress * 0.8 + msv.liquidity_stress * 0.2)
            
        elif has_disagreement and has_retail_panic_window and not msv.immediate_impact_expected:
            # Disagreement + retail panic window coming = passive accumulation setup
            signal_type = SignalType.PASSIVE_ACCUMULATION
            direction = "BUY"
            strength = msv.disagreement_index * 0.7
            
        elif msv.regime_fragility > 0.7 and msv.liquidity_stress > 0.5:
            # Fragile regime + stress = position reduction (sell)
            signal_type = SignalType.PASSIVE_DISTRIBUTION
            direction = "SELL"
            strength = msv.regime_fragility * 0.6
            
        elif msv.hft_volatility_spike and has_volatility_spike:
            # HFT spike = capture volatility
            signal_type = SignalType.VOLATILITY_CAPTURE
            direction = "NEUTRAL"  # Could go either way
            strength = msv.volatility_stress * 0.8
            
        elif has_liquidity_stress and has_disagreement and not msv.hft_volatility_spike:
            # Spread differences across venues / participant types = liquidity arb
            signal_type = SignalType.LIQUIDITY_ARBITRAGE
            direction = "NEUTRAL"  # Market-neutral arb
            strength = min(1.0, msv.liquidity_stress * 0.6 + msv.disagreement_index * 0.4)
            
        elif has_liquidity_stress and msv.regime_fragility < 0.4 and not msv.immediate_impact_expected:
            # Stress present but regime stable = safe to provide liquidity
            signal_type = SignalType.LIQUIDITY_PROVISION
            direction = "NEUTRAL"  # Post both sides
            strength = min(1.0, msv.liquidity_stress * 0.7 + msv.structural_opportunity * 0.3)
            
        elif msv.regime_fragility > 0.6 and msv.reaction_asymmetry > 0.5:
            # Regime shift likely over-estimated = fade the move
            signal_type = SignalType.REGIME_FADE
            direction = "BUY" if msv.reaction_asymmetry > 0.6 else "SELL"  # Fade dominant direction
            strength = min(1.0, msv.regime_fragility * 0.5 + msv.reaction_asymmetry * 0.5)
            
        else:
            # Insufficient structure
            return self._create_no_trade_signal(signal_id, "No clear signal type identified")
        
        # =====================================================
        # STEP 2: Set confidence level
        # =====================================================
        
        if msv.confidence_in_assessment > 0.85:
            confidence = ConfidenceLevel.VERY_HIGH
        elif msv.confidence_in_assessment > 0.75:
            confidence = ConfidenceLevel.HIGH
        elif msv.confidence_in_assessment > 0.65:
            confidence = ConfidenceLevel.MEDIUM
        elif msv.confidence_in_assessment > 0.55:
            confidence = ConfidenceLevel.LOW
        else:
            confidence = ConfidenceLevel.VERY_LOW
        
        # =====================================================
        # STEP 3: Set execution mode
        # =====================================================
        
        if signal_type == SignalType.PASSIVE_ACCUMULATION:
            execution_mode = ExecutionMode.PASSIVE
            urgency = 0.3
        elif signal_type == SignalType.PASSIVE_DISTRIBUTION:
            execution_mode = ExecutionMode.PASSIVE
            urgency = 0.4
        elif signal_type == SignalType.AGGRESSIVE_MEAN_REVERSION:
            execution_mode = ExecutionMode.AGGRESSIVE
            urgency = 0.95
        elif signal_type == SignalType.VOLATILITY_CAPTURE:
            execution_mode = ExecutionMode.ALGORITHMIC
            urgency = 0.8
        elif signal_type == SignalType.LIQUIDITY_ARBITRAGE:
            execution_mode = ExecutionMode.ALGORITHMIC
            urgency = 0.7
        elif signal_type == SignalType.LIQUIDITY_PROVISION:
            execution_mode = ExecutionMode.PASSIVE
            urgency = 0.2  # Patient — post and wait
        elif signal_type == SignalType.REGIME_FADE:
            execution_mode = ExecutionMode.ALGORITHMIC
            urgency = 0.6
        else:
            execution_mode = ExecutionMode.PASSIVE
            urgency = 0.5
        
        # =====================================================
        # STEP 4: Position sizing
        # =====================================================
        
        # Base position size: strength * confidence
        base_position = strength * 0.10  # Up to 10% of account
        
        # Adjust by urgency (urgent = smaller, more focused)
        if urgency > 0.8:
            suggested_position_pct = max(0.01, base_position * 0.5)  # Cut in half if urgent
        else:
            suggested_position_pct = base_position
        
        max_position_pct = min(0.15, suggested_position_pct * 1.5)  # 1.5x max
        
        # =====================================================
        # STEP 5: Stop loss & profit targets
        # =====================================================
        
        # High volatility = wider stops
        vol_adjusted_stop = msv.volatility_stress * 0.08 + 0.02  # 2-10%
        
        if signal_type == SignalType.AGGRESSIVE_MEAN_REVERSION:
            stop_loss_distance = vol_adjusted_stop * 1.5  # Wider stops for aggressive
            profit_target_distance = 0.04  # 4% target (quick)
        elif signal_type == SignalType.PASSIVE_ACCUMULATION:
            stop_loss_distance = vol_adjusted_stop * 2.0  # Very wide
            profit_target_distance = 0.06  # 6% target
        elif signal_type == SignalType.LIQUIDITY_ARBITRAGE:
            stop_loss_distance = vol_adjusted_stop * 0.5  # Tight — arb is market-neutral
            profit_target_distance = 0.015  # 1.5% spread capture
        elif signal_type == SignalType.LIQUIDITY_PROVISION:
            stop_loss_distance = vol_adjusted_stop * 1.2  # Moderate
            profit_target_distance = 0.025  # 2.5% spread income
        elif signal_type == SignalType.REGIME_FADE:
            stop_loss_distance = vol_adjusted_stop * 1.8  # Wide — fading is risky
            profit_target_distance = 0.07  # 7% — expecting large reversion
        else:
            stop_loss_distance = vol_adjusted_stop
            profit_target_distance = 0.05
        
        # =====================================================
        # STEP 6: Time windows
        # =====================================================
        
        if signal_type == SignalType.AGGRESSIVE_MEAN_REVERSION:
            # Must enter immediately
            entry_window_open_sec = 0.0
            entry_window_close_sec = 30.0  # 30 seconds only
            hold_duration_sec = 300.0  # 5 minutes
            exit_time_sec = 600.0  # Hard exit at 10 min
            
        elif signal_type == SignalType.PASSIVE_ACCUMULATION:
            # Can be patient
            entry_window_open_sec = 180.0  # Start in 3 minutes
            entry_window_close_sec = 420.0  # Close at 7 minutes
            hold_duration_sec = 1800.0  # 30 minutes
            exit_time_sec = 3600.0  # 1 hour hard exit
            
        elif signal_type == SignalType.VOLATILITY_CAPTURE:
            entry_window_open_sec = 0.0
            entry_window_close_sec = 60.0  # 1 minute
            hold_duration_sec = 900.0  # 15 minutes
            exit_time_sec = 1800.0  # 30 min hard exit
            
        elif signal_type == SignalType.LIQUIDITY_ARBITRAGE:
            entry_window_open_sec = 0.0
            entry_window_close_sec = 45.0  # Quick entry
            hold_duration_sec = 120.0  # 2 minutes
            exit_time_sec = 300.0  # 5 min hard exit
            
        elif signal_type == SignalType.LIQUIDITY_PROVISION:
            entry_window_open_sec = 60.0  # Wait for dust to settle
            entry_window_close_sec = 600.0  # 10 min window
            hold_duration_sec = 3600.0  # 1 hour
            exit_time_sec = 7200.0  # 2 hour hard exit
            
        elif signal_type == SignalType.REGIME_FADE:
            entry_window_open_sec = 300.0  # Wait 5 min for overshoot
            entry_window_close_sec = 900.0  # 15 min window
            hold_duration_sec = 3600.0  # 1 hour
            exit_time_sec = 7200.0  # 2 hour hard exit
            
        else:
            entry_window_open_sec = 0.0
            entry_window_close_sec = 120.0
            hold_duration_sec = 600.0
            exit_time_sec = 1200.0
        
        # =====================================================
        # STEP 7: Reasoning & invalidation
        # =====================================================
        
        reason = self._build_reason(signal_type, msv)
        
        participant_drivers = []
        if msv.hft_volatility_spike:
            participant_drivers.append(ParticipantType.HFT)
        if has_retail_panic_window:
            participant_drivers.append(ParticipantType.RETAIL)
        if msv.reaction_asymmetry > 0.6:
            participant_drivers.append(ParticipantType.HEDGE_FUND)
        
        invalidation_conditions = self._build_invalidation_conditions(signal_type, msv)
        
        # =====================================================
        # CREATE SIGNAL OBJECT
        # =====================================================
        
        signal = TradableSignal(
            signal_id=signal_id,
            signal_type=signal_type,
            direction=direction,
            strength=strength,
            confidence=confidence,
            execution_mode=execution_mode,
            urgency=urgency,
            suggested_position_pct=suggested_position_pct,
            max_position_pct=max_position_pct,
            stop_loss_distance=stop_loss_distance,
            profit_target_distance=profit_target_distance,
            entry_window_open_sec=entry_window_open_sec,
            entry_window_close_sec=entry_window_close_sec,
            hold_duration_sec=hold_duration_sec,
            exit_time_sec=exit_time_sec,
            reason=reason,
            participant_drivers=participant_drivers,
            invalidation_conditions=invalidation_conditions,
            market_stress_snapshot=msv.to_dict(),
        )
        
        return signal
    
    def _create_no_trade_signal(self, signal_id: str, reason: str) -> TradableSignal:
        """Create a NO_TRADE signal with reasoning"""
        return TradableSignal(
            signal_id=signal_id,
            signal_type=SignalType.NO_TRADE,
            direction="NEUTRAL",
            strength=0.0,
            confidence=ConfidenceLevel.VERY_LOW,
            execution_mode=ExecutionMode.PASSIVE,
            urgency=0.0,
            suggested_position_pct=0.0,
            max_position_pct=0.0,
            stop_loss_distance=0.0,
            profit_target_distance=0.0,
            entry_window_open_sec=0.0,
            entry_window_close_sec=0.0,
            hold_duration_sec=0.0,
            exit_time_sec=0.0,
            reason=reason,
        )
    
    def _build_reason(self, signal_type: SignalType, msv: MarketStressVector) -> str:
        """Build human-readable reason for signal"""
        
        if signal_type == SignalType.AGGRESSIVE_MEAN_REVERSION:
            return (
                f"Liquidity stress ({msv.liquidity_stress:.2f}) + volatility spike "
                f"({msv.volatility_stress:.2f}) detected. HFT selling exhaustion expected. "
                f"High confidence mean reversion setup."
            )
        elif signal_type == SignalType.PASSIVE_ACCUMULATION:
            return (
                f"Expectation disagreement ({msv.disagreement_index:.2f}) present. "
                f"Retail panic window expected in {msv.retail_panic_window[0]:.0f}-{msv.retail_panic_window[1]:.0f}min. "
                f"Passive accumulation into weakness."
            )
        elif signal_type == SignalType.PASSIVE_DISTRIBUTION:
            return (
                f"Regime fragility ({msv.regime_fragility:.2f}) + liquidity stress. "
                f"Risk-off environment. Position reduction recommended."
            )
        elif signal_type == SignalType.VOLATILITY_CAPTURE:
            return (
                f"Volatility spike expected ({msv.volatility_stress:.2f}). "
                f"Structural opportunity to capture directional vol."
            )
        elif signal_type == SignalType.LIQUIDITY_ARBITRAGE:
            return (
                f"Liquidity stress ({msv.liquidity_stress:.2f}) with participant disagreement "
                f"({msv.disagreement_index:.2f}). Spread discrepancies across venues exploitable. "
                f"Market-neutral arbitrage setup."
            )
        elif signal_type == SignalType.LIQUIDITY_PROVISION:
            return (
                f"Liquidity stress ({msv.liquidity_stress:.2f}) in a stable regime "
                f"(fragility {msv.regime_fragility:.2f}). Safe to post spreads and earn bid-ask. "
                f"Passive liquidity provision."
            )
        elif signal_type == SignalType.REGIME_FADE:
            return (
                f"Regime fragility ({msv.regime_fragility:.2f}) with asymmetric reaction "
                f"({msv.reaction_asymmetry:.2f}). Market overshooting likely. "
                f"Fading the regime shift for mean reversion."
            )
        else:
            return "Custom signal based on market stress assessment"
    
    def _build_invalidation_conditions(self, signal_type: SignalType, msv: MarketStressVector) -> List[str]:
        """Define conditions that would invalidate this signal"""
        
        conditions = []
        
        if signal_type == SignalType.AGGRESSIVE_MEAN_REVERSION:
            conditions.append("Liquidity stress drops below 0.4")
            conditions.append("Volatility collapses")
            conditions.append("Market maker spreads normalize quickly")
            
        elif signal_type == SignalType.PASSIVE_ACCUMULATION:
            conditions.append("Regime shifts (new news)")
            conditions.append("Retail panic doesn't materialize within 10 min")
            conditions.append("Institutional rebalancing begins immediately")
            
        elif signal_type == SignalType.PASSIVE_DISTRIBUTION:
            conditions.append("Risk sentiment improves suddenly")
            conditions.append("New buying pressure emerges")
            
        elif signal_type == SignalType.VOLATILITY_CAPTURE:
            conditions.append("Volatility collapses")
            conditions.append("Direction becomes clearly one-sided")
            
        elif signal_type == SignalType.LIQUIDITY_ARBITRAGE:
            conditions.append("Spreads converge across venues")
            conditions.append("Liquidity stress drops below 0.3")
            conditions.append("Single venue dominates order flow")
            
        elif signal_type == SignalType.LIQUIDITY_PROVISION:
            conditions.append("Regime fragility rises above 0.6")
            conditions.append("Immediate impact event occurs")
            conditions.append("Inventory imbalance exceeds threshold")
            
        elif signal_type == SignalType.REGIME_FADE:
            conditions.append("Regime shift confirmed by fundamentals")
            conditions.append("New information validates the move")
            conditions.append("Second wave of selling/buying emerges")
        
        return conditions


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "SignalType",
    "ConfidenceLevel",
    "ExecutionMode",
    "TradableSignal",
    "TradableSignalTranslator",
]
