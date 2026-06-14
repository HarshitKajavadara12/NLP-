"""
CONTAGION MODEL — Crisis spread modeling across markets

Models how financial stress propagates:
- Direct exposure channels
- Market confidence channels
- Liquidity channels
- Information contagion

Implements a simplified network contagion model.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import math


@dataclass
class ContagionNode:
    """A node in the contagion network."""
    asset: str = ""
    stress_level: float = 0.0        # 0-1 current stress
    susceptibility: float = 0.5      # 0-1 how easily stress spreads to this node
    infected: bool = False
    infection_time: str = ""
    source_of_infection: str = ""


@dataclass
class ContagionSimulation:
    """Result of a contagion simulation."""
    initial_shock: str = ""
    shock_magnitude: float = 0.0
    
    # Propagation
    infected_nodes: List[Dict] = field(default_factory=list)
    propagation_steps: int = 0
    total_spread: float = 0.0        # Sum of all stress levels
    max_reach: int = 0               # How many assets were affected
    
    # Timeline
    propagation_timeline: List[Dict] = field(default_factory=list)
    
    # Risk assessment
    systemic_risk: float = 0.0
    containment_probability: float = 0.5
    critical_nodes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "initial_shock": self.initial_shock,
            "shock_magnitude": round(self.shock_magnitude, 3),
            "infected_count": len(self.infected_nodes),
            "propagation_steps": self.propagation_steps,
            "total_spread": round(self.total_spread, 3),
            "systemic_risk": round(self.systemic_risk, 3),
            "containment_probability": round(self.containment_probability, 3),
            "critical_nodes": self.critical_nodes,
            "timeline": self.propagation_timeline[:20],
            "infected_nodes": self.infected_nodes[:20],
        }


class ContagionModel:
    """
    Models how financial stress spreads across connected markets.
    
    Uses a network model where:
    - Nodes = assets/markets
    - Edges = transmission channels (correlations, exposures)
    - Stress propagates via probability-weighted edges
    """
    
    # Transmission channels between asset classes
    TRANSMISSION_CHANNELS = {
        # Equity → Other
        ("SPX", "NASDAQ"): 0.90,
        ("SPX", "VIX"): 0.85,
        ("SPX", "HY_CREDIT"): 0.70,
        ("SPX", "EM_EQUITY"): 0.65,
        ("SPX", "USD"): 0.40,
        
        # Bond → Other
        ("US_10Y", "HY_CREDIT"): 0.55,
        ("US_10Y", "EM_DEBT"): 0.50,
        ("US_10Y", "MORTGAGE"): 0.75,
        
        # Currency → Other
        ("USD", "EM_FX"): 0.70,
        ("USD", "COMMODITIES"): 0.55,
        ("USD", "EM_DEBT"): 0.60,
        
        # Commodity → Other
        ("OIL_WTI", "ENERGY_STOCKS"): 0.80,
        ("OIL_WTI", "INFLATION_EXP"): 0.50,
        
        # Credit → Other  
        ("HY_CREDIT", "BANK_STOCKS"): 0.65,
        ("HY_CREDIT", "LENDING"): 0.60,
        
        # Bidirectional feedback
        ("VIX", "SPX"): 0.80,
        ("EM_FX", "EM_EQUITY"): 0.75,
        ("BANK_STOCKS", "HY_CREDIT"): 0.60,
    }
    
    # Asset susceptibility (how easily stress spreads here)
    SUSCEPTIBILITY = {
        "SPX": 0.3,           # Large, liquid → lower susceptibility
        "NASDAQ": 0.4,
        "DJIA": 0.25,
        "US_10Y": 0.2,        # Treasury → very liquid
        "US_2Y": 0.2,
        "VIX": 0.9,           # VIX is highly reactive
        "GOLD": 0.2,          # Safe haven → less susceptible
        "USD": 0.2,
        "OIL_WTI": 0.5,
        "BTC": 0.7,           # Crypto → highly susceptible
        "EM_FX": 0.7,
        "EM_EQUITY": 0.7,
        "EM_DEBT": 0.6,
        "HY_CREDIT": 0.6,
        "BANK_STOCKS": 0.5,
        "ENERGY_STOCKS": 0.5,
        "MORTGAGE": 0.4,
        "LENDING": 0.5,
        "INFLATION_EXP": 0.3,
        "COMMODITIES": 0.4,
    }
    
    def __init__(self, correlation_engine=None):
        """
        Initialize ContagionModel.
        
        Args:
            correlation_engine: CorrelationEngine for dynamic correlations
        """
        self.correlation_engine = correlation_engine
        self.simulation_count = 0
        print("[CONTAGION] Model initialized")
    
    def simulate(self, shock_asset: str, shock_magnitude: float = 0.5,
                 max_steps: int = 10, threshold: float = 0.1) -> ContagionSimulation:
        """
        Simulate contagion spread from an initial shock.
        
        Args:
            shock_asset: Asset where shock originates
            shock_magnitude: Initial shock severity (0-1)
            max_steps: Maximum propagation steps
            threshold: Minimum stress to continue propagation
            
        Returns:
            ContagionSimulation with full propagation path
        """
        sim = ContagionSimulation(
            initial_shock=shock_asset,
            shock_magnitude=shock_magnitude,
        )
        
        # Initialize nodes
        nodes = {}
        for asset, suscept in self.SUSCEPTIBILITY.items():
            nodes[asset] = ContagionNode(
                asset=asset,
                susceptibility=suscept,
            )
        
        # Add shock asset if not in predefined list
        if shock_asset not in nodes:
            nodes[shock_asset] = ContagionNode(
                asset=shock_asset,
                susceptibility=0.5,
            )
        
        # Apply initial shock
        nodes[shock_asset].stress_level = shock_magnitude
        nodes[shock_asset].infected = True
        nodes[shock_asset].infection_time = "T+0"
        
        sim.propagation_timeline.append({
            "step": 0,
            "newly_infected": [shock_asset],
            "total_stress": shock_magnitude,
        })
        
        # Propagate
        active_nodes = {shock_asset}
        
        for step in range(1, max_steps + 1):
            new_infections = set()
            step_stress = 0
            
            for source in list(active_nodes):
                source_stress = nodes[source].stress_level
                if source_stress < threshold:
                    continue
                
                # Find all transmission targets
                for (a, b), transmission_strength in self.TRANSMISSION_CHANNELS.items():
                    target = None
                    if a == source:
                        target = b
                    elif b == source:
                        target = a
                        transmission_strength *= 0.7  # Reverse direction is weaker
                    
                    if target is None or target not in nodes:
                        continue
                    
                    target_node = nodes[target]
                    
                    # Calculate transmitted stress
                    transmitted = (
                        source_stress * 
                        transmission_strength * 
                        target_node.susceptibility *
                        (1 - target_node.stress_level)  # Diminishing impact
                    )
                    
                    if transmitted > threshold * 0.5:
                        target_node.stress_level = min(1.0, 
                            target_node.stress_level + transmitted
                        )
                        step_stress += transmitted
                        
                        if not target_node.infected:
                            target_node.infected = True
                            target_node.infection_time = f"T+{step}"
                            target_node.source_of_infection = source
                            new_infections.add(target)
            
            if not new_infections and step_stress < threshold:
                break
            
            active_nodes = active_nodes | new_infections
            
            sim.propagation_timeline.append({
                "step": step,
                "newly_infected": list(new_infections),
                "total_stress": round(
                    sum(n.stress_level for n in nodes.values()), 3
                ),
            })
            
            sim.propagation_steps = step
        
        # Compile results
        for asset, node in nodes.items():
            if node.infected:
                sim.infected_nodes.append({
                    "asset": asset,
                    "stress_level": round(node.stress_level, 4),
                    "infection_time": node.infection_time,
                    "source": node.source_of_infection,
                    "susceptibility": node.susceptibility,
                })
        
        sim.infected_nodes.sort(key=lambda x: x["stress_level"], reverse=True)
        sim.max_reach = len([n for n in nodes.values() if n.infected])
        sim.total_spread = sum(n.stress_level for n in nodes.values())
        
        # Risk assessment
        sim.systemic_risk = self._assess_systemic_risk(sim, nodes)
        sim.containment_probability = self._assess_containment(sim)
        sim.critical_nodes = self._find_critical_nodes(nodes)
        
        self.simulation_count += 1
        return sim
    
    def stress_test(self, scenarios: List[Dict]) -> List[ContagionSimulation]:
        """
        Run multiple contagion scenarios.
        
        Args:
            scenarios: List of {asset, magnitude} dicts
            
        Returns:
            List of ContagionSimulations
        """
        results = []
        for scenario in scenarios:
            sim = self.simulate(
                shock_asset=scenario.get("asset", "SPX"),
                shock_magnitude=scenario.get("magnitude", 0.5),
            )
            results.append(sim)
        
        return results
    
    def _assess_systemic_risk(self, sim: ContagionSimulation,
                              nodes: Dict) -> float:
        """Assess systemic risk from simulation results."""
        if not nodes:
            return 0.0
        
        total_nodes = len(nodes)
        infected = sim.max_reach
        avg_stress = sim.total_spread / max(1, total_nodes)
        
        # Risk factors
        infection_rate = infected / total_nodes
        stress_factor = avg_stress
        speed_factor = min(1.0, sim.propagation_steps / 5) if sim.propagation_steps > 0 else 0
        
        risk = (
            infection_rate * 0.4 +
            stress_factor * 0.35 +
            (1 - speed_factor) * 0.25  # Faster spread = higher risk
        )
        
        return round(min(1.0, risk), 4)
    
    def _assess_containment(self, sim: ContagionSimulation) -> float:
        """Assess probability of containment."""
        if sim.max_reach <= 3:
            return 0.8
        elif sim.max_reach <= 6:
            return 0.5
        elif sim.max_reach <= 10:
            return 0.3
        else:
            return 0.1
    
    def _find_critical_nodes(self, nodes: Dict) -> List[str]:
        """Find nodes that are critical for contagion spread."""
        critical = []
        
        # Count how many transmission channels each node has
        connection_count = defaultdict(int)
        for (a, b) in self.TRANSMISSION_CHANNELS:
            connection_count[a] += 1
            connection_count[b] += 1
        
        # Critical = highly connected AND currently stressed
        for asset, node in nodes.items():
            connections = connection_count.get(asset, 0)
            if connections >= 3 and node.stress_level > 0.3:
                critical.append(asset)
        
        return critical
