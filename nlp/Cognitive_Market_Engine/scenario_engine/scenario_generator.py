"""
SCENARIO GENERATOR — Branching probability-weighted scenario trees

Given a news event, generates multiple possible futures:
- Base case (most likely)
- Bull/bear scenarios
- Tail risk scenarios
- Black swan paths

Each scenario has:
- Probability weight
- Expected market impact
- Timeline
- Key triggers / invalidation points
"""

import uuid
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ScenarioNode:
    """A single node in a scenario tree."""
    node_id: str = ""
    label: str = ""
    description: str = ""
    probability: float = 0.0
    
    # Market expectations
    direction: str = "neutral"          # bullish, bearish, neutral
    magnitude: float = 0.0             # Expected move (0-1 scale)
    volatility_change: float = 0.0     # Expected vol change
    timeline_hours: float = 24.0       # When this plays out
    
    # Conditions
    triggers: List[str] = field(default_factory=list)
    invalidation: List[str] = field(default_factory=list)
    
    # Sub-scenarios (children)
    children: List['ScenarioNode'] = field(default_factory=list)
    
    # Metadata
    depth: int = 0
    confidence: float = 0.5
    
    def __post_init__(self):
        if not self.node_id:
            self.node_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "description": self.description,
            "probability": self.probability,
            "direction": self.direction,
            "magnitude": self.magnitude,
            "volatility_change": self.volatility_change,
            "timeline_hours": self.timeline_hours,
            "triggers": self.triggers,
            "invalidation": self.invalidation,
            "depth": self.depth,
            "confidence": self.confidence,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class ScenarioTree:
    """Complete scenario tree for a news event."""
    event_id: str = ""
    event_text: str = ""
    generated_at: str = ""
    root: ScenarioNode = None
    
    # Aggregate metrics
    expected_direction: str = "neutral"
    probability_weighted_move: float = 0.0
    max_upside: float = 0.0
    max_downside: float = 0.0
    tail_risk_probability: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_text": self.event_text[:200],
            "generated_at": self.generated_at,
            "root": self.root.to_dict() if self.root else {},
            "expected_direction": self.expected_direction,
            "probability_weighted_move": self.probability_weighted_move,
            "max_upside": self.max_upside,
            "max_downside": self.max_downside,
            "tail_risk_probability": self.tail_risk_probability,
        }


