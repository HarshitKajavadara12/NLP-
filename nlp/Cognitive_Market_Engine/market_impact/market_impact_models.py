"""
Phase 4: Behavior → Market Impact Modeling

This module maps aggregated behavioral profiles to observable market impacts.

Core Principle: Impact ≠ Direction

Market impact describes measurable changes in market microstructure:
- Liquidity (depth, concentration, asymmetry)
- Volatility (instant spike, clustering, sustained)
- Spreads (widening, instability, asymmetry)
- Order flow (imbalance, fragmentation, one-sided)
- Price dynamics (jump risk, drift, mean reversion, range)
- Regime stability (transition probability, dislocation)

Direction (up/down) emerges from aggregated impacts, not predicted directly.

Time Structure: Every impact has onset_delay, peak_window, decay_time, persistence
Non-Linearity: Small news → large impact (threshold). Large news → nothing (saturation).
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
try:
    from participant_cognition.participant_models import ParticipantType
except ImportError:
    try:
        from shared import ParticipantType
    except ImportError:
        from enum import Enum
        class ParticipantType(str, Enum):
            RETAIL = "retail"
            HFT = "hft"
            HEDGE_FUND = "hedge_fund"
            BANK = "bank"
            MARKET_MAKER = "market_maker"

try:
    from market_response import BehaviorProfile
except ImportError:
    from market_response.behavior_models import BehaviorProfile


class LiquidityImpactType(Enum):
    """Types of liquidity impacts observable in market."""
    DEPTH_REDUCTION = "depth_reduction"           # Smaller order books
    DEPTH_CONCENTRATION = "depth_concentration"   # Liquidity at certain price levels
    LIQUIDITY_ASYMMETRY = "liquidity_asymmetry"   # Bid/ask imbalance
    TEMPORARY_VACUUM = "temporary_vacuum"         # No liquidity at any price


class VolatilityImpactType(Enum):
    """Types of volatility impacts observable in market."""
    INSTANT_SPIKE = "instant_spike"               # Sudden jump in vol
    SUSTAINED_VOLATILITY = "sustained_volatility" # Elevated vol over time
    VOLATILITY_CLUSTERING = "volatility_clustering"  # Vol shocks cluster
    VOLATILITY_SUPPRESSION = "volatility_suppression"  # Unexpected vol reduction


class SpreadImpactType(Enum):
    """Types of spread impacts observable in market."""
    SPREAD_WIDENING = "spread_widening"           # Bid-ask gap increases
    SPREAD_INSTABILITY = "spread_instability"     # Spreads jump around
    ASYMMETRIC_SPREADS = "asymmetric_spreads"     # Different bid vs ask changes


class OrderFlowImpactType(Enum):
    """Types of order flow impacts observable in market."""
    AGGRESSIVE_IMBALANCE = "aggressive_imbalance" # Many aggressive buys or sells
    PASSIVE_IMBALANCE = "passive_imbalance"       # Passive side overwhelmed
    ONE_SIDED_FLOW = "one_sided_flow"             # Only buys or only sells
    FLOW_FRAGMENTATION = "flow_fragmentation"     # Order flow splits across venues


class PriceDynamicsType(Enum):
    """Types of price dynamics observable in market."""
    JUMP_RISK = "jump_risk"                       # Probability of gap
    DRIFT = "drift"                               # Directional pressure (emergent)
    MEAN_REVERSION_PRESSURE = "mean_reversion_pressure"  # Pull back to recent price
    RANGE_EXPANSION = "range_expansion"           # Wider trading range


class RegimeImpactType(Enum):
    """Types of regime impacts observable in market."""
    REGIME_TRANSITION_PROBABILITY = "regime_transition_probability"  # Regime change risk
    REGIME_INSTABILITY = "regime_instability"     # Current regime unstable
    TEMPORARY_DISLOCATION = "temporary_dislocation"  # Temporary anomaly


@dataclass
class ImpactTiming:
    """Time structure of a market impact (when does it happen?)."""
    onset_delay: timedelta                         # Delay before impact starts
    peak_window: timedelta                         # Duration until peak
    decay_time: timedelta                          # Time to dissipate
    persistence: timedelta                         # How long does effect linger?
    
    def get_summary(self) -> str:
        return f"Onset: {self.onset_delay.total_seconds():.0f}s, Peak: {self.peak_window.total_seconds():.0f}s, Decay: {self.decay_time.total_seconds():.0f}s, Persist: {self.persistence.total_seconds():.0f}s"


@dataclass
class ImpactMeasurement:
    """Quantitative measurement of one impact dimension."""
    impact_type: Enum                              # Which type of impact
    magnitude: float                               # 0.0-1.0, intensity
    confidence: float                              # 0.0-1.0, how sure
    timing: ImpactTiming                           # When does it happen
    reasoning: str                                 # Why this impact expected
    
    def get_summary(self) -> str:
        return f"{self.impact_type.value}: mag={self.magnitude:.2f}, conf={self.confidence:.2f}, {self.timing.get_summary()}"


@dataclass
class MarketImpactProfile:
    """
    Complete market impact profile resulting from aggregated behaviors.
    
    This is the output of Phase 4.
    NOT prediction of direction or prices.
    IS prediction of observable market state changes.
    """
    # Identity
    news_event_id: str
    timestamp: datetime
    
    # Impact Dimensions
    liquidity_impacts: List[ImpactMeasurement]
    volatility_impacts: List[ImpactMeasurement]
    spread_impacts: List[ImpactMeasurement]
    order_flow_impacts: List[ImpactMeasurement]
    price_dynamics: List[ImpactMeasurement]
    regime_impacts: List[ImpactMeasurement]
    
    # Aggregate Properties
    overall_market_stress: float                   # 0.0-1.0, "how stressed is market?"
    confidence_in_impact: float                    # 0.0-1.0, how confident in this prediction?
    
    # Non-Linearity Indicators
    threshold_breached: bool                       # Did behavior cross threshold for phase transition?
    saturation_detected: bool                      # Did market reach saturation? (impact saturates)
    feedback_loop_risk: bool                       # Could this create feedback loops?
    
    # Explanation
    reasoning: str                                 # Human-readable summary
    
    def get_summary(self) -> str:
        """Human-readable summary of all impacts."""
        summary = f"""
