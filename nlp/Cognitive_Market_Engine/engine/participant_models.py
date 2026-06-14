"""
PARTICIPANT MODELS

Define how each participant type THINKS, not what they do.

This is the core cognitive differentiation that makes the system work.
Each participant has a different transformation function:

News → (Cognitive Model) → Expectation Vector

This is where alpha is hidden.
"""

from typing import Callable
from dataclasses import dataclass
from .core_cognitive_structures import (
    ParticipantType, LatencyClass, CapitalScale, ParticipantProfile,
    LinguisticShockVector, CognitiveState, ExpectationVector,
    BehaviorIntention, ParticipantResponse, NewsEvent
)
from datetime import datetime


# ============================================================================
# PARTICIPANT MODEL DEFINITIONS
# ============================================================================

class RetailTraderModel:
    """
    Retail Trader Cognition
    
    Characteristics:
    - Emotion-dominant thinking
    - Delayed reaction (minutes)
    - Overweights narrative tone and certainty
    - Prone to FOMO and panic
    - Small position sizes
    - Low historical accuracy
    """
    
    profile = ParticipantProfile(
        type=ParticipantType.RETAIL,
        latency_class=LatencyClass.FAST,  # 5-15 minutes
        capital_scale=CapitalScale.RETAIL,
        max_position_pct=0.05,  # Max 5% in one stock
        leverage_limit=1.0,  # No leverage
        historical_reliability=0.45,  # Poor
        overreaction_tendency=0.85,  # Very emotional
        reversal_tendency=0.80,  # Quick reversals
        uses_sentiment=True,
        uses_technicals=True,
        uses_fundamentals=False,
        provides_liquidity=False,
        consumes_liquidity=True,
        name="Retail Trader",
        description="Emotion-driven, fast but inaccurate"
    )
    
    @staticmethod
    def interpret(news_event: NewsEvent) -> ParticipantResponse:
        """
        How retail traders interpret news
        
        Key mechanism: uncertainty + novelty → panic/FOMO
        """
        
        lsv = news_event.linguistic_shock
        
        # Retail belief shift heavily weighted on emotional tone
        # High surprise + high ambiguity = high uncertainty = potential panic
        belief_shift = (
            lsv.surprise_level * 0.4 +
            lsv.novelty_score * 0.3 +
            (1.0 - lsv.certainty_level) * 0.3  # Ambiguity causes uncertainty
        )
        
        # Retail is very sensitive to narrative change
        if lsv.narrative_shift.value == "regime_change":
            belief_shift = min(1.0, belief_shift + 0.3)
        
        # Risk perception: retail overestimates tail risk
        risk_perception = (
            lsv.surprise_level * 0.4 +
            lsv.ambiguity_level * 0.3 +
            (1.0 - lsv.certainty_level) * 0.3
        )
        
        # Confidence: inverse of ambiguity for retail (they trade what's certain)
        confidence = max(0.2, 1.0 - lsv.ambiguity_level)
        
        # Urgency: high surprise = high urgency for retail
        urgency = min(0.95, lsv.surprise_level * 0.8 + lsv.novelty_score * 0.2)
        
        # Uncertainty: high ambiguity = high uncertainty
        uncertainty = lsv.ambiguity_level
        
        # Action bias: if emotional, retail acts
        action_bias = max(0.6, belief_shift * 0.8)
        
        cognitive_state = CognitiveState(
            belief_shift=belief_shift,
            risk_perception=risk_perception,
            confidence=confidence,
            urgency=urgency,
            uncertainty=uncertainty,
            action_bias=action_bias,
            information_latency=180.0,  # 3 minutes to process
            source_credibility=lsv.authority_strength * 0.8,  # Slightly discount authority
        )
        
        # Expectations: retail expects vol spike + directional move
        # But they're often wrong, so we'll use weaker weights
        direction_bias = (
            lsv.surprise_level * 0.5 - 0.25  # Surprise = slightly bearish (fear)
        ) if lsv.surprise_level > 0.6 else 0.0
        
        expectation_vector = ExpectationVector(
            volatility_expectation=min(0.95, lsv.surprise_level * 0.9),
            liquidity_expectation=0.6,  # Retail assumes liquidity exists
            spread_expectation=lsv.surprise_level * 0.4,
            direction_bias=direction_bias,
            volume_expectation=lsv.surprise_level * 0.8,
            tail_risk_awareness=lsv.ambiguity_level * 0.8,
            correlation_expectation=0.5,  # Neutral
            time_horizon=30.0,  # Thinks in minutes
            peak_impact_time=5.0,  # Thinks impact is immediate
        )
        
        # Behavior: retail buys/sells aggressively and immediately
        behavior_intention = BehaviorIntention(
            aggressiveness=0.85,
            patience=0.2,
            size_preference=0.3,
            execution_style="aggressive",
            reaction_delay_seconds=max(60, 180 + int(uncertainty * 120)),
            is_mechanical=False,
            uses_stops=False,  # Most don't
            stop_loss_distance=0.05,
            takes_profits=True,
            profit_target_distance=0.03,
        )
        
        stimulus_time = datetime.now()
        response_time = datetime.now()  # Will be updated with latency
        
        return ParticipantResponse(
            profile=RetailTraderModel.profile,
            news_event_id=news_event.event_id,
            linguistic_shock=lsv,
            cognitive_state=cognitive_state,
            expectation_vector=expectation_vector,
            behavior_intention=behavior_intention,
            stimulus_time=stimulus_time,
            response_time=response_time,
        )


