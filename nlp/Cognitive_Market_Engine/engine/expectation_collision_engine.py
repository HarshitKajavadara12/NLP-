"""
EXPECTATION COLLISION ENGINE

This is the core of the cognitive market system.

Instead of predicting price, we predict:
- Expectation DIVERGENCE (disagreement)
- Time-indexed liquidity stress
- Participant reaction sequencing
- Structural market deformation

This is where real alpha hides.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import numpy as np
from datetime import datetime
from .core_cognitive_structures import (
    ParticipantResponse, NewsEvent, ExpectationVector,
    ParticipantType, LatencyClass
)


# ============================================================================
# COLLISION METRICS
# ============================================================================

@dataclass
class ExpectationCollisionMetrics:
    """
    Metrics quantifying the collision of expectations
    """
    
    # Core collision measures
    expectation_variance: float  # How different are expectations? [0,1]
    direction_disagreement: float  # Do they agree on direction? [0,1]
    timing_disagreement: float  # Do they agree on timing? [0,1]
    magnitude_disagreement: float  # Do they agree on vol? [0,1]
    
    # Liquidity stress
    total_expected_consumption: float  # Aggregate liquidity demand [0,1]
    total_expected_provision: float  # Aggregate liquidity supply [0,1]
    liquidity_stress_index: float  # Supply - Demand balance [-1,1]
    
    # Participant positioning
    buyers_expected: int  # Number expecting price up
    sellers_expected: int  # Number expecting price down
    neutral_expected: int  # Number neutral
    
    # Reaction sequencing
    fastest_reactor: ParticipantType  # Who acts first?
    fastest_reaction_time_sec: float  # When do they act?
    liquidity_providers_acting: bool  # Are MMs withdrawing?
    
    # Time windows (when does collision happen?)
    collision_start_sec: float  # When does impact start?
    collision_peak_sec: float  # When is peak stress?
    collision_end_sec: float  # When does it resolve?
    
    # Overall stress
    market_stress_index: float  # Combined stress [-1,1]
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "expectation_variance": self.expectation_variance,
            "direction_disagreement": self.direction_disagreement,
            "timing_disagreement": self.timing_disagreement,
            "magnitude_disagreement": self.magnitude_disagreement,
            "total_expected_consumption": self.total_expected_consumption,
            "total_expected_provision": self.total_expected_provision,
            "liquidity_stress_index": self.liquidity_stress_index,
            "buyers_expected": self.buyers_expected,
            "sellers_expected": self.sellers_expected,
            "neutral_expected": self.neutral_expected,
            "fastest_reactor": self.fastest_reactor.value if self.fastest_reactor else None,
            "fastest_reaction_time_sec": self.fastest_reaction_time_sec,
            "liquidity_providers_acting": self.liquidity_providers_acting,
            "collision_start_sec": self.collision_start_sec,
            "collision_peak_sec": self.collision_peak_sec,
            "collision_end_sec": self.collision_end_sec,
            "market_stress_index": self.market_stress_index,
        }


@dataclass
class MarketStressVector:
    """
    Complete market-wide stress assessment
    
    This is what the system outputs for trading decisions.
    """
    
    liquidity_stress: float  # [0,1]: How stressed is liquidity?
    volatility_stress: float  # [0,1]: How much vol expected?
    disagreement_index: float  # [0,1]: How much disagreement?
    reaction_asymmetry: float  # [0,1]: Unequal participation?
    regime_fragility: float  # [0,1]: System fragility?
    
    # Time projection
    immediate_impact_expected: bool  # Next 1 minute?
    hft_volatility_spike: bool  # Expected HFT reaction?
    structural_opportunity: float  # [0,1]: Is there alpha?
    confidence_in_assessment: float  # [0,1]: How confident in this?
    
    # Defaults
    retail_panic_window: Tuple[float, float] = (0, 0)  # Minutes
    institutional_rebalance_window: Tuple[float, float] = (0, 0)  # Minutes
    collision_metrics: Optional[ExpectationCollisionMetrics] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "liquidity_stress": self.liquidity_stress,
            "volatility_stress": self.volatility_stress,
            "disagreement_index": self.disagreement_index,
            "reaction_asymmetry": self.reaction_asymmetry,
            "regime_fragility": self.regime_fragility,
            "immediate_impact_expected": self.immediate_impact_expected,
            "hft_volatility_spike": self.hft_volatility_spike,
            "retail_panic_window": self.retail_panic_window,
            "institutional_rebalance_window": self.institutional_rebalance_window,
            "structural_opportunity": self.structural_opportunity,
            "confidence_in_assessment": self.confidence_in_assessment,
            "collision_metrics": self.collision_metrics.to_dict() if self.collision_metrics else None,
        }


# ============================================================================
# COLLISION ENGINE
# ============================================================================

class ExpectationCollisionEngine:
    """
    The core engine that computes expectation collisions
    
    This is where the system becomes unique.
    """
    
    def __init__(self):
        self.collision_history: List[ExpectationCollisionMetrics] = []
    
    def compute_collision(self, news_event: NewsEvent) -> Tuple[ExpectationCollisionMetrics, MarketStressVector]:
        """
        Compute the collision of all participant expectations
        
        Returns:
            - ExpectationCollisionMetrics: Detailed collision analysis
            - MarketStressVector: Trading-actionable stress assessment
        """
        
        responses = list(news_event.participant_responses.values())
        
        if not responses:
            raise ValueError("No participant responses to collide")
        
        # =====================================================
        # STEP 1: Extract expectations
        # =====================================================
        
        expectations_by_type: Dict[ParticipantType, ExpectationVector] = {
            r.profile.type: r.expectation_vector for r in responses
        }
        
        # =====================================================
        # STEP 2: Compute expectation variance
        # =====================================================
        
        vol_expectations = np.array([e.volatility_expectation for e in expectations_by_type.values()])
        liquidity_expectations = np.array([e.liquidity_expectation for e in expectations_by_type.values()])
        spread_expectations = np.array([e.spread_expectation for e in expectations_by_type.values()])
        time_horizons = np.array([e.time_horizon for e in expectations_by_type.values()])
        peak_times = np.array([e.peak_impact_time for e in expectations_by_type.values()])
        
        expectation_variance = np.mean([
            np.var(vol_expectations) / (np.mean(vol_expectations) + 0.01),
            np.var(liquidity_expectations) / (np.mean(liquidity_expectations) + 0.01),
            np.var(spread_expectations) / (np.mean(spread_expectations) + 0.01),
        ])
        expectation_variance = min(1.0, expectation_variance)
        
        # =====================================================
        # STEP 3: Compute direction disagreement
        # =====================================================
        
        direction_biases = np.array([e.direction_bias for e in expectations_by_type.values()])
        buyers = np.sum(direction_biases > 0.1)
        sellers = np.sum(direction_biases < -0.1)
        neutral = len(responses) - buyers - sellers
        
        direction_disagreement = 0.0
        if len(responses) > 1:
            if buyers > 0 and sellers > 0:
                direction_disagreement = abs(buyers - sellers) / len(responses)
            elif buyers > 0 or sellers > 0:
                direction_disagreement = 0.5  # One-sided is moderate disagreement
        
        # =====================================================
        # STEP 4: Compute timing disagreement
        # =====================================================
        
        timing_disagreement = np.std(peak_times) / (np.mean(peak_times) + 1.0)
        timing_disagreement = min(1.0, timing_disagreement)
        
        # =====================================================
        # STEP 5: Compute magnitude disagreement
        # =====================================================
        
        magnitude_disagreement = np.std(vol_expectations) / (np.mean(vol_expectations) + 0.01)
        magnitude_disagreement = min(1.0, magnitude_disagreement)
        
        # =====================================================
        # STEP 6: Compute liquidity stress
        # =====================================================
        
        total_consumption = 0.0
        total_provision = 0.0
        
        for response in responses:
            will_act = response.will_act
            if will_act:
                action_mag = response.action_magnitude
                
                # Does this participant consume or provide liquidity?
                if response.profile.consumes_liquidity:
                    total_consumption += action_mag
                if response.profile.provides_liquidity:
                    total_provision += action_mag
        
        total_consumption = min(1.0, total_consumption)
        total_provision = min(1.0, total_provision)
        
        # Liquidity stress: consumption minus provision
        # Negative = stressed (more consumption than provision)
        # Positive = ample (more provision than consumption)
        liquidity_stress_index = total_provision - total_consumption  # Range: [-1, 1]
        
        # =====================================================
        # STEP 7: Reaction sequencing
        # =====================================================
        
        fastest_response = min(responses, key=lambda r: r.behavior_intention.reaction_delay_seconds)
        fastest_reactor = fastest_response.profile.type
        fastest_reaction_time = fastest_response.behavior_intention.reaction_delay_seconds
        
        # Do liquidity providers (MMs) have high urgency? (withdrawal signal)
        mm_responses = [r for r in responses if r.profile.type == ParticipantType.MARKET_MAKER]
        liquidity_providers_withdrawing = any(r.cognitive_state.urgency > 0.7 for r in mm_responses) if mm_responses else False
        
        # =====================================================
        # STEP 8: Time windows (when does collision happen?)
        # =====================================================
        
        collision_start = fastest_reaction_time / 60.0  # Convert to minutes
        collision_peak = np.mean(peak_times) / 60.0 if len(peak_times) > 0 else 0.5
        collision_end = np.max(time_horizons) / 60.0 if len(time_horizons) > 0 else 60.0
        
        # =====================================================
        # STEP 9: Market stress index
        # =====================================================
        
        # Stress is high when:
        # - High disagreement
        # - High liquidity stress
        # - High volatility expectations
        # - Market makers withdrawing
        
        mean_vol_expectation = np.mean(vol_expectations)
        
        market_stress_index = (
            expectation_variance * 0.25 +
            abs(liquidity_stress_index) * 0.25 +
            mean_vol_expectation * 0.25 +
            (0.25 if liquidity_providers_withdrawing else 0.0)
        )
        market_stress_index = min(1.0, market_stress_index)
        
        # =====================================================
        # BUILD COLLISION METRICS OBJECT
        # =====================================================
        
        collision_metrics = ExpectationCollisionMetrics(
            expectation_variance=expectation_variance,
            direction_disagreement=direction_disagreement,
            timing_disagreement=timing_disagreement,
            magnitude_disagreement=magnitude_disagreement,
            total_expected_consumption=total_consumption,
            total_expected_provision=total_provision,
            liquidity_stress_index=liquidity_stress_index,
            buyers_expected=int(buyers),
            sellers_expected=int(sellers),
            neutral_expected=int(neutral),
            fastest_reactor=fastest_reactor,
            fastest_reaction_time_sec=fastest_reaction_time,
            liquidity_providers_acting=liquidity_providers_withdrawing,
            collision_start_sec=collision_start * 60.0,  # Back to seconds
            collision_peak_sec=collision_peak * 60.0,
            collision_end_sec=collision_end * 60.0,
            market_stress_index=market_stress_index,
        )
        
        # =====================================================
        # BUILD MARKET STRESS VECTOR (TRADING SIGNAL)
        # =====================================================
        
        # Liquidity stress is the scaled stress index
        liquidity_stress = max(0.0, -liquidity_stress_index)  # Higher if more consumption
        
        # Volatility stress: mean expected vol
        volatility_stress = mean_vol_expectation
        
        # Disagreement index: how much do they disagree?
        disagreement_index = expectation_variance
        
        # Reaction asymmetry: Is one participant group dominant?
        reaction_sizes = [r.action_magnitude for r in responses if r.will_act]
        if len(reaction_sizes) > 1:
            reaction_asymmetry = np.std(reaction_sizes) / (np.mean(reaction_sizes) + 0.01)
            reaction_asymmetry = min(1.0, reaction_asymmetry)
        else:
            reaction_asymmetry = 0.0
        
        # Regime fragility: When multiple things are uncertain, system is fragile
        regime_fragility = (
            expectation_variance * 0.4 +
            timing_disagreement * 0.3 +
            liquidity_stress * 0.3
        )
        
        # Timing projections
        immediate_impact = fastest_reaction_time < 1.0  # Less than 1 second = immediate
        hft_volatility = any(r.profile.type == ParticipantType.HFT and r.will_act 
                            for r in responses)
        
        # Retail panic window (retail reacts 3-7 minutes after HFT)
        retail_panic_window = (3.0, 7.0)
        
        # Institutional rebalance window (30min-2hour after HFT)
        institutional_rebalance_window = (30.0, 120.0)
        
        # Structural opportunity
        # High opportunity when:
        # - High disagreement (others are wrong)
        # - But not too fragile (system holds together)
        structural_opportunity = (
            expectation_variance * 0.4 +
            direction_disagreement * 0.3 -
            regime_fragility * 0.3
        )
        structural_opportunity = max(0.0, min(1.0, structural_opportunity))
        
        # Confidence in this assessment
        confidence = min(1.0, 1.0 - expectation_variance / 2.0)  # Higher variance = lower confidence
        
        market_stress_vector = MarketStressVector(
            liquidity_stress=liquidity_stress,
            volatility_stress=volatility_stress,
            disagreement_index=disagreement_index,
            reaction_asymmetry=reaction_asymmetry,
            regime_fragility=regime_fragility,
            immediate_impact_expected=immediate_impact,
            hft_volatility_spike=hft_volatility,
            retail_panic_window=retail_panic_window,
            institutional_rebalance_window=institutional_rebalance_window,
            structural_opportunity=structural_opportunity,
            confidence_in_assessment=confidence,
            collision_metrics=collision_metrics,
        )
        
        # Store in history
        self.collision_history.append(collision_metrics)
        
        return collision_metrics, market_stress_vector


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "ExpectationCollisionMetrics",
    "MarketStressVector",
    "ExpectationCollisionEngine",
]