Market Impact Profile:
  Stress Level: {self.overall_market_stress:.2f} (0=calm, 1=crisis)
  Confidence: {self.confidence_in_impact:.2f}
  Threshold Breached: {self.threshold_breached}
  Saturation Detected: {self.saturation_detected}
  Feedback Loop Risk: {self.feedback_loop_risk}
  
Liquidity Impacts: {len(self.liquidity_impacts)} identified
{chr(10).join(f'  - {i.get_summary()}' for i in self.liquidity_impacts)}

Volatility Impacts: {len(self.volatility_impacts)} identified
{chr(10).join(f'  - {i.get_summary()}' for i in self.volatility_impacts)}

Spread Impacts: {len(self.spread_impacts)} identified
{chr(10).join(f'  - {i.get_summary()}' for i in self.spread_impacts)}

Order Flow Impacts: {len(self.order_flow_impacts)} identified
{chr(10).join(f'  - {i.get_summary()}' for i in self.order_flow_impacts)}

Price Dynamics: {len(self.price_dynamics)} identified
{chr(10).join(f'  - {i.get_summary()}' for i in self.price_dynamics)}

Regime Impacts: {len(self.regime_impacts)} identified
{chr(10).join(f'  - {i.get_summary()}' for i in self.regime_impacts)}

Reasoning: {self.reasoning}
        """
        return summary


@dataclass
class AggregatedBehavior:
    """
    Aggregated behavioral state across all participants.
    
    Not just sum of behaviors.
    Weighted by: speed, liquidity role, market share, timing overlap.
    """
    # Raw aggregates
    avg_risk_posture_signal: float                 # -1 (decrease risk) to +1 (increase risk)
    avg_liquidity_posture_signal: float            # -1 (withdraw) to +1 (provide)
    avg_exposure_intent_signal: float              # -1 (reduce exposure) to +1 (increase)
    avg_urgency_signal: float                      # 0 (passive) to 1 (immediate)
    avg_optionality_signal: float                  # 0 (committed) to 1 (flexible)
    
    # Weighted aggregates (account for participant importance)
    hft_weighted_urgency: float                    # HFTs move fast, weight matters
    bank_weighted_risk_reduction: float            # Banks provide liquidity, their risk reduction hurts liq
    mm_weighted_liquidity_withdrawal: float        # MMs are liquidity providers, their withdrawal is critical
    
    # Dispersion (disagreement)
    behavior_disagreement: float                   # 0 (all agree) to 1 (all disagree)
    participant_divergence: List[Tuple[ParticipantType, float]]  # Which participants diverge?
    
    # Concentration (one-sidedness)
    behavior_concentration: float                  # 0 (balanced) to 1 (one-sided)
    
    def get_summary(self) -> str:
        return f"""
Aggregated Behavior:
  Risk Signal: {self.avg_risk_posture_signal:+.2f} (reduce to increase risk)
  Liquidity Signal: {self.avg_liquidity_posture_signal:+.2f} (withdraw to provide)
  Exposure Signal: {self.avg_exposure_intent_signal:+.2f} (reduce to increase)
  Urgency Signal: {self.avg_urgency_signal:.2f} (passive to immediate)
  Optionality Signal: {self.avg_optionality_signal:.2f} (committed to flexible)
  
Weighted Signals:
  HFT Urgency Weight: {self.hft_weighted_urgency:.2f}
  Bank Risk Reduction Weight: {self.bank_weighted_risk_reduction:.2f}
  MM Liquidity Withdrawal Weight: {self.mm_weighted_liquidity_withdrawal:.2f}
  