class HFTModel:
    """
    High-Frequency Trading Bot Cognition
    
    Characteristics:
    - ZERO belief in news
    - ZERO narrative interpretation
    - Pure microstructure reaction
    - Instant latency (microseconds)
    - Large but short-lived positions
    - Very high historical accuracy on structure
    """
    
    profile = ParticipantProfile(
        type=ParticipantType.HFT,
        latency_class=LatencyClass.INSTANT,
        capital_scale=CapitalScale.MEGA,
        max_position_pct=0.20,  # Smaller positions, high churn
        leverage_limit=5.0,  # Significant leverage
        historical_reliability=0.92,  # Excellent on structure
        overreaction_tendency=0.05,  # No emotion
        reversal_tendency=0.15,  # Holds for seconds
        uses_sentiment=False,
        uses_technicals=False,
        uses_fundamentals=False,
        provides_liquidity=True,
        consumes_liquidity=True,
        name="HFT Algorithm",
        description="Zero belief, pure structure reaction"
    )
    
    @staticmethod
    def interpret(news_event: NewsEvent) -> ParticipantResponse:
        """
        HFT interpretation: NOT the news itself, but market reaction to others' reactions
        
        HFT reacts to:
        - Volatility spike
        - Ambiguity (creates order flow imbalance)
        - OTHER participants panicking
        
        HFT does NOT react to:
        - Direction
        - Fundamentals
        - Narrative
        """
        
        lsv = news_event.linguistic_shock
        
        # HFT: zero belief in fundamental meaning
        belief_shift = 0.0  # HFT doesn't believe the news
        
        # Risk perception: HFT cares about microstructure risk (adverse selection)
        risk_perception = (
            lsv.ambiguity_level * 0.7 +  # Ambiguity = order flow imbalance
            lsv.surprise_level * 0.3  # Surprise = volatility
        )
        
        # Confidence: HFT is confident in structural reactions
        confidence = 0.95  # HFTs know how to trade vol
        
        # Urgency: MAXIMUM (must act first)
        urgency = 1.0
        
        # Uncertainty: LOW (HFTs understand structure)
        uncertainty = lsv.ambiguity_level * 0.2
        
        # Action bias: ALWAYS act (HFT is a trading machine)
        action_bias = 1.0
        
        cognitive_state = CognitiveState(
            belief_shift=belief_shift,
            risk_perception=risk_perception,
            confidence=confidence,
            urgency=urgency,
            uncertainty=uncertainty,
            action_bias=action_bias,
            information_latency=0.001,  # 1ms processing
            source_credibility=0.0,  # HFT doesn't care about source
        )
        
        # Expectations: HFT expects volatility spike + order flow imbalance
        # No directional bias (HFTs are market-neutral)
        
        expectation_vector = ExpectationVector(
            volatility_expectation=min(1.0, lsv.surprise_level * 0.9 + lsv.ambiguity_level * 0.5),
            liquidity_expectation=max(0.2, 1.0 - lsv.ambiguity_level),  # Ambiguity = thinner liquidity
            spread_expectation=min(0.95, lsv.surprise_level * 0.8 + lsv.ambiguity_level * 0.6),
            direction_bias=0.0,  # HFT is neutral
            volume_expectation=lsv.surprise_level * 0.9,
            tail_risk_awareness=lsv.ambiguity_level * 0.3,  # HFT doesn't worry about tails
            correlation_expectation=0.7,  # Expects spillovers
            time_horizon=2.0,  # Thinks in seconds
            peak_impact_time=0.5,  # Peak is immediate
        )
        
        # Behavior: HFT executes immediately and mechanically
        behavior_intention = BehaviorIntention(
            aggressiveness=1.0,  # Always aggressive
            patience=0.0,  # Zero patience
            size_preference=0.7,  # Large positions
            execution_style="predatory",  # Predatory algorithms
            reaction_delay_seconds=0.001,  # Microseconds
            is_mechanical=True,  # Fully automated
            uses_stops=False,  # No stops (speed exits instead)
            stop_loss_distance=0.0,
            takes_profits=False,  # Auto-exits on structure
            profit_target_distance=0.0001,  # Tiny targets
        )
        
        stimulus_time = datetime.now()
        response_time = datetime.now()
        
        return ParticipantResponse(
            profile=HFTModel.profile,
            news_event_id=news_event.event_id,
            linguistic_shock=lsv,
            cognitive_state=cognitive_state,
            expectation_vector=expectation_vector,
            behavior_intention=behavior_intention,
            stimulus_time=stimulus_time,
            response_time=response_time,
        )


