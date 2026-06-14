"""
MONTE CARLO SIMULATOR — Probability-weighted outcome distribution

Runs N simulations of scenario outcomes to:
- Estimate probability distributions of returns
- Calculate VaR and Expected Shortfall
- Test scenario robustness
- Generate confidence intervals
Noise Model: Student-t (fat tails) + Jump Diffusion (rare large moves)"""

import random
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class SimulationResult:
    """Result of a Monte Carlo simulation run."""
    n_simulations: int = 0
    mean_return: float = 0.0
    median_return: float = 0.0
    std_dev: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    
    # Risk metrics
    var_95: float = 0.0       # Value at Risk (95%)
    var_99: float = 0.0       # Value at Risk (99%)
    cvar_95: float = 0.0      # Conditional VaR (Expected Shortfall)
    max_drawdown: float = 0.0
    
    # Probability of outcomes
    prob_positive: float = 0.0
    prob_negative: float = 0.0
    prob_extreme_up: float = 0.0    # >2 sigma
    prob_extreme_down: float = 0.0  # <-2 sigma
    
    # Distribution histogram
    histogram: Dict = field(default_factory=dict)
    
    # All simulated returns
    returns: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "n_simulations": self.n_simulations,
            "mean_return": round(self.mean_return, 6),
            "median_return": round(self.median_return, 6),
            "std_dev": round(self.std_dev, 6),
            "skewness": round(self.skewness, 4),
            "kurtosis": round(self.kurtosis, 4),
            "var_95": round(self.var_95, 6),
            "var_99": round(self.var_99, 6),
            "cvar_95": round(self.cvar_95, 6),
            "max_drawdown": round(self.max_drawdown, 6),
            "prob_positive": round(self.prob_positive, 4),
            "prob_negative": round(self.prob_negative, 4),
            "prob_extreme_up": round(self.prob_extreme_up, 4),
            "prob_extreme_down": round(self.prob_extreme_down, 4),
            "histogram": self.histogram,
        }


