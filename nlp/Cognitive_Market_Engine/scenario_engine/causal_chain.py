"""
CAUSAL CHAIN BUILDER — 1st → 2nd → 3rd order effect analysis

Maps how an initial event propagates through:
- Direct market effects (1st order)
- Participant behavior changes (2nd order)  
- Systemic / feedback effects (3rd order)

Uses knowledge graph relationships to trace propagation paths.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class CausalEffect:
    """A single cause-effect relationship."""
    effect_id: str = ""
    order: int = 1                          # 1st, 2nd, 3rd order
    cause: str = ""
    effect: str = ""
    mechanism: str = ""                     # How the cause leads to effect
    
    direction: str = "neutral"              # bullish, bearish, neutral
    magnitude: float = 0.0                  # 0-1 scale
    confidence: float = 0.5
    delay_hours: float = 0.0               # How long until effect manifests
    
    affected_assets: List[str] = field(default_factory=list)
    affected_participants: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.effect_id:
            self.effect_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict:
        return {
            "effect_id": self.effect_id,
            "order": self.order,
            "cause": self.cause,
            "effect": self.effect,
            "mechanism": self.mechanism,
            "direction": self.direction,
            "magnitude": round(self.magnitude, 4),
            "confidence": round(self.confidence, 4),
            "delay_hours": self.delay_hours,
            "affected_assets": self.affected_assets,
            "affected_participants": self.affected_participants,
        }


@dataclass
class CausalChain:
    """Complete causal chain from an event."""
    event_id: str = ""
    event_text: str = ""
    generated_at: str = ""
    
    first_order: List[CausalEffect] = field(default_factory=list)
    second_order: List[CausalEffect] = field(default_factory=list)
    third_order: List[CausalEffect] = field(default_factory=list)
    
    # Summary
    total_effects: int = 0
    dominant_direction: str = "neutral"
    systemic_risk_score: float = 0.0
    feedback_loop_detected: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_text": self.event_text[:200],
            "generated_at": self.generated_at,
            "first_order": [e.to_dict() for e in self.first_order],
            "second_order": [e.to_dict() for e in self.second_order],
            "third_order": [e.to_dict() for e in self.third_order],
            "total_effects": self.total_effects,
            "dominant_direction": self.dominant_direction,
            "systemic_risk_score": round(self.systemic_risk_score, 4),
            "feedback_loop_detected": self.feedback_loop_detected,
        }


class CausalChainBuilder:
    """
    Builds causal chains tracing event → market effects → behavioral
    changes → systemic consequences.
    
    Uses knowledge graph when available, falls back to rule-based templates.
    """
    
    # ================================================================
    # 1st ORDER EFFECT TEMPLATES
    # ================================================================
    FIRST_ORDER_TEMPLATES = {
        "rate_hike": [
            CausalEffect(
                cause="Rate hike", effect="Bond yields rise",
                mechanism="Direct yield curve response to higher policy rate",
                direction="bearish", magnitude=0.6, confidence=0.9,
                delay_hours=0.1, affected_assets=["US_10Y", "US_2Y"],
                affected_participants=["institutional"]
            ),
            CausalEffect(
                cause="Rate hike", effect="USD strengthens",
                mechanism="Higher rates attract capital inflows",
                direction="bullish", magnitude=0.5, confidence=0.85,
                delay_hours=0.1, affected_assets=["USD", "DXY"],
                affected_participants=["institutional", "algorithmic"]
            ),
            CausalEffect(
                cause="Rate hike", effect="Equity pressure",
                mechanism="Higher discount rate lowers equity valuations",
                direction="bearish", magnitude=0.4, confidence=0.75,
                delay_hours=0.5, affected_assets=["SPX", "NASDAQ"],
                affected_participants=["institutional", "retail"]
            ),
            CausalEffect(
                cause="Rate hike", effect="Gold weakens",
                mechanism="Higher real yields reduce gold's relative attractiveness",
                direction="bearish", magnitude=0.4, confidence=0.70,
                delay_hours=0.5, affected_assets=["GOLD", "SILVER"],
                affected_participants=["institutional"]
            ),
        ],
        "rate_cut": [
            CausalEffect(
                cause="Rate cut", effect="Bond yields fall",
                mechanism="Lower policy rate compresses yield curve",
                direction="bullish", magnitude=0.6, confidence=0.9,
                delay_hours=0.1, affected_assets=["US_10Y", "US_2Y"],
            ),
            CausalEffect(
                cause="Rate cut", effect="USD weakens",
                mechanism="Lower rates reduce yield advantage",
                direction="bearish", magnitude=0.5, confidence=0.85,
                delay_hours=0.1, affected_assets=["USD"],
            ),
            CausalEffect(
                cause="Rate cut", effect="Equities rally",
                mechanism="Lower discount rate boosts valuations + risk appetite",
                direction="bullish", magnitude=0.5, confidence=0.80,
                delay_hours=0.5, affected_assets=["SPX", "NASDAQ"],
            ),
            CausalEffect(
                cause="Rate cut", effect="Gold strengthens",
                mechanism="Lower real yields increase gold appeal",
                direction="bullish", magnitude=0.4, confidence=0.75,
                delay_hours=0.5, affected_assets=["GOLD"],
            ),
        ],
        "inflation_high": [
            CausalEffect(
                cause="High inflation data", effect="Rate hike expectations rise",
                mechanism="Market prices in more aggressive tightening",
                direction="bearish", magnitude=0.5, confidence=0.85,
                delay_hours=0.1, affected_assets=["FED_FUNDS_RATE", "US_2Y"],
            ),
            CausalEffect(
                cause="High inflation", effect="Real yields fall",
                mechanism="Inflation erodes real return on bonds",
                direction="bearish", magnitude=0.3, confidence=0.70,
                delay_hours=1, affected_assets=["US_10Y"],
            ),
            CausalEffect(
                cause="High inflation", effect="Gold rises",
                mechanism="Inflation hedge demand increases",
                direction="bullish", magnitude=0.4, confidence=0.65,
                delay_hours=2, affected_assets=["GOLD"],
            ),
        ],
        "geopolitical_crisis": [
            CausalEffect(
                cause="Geopolitical crisis", effect="Risk-off flight",
                mechanism="Uncertainty drives capital to safe havens",
                direction="bearish", magnitude=0.6, confidence=0.80,
                delay_hours=0.5, affected_assets=["SPX", "NASDAQ"],
            ),
            CausalEffect(
                cause="Geopolitical crisis", effect="Safe haven bid",
                mechanism="Capital flows to USD, gold, treasuries",
                direction="bullish", magnitude=0.5, confidence=0.85,
                delay_hours=0.3, affected_assets=["USD", "GOLD", "US_10Y"],
            ),
            CausalEffect(
                cause="Geopolitical crisis", effect="Oil spikes",
                mechanism="Supply disruption fears + risk premium",
                direction="bullish", magnitude=0.7, confidence=0.70,
                delay_hours=0.2, affected_assets=["OIL_WTI", "OIL_BRENT"],
            ),
        ],
        "economic_weakness": [
            CausalEffect(
                cause="Weak economic data", effect="Rate cut expectations rise",
                mechanism="Weak data increases dovish policy expectations",
                direction="bullish", magnitude=0.4, confidence=0.75,
                delay_hours=0.5, affected_assets=["US_2Y"],
            ),
            CausalEffect(
                cause="Weak data", effect="Equity sell-off",
                mechanism="Lower growth expectations reduce earnings forecasts",
                direction="bearish", magnitude=0.4, confidence=0.70,
                delay_hours=1, affected_assets=["SPX"],
            ),
        ],
        "strong_earnings": [
            CausalEffect(
                cause="Strong earnings", effect="Sector rally",
                mechanism="Beat & raise guidance lifts sector sentiment",
                direction="bullish", magnitude=0.4, confidence=0.70,
                delay_hours=0.5, affected_assets=["SPX"],
            ),
        ],
        "generic": [
            CausalEffect(
                cause="News event", effect="Sentiment shift",
                mechanism="Market digests new information",
                direction="neutral", magnitude=0.2, confidence=0.50,
                delay_hours=2, affected_assets=["SPX"],
            ),
        ],
    }
    
    # ================================================================
    # 2nd ORDER EFFECT TEMPLATES
    # ================================================================
    SECOND_ORDER_RULES = {
        "equity_bearish": [
            CausalEffect(
                cause="Equity decline", effect="Margin calls trigger forced selling",
                mechanism="Leveraged positions hit stop-losses",
                order=2, direction="bearish", magnitude=0.3, confidence=0.60,
                delay_hours=4, affected_participants=["algorithmic", "retail"]
            ),
            CausalEffect(
                cause="Equity decline", effect="Volatility spike",
                mechanism="VIX rises → systematic de-risking",
                order=2, direction="bearish", magnitude=0.4, confidence=0.70,
                delay_hours=2, affected_assets=["VIX"]
            ),
            CausalEffect(
                cause="Equity decline", effect="Credit spreads widen",
                mechanism="Risk-off reprices corporate credit risk",
                order=2, direction="bearish", magnitude=0.3, confidence=0.65,
                delay_hours=6
            ),
        ],
        "equity_bullish": [
            CausalEffect(
                cause="Equity rally", effect="Short covering amplification",
                mechanism="Short sellers forced to cover, amplifying move",
                order=2, direction="bullish", magnitude=0.3, confidence=0.55,
                delay_hours=4
            ),
            CausalEffect(
                cause="Equity rally", effect="FOMO retail buying",
                mechanism="Retail investors chase performance",
                order=2, direction="bullish", magnitude=0.2, confidence=0.50,
                delay_hours=24, affected_participants=["retail"]
            ),
        ],
        "usd_strong": [
            CausalEffect(
                cause="USD strength", effect="EM currency pressure",
                mechanism="Dollar strength creates EM funding stress",
                order=2, direction="bearish", magnitude=0.3, confidence=0.65,
                delay_hours=12
            ),
            CausalEffect(
                cause="USD strength", effect="Commodity weakness",
                mechanism="Dollar-denominated commodities become more expensive",
                order=2, direction="bearish", magnitude=0.3, confidence=0.60,
                delay_hours=6, affected_assets=["OIL_WTI", "GOLD", "COPPER"]
            ),
        ],
        "usd_weak": [
            CausalEffect(
                cause="USD weakness", effect="EM relief rally",
                mechanism="Dollar weakness eases EM funding conditions",
                order=2, direction="bullish", magnitude=0.3, confidence=0.60,
                delay_hours=12
            ),
        ],
        "oil_spike": [
            CausalEffect(
                cause="Oil price spike", effect="Inflation expectations rise",
                mechanism="Energy costs feed through to broader prices",
                order=2, direction="bearish", magnitude=0.3, confidence=0.70,
                delay_hours=24
            ),
            CausalEffect(
                cause="Oil spike", effect="Consumer spending pressure",
                mechanism="Higher energy costs reduce disposable income",
                order=2, direction="bearish", magnitude=0.2, confidence=0.60,
                delay_hours=168  # 1 week
            ),
        ],
    }
    
    # ================================================================
    # 3rd ORDER EFFECT TEMPLATES
    # ================================================================
    THIRD_ORDER_RULES = {
        "systemic_stress": [
            CausalEffect(
                cause="Multiple 2nd order cascades", 
                effect="Liquidity crisis",
                mechanism="Simultaneous deleveraging creates liquidity vacuum",
                order=3, direction="bearish", magnitude=0.7, confidence=0.40,
                delay_hours=48
            ),
            CausalEffect(
                cause="Liquidity crisis", 
                effect="Central bank intervention",
                mechanism="Emergency liquidity provision / rate cut",
                order=3, direction="bullish", magnitude=0.5, confidence=0.60,
                delay_hours=72
            ),
        ],
        "feedback_loop": [
            CausalEffect(
                cause="Self-reinforcing decline",
                effect="Correlation breakdown",
                mechanism="All assets correlate to 1 during crisis",
                order=3, direction="bearish", magnitude=0.5, confidence=0.45,
                delay_hours=24
            ),
        ],
        "policy_response": [
            CausalEffect(
                cause="Market stress",
                effect="Fiscal/monetary policy response",
                mechanism="Government/central bank forces intervene",
                order=3, direction="bullish", magnitude=0.4, confidence=0.55,
                delay_hours=72
            ),
        ],
    }
    
    def __init__(self, knowledge_graph=None):
        """
        Initialize CausalChainBuilder.
        
        Args:
            knowledge_graph: KnowledgeGraph for relationship-aware propagation
        """
        self.knowledge_graph = knowledge_graph
        self.chain_count = 0
        print("[CAUSAL] Chain builder initialized")
    
    def build_chain(self, event_data: Dict, max_depth: int = 3) -> CausalChain:
        """
        Build complete causal chain from an event.
        
        Args:
            event_data: Parsed news event data
            max_depth: Maximum chain depth (1-3)
            
        Returns:
            CausalChain with all orders of effects
        """
        chain = CausalChain(
            event_id=event_data.get("event_id", str(uuid.uuid4())[:8]),
            event_text=event_data.get("raw_text", ""),
            generated_at=datetime.now().isoformat(),
        )
        
        # Classify event type
        event_type = self._classify_event(event_data)
        
        # 1st order effects
        chain.first_order = self._get_first_order(event_type, event_data)
        
        # 2nd order effects (derived from 1st order)
        if max_depth >= 2:
            chain.second_order = self._get_second_order(chain.first_order)
        
        # 3rd order effects (systemic / feedback)
        if max_depth >= 3:
            chain.third_order = self._get_third_order(
                chain.first_order, chain.second_order
            )
        
        # Enhance with knowledge graph relationships
        if self.knowledge_graph:
            self._enhance_with_graph(chain, event_data)
        
        # Calculate summary metrics
        self._compute_chain_metrics(chain)
        
        self.chain_count += 1
        return chain
    
    def _classify_event(self, event_data: Dict) -> str:
        """Classify event for template matching."""
        text = event_data.get("raw_text", "").lower()
        
        classifiers = {
            "rate_hike": ["rate hike", "raise rates", "tighten", "hawkish", "basis points higher"],
            "rate_cut": ["rate cut", "lower rates", "dovish", "ease", "basis points lower"],
            "inflation_high": ["inflation", "cpi above", "prices rising", "cost pressure"],
            "geopolitical_crisis": ["war", "conflict", "sanctions", "invasion", "military", "nuclear"],
            "economic_weakness": ["recession", "contraction", "decline", "miss expectations", "weak"],
            "strong_earnings": ["beat", "exceeded", "strong earnings", "raise guidance"],
        }
        
        best_match = "generic"
        best_score = 0
        
        for event_type, keywords in classifiers.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_match = event_type
        
        return best_match
    
    def _get_first_order(self, event_type: str, event_data: Dict) -> List[CausalEffect]:
        """Generate 1st order effects."""
        templates = self.FIRST_ORDER_TEMPLATES.get(
            event_type, self.FIRST_ORDER_TEMPLATES["generic"]
        )
        
        effects = []
        for template in templates:
            effect = CausalEffect(
                order=1,
                cause=template.cause,
                effect=template.effect,
                mechanism=template.mechanism,
                direction=template.direction,
                magnitude=template.magnitude,
                confidence=template.confidence,
                delay_hours=template.delay_hours,
                affected_assets=template.affected_assets.copy(),
                affected_participants=template.affected_participants.copy(),
            )
            
            # Adjust magnitude based on event intensity
            complexity = event_data.get("complexity_score", 0.5)
            certainty = event_data.get("certainty_score", 0.5)
            effect.magnitude *= (0.5 + complexity * 0.5)
            effect.confidence *= (0.5 + certainty * 0.5)
            
            effects.append(effect)
        
        return effects
    
    def _get_second_order(self, first_order: List[CausalEffect]) -> List[CausalEffect]:
        """Derive 2nd order effects from 1st order."""
        second_order = []
        
        for fo in first_order:
            # Map 1st order effects to 2nd order rule sets
            rule_keys = []
            
            for asset in fo.affected_assets:
                if asset in ("SPX", "NASDAQ", "DJIA"):
                    if fo.direction == "bearish":
                        rule_keys.append("equity_bearish")
                    else:
                        rule_keys.append("equity_bullish")
                elif asset in ("USD", "DXY"):
                    if fo.direction == "bullish":
                        rule_keys.append("usd_strong")
                    else:
                        rule_keys.append("usd_weak")
                elif asset in ("OIL_WTI", "OIL_BRENT"):
                    if fo.direction == "bullish":
                        rule_keys.append("oil_spike")
            
            # Generate 2nd order effects
            for key in set(rule_keys):
                templates = self.SECOND_ORDER_RULES.get(key, [])
                for template in templates:
                    effect = CausalEffect(
                        order=2,
                        cause=template.cause,
                        effect=template.effect,
                        mechanism=template.mechanism,
                        direction=template.direction,
                        magnitude=template.magnitude * fo.magnitude,
                        confidence=template.confidence * fo.confidence,
                        delay_hours=fo.delay_hours + template.delay_hours,
                        affected_assets=template.affected_assets.copy(),
                        affected_participants=template.affected_participants.copy(),
                    )
                    second_order.append(effect)
        
        return second_order
    
    def _get_third_order(self, first_order: List[CausalEffect],
                         second_order: List[CausalEffect]) -> List[CausalEffect]:
        """Derive 3rd order effects (systemic / feedback)."""
        third_order = []
        
        # Check for systemic stress conditions
        bearish_count = sum(1 for e in second_order if e.direction == "bearish")
        total_magnitude = sum(e.magnitude for e in second_order)
        
        if bearish_count >= 2 and total_magnitude > 0.5:
            # Systemic stress scenario
            for template in self.THIRD_ORDER_RULES.get("systemic_stress", []):
                effect = CausalEffect(
                    order=3,
                    cause=template.cause,
                    effect=template.effect,
                    mechanism=template.mechanism,
                    direction=template.direction,
                    magnitude=template.magnitude * min(1.0, total_magnitude),
                    confidence=template.confidence,
                    delay_hours=template.delay_hours,
                )
                third_order.append(effect)
        
        # Check for feedback loops
        affected_assets_1 = set()
        for e in first_order:
            affected_assets_1.update(e.affected_assets)
        affected_assets_2 = set()
        for e in second_order:
            affected_assets_2.update(e.affected_assets)
        
        if affected_assets_1 & affected_assets_2:
            for template in self.THIRD_ORDER_RULES.get("feedback_loop", []):
                effect = CausalEffect(
                    order=3,
                    cause=template.cause,
                    effect=template.effect,
                    mechanism=template.mechanism,
                    direction=template.direction,
                    magnitude=template.magnitude,
                    confidence=template.confidence * 0.5,
                    delay_hours=template.delay_hours,
                )
                third_order.append(effect)
        
        # Policy response (always possible at 3rd order)
        if total_magnitude > 0.3:
            for template in self.THIRD_ORDER_RULES.get("policy_response", []):
                effect = CausalEffect(
                    order=3,
                    cause=template.cause,
                    effect=template.effect,
                    mechanism=template.mechanism,
                    direction=template.direction,
                    magnitude=template.magnitude,
                    confidence=template.confidence,
                    delay_hours=template.delay_hours,
                )
                third_order.append(effect)
        
        return third_order
    
    def _enhance_with_graph(self, chain: CausalChain, event_data: Dict):
        """Use knowledge graph to discover additional propagation paths."""
        entities = event_data.get("entities", [])
        
        for ent in entities:
            ent_name = ent if isinstance(ent, str) else ent.get("text", "")
            if not ent_name:
                continue
            
            # Trace influence chain
            influences = self.knowledge_graph.get_influence_chain(ent_name, depth=2)
            
            for inf in influences[:3]:  # Top 3 influences
                effect = CausalEffect(
                    order=inf.get("depth", 1),
                    cause=f"{ent_name} impact",
                    effect=f"{inf['entity']} affected via {inf.get('relationship', 'influence')}",
                    mechanism=f"Knowledge graph: {ent_name} → {inf['entity']}",
                    direction="neutral",  
                    magnitude=abs(inf.get("cumulative_influence", 0.3)),
                    confidence=0.4,
                    delay_hours=inf.get("depth", 1) * 12,
                    affected_assets=[inf["entity"]],
                )
                
                if inf.get("depth", 1) == 1:
                    chain.first_order.append(effect)
                elif inf.get("depth", 1) == 2:
                    chain.second_order.append(effect)
                else:
                    chain.third_order.append(effect)
    
    def _compute_chain_metrics(self, chain: CausalChain):
        """Compute summary metrics for the chain."""
        all_effects = chain.first_order + chain.second_order + chain.third_order
        chain.total_effects = len(all_effects)
        
        if not all_effects:
            return
        
        # Dominant direction
        bullish_score = sum(e.magnitude * e.confidence for e in all_effects 
                          if e.direction == "bullish")
        bearish_score = sum(e.magnitude * e.confidence for e in all_effects 
                          if e.direction == "bearish")
        
        if bullish_score > bearish_score * 1.2:
            chain.dominant_direction = "bullish"
        elif bearish_score > bullish_score * 1.2:
            chain.dominant_direction = "bearish"
        else:
            chain.dominant_direction = "neutral"
        
        # Systemic risk
        third_order_magnitude = sum(e.magnitude for e in chain.third_order)
        chain.systemic_risk_score = min(1.0, third_order_magnitude)
        
        # Feedback loops
        first_assets = set()
        for e in chain.first_order:
            first_assets.update(e.affected_assets)
        second_assets = set()
        for e in chain.second_order:
            second_assets.update(e.affected_assets)
        
        chain.feedback_loop_detected = bool(first_assets & second_assets)