class HedgeFundModel:
    """
    Hedge Fund Cognition
    
    Characteristics:
    - Thesis-driven interpretation
    - Medium reaction time (minutes to hours)
    - Analyzes fundamentals + technicals
    - Positions held for hours/days
    - High research quality
    - Good historical accuracy
    """
    
    profile = ParticipantProfile(
        type=ParticipantType.HEDGE_FUND,
        latency_class=LatencyClass.MEDIUM,  # 10-30 minutes
        capital_scale=CapitalScale.MEGA,
        max_position_pct=0.15,  # Medium conviction
        leverage_limit=3.0,
        historical_reliability=0.75,  # Good
        overreaction_tendency=0.35,  # Thoughtful
        reversal_tendency=0.40,  # Medium reversals
        uses_sentiment=True,
        uses_technicals=True,
        uses_fundamentals=True,
        provides_liquidity=False,
        consumes_liquidity=True,
        name="Hedge Fund",
        description="Thesis-driven, balanced research"
    )
    
    @staticmethod
    def interpret(news_event: NewsEvent) -> ParticipantResponse:
        """
        Hedge fund interpretation: research-quality assessment
        
        Key mechanism: certainty + authority → thesis validation/invalidation
        """
        
        lsv = news_event.linguistic_shock
        
        # HF belief shift: weighted on certainty + authority (research quality)
        belief_shift = (
            lsv.certainty_level * 0.4 +  # Certainty validates/invalidates thesis
            lsv.authority_strength * 0.3 +  # Authoritative sources matter
            lsv.surprise_level * 0.3  # Surprises adjust thesis
        )
        
        # Risk perception: HF is sophisticated
        risk_perception = (
            lsv.novelty_score * 0.4 +
            lsv.ambiguity_level * 0.3 +
            (1.0 - lsv.certainty_level) * 0.3
        )
        
        # Confidence: HF is more confident (they research)
        confidence = min(0.95, lsv.certainty_level * 0.9 + lsv.authority_strength * 0.1)
        
        # Urgency: Medium (they have time to analyze)
        urgency = belief_shift * 0.6  # Only urgent if thesis is threatened
        
        # Uncertainty: Low (they research)
        uncertainty = lsv.ambiguity_level * 0.5
        
        # Action bias: Depends on thesis validation
        action_bias = belief_shift * 0.7
        
        cognitive_state = CognitiveState(
            belief_shift=belief_shift,
            risk_perception=risk_perception,
            confidence=confidence,
            urgency=urgency,
            uncertainty=uncertainty,
            action_bias=action_bias,
            information_latency=600.0,  # 10 minutes research
            source_credibility=lsv.authority_strength,  # Value authority
        )
        
        # Expectations: HF expects medium-term impact
        direction_bias = (
            lsv.certainty_level * 0.4 - 0.2  # Certainty suggests direction
        ) if lsv.certainty_level > 0.7 else 0.0
        
        expectation_vector = ExpectationVector(
            volatility_expectation=lsv.surprise_level * 0.6,
            liquidity_expectation=0.7,
            spread_expectation=lsv.surprise_level * 0.3,
            direction_bias=direction_bias,
            volume_expectation=lsv.surprise_level * 0.6,
            tail_risk_awareness=lsv.ambiguity_level * 0.6,
            correlation_expectation=0.6,
            time_horizon=300.0,  # 5 hours
            peak_impact_time=60.0,  # 1 hour
        )
        
        # Behavior: HF is patient and methodical
        behavior_intention = BehaviorIntention(
            aggressiveness=0.60,
            patience=0.75,
            size_preference=0.70,
            execution_style="algorithmic",
            reaction_delay_seconds=int(600 + uncertainty * 300),
            is_mechanical=False,
            uses_stops=True,
            stop_loss_distance=0.08,
            takes_profits=True,
            profit_target_distance=0.05,
        )
        
        stimulus_time = datetime.now()
        response_time = datetime.now()
        
        return ParticipantResponse(
            profile=HedgeFundModel.profile,
            news_event_id=news_event.event_id,
            linguistic_shock=lsv,
            cognitive_state=cognitive_state,
            expectation_vector=expectation_vector,
            behavior_intention=behavior_intention,
            stimulus_time=stimulus_time,
            response_time=response_time,
        )