Consensus:
  Disagreement: {self.behavior_disagreement:.2f} (0=unanimous, 1=split)
  Concentration: {self.behavior_concentration:.2f} (0=balanced, 1=one-sided)
        """


class BehaviorAggregator:
    """
    Aggregates multiple BehaviorProfile objects into AggregatedBehavior.
    
    Weights behaviors by:
    - Participant type (HFT/MM more impactful than retail)
    - Urgency (faster actors matter more)
    - Liquidity role (MM liquidity provision is critical)
    
    Weights are adaptive: they learn from historical prediction accuracy
    using exponential moving average (EMA) tracking.
    """
    
    def __init__(self):
        """Initialize aggregator with adaptive participant weights."""
        # Base weights (importance in market microstructure)
        self._default_weights = {
            ParticipantType.HFT: 0.25,
            ParticipantType.MARKET_MAKER: 0.25,
            ParticipantType.BANK: 0.20,
            ParticipantType.HEDGE_FUND: 0.20,
            ParticipantType.RETAIL: 0.10,
        }
        
        # Adaptive weights (start at defaults, evolve over time)
        self.base_weights = dict(self._default_weights)
        
        # EMA tracking for weight adaptation
        self._ema_alpha = 0.15  # Learning rate
        self._accuracy_ema: Dict[ParticipantType, float] = {
            pt: 0.5 for pt in self._default_weights
        }
        self._outcome_count: Dict[ParticipantType, int] = {
            pt: 0 for pt in self._default_weights
        }
        self._min_weight = 0.05   # Floor: no participant drops below 5%
        self._max_weight = 0.40   # Ceiling: no participant exceeds 40%
    
    def record_participant_accuracy(
        self,
        participant_type: ParticipantType,
        accuracy: float
    ):
        """
        Record how accurate a participant's model was for a given event.
        
        Args:
            participant_type: Which participant model
            accuracy: 0.0 (completely wrong) to 1.0 (perfectly correct)
        """
        if participant_type not in self._accuracy_ema:
            return
        
        # Update EMA
        old_ema = self._accuracy_ema[participant_type]
        self._accuracy_ema[participant_type] = (
            self._ema_alpha * accuracy + (1 - self._ema_alpha) * old_ema
        )
        self._outcome_count[participant_type] += 1
        
        # Rebalance weights after every 5 new outcomes
        total_outcomes = sum(self._outcome_count.values())
        if total_outcomes > 0 and total_outcomes % 5 == 0:
            self._rebalance_weights()
    
    def _rebalance_weights(self):
        """
        Rebalance participant weights based on historical accuracy.
        
        Blends 60% default weight + 40% accuracy-proportional weight.
        Clamps to [min_weight, max_weight] and renormalizes.
        """
        # Only adapt participants with enough data
        total_accuracy = sum(self._accuracy_ema.values())
        if total_accuracy <= 0:
            return
        
        new_weights = {}
        for pt in self._default_weights:
            default_w = self._default_weights[pt]
            accuracy_w = self._accuracy_ema[pt] / total_accuracy
            
            if self._outcome_count[pt] >= 3:
                # Blend: 60% default + 40% accuracy-proportional
                blended = 0.6 * default_w + 0.4 * accuracy_w
            else:
                # Not enough data, stay at default
                blended = default_w
            
            # Clamp
            new_weights[pt] = max(self._min_weight, min(self._max_weight, blended))
        
        # Renormalize to sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            for pt in new_weights:
                new_weights[pt] /= total
        
        self.base_weights = new_weights
    
    def get_weight_diagnostics(self) -> Dict[str, Dict]:
        """Return current weight state for monitoring/debugging."""
        return {
            pt.value if hasattr(pt, 'value') else str(pt): {
                "current_weight": round(self.base_weights[pt], 4),
                "default_weight": round(self._default_weights[pt], 4),
                "accuracy_ema": round(self._accuracy_ema[pt], 4),
                "outcome_count": self._outcome_count[pt],
            }
            for pt in self._default_weights
        }
    
    def aggregate(
        self,
        behaviors: Dict[ParticipantType, BehaviorProfile]
    ) -> AggregatedBehavior:
        """
        Aggregate behavioral profiles into single AggregatedBehavior.
        
        Process:
        1. Extract signals from each behavior
        2. Weight by participant type + urgency
        3. Calculate disagreement and concentration
        4. Return aggregated behavior
        """
        
        if not behaviors:
            raise ValueError("Must provide at least one behavior")
        
        # Step 1: Extract raw signals from each behavior
        signals = {}
        for participant_type, behavior in behaviors.items():
            signals[participant_type] = self._extract_signals(behavior)
        
        # Step 2: Calculate weighted aggregates
        weighted_risk = 0.0
        weighted_liquidity = 0.0
        weighted_exposure = 0.0
        weighted_urgency = 0.0
        weighted_optionality = 0.0
        hft_urgency = 0.0
        bank_risk_reduction = 0.0
        mm_liquidity_withdrawal = 0.0
        
        for participant_type, signal in signals.items():
            weight = self.base_weights[participant_type]
            
            # Apply urgency multiplier (faster = more impact)
            urgency_multiplier = 0.5 + (signal['urgency'] * 0.5)  # 0.5-1.0
            adjusted_weight = weight * urgency_multiplier
            
            weighted_risk += signal['risk'] * adjusted_weight
            weighted_liquidity += signal['liquidity'] * adjusted_weight
            weighted_exposure += signal['exposure'] * adjusted_weight
            weighted_urgency += signal['urgency'] * adjusted_weight
            weighted_optionality += signal['optionality'] * adjusted_weight
            
            # Special weights
            if participant_type == ParticipantType.HFT:
                hft_urgency = signal['urgency']
            elif participant_type == ParticipantType.BANK:
                bank_risk_reduction = max(0, -signal['risk'])  # Negative risk = risk reduction
            elif participant_type == ParticipantType.MARKET_MAKER:
                mm_liquidity_withdrawal = max(0, -signal['liquidity'])  # Negative liq = withdrawal
        
        # Normalize
        total_weight = sum(
            self.base_weights[pt] * (0.5 + (signals[pt]['urgency'] * 0.5))
            for pt in behaviors.keys()
        )
        
        avg_risk = weighted_risk / total_weight
        avg_liquidity = weighted_liquidity / total_weight
        avg_exposure = weighted_exposure / total_weight
        avg_urgency = weighted_urgency / total_weight
        avg_optionality = weighted_optionality / total_weight
        
        # Step 3: Calculate disagreement (dispersion of signals)
        disagreement = self._calculate_disagreement(signals)
        
        # Step 4: Calculate concentration (one-sidedness)
        concentration = self._calculate_concentration(signals)
        
        # Step 5: Identify divergent participants
        divergence = self._identify_divergence(signals, avg_risk, avg_liquidity, avg_exposure)
        
        return AggregatedBehavior(
            avg_risk_posture_signal=avg_risk,
            avg_liquidity_posture_signal=avg_liquidity,
            avg_exposure_intent_signal=avg_exposure,
            avg_urgency_signal=avg_urgency,
            avg_optionality_signal=avg_optionality,
            hft_weighted_urgency=hft_urgency,
            bank_weighted_risk_reduction=bank_risk_reduction,
            mm_weighted_liquidity_withdrawal=mm_liquidity_withdrawal,
            behavior_disagreement=disagreement,
            participant_divergence=divergence,
            behavior_concentration=concentration
        )
    
    def _extract_signals(self, behavior: BehaviorProfile) -> Dict[str, float]:
        """Extract numeric signals from behavior profile."""
        
        # Risk signal: -1 (decrease) to +1 (increase)
        risk_map = {
            "decrease_risk": -1.0,
            "hedge": -0.5,
            "neutral": 0.0,
            "increase_risk": +1.0,
        }
        risk_signal = risk_map.get(behavior.risk_posture.value, 0.0)
        risk_signal *= behavior.risk_probability.likelihood
        
        # Liquidity signal: -1 (withdraw) to +1 (provide)
        liquidity_map = {
            "withdraw_liquidity": -1.0,
            "reduce_liquidity": -0.5,
            "neutral": 0.0,
            "provide_liquidity": +1.0,
        }
        liquidity_signal = liquidity_map.get(behavior.liquidity_posture.value, 0.0)
        liquidity_signal *= behavior.liquidity_probability.likelihood
        
        # Exposure signal: -1 (reduce) to +1 (increase)
        exposure_map = {
            "decrease_exposure": -1.0,
            "maintain_exposure": 0.0,
            "increase_exposure": +1.0,
            "convert_exposure": 0.0,  # Neutral for this aggregation
        }
        exposure_signal = exposure_map.get(behavior.exposure_intent.value, 0.0)
        exposure_signal *= behavior.exposure_probability.likelihood
        
        # Urgency signal: 0 (passive) to 1 (immediate)
        urgency_map = {
            "passive": 0.0,
            "delayed": 0.33,
            "same_day": 0.67,
            "immediate": 1.0,
        }
        urgency_signal = urgency_map.get(behavior.urgency.value, 0.0)
        urgency_signal *= behavior.urgency_probability.likelihood
        
        # Optionality signal: 0 (committed) to 1 (flexible)
        optionality_map = {
            "nothing": 0.0,
            "hedge": 0.25,
            "rebalance": 0.5,
            "wait": 0.75,
            "convert": 0.75,
        }
        optionality_signal = optionality_map.get(behavior.optionality.value, 0.0)
        optionality_signal *= behavior.optionality_probability.likelihood
        
        return {
            'risk': risk_signal,
            'liquidity': liquidity_signal,
            'exposure': exposure_signal,
            'urgency': urgency_signal,
            'optionality': optionality_signal,
        }
    
    def _calculate_disagreement(self, signals: Dict) -> float:
        """Calculate how much participants disagree (0=unanimous, 1=split)."""
        if len(signals) < 2:
            return 0.0
        
        # Calculate standard deviation of signals
        dimensions = ['risk', 'liquidity', 'exposure']
        stds = []
        for dim in dimensions:
            values = [s[dim] for s in signals.values()]
            if values:
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                std = variance ** 0.5
                stds.append(min(1.0, std))  # Cap at 1.0
        
        return sum(stds) / len(stds) if stds else 0.0
    
    def _calculate_concentration(self, signals: Dict) -> float:
        """Calculate concentration (0=balanced, 1=one-sided)."""
        if len(signals) < 2:
            return 0.0
        
        # Check if all signals point same direction
        dimensions = ['risk', 'liquidity', 'exposure']
        concentrations = []
        for dim in dimensions:
            values = [s[dim] for s in signals.values()]
            if values:
                # If all positive or all negative, concentration is high
                all_positive = all(v >= -0.1 for v in values)
                all_negative = all(v <= 0.1 for v in values)
                
                if all_positive or all_negative:
                    concentrations.append(1.0)
                else:
                    # Calculate how skewed
                    positive_count = sum(1 for v in values if v > 0.1)
                    negative_count = sum(1 for v in values if v < -0.1)
                    skew = abs(positive_count - negative_count) / len(values)
                    concentrations.append(skew)
        
        return sum(concentrations) / len(concentrations) if concentrations else 0.0
    
    def _identify_divergence(self, signals: Dict, avg_risk: float, avg_liquidity: float, avg_exposure: float) -> List[Tuple[ParticipantType, float]]:
        """Identify which participants diverge from average."""
        divergence = []
        for participant_type, signal in signals.items():
            # Divergence = distance from average
            risk_div = abs(signal['risk'] - avg_risk)
            liq_div = abs(signal['liquidity'] - avg_liquidity)
            exp_div = abs(signal['exposure'] - avg_exposure)
            
            total_divergence = (risk_div + liq_div + exp_div) / 3.0
            
            if total_divergence > 0.2:  # Threshold for "significant divergence"
                divergence.append((participant_type, total_divergence))
        
        return sorted(divergence, key=lambda x: x[1], reverse=True)


class ImpactTranslator:
    """
    Translates AggregatedBehavior into MarketImpactProfile.
    
    Maps behavioral signals to observable market impacts.
    Accounts for time structure and non-linearity.
    """
    
    def __init__(self):
        """Initialize with impact mapping rules."""
        pass
    
    def translate(
        self,
        aggregated_behavior: AggregatedBehavior,
        news_event_id: str
    ) -> MarketImpactProfile:
        """
        Translate aggregated behavior to market impact profile.
        
        Process:
        1. Identify primary behavioral drivers
        2. Map each driver to expected impacts
        3. Apply non-linearity rules
        4. Calculate time structure for each impact
        5. Assess overall market stress
        6. Return complete impact profile
        """
        
        # Step 1: Identify primary drivers
        drivers = self._identify_drivers(aggregated_behavior)
        
        # Step 2: Generate impacts from drivers
        liquidity_impacts = self._generate_liquidity_impacts(aggregated_behavior, drivers)
        volatility_impacts = self._generate_volatility_impacts(aggregated_behavior, drivers)
        spread_impacts = self._generate_spread_impacts(aggregated_behavior, drivers)
        order_flow_impacts = self._generate_order_flow_impacts(aggregated_behavior, drivers)
        price_impacts = self._generate_price_impacts(aggregated_behavior, drivers)
        regime_impacts = self._generate_regime_impacts(aggregated_behavior, drivers)
        
        # Step 3: Apply non-linearity (threshold, saturation)
        threshold_breached = self._check_threshold_breach(aggregated_behavior)
        saturation = self._check_saturation(aggregated_behavior)
        feedback_risk = self._check_feedback_loops(aggregated_behavior)
        
        # Step 4: Calculate overall market stress
        overall_stress = self._calculate_overall_stress(
            liquidity_impacts, volatility_impacts, spread_impacts,
            order_flow_impacts, price_impacts, regime_impacts
        )
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(aggregated_behavior, drivers)
        
        # Step 6: Generate reasoning
        reasoning = self._generate_reasoning(
            aggregated_behavior, drivers, overall_stress, threshold_breached, saturation
        )
        
        return MarketImpactProfile(
            news_event_id=news_event_id,
            timestamp=datetime.now(),
            liquidity_impacts=liquidity_impacts,
            volatility_impacts=volatility_impacts,
            spread_impacts=spread_impacts,
            order_flow_impacts=order_flow_impacts,
            price_dynamics=price_impacts,
            regime_impacts=regime_impacts,
            overall_market_stress=overall_stress,
            confidence_in_impact=confidence,
            threshold_breached=threshold_breached,
            saturation_detected=saturation,
            feedback_loop_risk=feedback_risk,
            reasoning=reasoning
        )
    
    def _identify_drivers(self, agg: AggregatedBehavior) -> Dict[str, float]:
        """Identify which behaviors are driving impacts."""
        return {
            'liquidity_withdrawal': max(0, -agg.avg_liquidity_posture_signal),
            'risk_reduction': max(0, -agg.avg_risk_posture_signal),
            'exposure_reduction': max(0, -agg.avg_exposure_intent_signal),
            'high_urgency': agg.avg_urgency_signal,
            'behavior_disagreement': agg.behavior_disagreement,
            'behavior_concentration': agg.behavior_concentration,
            'mm_withdrawal': agg.mm_weighted_liquidity_withdrawal,
            'bank_risk_reduction': agg.bank_weighted_risk_reduction,
            'hft_urgency': agg.hft_weighted_urgency,
        }
    
    def _generate_liquidity_impacts(
        self,
        agg: AggregatedBehavior,
        drivers: Dict[str, float]
    ) -> List[ImpactMeasurement]:
        """Generate expected liquidity impacts."""
        impacts = []
        
        # Market maker withdrawal → depth reduction
        if drivers['mm_withdrawal'] > 0.3:
            impacts.append(ImpactMeasurement(
                impact_type=LiquidityImpactType.DEPTH_REDUCTION,
                magnitude=drivers['mm_withdrawal'],
                confidence=0.85,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=0),      # Immediate
                    peak_window=timedelta(seconds=5),
                    decay_time=timedelta(minutes=5),
                    persistence=timedelta(minutes=15)
                ),
                reasoning=f"Market makers withdrawing (withdrawal={drivers['mm_withdrawal']:.2f}), reducing order book depth"
            ))
        
        # Liquidity withdrawal + high disagreement → asymmetry
        if drivers['liquidity_withdrawal'] > 0.4 and agg.behavior_disagreement > 0.3:
            impacts.append(ImpactMeasurement(
                impact_type=LiquidityImpactType.LIQUIDITY_ASYMMETRY,
                magnitude=drivers['liquidity_withdrawal'] * 0.7,
                confidence=0.65,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=1),
                    peak_window=timedelta(seconds=10),
                    decay_time=timedelta(minutes=3),
                    persistence=timedelta(minutes=10)
                ),
                reasoning=f"Liquidity withdrawal ({drivers['liquidity_withdrawal']:.2f}) + disagreement ({agg.behavior_disagreement:.2f}) creating bid-ask imbalance"
            ))
        
        # Extreme liquidity withdrawal → temporary vacuum
        if drivers['liquidity_withdrawal'] > 0.7:
            impacts.append(ImpactMeasurement(
                impact_type=LiquidityImpactType.TEMPORARY_VACUUM,
                magnitude=min(1.0, drivers['liquidity_withdrawal'] - 0.3),
                confidence=0.5,  # Lower confidence, rare event
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=0),
                    peak_window=timedelta(seconds=2),
                    decay_time=timedelta(seconds=30),
                    persistence=timedelta(minutes=1)
                ),
                reasoning=f"Severe liquidity withdrawal ({drivers['liquidity_withdrawal']:.2f}) may create temporary price gaps"
            ))
        
        return impacts
    
    def _generate_volatility_impacts(
        self,
        agg: AggregatedBehavior,
        drivers: Dict[str, float]
    ) -> List[ImpactMeasurement]:
        """Generate expected volatility impacts."""
        impacts = []
        
        # High urgency → instant volatility spike
        if drivers['hft_urgency'] > 0.6:
            impacts.append(ImpactMeasurement(
                impact_type=VolatilityImpactType.INSTANT_SPIKE,
                magnitude=drivers['hft_urgency'],
                confidence=0.9,
                timing=ImpactTiming(
                    onset_delay=timedelta(milliseconds=500),  # Sub-second
                    peak_window=timedelta(seconds=1),
                    decay_time=timedelta(seconds=5),
                    persistence=timedelta(seconds=10)
                ),
                reasoning=f"HFT urgency ({drivers['hft_urgency']:.2f}) triggers immediate volatility spike"
            ))
        
        # Risk reduction + high disagreement → sustained volatility
        if drivers['risk_reduction'] > 0.4 and agg.behavior_disagreement > 0.4:
            impacts.append(ImpactMeasurement(
                impact_type=VolatilityImpactType.SUSTAINED_VOLATILITY,
                magnitude=drivers['risk_reduction'] * 0.8,
                confidence=0.75,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=2),
                    peak_window=timedelta(minutes=5),
                    decay_time=timedelta(minutes=30),
                    persistence=timedelta(hours=1)
                ),
                reasoning=f"Risk reduction ({drivers['risk_reduction']:.2f}) + disagreement ({agg.behavior_disagreement:.2f}) sustains elevated volatility"
            ))
        
        # Concentration (one-sided) → volatility clustering
        if agg.behavior_concentration > 0.6:
            impacts.append(ImpactMeasurement(
                impact_type=VolatilityImpactType.VOLATILITY_CLUSTERING,
                magnitude=agg.behavior_concentration,
                confidence=0.65,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=5),
                    peak_window=timedelta(minutes=10),
                    decay_time=timedelta(minutes=20),
                    persistence=timedelta(hours=2)
                ),
                reasoning=f"One-sided behavior (concentration={agg.behavior_concentration:.2f}) may trigger volatility clustering"
            ))
        
        return impacts
    
    def _generate_spread_impacts(
        self,
        agg: AggregatedBehavior,
        drivers: Dict[str, float]
    ) -> List[ImpactMeasurement]:
        """Generate expected spread impacts."""
        impacts = []
        
        # Liquidity withdrawal → spread widening
        if drivers['liquidity_withdrawal'] > 0.3:
            impacts.append(ImpactMeasurement(
                impact_type=SpreadImpactType.SPREAD_WIDENING,
                magnitude=drivers['liquidity_withdrawal'],
                confidence=0.88,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=0),
                    peak_window=timedelta(seconds=3),
                    decay_time=timedelta(minutes=5),
                    persistence=timedelta(minutes=20)
                ),
                reasoning=f"Liquidity withdrawal ({drivers['liquidity_withdrawal']:.2f}) directly widens bid-ask spread"
            ))
        
        # High urgency + spread widening → spread instability
        if drivers['high_urgency'] > 0.5 and drivers['liquidity_withdrawal'] > 0.3:
            impacts.append(ImpactMeasurement(
                impact_type=SpreadImpactType.SPREAD_INSTABILITY,
                magnitude=min(1.0, drivers['high_urgency'] + drivers['liquidity_withdrawal']) / 2.0,
                confidence=0.6,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=1),
                    peak_window=timedelta(seconds=5),
                    decay_time=timedelta(minutes=3),
                    persistence=timedelta(minutes=10)
                ),
                reasoning=f"Urgency ({drivers['high_urgency']:.2f}) + withdrawal creates spread instability"
            ))
        
        return impacts
    
    def _generate_order_flow_impacts(
        self,
        agg: AggregatedBehavior,
        drivers: Dict[str, float]
    ) -> List[ImpactMeasurement]:
        """Generate expected order flow impacts."""
        impacts = []
        
        # Concentrated behavior → one-sided flow
        if agg.behavior_concentration > 0.6:
            impacts.append(ImpactMeasurement(
                impact_type=OrderFlowImpactType.ONE_SIDED_FLOW,
                magnitude=agg.behavior_concentration,
                confidence=0.82,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=1),
                    peak_window=timedelta(minutes=2),
                    decay_time=timedelta(minutes=10),
                    persistence=timedelta(minutes=30)
                ),
                reasoning=f"One-sided behavior (concentration={agg.behavior_concentration:.2f}) creates one-sided order flow"
            ))
        
        # High urgency → aggressive imbalance
        if drivers['high_urgency'] > 0.6:
            impacts.append(ImpactMeasurement(
                impact_type=OrderFlowImpactType.AGGRESSIVE_IMBALANCE,
                magnitude=drivers['high_urgency'],
                confidence=0.79,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=0),
                    peak_window=timedelta(seconds=5),
                    decay_time=timedelta(seconds=30),
                    persistence=timedelta(minutes=2)
                ),
                reasoning=f"High urgency ({drivers['high_urgency']:.2f}) produces aggressive orders"
            ))
        
        # Disagreement → flow fragmentation
        if agg.behavior_disagreement > 0.5:
            impacts.append(ImpactMeasurement(
                impact_type=OrderFlowImpactType.FLOW_FRAGMENTATION,
                magnitude=agg.behavior_disagreement,
                confidence=0.65,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=2),
                    peak_window=timedelta(minutes=3),
                    decay_time=timedelta(minutes=15),
                    persistence=timedelta(minutes=45)
                ),
                reasoning=f"Disagreement ({agg.behavior_disagreement:.2f}) fragments order flow across sides"
            ))
        
        return impacts
    
    def _generate_price_impacts(
        self,
        agg: AggregatedBehavior,
        drivers: Dict[str, float]
    ) -> List[ImpactMeasurement]:
        """Generate expected price dynamics."""
        impacts = []
        
        # High urgency → jump risk
        if drivers['high_urgency'] > 0.7:
            impacts.append(ImpactMeasurement(
                impact_type=PriceDynamicsType.JUMP_RISK,
                magnitude=drivers['high_urgency'],
                confidence=0.7,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=0),
                    peak_window=timedelta(seconds=2),
                    decay_time=timedelta(minutes=1),
                    persistence=timedelta(minutes=5)
                ),
                reasoning=f"High urgency ({drivers['high_urgency']:.2f}) creates jump risk, prices may gap"
            ))
        
        # Concentrated behavior + high urgency → drift (emergent direction)
        if agg.behavior_concentration > 0.5 and drivers['high_urgency'] > 0.5:
            drift_direction = "unknown"  # We don't predict direction in Phase 4
            impacts.append(ImpactMeasurement(
                impact_type=PriceDynamicsType.DRIFT,
                magnitude=min(agg.behavior_concentration, drivers['high_urgency']),
                confidence=0.55,  # Lower confidence on direction
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=2),
                    peak_window=timedelta(minutes=5),
                    decay_time=timedelta(minutes=30),
                    persistence=timedelta(hours=1)
                ),
                reasoning=f"One-sided behavior creates price drift (concentration={agg.behavior_concentration:.2f}, urgency={drivers['high_urgency']:.2f}) - direction emergent"
            ))
        
        # Risk reduction → mean reversion pressure
        if drivers['risk_reduction'] > 0.4 and agg.behavior_disagreement > 0.3:
            impacts.append(ImpactMeasurement(
                impact_type=PriceDynamicsType.MEAN_REVERSION_PRESSURE,
                magnitude=drivers['risk_reduction'],
                confidence=0.6,
                timing=ImpactTiming(
                    onset_delay=timedelta(minutes=1),
                    peak_window=timedelta(minutes=10),
                    decay_time=timedelta(hours=1),
                    persistence=timedelta(hours=4)
                ),
                reasoning=f"Risk reduction creates temporary mispricing, mean reversion pressure builds"
            ))
        
        return impacts
    
    def _generate_regime_impacts(
        self,
        agg: AggregatedBehavior,
        drivers: Dict[str, float]
    ) -> List[ImpactMeasurement]:
        """Generate expected regime impacts."""
        impacts = []
        
        # High disagreement → regime instability
        if agg.behavior_disagreement > 0.5:
            impacts.append(ImpactMeasurement(
                impact_type=RegimeImpactType.REGIME_INSTABILITY,
                magnitude=agg.behavior_disagreement,
                confidence=0.7,
                timing=ImpactTiming(
                    onset_delay=timedelta(seconds=5),
                    peak_window=timedelta(minutes=10),
                    decay_time=timedelta(hours=1),
                    persistence=timedelta(hours=4)
                ),
                reasoning=f"High disagreement ({agg.behavior_disagreement:.2f}) destabilizes current market regime"
            ))
        
        # Threshold breach → regime transition probability
        if self._check_threshold_breach(agg):
            impacts.append(ImpactMeasurement(
                impact_type=RegimeImpactType.REGIME_TRANSITION_PROBABILITY,
                magnitude=0.6,  # Moderate probability
                confidence=0.5,  # Uncertain when it happens
                timing=ImpactTiming(
                    onset_delay=timedelta(minutes=5),
                    peak_window=timedelta(hours=1),
                    decay_time=timedelta(hours=4),
                    persistence=timedelta(hours=12)
                ),
                reasoning="Behavioral threshold breached, probability of regime transition increases"
            ))
        
        return impacts
    
    def _check_threshold_breach(self, agg: AggregatedBehavior) -> bool:
        """Check if behavior crosses threshold for phase transition."""
        # Threshold: extreme one-sidedness or disagreement
        return (
            (agg.behavior_concentration > 0.75) or  # Extremely one-sided
            (agg.behavior_disagreement > 0.7) or    # Extreme disagreement
            (agg.mm_weighted_liquidity_withdrawal > 0.6)  # MMs withdrawing heavily
        )
    
    def _check_saturation(self, agg: AggregatedBehavior) -> bool:
        """Check if market has reached saturation (impact stops growing)."""
        # Saturation: when extreme behavior doesn't produce proportional impact
        # This happens when market is already under stress
        return (
            (agg.behavior_concentration > 0.8 and agg.hft_weighted_urgency < 0.3) or
            (agg.mm_weighted_liquidity_withdrawal > 0.8)
        )
    
    def _check_feedback_loops(self, agg: AggregatedBehavior) -> bool:
        """Check if conditions could create feedback loops."""
        # Risk: high volatility + more risk reduction + more liquidity withdrawal
        return (
            (agg.behavior_disagreement > 0.6 and agg.hft_weighted_urgency > 0.5) or
            (agg.mm_weighted_liquidity_withdrawal > 0.5 and agg.behavior_concentration > 0.6)
        )
    
    def _calculate_overall_stress(
        self,
        liquidity_impacts: List[ImpactMeasurement],
        volatility_impacts: List[ImpactMeasurement],
        spread_impacts: List[ImpactMeasurement],
        order_flow_impacts: List[ImpactMeasurement],
        price_impacts: List[ImpactMeasurement],
        regime_impacts: List[ImpactMeasurement]
    ) -> float:
        """Calculate overall market stress (0=calm, 1=crisis)."""
        
        all_impacts = (
            liquidity_impacts + volatility_impacts + spread_impacts +
            order_flow_impacts + price_impacts + regime_impacts
        )
        
        if not all_impacts:
            return 0.0
        
        # Weighted average of impact magnitudes
        total_magnitude = sum(i.magnitude * i.confidence for i in all_impacts)
        total_weight = sum(i.confidence for i in all_impacts)
        
        if total_weight == 0:
            return 0.0
        
        return min(1.0, total_magnitude / total_weight)
    
    def _calculate_confidence(self, agg: AggregatedBehavior, drivers: Dict[str, float]) -> float:
        """Calculate overall confidence in impact predictions."""
        
        # Higher confidence when:
        # - Participants agree (low disagreement)
        # - Behavior is concentrated (clear signal)
        # - Drivers are strong
        
        disagreement_penalty = agg.behavior_disagreement * 0.2
        strength = max(drivers.values()) if drivers else 0.0
        concentration_bonus = agg.behavior_concentration * 0.1
        
        base_confidence = 0.6
        confidence = base_confidence + concentration_bonus - disagreement_penalty + (strength * 0.1)
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_reasoning(
        self,
        agg: AggregatedBehavior,
        drivers: Dict[str, float],
        overall_stress: float,
        threshold_breached: bool,
        saturation: bool
    ) -> str:
        """Generate human-readable explanation of impacts."""
        
        reasoning = f"""