class MonteCarloSimulator:
    """
    Monte Carlo simulation engine for scenario analysis.
    
    Takes scenario trees and runs N simulations to estimate
    the distribution of possible outcomes.
    """
    
    def __init__(self, seed: int = None):
        """
        Initialize simulator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        
        self.default_n_sims = 10000
        self.simulation_count = 0
        print("[MONTE_CARLO] Simulator initialized")
    
    def _generate_fat_tailed_noise(self, volatility: float) -> float:
        """
        Generate noise using Student-t distribution (fat tails) + jump diffusion.
        
        This replaces simple Gaussian noise to better model financial markets:
        - Student-t with df=5 produces realistic kurtosis (~9 vs Gaussian ~3)
        - Jump diffusion adds rare large moves (flash crashes, gap opens)
        
        Args:
            volatility: Base volatility scale
            
        Returns:
            Noise sample with fat tails
        """
        vol = max(0.01, volatility * 0.3)
        
        # Student-t noise (df=5 gives excess kurtosis ~6, realistic for markets)
        # Approximation: t(df) ≈ Normal(0,1) / sqrt(Chi²(df)/df)
        # Using Box-Muller + chi-squared approximation
        df = 5.0
        normal = random.gauss(0, 1)
        chi2 = sum(random.gauss(0, 1) ** 2 for _ in range(int(df)))
        t_sample = normal / math.sqrt(max(chi2 / df, 0.001))
        base_noise = t_sample * vol
        
        # Jump diffusion component (Poisson jumps)
        # ~5% chance of a jump per step, jump magnitude ~ 2-5x normal vol
        jump = 0.0
        if random.random() < 0.05:  # Jump probability
            jump_sign = random.choice([-1, 1])
            jump_magnitude = random.expovariate(1.0) * vol * 3.0
            jump = jump_sign * jump_magnitude
        
        return base_noise + jump
    
    def simulate_scenario_tree(self, scenario_tree, n_sims: int = None) -> SimulationResult:
        """
        Run Monte Carlo simulation on a scenario tree.
        
        For each simulation:
        1. Walk the tree, selecting branches by probability
        2. Add noise around the expected magnitude
        3. Aggregate the return path
        
        Args:
            scenario_tree: ScenarioTree from ScenarioGenerator
            n_sims: Number of simulations (default: 10000)
            
        Returns:
            SimulationResult with full distribution
        """
        n = n_sims or self.default_n_sims
        returns = []
        
        root = scenario_tree.root if hasattr(scenario_tree, 'root') else None
        if root is None:
            return SimulationResult()
        
        for _ in range(n):
            sim_return = self._simulate_single_path(root)
            returns.append(sim_return)
        
        result = self._compute_statistics(returns, n)
        self.simulation_count += 1
        return result
    
    def simulate_from_scenarios(self, scenarios: List[Dict], 
                                n_sims: int = None) -> SimulationResult:
        """
        Run simulation from flat scenario list.
        
        Args:
            scenarios: List of {probability, direction, magnitude} dicts
            n_sims: Number of simulations
            
        Returns:
            SimulationResult
        """
        n = n_sims or self.default_n_sims
        returns = []
        
        # Normalize probabilities
        total_prob = sum(s.get("probability", 0) for s in scenarios)
        if total_prob <= 0:
            return SimulationResult()
        
        normalized = []
        cumulative = 0.0
        for s in scenarios:
            prob = s.get("probability", 0) / total_prob
            cumulative += prob
            normalized.append({
                "cumulative_prob": cumulative,
                "direction": s.get("direction", "neutral"),
                "magnitude": s.get("magnitude", 0.1),
                "volatility": s.get("volatility_change", 0.2),
            })
        
        for _ in range(n):
            r = random.random()
            selected = normalized[-1]
            for s in normalized:
                if r <= s["cumulative_prob"]:
                    selected = s
                    break
            
            # Generate return with fat-tailed noise (Student-t + jump diffusion)
            base_return = selected["magnitude"]
            if selected["direction"] == "bearish":
                base_return = -base_return
            elif selected["direction"] == "neutral":
                base_return *= random.choice([-1, 1]) * 0.3
            
            noise = self._generate_fat_tailed_noise(selected["volatility"])
            sim_return = base_return + noise
            returns.append(sim_return)
        
        result = self._compute_statistics(returns, n)
        self.simulation_count += 1
        return result
    
    def stress_test(self, scenarios: List[Dict], 
                    stress_multiplier: float = 2.0,
                    n_sims: int = None) -> SimulationResult:
        """
        Run stress test with amplified tail risks.
        
        Increases magnitude of adverse scenarios and widens volatility.
        """
        stressed = []
        for s in scenarios:
            stressed_s = s.copy()
            if s.get("direction") == "bearish":
                stressed_s["magnitude"] = s.get("magnitude", 0.1) * stress_multiplier
                stressed_s["volatility_change"] = s.get("volatility_change", 0.2) * stress_multiplier
            stressed.append(stressed_s)
        
        return self.simulate_from_scenarios(stressed, n_sims)
    
    def _simulate_single_path(self, root) -> float:
        """Simulate a single path through the scenario tree."""
        total_return = 0.0
        current_nodes = [root] if root.children else []
        
        # Walk through each level
        nodes_to_process = root.children if hasattr(root, 'children') else []
        
        while nodes_to_process:
            # Select branch by probability
            r = random.random()
            cumulative = 0.0
            selected = nodes_to_process[-1]
            
            for node in nodes_to_process:
                cumulative += node.probability
                if r <= cumulative:
                    selected = node
                    break
            
            # Calculate return for this node
            base_mag = selected.magnitude
            if selected.direction == "bearish":
                base_mag = -base_mag
            elif selected.direction == "neutral":
                base_mag *= random.choice([-1, 1]) * 0.3
            
            # Add noise proportional to volatility (fat-tailed)
            vol = max(0.01, abs(selected.volatility_change) * 0.2)
            noise = self._generate_fat_tailed_noise(vol)
            
            step_return = base_mag + noise
            total_return += step_return
            
            # Move to children
            nodes_to_process = selected.children if hasattr(selected, 'children') else []
        
        return total_return
    
    def _compute_statistics(self, returns: List[float], n: int) -> SimulationResult:
        """Compute comprehensive statistics from simulation returns."""
        if not returns:
            return SimulationResult()
        
        sorted_returns = sorted(returns)
        mean = sum(returns) / n
        
        # Median
        mid = n // 2
        median = sorted_returns[mid] if n % 2 == 1 else (
            (sorted_returns[mid - 1] + sorted_returns[mid]) / 2
        )
        
        # Std dev
        variance = sum((r - mean) ** 2 for r in returns) / max(1, n - 1)
        std_dev = math.sqrt(variance)
        
        # Skewness
        if std_dev > 0:
            skewness = sum((r - mean) ** 3 for r in returns) / (n * std_dev ** 3)
        else:
            skewness = 0
        
        # Kurtosis
        if std_dev > 0:
            kurtosis = sum((r - mean) ** 4 for r in returns) / (n * std_dev ** 4) - 3
        else:
            kurtosis = 0
        
        # VaR (Value at Risk) - percentile
        var_95_idx = int(n * 0.05)
        var_99_idx = int(n * 0.01)
        var_95 = sorted_returns[var_95_idx]
        var_99 = sorted_returns[var_99_idx]
        
        # CVaR (Expected Shortfall) - average of worst 5%
        worst_5pct = sorted_returns[:max(1, var_95_idx)]
        cvar_95 = sum(worst_5pct) / len(worst_5pct)
        
        # Max drawdown (simplified: max negative return)
        max_drawdown = min(returns) if returns else 0
        
        # Probabilities
        prob_positive = sum(1 for r in returns if r > 0) / n
        prob_negative = sum(1 for r in returns if r < 0) / n
        
        two_sigma = 2 * std_dev if std_dev > 0 else 0.1
        prob_extreme_up = sum(1 for r in returns if r > mean + two_sigma) / n
        prob_extreme_down = sum(1 for r in returns if r < mean - two_sigma) / n
        
        # Histogram (10 bins)
        histogram = self._build_histogram(sorted_returns)
        
        return SimulationResult(
            n_simulations=n,
            mean_return=mean,
            median_return=median,
            std_dev=std_dev,
            skewness=skewness,
            kurtosis=kurtosis,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            max_drawdown=max_drawdown,
            prob_positive=prob_positive,
            prob_negative=prob_negative,
            prob_extreme_up=prob_extreme_up,
            prob_extreme_down=prob_extreme_down,
            histogram=histogram,
            returns=returns,
        )
    
    def _build_histogram(self, sorted_returns: List[float], n_bins: int = 10) -> Dict:
        """Build histogram from sorted returns."""
        if not sorted_returns:
            return {}
        
        min_val = sorted_returns[0]
        max_val = sorted_returns[-1]
        
        if min_val == max_val:
            return {"0": len(sorted_returns)}
        
        bin_width = (max_val - min_val) / n_bins
        bins = defaultdict(int)
        
        for r in sorted_returns:
            bin_idx = min(n_bins - 1, int((r - min_val) / bin_width))
            bin_lower = round(min_val + bin_idx * bin_width, 4)
            bin_upper = round(min_val + (bin_idx + 1) * bin_width, 4)
            bin_label = f"{bin_lower:.4f} to {bin_upper:.4f}"
            bins[bin_label] += 1
        
        return dict(bins)