class BankModel:
    """
    Bank Cognition
    
    Characteristics:
    - Balance-sheet driven thinking
    - Regulatory constraint focus
    - Very slow reaction (hours to days)
    - Huge position sizes
    - Risk-averse
    - Can cause regime shifts
    """
    
    profile = ParticipantProfile(
        type=ParticipantType.BANK,
        latency_class=LatencyClass.VERY_SLOW,  # Hours to days
        capital_scale=CapitalScale.MEGA,
        max_position_pct=0.25,  # Large absolute size
        leverage_limit=15.0,  # But regulatory cap
        historical_reliability=0.70,  # Slow but steady
        overreaction_tendency=0.20,  # Very conservative
        reversal_tendency=0.10,  # Positions persist
        uses_sentiment=False,
        uses_technicals=False,
        uses_fundamentals=True,
        provides_liquidity=True,
        consumes_liquidity=False,
        name="Bank",
        description="Regulatory, balance-sheet driven"
    )
    
    @staticmethod
    def interpret(news_event: NewsEvent) -> ParticipantResponse:
        """
        Bank interpretation: regulatory + balance sheet impact
        
        Key mechanism: regulatory keywords + certainty → rebalancing
        """
        
        lsv = news_event.linguistic_shock
        
        # Bank belief shift: weighted on macro relevance + authority
        is_regulatory = any(word in news_event.raw_text.lower() 
                           for word in ["regulation", "stress test", "capital", "basel"])
        
        belief_shift = (
            lsv.authority_strength * 0.5 +  # Banks trust authorities
            lsv.certainty_level * 0.3 +
            (0.3 if is_regulatory else 0.0)  # Regulatory news matters
        )
        
        # Risk perception: Banks are very risk-sensitive
        risk_perception = (
            (0.5 if is_regulatory else 0.0) +
            lsv.surprise_level * 0.3 +
            (1.0 - lsv.certainty_level) * 0.2
        )
        
        # Confidence: Banks are confident (have access to info)
        confidence = lsv.authority_strength * 0.9
        
        # Urgency: Very low (they don't panic)
        urgency = risk_perception * 0.3
        
        # Uncertainty: Medium
        uncertainty = lsv.ambiguity_level * 0.4
        
        # Action bias: Low (they move slowly)
        action_bias = belief_shift * 0.3
        
        cognitive_state = CognitiveState(
            belief_shift=belief_shift,
            risk_perception=risk_perception,
            confidence=confidence,
            urgency=urgency,
            uncertainty=uncertainty,
            action_bias=action_bias,
            information_latency=3600.0,  # 1 hour minimum
            source_credibility=lsv.authority_strength,
        )
        
        # Expectations: Banks expect regime change, not daily noise
        direction_bias = 0.0  # Banks don't predict direction
        
        expectation_vector = ExpectationVector(
            volatility_expectation=0.3,  # Banks don't expect vol
            liquidity_expectation=0.8,  # Banks assume liquidity
            spread_expectation=0.1,  # Banks don't expect spread widening
            direction_bias=direction_bias,
            volume_expectation=0.2,  # Banks aren't volume-focused
            tail_risk_awareness=0.6,  # Banks worry about tails
            correlation_expectation=0.8,  # Banks expect systemic effects
            time_horizon=480.0,  # 8 hours
            peak_impact_time=240.0,  # 4 hours
        )
        
        # Behavior: Banks are mechanical and institutional
        behavior_intention = BehaviorIntention(
            aggressiveness=0.30,
            patience=0.95,
            size_preference=1.0,  # Largest size
            execution_style="algorithmic",
            reaction_delay_seconds=int(3600 + uncertainty * 3600),
            is_mechanical=True,
            uses_stops=False,  # Never
            stop_loss_distance=0.0,
            takes_profits=False,  # Position management only
            profit_target_distance=0.0,
        )
        
        stimulus_time = datetime.now()
        response_time = datetime.now()
        
        return ParticipantResponse(
            profile=BankModel.profile,
            news_event_id=news_event.event_id,
            linguistic_shock=lsv,
            cognitive_state=cognitive_state,
            expectation_vector=expectation_vector,
            behavior_intention=behavior_intention,
            stimulus_time=stimulus_time,
            response_time=response_time,
        )