class ScenarioGenerator:
    """
    Generates branching scenario trees from news events.
    
    Flow:
    1. Classify event type (rate decision, earnings, geopolitical, etc.)
    2. Generate base case + alternatives
    3. For each scenario, generate 2nd-order effects
    4. Assign probabilities (must sum to 1 at each level)
    5. Calculate expected values
    """
    
    # Event type templates
    EVENT_TEMPLATES = {
        "rate_decision": {
            "scenarios": [
                {"label": "As Expected", "prob": 0.50, "dir": "neutral", "mag": 0.1, "vol": -0.2},
                {"label": "Hawkish Surprise", "prob": 0.15, "dir": "bearish", "mag": 0.5, "vol": 0.6},
                {"label": "Dovish Surprise", "prob": 0.15, "dir": "bullish", "mag": 0.5, "vol": 0.5},
                {"label": "Emergency Cut", "prob": 0.05, "dir": "bullish", "mag": 0.8, "vol": 0.9},
                {"label": "Forward Guidance Shift", "prob": 0.15, "dir": "neutral", "mag": 0.3, "vol": 0.3},
            ]
        },
        "economic_data": {
            "scenarios": [
                {"label": "In-Line", "prob": 0.40, "dir": "neutral", "mag": 0.05, "vol": -0.1},
                {"label": "Beat Expectations", "prob": 0.20, "dir": "bullish", "mag": 0.3, "vol": 0.2},
                {"label": "Miss Expectations", "prob": 0.20, "dir": "bearish", "mag": 0.3, "vol": 0.3},
                {"label": "Major Revision", "prob": 0.10, "dir": "neutral", "mag": 0.4, "vol": 0.5},
                {"label": "Paradigm Shift", "prob": 0.10, "dir": "neutral", "mag": 0.6, "vol": 0.7},
            ]
        },
        "earnings": {
            "scenarios": [
                {"label": "Beat & Raise", "prob": 0.25, "dir": "bullish", "mag": 0.4, "vol": 0.3},
                {"label": "Beat & Maintain", "prob": 0.20, "dir": "bullish", "mag": 0.2, "vol": 0.1},
                {"label": "In-Line", "prob": 0.20, "dir": "neutral", "mag": 0.05, "vol": -0.1},
                {"label": "Miss & Maintain", "prob": 0.15, "dir": "bearish", "mag": 0.3, "vol": 0.3},
                {"label": "Miss & Lower", "prob": 0.10, "dir": "bearish", "mag": 0.5, "vol": 0.6},
                {"label": "Accounting Issues", "prob": 0.10, "dir": "bearish", "mag": 0.7, "vol": 0.8},
            ]
        },
        "geopolitical": {
            "scenarios": [
                {"label": "Diplomatic Resolution", "prob": 0.20, "dir": "bullish", "mag": 0.3, "vol": -0.3},
                {"label": "Status Quo", "prob": 0.35, "dir": "neutral", "mag": 0.1, "vol": 0.1},
                {"label": "Escalation", "prob": 0.25, "dir": "bearish", "mag": 0.4, "vol": 0.5},
                {"label": "Sanctions", "prob": 0.10, "dir": "bearish", "mag": 0.5, "vol": 0.6},
                {"label": "Full Crisis", "prob": 0.10, "dir": "bearish", "mag": 0.8, "vol": 0.9},
            ]
        },
        "policy_announcement": {
            "scenarios": [
                {"label": "Market-Friendly", "prob": 0.25, "dir": "bullish", "mag": 0.3, "vol": 0.2},
                {"label": "Neutral Impact", "prob": 0.30, "dir": "neutral", "mag": 0.1, "vol": 0.1},
                {"label": "Market-Unfriendly", "prob": 0.25, "dir": "bearish", "mag": 0.3, "vol": 0.3},
                {"label": "Implementation Concerns", "prob": 0.10, "dir": "bearish", "mag": 0.2, "vol": 0.4},
                {"label": "Policy Reversal", "prob": 0.10, "dir": "neutral", "mag": 0.5, "vol": 0.6},
            ]
        },
        "market_crash": {
            "scenarios": [
                {"label": "V-Shape Recovery", "prob": 0.20, "dir": "bullish", "mag": 0.6, "vol": 0.7},
                {"label": "Gradual Recovery", "prob": 0.25, "dir": "bullish", "mag": 0.3, "vol": 0.3},
                {"label": "Range-Bound", "prob": 0.25, "dir": "neutral", "mag": 0.1, "vol": 0.2},
                {"label": "Further Decline", "prob": 0.20, "dir": "bearish", "mag": 0.4, "vol": 0.5},
                {"label": "Systemic Contagion", "prob": 0.10, "dir": "bearish", "mag": 0.8, "vol": 0.9},
            ]
        },
        "generic": {
            "scenarios": [
                {"label": "Bullish Interpretation", "prob": 0.25, "dir": "bullish", "mag": 0.3, "vol": 0.2},
                {"label": "Neutral / Priced In", "prob": 0.35, "dir": "neutral", "mag": 0.05, "vol": 0.0},
                {"label": "Bearish Interpretation", "prob": 0.25, "dir": "bearish", "mag": 0.3, "vol": 0.2},
                {"label": "Tail Risk", "prob": 0.15, "dir": "neutral", "mag": 0.6, "vol": 0.7},
            ]
        }
    }
    
    # 2nd order effect templates
    SECOND_ORDER_EFFECTS = {
        "bullish": [
            {"label": "Momentum Continuation", "prob": 0.40, "dir": "bullish", "mag_mult": 0.5},
            {"label": "Profit Taking", "prob": 0.30, "dir": "bearish", "mag_mult": 0.3},
            {"label": "FOMO Rally", "prob": 0.15, "dir": "bullish", "mag_mult": 0.7},
            {"label": "Exhaustion / Reversal", "prob": 0.15, "dir": "bearish", "mag_mult": 0.5},
        ],
        "bearish": [
            {"label": "Panic Selling", "prob": 0.25, "dir": "bearish", "mag_mult": 0.7},
            {"label": "Dip Buying", "prob": 0.30, "dir": "bullish", "mag_mult": 0.4},
            {"label": "Stabilization", "prob": 0.30, "dir": "neutral", "mag_mult": 0.2},
            {"label": "Contagion", "prob": 0.15, "dir": "bearish", "mag_mult": 0.8},
        ],
        "neutral": [
            {"label": "Drift Higher", "prob": 0.30, "dir": "bullish", "mag_mult": 0.2},
            {"label": "Drift Lower", "prob": 0.30, "dir": "bearish", "mag_mult": 0.2},
            {"label": "Range Bound", "prob": 0.30, "dir": "neutral", "mag_mult": 0.1},
            {"label": "Breakout on Catalyst", "prob": 0.10, "dir": "neutral", "mag_mult": 0.5},
        ],
    }
    
    def __init__(self, knowledge_graph=None, historical_data=None):
        """
        Initialize ScenarioGenerator.
        
        Args:
            knowledge_graph: KnowledgeGraph instance for relationship awareness
            historical_data: Historical pattern data for calibration
        """
        self.knowledge_graph = knowledge_graph
        self.historical_data = historical_data or {}
        self.generated_count = 0
        print("[SCENARIO] Generator initialized")
    
    def generate(self, event_data: Dict, 
                 depth: int = 2, 
                 include_tail_risks: bool = True) -> ScenarioTree:
        """
        Generate a scenario tree from a news event.
        
        Args:
            event_data: Parsed news event data
            depth: How many levels of branching (1-3)
            include_tail_risks: Include low-probability extreme scenarios
            
        Returns:
            ScenarioTree with probability-weighted scenarios
        """
        event_type = self._classify_event_type(event_data)
        template = self.EVENT_TEMPLATES.get(event_type, self.EVENT_TEMPLATES["generic"])
        
        # Adjust probabilities based on event data
        adjusted = self._adjust_probabilities(template, event_data)
        
        # Build root node
        root = ScenarioNode(
            label="Current Event",
            description=event_data.get("raw_text", "")[:200],
            probability=1.0,
            depth=0,
        )
        
        # Generate first level scenarios
        for s in adjusted:
            node = ScenarioNode(
                label=s["label"],
                description=self._generate_description(s, event_data),
                probability=s["prob"],
                direction=s["dir"],
                magnitude=s["mag"],
                volatility_change=s.get("vol", 0),
                timeline_hours=self._estimate_timeline(s, event_type),
                triggers=self._generate_triggers(s, event_data),
                invalidation=self._generate_invalidation(s, event_data),
                depth=1,
                confidence=min(0.9, s["prob"] * 1.5),
            )
            
            # Generate 2nd order effects if depth > 1
            if depth >= 2:
                second_order = self.SECOND_ORDER_EFFECTS.get(s["dir"], 
                              self.SECOND_ORDER_EFFECTS["neutral"])
                for so in second_order:
                    child = ScenarioNode(
                        label=so["label"],
                        description=f"Following '{s['label']}': {so['label']}",
                        probability=so["prob"],
                        direction=so["dir"],
                        magnitude=s["mag"] * so["mag_mult"],
                        volatility_change=s.get("vol", 0) * so["mag_mult"],
                        timeline_hours=self._estimate_timeline(s, event_type) * 2,
                        depth=2,
                        confidence=s["prob"] * so["prob"],
                    )
                    
                    # Generate 3rd order if depth > 2
                    if depth >= 3:
                        third_order = self.SECOND_ORDER_EFFECTS.get(so["dir"],
                                     self.SECOND_ORDER_EFFECTS["neutral"])
                        for to in third_order[:2]:  # Only top 2 at depth 3
                            grandchild = ScenarioNode(
                                label=to["label"],
                                description=f"3rd order: {to['label']}",
                                probability=to["prob"],
                                direction=to["dir"],
                                magnitude=s["mag"] * so["mag_mult"] * to["mag_mult"],
                                timeline_hours=self._estimate_timeline(s, event_type) * 4,
                                depth=3,
                                confidence=s["prob"] * so["prob"] * to["prob"],
                            )
                            child.children.append(grandchild)
                    
                    node.children.append(child)
            
            root.children.append(node)
        
        # Build tree
        tree = ScenarioTree(
            event_id=event_data.get("event_id", str(uuid.uuid4())[:8]),
            event_text=event_data.get("raw_text", ""),
            generated_at=datetime.now().isoformat(),
            root=root,
        )
        
        # Calculate aggregate metrics
        self._calculate_tree_metrics(tree)
        
        self.generated_count += 1
        return tree
    
    def _classify_event_type(self, event_data: Dict) -> str:
        """Classify the event type from parsed data."""
        text = event_data.get("raw_text", "").lower()
        narrative_types = event_data.get("narrative_types", [])
        
        # Keyword-based classification
        keywords = {
            "rate_decision": ["rate", "basis point", "bps", "monetary policy", "fomc", "ecb meeting", "fed"],
            "economic_data": ["gdp", "inflation", "cpi", "pmi", "employment", "jobs", "nfp", "unemployment", "retail sales"],
            "earnings": ["earnings", "revenue", "profit", "eps", "quarterly results", "guidance"],
            "geopolitical": ["war", "conflict", "sanctions", "tensions", "military", "invasion", "nuclear", "territorial"],
            "policy_announcement": ["regulation", "legislation", "tax", "stimulus", "fiscal policy", "executive order"],
            "market_crash": ["crash", "plunge", "circuit breaker", "black monday", "flash crash", "panic"],
        }
        
        scores = {k: 0 for k in keywords}
        for event_type, words in keywords.items():
            for word in words:
                if word in text:
                    scores[event_type] += 1
        
        best_type = max(scores, key=scores.get)
        if scores[best_type] > 0:
            return best_type
        
        # Check narrative types
        for nt in narrative_types:
            if isinstance(nt, str):
                nt_lower = nt.lower()
                if "monetary" in nt_lower or "rate" in nt_lower:
                    return "rate_decision"
                if "data" in nt_lower or "economic" in nt_lower:
                    return "economic_data"
        
        return "generic"
    
    def _adjust_probabilities(self, template: Dict, event_data: Dict) -> List[Dict]:
        """
        Adjust scenario probabilities using:
        1. Event certainty/ambiguity (original logic)
        2. Bayesian updating from historical outcomes if available
        3. Market regime awareness
        """
        scenarios = [s.copy() for s in template["scenarios"]]
        
        # --- Layer 1: Certainty/Ambiguity adjustment ---
        certainty = event_data.get("certainty_score", 0.5)
        ambiguity = event_data.get("ambiguity_score", 0.5)
        
        for s in scenarios:
            if s["dir"] == "neutral":
                s["prob"] *= (1 + (certainty - 0.5) * 0.3)
            else:
                s["prob"] *= (1 + (ambiguity - 0.5) * 0.4)
        
        # --- Layer 2: Bayesian update from historical data ---
        if self.historical_data:
            event_type = event_data.get("event_type", "generic")
            historical_outcomes = [
                h for h in self.historical_data 
                if h.get("event_type") == event_type
            ]
            if historical_outcomes:
                # Count historical outcome directions
                dir_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
                for h in historical_outcomes:
                    d = h.get("actual_direction", "neutral")
                    if d in dir_counts:
                        dir_counts[d] += 1
                total_hist = sum(dir_counts.values())
                if total_hist > 5:  # Only update if enough history
                    for s in scenarios:
                        hist_freq = dir_counts.get(s["dir"], 0) / total_hist
                        prior = s["prob"]
                        # Bayesian blend: 60% prior + 40% historical
                        s["prob"] = prior * 0.6 + hist_freq * 0.4
        
        # --- Layer 3: Market regime adjustment ---
        regime = event_data.get("market_regime", None)
        if regime == "high_volatility":
            for s in scenarios:
                if s["dir"] != "neutral":
                    s["mag"] *= 1.3  # Amplify moves in volatile regime
                    s["vol"] *= 1.2
        elif regime == "low_volatility":
            for s in scenarios:
                s["mag"] *= 0.7  # Compress moves in calm regime
                s["vol"] *= 0.6
        
        # Normalize to sum to 1
        total = sum(s["prob"] for s in scenarios)
        if total > 0:
            for s in scenarios:
                s["prob"] = round(s["prob"] / total, 3)
        
        return scenarios
    
    def _generate_description(self, scenario: Dict, event_data: Dict) -> str:
        """Generate human-readable scenario description."""
        direction_desc = {
            "bullish": "Markets rally as",
            "bearish": "Markets decline as",
            "neutral": "Markets stay range-bound as",
        }
        
        base = direction_desc.get(scenario["dir"], "Markets react as")
        label = scenario["label"].lower()
        
        mag_desc = "modest" if scenario["mag"] < 0.3 else "significant" if scenario["mag"] < 0.6 else "dramatic"
        
        return f"{base} {label} scenario unfolds with {mag_desc} moves."
    
    def _estimate_timeline(self, scenario: Dict, event_type: str) -> float:
        """Estimate how many hours until this scenario plays out."""
        base_timelines = {
            "rate_decision": 4,
            "economic_data": 2,
            "earnings": 24,
            "geopolitical": 72,
            "policy_announcement": 48,
            "market_crash": 1,
            "generic": 24,
        }
        
        base = base_timelines.get(event_type, 24)
        
        # Higher magnitude events play out faster
        if scenario["mag"] > 0.6:
            base *= 0.5
        elif scenario["mag"] < 0.2:
            base *= 2
        
        return round(base, 1)
    
    def _generate_triggers(self, scenario: Dict, event_data: Dict) -> List[str]:
        """Generate trigger conditions for a scenario."""
        triggers = []
        
        if scenario["dir"] == "bullish":
            triggers = [
                "Risk-on sentiment accelerates",
                "Follow-through buying above key resistance",
                "Confirming data releases",
            ]
        elif scenario["dir"] == "bearish":
            triggers = [
                "Risk-off sentiment intensifies",
                "Key support levels break",
                "Negative follow-up developments",
            ]
        else:
            triggers = [
                "No significant follow-up catalysts",
                "Market absorption of news",
                "Mixed data/signals",
            ]
        
        return triggers[:3]
    
    def _generate_invalidation(self, scenario: Dict, event_data: Dict) -> List[str]:
        """Generate invalidation conditions."""
        if scenario["dir"] == "bullish":
            return ["Central bank pushback", "Negative surprise data", "Geopolitical escalation"]
        elif scenario["dir"] == "bearish":
            return ["Policy support announcement", "Better-than-expected data", "De-escalation"]
        else:
            return ["Strong directional catalyst", "Unexpected policy shift"]
    
    def _calculate_tree_metrics(self, tree: ScenarioTree):
        """Calculate aggregate metrics for the scenario tree."""
        if not tree.root or not tree.root.children:
            return
        
        # Probability-weighted expected move
        weighted_move = 0.0
        max_up = 0.0
        max_down = 0.0
        tail_prob = 0.0
        
        bull_prob = 0.0
        bear_prob = 0.0
        
        for child in tree.root.children:
            signed_mag = child.magnitude if child.direction == "bullish" else (
                -child.magnitude if child.direction == "bearish" else 0
            )
            weighted_move += child.probability * signed_mag
            
            if child.direction == "bullish":
                max_up = max(max_up, child.magnitude)
                bull_prob += child.probability
            elif child.direction == "bearish":
                max_down = max(max_down, child.magnitude)
                bear_prob += child.probability
            
            # Tail risk: magnitude > 0.6
            if child.magnitude > 0.6:
                tail_prob += child.probability
        
        tree.probability_weighted_move = round(weighted_move, 4)
        tree.max_upside = round(max_up, 4)
        tree.max_downside = round(max_down, 4)
        tree.tail_risk_probability = round(tail_prob, 4)
        
        if bull_prob > bear_prob + 0.1:
            tree.expected_direction = "bullish"
        elif bear_prob > bull_prob + 0.1:
            tree.expected_direction = "bearish"
        else:
            tree.expected_direction = "neutral"
    
    def get_flat_scenarios(self, tree: ScenarioTree) -> List[Dict]:
        """Flatten tree into sorted list of scenarios by probability."""
        results = []
        
        def _traverse(node, parent_prob=1.0, path=""):
            if node.depth > 0:
                entry = {
                    "path": path + node.label,
                    "probability": round(parent_prob * node.probability, 4),
                    "direction": node.direction,
                    "magnitude": node.magnitude,
                    "volatility_change": node.volatility_change,
                    "timeline_hours": node.timeline_hours,
                    "depth": node.depth,
                }
                results.append(entry)
            
            for child in node.children:
                _traverse(child, 
                         parent_prob * node.probability if node.depth > 0 else 1.0,
                         (path + node.label + " → ") if node.depth > 0 else "")
        
        _traverse(tree.root)
        results.sort(key=lambda x: x["probability"], reverse=True)
        return results
