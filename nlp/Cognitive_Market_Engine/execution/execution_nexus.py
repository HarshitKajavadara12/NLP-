"""
Phase 7: Execution Nexus

The final phase where authorized trading signals become live market actions.

Phase 7 takes Phase 6 signals and executes them through:
1. Order Manager -- Position sizing, routing, execution
2. Risk Manager -- Limits, exposure tracking, breach detection
3. Circuit Breaker -- Drawdown limits, emergency stops
4. Position Tracker -- Real-time monitoring and feedback
"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Dict, Optional, List


# ============================================================================
# ENUMS: Execution Status
# ============================================================================

class ExecutionStatus(Enum):
    """Current state of an order"""
    PENDING = "pending"         # Waiting for execution
    PARTIAL = "partial"         # Partially filled
    FILLED = "filled"           # Fully filled
    CANCELLED = "cancelled"     # Cancelled
    REJECTED = "rejected"       # Rejected by system


class RiskLevel(Enum):
    """Current portfolio risk"""
    GREEN = "green"             # Safe zone
    YELLOW = "yellow"           # Elevated risk
    RED = "red"                 # Critical


class CircuitBreakerReason(Enum):
    """Why circuit breaker triggered"""
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    INTRADAY_DRAWDOWN = "intraday_drawdown"
    VOLATILITY_SPIKE = "volatility_spike"
    EXECUTION_FAILURE = "execution_failure"
    MANUAL_STOP = "manual_stop"


# ============================================================================
# INPUT: Signal from Phase 6
# ============================================================================

@dataclass
class ApprovedSignal:
    """Signal authorized for execution (from Phase 6)"""
    signal_id: str
    timestamp: datetime
    direction: str              # BUY, SELL, NEUTRAL
    strength: float             # 0.0-1.0
    volatility_impact: str      # LOW, MEDIUM, HIGH, EXTREME
    trust_score: float          # 0.0-1.0
    reaction_horizon: str       # IMMEDIATE, SHORT_TERM, MEDIUM_TERM, LONG_TERM
    participant_weights: Dict   # {hft: 0.95, ...}
    source_news_ids: List[str]
    expiration_timestamp: datetime


# ============================================================================
# OUTPUT: Execution Results
# ============================================================================

@dataclass
class ExecutedOrder:
    """Record of executed order"""
    order_id: str
    signal_id: str              # Which signal triggered
    timestamp: datetime
    direction: str              # BUY or SELL
    order_size: float           # Position size in units
    entry_price: float          # Execution price
    status: ExecutionStatus
    profit_loss: float          # Realized P&L
    exit_timestamp: Optional[datetime] = None
    exit_price: Optional[float] = None


@dataclass
class PositionSnapshot:
    """Current position state"""
    position_id: str
    timestamp: datetime
    direction: str              # LONG, SHORT, FLAT
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    risk_level: RiskLevel
    stop_loss: float
    profit_target: float


# ============================================================================
# PHASE 7: Execution Manager (OUTLINE)
# ============================================================================

class ExecutionNexus:
    """
    Main execution engine. Orchestrates:
    1. Order Manager — Sizing and routing
    2. Risk Manager — Limits and monitoring
    3. Circuit Breaker — Emergency stops
    4. Position Tracker — Real-time feedback
    
    THIS IS WHERE SIGNALS BECOME REAL CAPITAL ALLOCATION.
    """
    
    def __init__(self):
        """Initialize execution system"""
        # Configuration (to be filled in Phase 7)
        self.max_position_size: float = 1000000.0  # $1M max per position
        self.daily_loss_limit: float = -50000.0    # Stop at -$50K daily loss
        self.intraday_drawdown_limit: float = -30000.0  # -$30K intraday
        self.volatility_threshold: float = 2.5     # Alert at 2.5x normal vol
        
        # State
        self.positions: List[PositionSnapshot] = []
        self.executed_orders: List[ExecutedOrder] = []
        self.daily_pnl: float = 0.0
        self.peak_daily_pnl: float = 0.0
        self.circuit_breaker_active: bool = False
        self.circuit_breaker_reason: Optional[CircuitBreakerReason] = None
    
    # ========================================================================
    # STEP 1: Order Manager (from Phase 6 signal)
    # ========================================================================
    
    def size_order(self, signal: ApprovedSignal, current_price: float) -> float:
        """
        Calculate position size based on signal strength and risk.
        
        Formula:
            position_size = (signal_strength ^ 2) × max_position_size
        
        Why square signal_strength?
        - 0.5 strength → 0.25 × max = 25% size (cautious)
        - 0.7 strength → 0.49 × max = 49% size (moderate)
        - 0.9 strength → 0.81 × max = 81% size (aggressive)
        
        Args:
            signal: ApprovedSignal from Phase 6
            current_price: Current market price
        
        Returns:
            position_size: Number of units to execute
        """
        # Base sizing on signal strength squared (convex)
        size_factor = signal.strength ** 2
        position_size = size_factor * self.max_position_size
        
        # Adjust down if volatility is extreme
        if signal.volatility_impact == "EXTREME":
            position_size *= 0.5  # Half size for extreme vol
        
        # Adjust down if trust is borderline
        if signal.trust_score < 0.7:
            position_size *= 0.8  # 20% reduction
        
        # Convert to units
        return int(position_size / current_price)
    
    def route_order(self, signal: ApprovedSignal, size: float) -> None:
        """
        Route order based on reaction horizon.
        
        IMMEDIATE (HFT):    → Algorithmic execution, aggressive fillingness
        SHORT_TERM:         → Smart order routing, VWAP
        MEDIUM_TERM:        → Passive limit orders
        LONG_TERM:          → Execution window over hours
        
        Args:
            signal: ApprovedSignal
            size: Position size
        """
        # Route algorithm selection based on reaction horizon
        if signal.reaction_horizon == "IMMEDIATE":
            execution_algorithm = "AGGRESSIVE"
            time_window = 5  # Execute in 5 seconds
        elif signal.reaction_horizon == "SHORT_TERM":
            execution_algorithm = "VWAP"
            time_window = 60  # Execute in 1 minute
        else:
            execution_algorithm = "PASSIVE"
            time_window = 300  # Execute over 5 minutes
        
        # Route to exchange/broker (implementation detail for Phase 7)
        # For now: placeholder
        pass
    
    # ========================================================================
    # STEP 2: Risk Manager (Continuous Monitoring)
    # ========================================================================
    
    def check_position_limits(self, new_signal: ApprovedSignal, new_size: float) -> bool:
        """
        Check if new position exceeds risk limits.
        
        Rules:
        - Max position size: $1M per trade
        - Max portfolio exposure: 80% of capital
        - Max single participant: 30% (HFT can be up to 30%)
        
        Args:
            new_signal: Signal to execute
            new_size: Proposed position size
        
        Returns:
            is_allowed (bool): Whether to allow execution
        """
        total_exposure = sum(p.quantity * p.current_price for p in self.positions)
        
        if total_exposure + new_size > 0.8 * 10000000:  # 80% of $10M capital
            return False
        
        return True
    
    def monitor_drawdown(self, current_pnl: float) -> Optional[CircuitBreakerReason]:
        """
        Monitor drawdown against limits.
        
        Daily Loss Limit: -$50K
        Intraday Drawdown: -$30K from peak
        
        Args:
            current_pnl: Current P&L
        
        Returns:
            CircuitBreakerReason if limit breached, else None
        """
        self.daily_pnl = current_pnl
        
        if self.daily_pnl < self.daily_loss_limit:
            return CircuitBreakerReason.DAILY_LOSS_LIMIT
        
        drawdown = self.peak_daily_pnl - self.daily_pnl
        if drawdown > abs(self.intraday_drawdown_limit):
            return CircuitBreakerReason.INTRADAY_DRAWDOWN
        
        return None
    
    def get_risk_level(self, current_pnl: float) -> RiskLevel:
        """
        Assess current portfolio risk.
        
        GREEN: >-$10K from daily target
        YELLOW: -$10K to -$30K
        RED: <-$30K or volatility spike
        
        Args:
            current_pnl: Current P&L
        
        Returns:
            RiskLevel: GREEN, YELLOW, or RED
        """
        if current_pnl > -10000:
            return RiskLevel.GREEN
        elif current_pnl > -30000:
            return RiskLevel.YELLOW
        else:
            return RiskLevel.RED
    
    # ========================================================================
    # STEP 3: Circuit Breaker (Emergency Stops)
    # ========================================================================
    
    def check_circuit_breaker(self, current_pnl: float, current_vol: float) -> None:
        """
        Check circuit breaker conditions.
        
        Triggers:
        - Daily loss limit breached
        - Intraday drawdown exceeded
        - Volatility spike >2.5x normal
        - Manual stop signal
        
        Args:
            current_pnl: Current P&L
            current_vol: Current realized volatility
        """
        # Check drawdown
        drawdown_reason = self.monitor_drawdown(current_pnl)
        if drawdown_reason:
            self.circuit_breaker_active = True
            self.circuit_breaker_reason = drawdown_reason
            return
        
        # Check volatility spike
        if current_vol > self.volatility_threshold:
            self.circuit_breaker_active = True
            self.circuit_breaker_reason = CircuitBreakerReason.VOLATILITY_SPIKE
            return
    
    def emergency_stop(self) -> None:
        """
        EMERGENCY: Close all positions immediately.
        
        This is the hard stop — executed only when circuit breaker fires.
        """
        for position in self.positions:
            if position.direction == "LONG":
                # Market sell
                self._execute_market_order(position, "SELL")
            elif position.direction == "SHORT":
                # Market buy to cover
                self._execute_market_order(position, "BUY")
        
        self.positions = []
    
    def _execute_market_order(self, position: PositionSnapshot, direction: str) -> Optional[ExecutedOrder]:
        """Execute market order to close position."""
        close_price = position.current_price
        
        # Calculate realized PnL
        if position.direction == "LONG":
            realized_pnl = (close_price - position.entry_price) * position.quantity
        else:
            realized_pnl = (position.entry_price - close_price) * position.quantity
        
        order = ExecutedOrder(
            order_id=f"ORD_CLOSE_{datetime.now().timestamp()}",
            signal_id="emergency_close",
            timestamp=datetime.now(),
            direction=direction,
            order_size=position.quantity,
            entry_price=close_price,
            status=ExecutionStatus.FILLED,
            profit_loss=realized_pnl,
            exit_timestamp=datetime.now(),
            exit_price=close_price,
        )
        
        self.daily_pnl += realized_pnl
        self.executed_orders.append(order)
        return order
    
    def close_position(self, position_id: str, current_price: float) -> Optional[ExecutedOrder]:
        """
        Close a specific position by ID.
        
        Args:
            position_id: Position to close
            current_price: Current market price for execution
            
        Returns:
            ExecutedOrder record or None if position not found
        """
        target = None
        for i, p in enumerate(self.positions):
            if p.position_id == position_id:
                target = p
                # Update current price for PnL calculation
                target = PositionSnapshot(
                    position_id=p.position_id,
                    timestamp=datetime.now(),
                    direction=p.direction,
                    quantity=p.quantity,
                    entry_price=p.entry_price,
                    current_price=current_price,
                    unrealized_pnl=p.unrealized_pnl,
                    realized_pnl=p.realized_pnl,
                    risk_level=p.risk_level,
                    stop_loss=p.stop_loss,
                    profit_target=p.profit_target,
                )
                close_dir = "SELL" if p.direction == "LONG" else "BUY"
                order = self._execute_market_order(target, close_dir)
                self.positions.pop(i)
                return order
        
        return None
    
    # ========================================================================
    # STEP 4: Position Tracker (Live Monitoring)
    # ========================================================================
    
    def update_position(
        self,
        position: PositionSnapshot,
        current_price: float,
        current_time: datetime
    ) -> PositionSnapshot:
        """
        Update position with current market data.
        
        Args:
            position: Current position
            current_price: Latest market price
            current_time: Current timestamp
        
        Returns:
            Updated PositionSnapshot
        """
        unrealized_pnl = (current_price - position.entry_price) * position.quantity
        if position.direction == "SHORT":
            unrealized_pnl *= -1
        
        return PositionSnapshot(
            position_id=position.position_id,
            timestamp=current_time,
            direction=position.direction,
            quantity=position.quantity,
            entry_price=position.entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=position.realized_pnl,
            risk_level=self.get_risk_level(unrealized_pnl + position.realized_pnl),
            stop_loss=position.stop_loss,
            profit_target=position.profit_target,
        )
    
    def check_exit_conditions(
        self,
        position: PositionSnapshot,
        current_price: float
    ) -> bool:
        """
        Check if position should be closed.
        
        Exit conditions:
        - Hit stop loss
        - Hit profit target
        - Position aged (expired)
        - Signal expired
        
        Args:
            position: Current position
            current_price: Current market price
        
        Returns:
            should_close (bool): Whether to close
        """
        # Hit stop loss
        if position.direction == "LONG" and current_price <= position.stop_loss:
            return True
        
        if position.direction == "SHORT" and current_price >= position.stop_loss:
            return True
        
        # Hit profit target
        if position.direction == "LONG" and current_price >= position.profit_target:
            return True
        
        if position.direction == "SHORT" and current_price <= position.profit_target:
            return True
        
        return False
    
    # ========================================================================
    # MAIN EXECUTION PIPELINE
    # ========================================================================
    
    def execute_signal(
        self,
        signal: ApprovedSignal,
        current_price: float,
        current_time: datetime
    ) -> Optional[ExecutedOrder]:
        """
        Main pipeline: Signal → Size → Risk Check → Route → Execute
        
        THIS IS THE ENTRY POINT FOR PHASE 6 SIGNALS.
        
        Args:
            signal: ApprovedSignal from Phase 6
            current_price: Current market price
            current_time: Current timestamp
        
        Returns:
            ExecutedOrder if successful, None if blocked
        """
        # Step 1: Check circuit breaker
        if self.circuit_breaker_active:
            return None  # All execution blocked
        
        # Step 2: Size order
        order_size = self.size_order(signal, current_price)
        
        # Step 3: Check risk limits
        if not self.check_position_limits(signal, order_size):
            return None  # Rejected: exceeds limits
        
        # Step 4: Route order
        self.route_order(signal, order_size)
        
        # Step 5: Execute and create position
        order = ExecutedOrder(
            order_id=f"ORD_{current_time.timestamp()}",
            signal_id=signal.signal_id,
            timestamp=current_time,
            direction=signal.direction,
            order_size=order_size,
            entry_price=current_price,
            status=ExecutionStatus.FILLED,
            profit_loss=0.0,
        )
        
        self.executed_orders.append(order)
        
        # Create live position to track
        stop_loss = (current_price * 0.98 if signal.direction == "BUY"
                     else current_price * 1.02)
        profit_target = (current_price * 1.03 if signal.direction == "BUY"
                         else current_price * 0.97)
        
        position = PositionSnapshot(
            position_id=f"POS_{current_time.timestamp()}",
            timestamp=current_time,
            direction="LONG" if signal.direction == "BUY" else "SHORT",
            quantity=order_size,
            entry_price=current_price,
            current_price=current_price,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            risk_level=RiskLevel.GREEN,
            stop_loss=stop_loss,
            profit_target=profit_target,
        )
        self.positions.append(position)
        
        # Update peak PnL
        if self.daily_pnl > self.peak_daily_pnl:
            self.peak_daily_pnl = self.daily_pnl
        
        return order
    
    def get_execution_report(self) -> Dict:
        """Generate execution summary for research feedback"""
        return {
            "total_orders": len(self.executed_orders),
            "active_positions": len([p for p in self.positions if p.direction != "FLAT"]),
            "daily_pnl": self.daily_pnl,
            "circuit_breaker_active": self.circuit_breaker_active,
            "risk_level": self.get_risk_level(self.daily_pnl).value,
        }


# ============================================================================
# INTEGRATION: Phase 6 → Phase 7
# ============================================================================

def execute_from_phase_6_signal(
    signal_from_phase_6: ApprovedSignal,
    current_market_data: Dict,
    execution_engine: ExecutionNexus,
) -> Optional[ExecutedOrder]:
    """
    Interface between Phase 6 (Signal Authorization) and Phase 7 (Execution).
    
    This function is called every time Phase 6 authorizes a signal.
    
    Args:
        signal_from_phase_6: Approved signal from SignalAuthorizer
        current_market_data: {price, time, volatility, ...}
        execution_engine: ExecutionNexus instance
    
    Returns:
        ExecutedOrder if executed, None if blocked
    """
    return execution_engine.execute_signal(
        signal=signal_from_phase_6,
        current_price=current_market_data["price"],
        current_time=current_market_data["timestamp"],
    )


# ============================================================================
# NOTES FOR PHASE 7 IMPLEMENTATION
# ============================================================================

"""
Phase 7 will be the largest phase. It needs:

1. MARKET DATA INTEGRATION
   - Real-time price feeds
   - Volatility calculation
   - Order book monitoring
   - Execution price slippage

2. EXECUTION ENGINES
   - AGGRESSIVE (market orders, immediate)
   - VWAP (volume-weighted average)
   - TWAP (time-weighted average)
   - PASSIVE (limit orders)

3. BROKER/EXCHANGE INTEGRATION
   - Order submission API
   - Position tracking
   - Execution confirmation
   - Fee calculation

4. RISK SYSTEMS
   - Real-time P&L tracking
   - Position limits enforcement
   - Margin requirements
   - Counterparty risk

5. FEEDBACK LOOP TO PHASE 5/6
   - Execution results → Phase 5 (update validation)
   - Actual market moves → Phase 6 (update trust weights)
   - Iterative learning

6. MONITORING & ALERTS
   - Real-time dashboard
   - Email/SMS alerts
   - Trade logging
   - Audit trail

7. COMPLIANCE
   - Regulatory reporting
   - Trade confirmation
   - Record keeping
   - Audit trail

Phase 7 is where NLP cognitive models meet real capital allocation.
Every signal that reaches here is backed by:
- News event classification (Phase 1)
- 5 cognitive interpretations (Phase 2)
- Behavioral constraints (Phase 3)
- Market impact prediction (Phase 4)
- Reality validation (Phase 5)
- Trust weighting & gating (Phase 6)

This is the culmination of the entire system.
"""