class MarketMakerModel:
    """
    Market Maker Cognition
    
    Characteristics:
    - Inventory-driven thinking
    - Spread-based survival logic
    - Instant reaction (microseconds)
    - Shallow positions
    - Defensive behavior
    - Zero belief, pure economics
    """
    
    profile = ParticipantProfile(
        type=ParticipantType.MARKET_MAKER,
        latency_class=LatencyClass.INSTANT,
        capital_scale=CapitalScale.INSTITUTIONAL,
        max_position_pct=0.05,  # Very small positions
        leverage_limit=3.0,
        historical_reliability=0.88,  # Good on execution
        overreaction_tendency=0.10,  # Very conservative
        reversal_tendency=0.95,  # Instant reversals
        uses_sentiment=False,
        uses_technicals=False,
        uses_fundamentals=False,
        provides_liquidity=True,
        consumes_liquidity=False,
        name="Market Maker",
        description="Inventory-driven, spread economics"
    )
    
    @staticmethod
    def interpret(news_event: NewsEvent) -> ParticipantResponse:
        """
        Market maker interpretation: disagr eement level
        
        Key mechanism: ambiguity → spread widening → reduce inventory
        """
        
        lsv = news_event.linguistic_shock
        
        # MM belief shift: zero
        belief_shift = 0.0
        
        # Risk perception: MM cares about inventory risk
        risk_perception = (
            lsv.ambiguity_level * 0.6 +  # Ambiguity = wider spreads needed
            lsv.surprise_level * 0.4  # Surprise = inventory risk
        )
        
        # Confidence: MM is confident in execution
        confidence = 0.95
        
        # Urgency: High (must rebalance)
        urgency = risk_perception * 0.9
        
        # Uncertainty: Low
        uncertainty = lsv.ambiguity_level * 0.3
        
        # Action bias: Always act (defensive)
        action_bias = risk_perception * 0.8
        
        cognitive_state = CognitiveState(
            belief_shift=belief_shift,
            risk_perception=risk_perception,
            confidence=confidence,
            urgency=urgency,
            uncertainty=uncertainty,
            action_bias=action_bias,
            information_latency=0.01,  # 10ms
            source_credibility=0.0,  # MM doesn't care about news source
        )
        
        # Expectations: MM expects wider spreads
        expectation_vector = ExpectationVector(
            volatility_expectation=min(0.8, lsv.surprise_level * 0.7 + lsv.ambiguity_level * 0.5),
            liquidity_expectation=max(0.2, 1.0 - lsv.ambiguity_level),
            spread_expectation=min(0.95, lsv.ambiguity_level * 0.9 + lsv.surprise_level * 0.5),
            direction_bias=0.0,
            volume_expectation=lsv.surprise_level * 0.7,
            tail_risk_awareness=lsv.ambiguity_level * 0.5,
            correlation_expectation=0.6,
            time_horizon=5.0,
            peak_impact_time=0.1,  # Immediate
        )
        
        # Behavior: MM is mechanical and defensive
        behavior_intention = BehaviorIntention(
            aggressiveness=0.50,  # Defensive aggression
            patience=0.0,  # No patience
            size_preference=0.3,  # Small positions
            execution_style="passive",  # Post spreads
            reaction_delay_seconds=0.01,  # 10ms
            is_mechanical=True,
            uses_stops=False,
            stop_loss_distance=0.0,
            takes_profits=False,
            profit_target_distance=0.001,
        )
        
        stimulus_time = datetime.now()
        response_time = datetime.now()
        
        return ParticipantResponse(
            profile=MarketMakerModel.profile,
            news_event_id=news_event.event_id,
            linguistic_shock=lsv,
            cognitive_state=cognitive_state,
            expectation_vector=expectation_vector,
            behavior_intention=behavior_intention,
            stimulus_time=stimulus_time,
            response_time=response_time,
        )


