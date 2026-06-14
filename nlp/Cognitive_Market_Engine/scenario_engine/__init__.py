"""
Scenario Engine — Priority 2 Module

Generates branching scenario trees, runs Monte Carlo simulations,
and builds causal chains from news events.
"""

from .scenario_generator import ScenarioGenerator
from .monte_carlo import MonteCarloSimulator
from .causal_chain import CausalChainBuilder

__all__ = ["ScenarioGenerator", "MonteCarloSimulator", "CausalChainBuilder"]