Behavioral Aggregation:
- Risk signal: {agg.avg_risk_posture_signal:+.2f} (negative = risk reduction)
- Liquidity signal: {agg.avg_liquidity_posture_signal:+.2f} (negative = withdrawal)
- Exposure signal: {agg.avg_exposure_intent_signal:+.2f} (negative = reduction)
- Disagreement: {agg.behavior_disagreement:.2f} (participants split: {len(agg.participant_divergence)} divergent)
- Concentration: {agg.behavior_concentration:.2f} (one-sidedness)

Market Impact Assessment:
- Overall stress: {overall_stress:.2f} (0=calm, 1=crisis)
- Threshold breached: {threshold_breached}
- Saturation detected: {saturation}

Primary Drivers:
- MM liquidity withdrawal: {drivers['mm_withdrawal']:.2f}
- Bank risk reduction: {drivers['bank_risk_reduction']:.2f}
- HFT urgency: {drivers['hft_urgency']:.2f}

Expected Observable Changes:
1. Liquidity: Market makers reducing depth and provisioning
2. Volatility: Mix of instant spikes (HFT) and sustained (banks)
3. Spreads: Widening as liquidity withdraws
4. Order Flow: One-sided flow concentration
5. Price: Jump risk + potential drift (direction emergent)
6. Regime: Possible transition probability increase
        """
        
        return reasoning


# ============================================================
# MARKET IMPACT CALCULATOR — Unified impact computation
# ============================================================

class MarketImpactCalculator:
    """
    Unified Market Impact Calculator that combines BehaviorAggregator
    and ImpactTranslator into a single end-to-end pipeline.
    
    Pipeline:
        List[BehaviorProfile] → BehaviorAggregator.aggregate()
                              → ImpactTranslator.translate()
                              → MarketImpactProfile
    
    Also provides:
    - Estimated price impact (Kyle's Lambda approximation)
    - Estimated spread impact
    - Estimated volatility impact (in basis points)
    """
    
    def __init__(self):
        self.aggregator = BehaviorAggregator()
        self.translator = ImpactTranslator()
        self.computation_count = 0
        print("[IMPACT_CALC] MarketImpactCalculator initialized")
    
    def calculate(self, behavior_profiles: list) -> dict:
        """
        Full pipeline: behaviors → aggregation → impact translation.
        
        Args:
            behavior_profiles: List of BehaviorProfile objects from Phase 3
            
        Returns:
            Dict with impact assessment including:
            - aggregated_behavior: AggregatedBehavior summary
            - impact_profile: Full 6-dimensional impact assessment
            - estimated_price_impact_bps: Estimated price impact in basis points
            - estimated_spread_widening_pct: Estimated spread widening percentage
            - estimated_vol_spike_pct: Estimated volatility spike percentage  
            - overall_stress: 0.0 to 1.0 stress score
            - reasoning: Human-readable explanation
        """
        self.computation_count += 1
        
        # Step 1: Aggregate behaviors
        try:
            aggregated = self.aggregator.aggregate(behavior_profiles)
        except Exception as e:
            return {
                "error": f"Aggregation failed: {str(e)}",
                "overall_stress": 0.0,
            }
        
        # Step 2: Translate to impact
        try:
            impact = self.translator.translate(aggregated)
        except Exception as e:
            return {
                "error": f"Translation failed: {str(e)}",
                "overall_stress": 0.0,
            }
        
        # Step 3: Compute derived metrics
        # Kyle's Lambda approximation: price impact ≈ stress * liquidity_withdrawal * 100 bps
        liquidity_signal = abs(aggregated.avg_liquidity_posture_signal)
        overall_stress = (
            liquidity_signal * 0.3 +
            abs(aggregated.avg_risk_posture_signal) * 0.25 +
            abs(aggregated.avg_exposure_intent_signal) * 0.2 +
            aggregated.behavior_disagreement * 0.15 +
            aggregated.behavior_concentration * 0.1
        )
        overall_stress = min(1.0, overall_stress)
        
        estimated_price_impact_bps = overall_stress * liquidity_signal * 100
        estimated_spread_widening_pct = liquidity_signal * 50  # bps
        
        # Vol spike estimate based on HFT urgency and disagreement
        vol_spike_pct = (
            aggregated.behavior_disagreement * 0.5 +
            aggregated.behavior_concentration * 0.3
        ) * 200  # In bps
        
        return {
            "overall_stress": round(overall_stress, 3),
            "estimated_price_impact_bps": round(estimated_price_impact_bps, 1),
            "estimated_spread_widening_bps": round(estimated_spread_widening_pct, 1),
            "estimated_vol_spike_bps": round(vol_spike_pct, 1),
            "liquidity_signal": round(aggregated.avg_liquidity_posture_signal, 3),
            "risk_signal": round(aggregated.avg_risk_posture_signal, 3),
            "exposure_signal": round(aggregated.avg_exposure_intent_signal, 3),
            "disagreement": round(aggregated.behavior_disagreement, 3),
            "concentration": round(aggregated.behavior_concentration, 3),
            "computation_id": self.computation_count,
        }