# ============================================================================
# MODEL REGISTRY
# ============================================================================

PARTICIPANT_MODELS = {
    ParticipantType.RETAIL: RetailTraderModel,
    ParticipantType.HFT: HFTModel,
    ParticipantType.HEDGE_FUND: HedgeFundModel,
    ParticipantType.BANK: BankModel,
    ParticipantType.MARKET_MAKER: MarketMakerModel,
}


def create_participant_response(news_event: NewsEvent, 
                               participant_type: ParticipantType) -> ParticipantResponse:
    """
    Factory function: create response from participant type + news
    """
    model_class = PARTICIPANT_MODELS.get(participant_type)
    if not model_class:
        raise ValueError(f"Unknown participant type: {participant_type}")
    
    return model_class.interpret(news_event)


def interpret_news_with_all_participants(news_event: NewsEvent) -> NewsEvent:
    """
    Have all 5 participants interpret the same news event
    
    This creates the collision map.
    """
    for participant_type in ParticipantType:
        response = create_participant_response(news_event, participant_type)
        news_event.add_response(response)
    
    return news_event


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "RetailTraderModel",
    "HFTModel",
    "HedgeFundModel",
    "BankModel",
    "MarketMakerModel",
    "PARTICIPANT_MODELS",
    "create_participant_response",
    "interpret_news_with_all_participants",
]
