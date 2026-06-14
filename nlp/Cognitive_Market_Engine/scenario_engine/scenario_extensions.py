"""
Scenario Engine Extensions — Categories 5.3, 5.4, 5.5
======================================================
5.3  Scenario Path Visualization — branching probability tree, Plotly or
     text/Mermaid-based rendering of scenario outcomes with branch weights
5.4  Counter-Factual Analysis — "what if X hadn't happened?" alternative
     scenario generation and comparison
5.5  Scenario-Based Portfolio Optimization — find robust position weights
     that perform well across the full scenario distribution
"""
import math
import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger("cme.scenario_engine.extensions")

# ---------------------------------------------------------------------------
#  5.3  Scenario Path Visualization
# ---------------------------------------------------------------------------

@dataclass
class ScenarioNode:
    node_id: str
    label: str
    probability: float
    expected_return: float
    depth: int
    children: List["ScenarioNode"] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class ScenarioTreeVisualizer:
    """
    Generate visual representations of scenario probability trees.
    
    Output formats:
    - Mermaid diagram (for Markdown / chatbot rendering)
    - Plotly treemap (for dashboard)
    - Text-based ASCII tree (for terminal)
    - JSON hierarchy (for frontend rendering)
    """

    def __init__(self):
        pass

    def build_tree(self, scenarios: List[Dict]) -> ScenarioNode:
        """
        Build a ScenarioNode tree from a flat list of scenario dicts.
        
        Each scenario dict:
        {
            path: ["base", "fed_hike", "recession"],
            probability: 0.15,
            expected_return: -0.08,
            metadata: {}
        }
        """
        root = ScenarioNode(
            node_id="root", label="Market Scenarios",
            probability=1.0, expected_return=0.0, depth=0,
        )

        for scenario in scenarios:
            path = scenario.get("path", [])
            prob = scenario.get("probability", 0)
            ret = scenario.get("expected_return", 0)
            meta = scenario.get("metadata", {})

            current = root
            for i, step in enumerate(path):
                # Find or create child
                existing = None
                for child in current.children:
                    if child.label == step:
                        existing = child
                        break

                if existing is None:
                    new_node = ScenarioNode(
                        node_id=f"{current.node_id}_{step}",
                        label=step,
                        probability=prob if i == len(path) - 1 else 0,
                        expected_return=ret if i == len(path) - 1 else 0,
                        depth=i + 1,
                        metadata=meta if i == len(path) - 1 else {},
                    )
                    current.children.append(new_node)
                    current = new_node
                else:
                    if i == len(path) - 1:
                        existing.probability += prob
                        existing.expected_return = ret
                        existing.metadata.update(meta)
                    current = existing

        # Roll up probabilities to intermediate nodes
        self._rollup_probabilities(root)
        return root

    def _rollup_probabilities(self, node: ScenarioNode) -> float:
        """Roll up child probabilities to parent."""
        if not node.children:
            return node.probability

        total = sum(self._rollup_probabilities(c) for c in node.children)
        if node.node_id != "root":
            node.probability = total
        return total

    def to_mermaid(self, root: ScenarioNode) -> str:
        """Generate Mermaid flowchart diagram."""
        lines = ["graph TD"]
        self._mermaid_recurse(root, lines)
        return "\n    ".join(lines)

    def _mermaid_recurse(self, node: ScenarioNode, lines: List[str]) -> None:
        for child in node.children:
            prob_pct = child.probability * 100
            ret_pct = child.expected_return * 100

            # Color-coded: green for positive, red for negative
            if child.expected_return > 0.02:
                style = ":::positive"
            elif child.expected_return < -0.02:
                style = ":::negative"
            else:
                style = ":::neutral"

            label = f"{child.label}\\n({prob_pct:.1f}% | {ret_pct:+.1f}%)"
            line = f'{node.node_id}["{node.label}"] -->|{prob_pct:.0f}%| {child.node_id}["{label}"]{style}'
            lines.append(line)
            self._mermaid_recurse(child, lines)

    def to_ascii(self, root: ScenarioNode, indent: int = 0) -> str:
        """Generate ASCII tree representation."""
        lines = []
        self._ascii_recurse(root, lines, "", True)
        return "\n".join(lines)

    def _ascii_recurse(self, node: ScenarioNode, lines: List[str],
                        prefix: str, is_last: bool) -> None:
        connector = "└── " if is_last else "├── "
        prob_pct = node.probability * 100
        ret_pct = node.expected_return * 100
        marker = "▲" if node.expected_return > 0 else "▼" if node.expected_return < 0 else "─"

        if node.depth == 0:
            lines.append(f"[{node.label}] (p=100%)")
        else:
            lines.append(
                f"{prefix}{connector}{node.label} "
                f"(p={prob_pct:.1f}% | ret={ret_pct:+.1f}% {marker})"
            )

        next_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            self._ascii_recurse(child, lines, next_prefix, i == len(node.children) - 1)

    def to_json_hierarchy(self, root: ScenarioNode) -> Dict:
        """Convert tree to JSON-serializable hierarchy."""
        return self._node_to_dict(root)

    def _node_to_dict(self, node: ScenarioNode) -> Dict:
        return {
            "id": node.node_id,
            "label": node.label,
            "probability": round(node.probability, 4),
            "expected_return": round(node.expected_return, 4),
            "depth": node.depth,
            "metadata": node.metadata,
            "children": [self._node_to_dict(c) for c in node.children],
        }

    def to_plotly_treemap_data(self, root: ScenarioNode) -> Dict:
        """Generate data for Plotly treemap rendering."""
        ids = []
        labels = []
        parents = []
        values = []
        colors = []
        texts = []

        def _collect(node, parent_id=""):
            ids.append(node.node_id)
            labels.append(node.label)
            parents.append(parent_id)
            values.append(max(0.001, node.probability))
            colors.append(node.expected_return)
            texts.append(
                f"P={node.probability * 100:.1f}%<br>"
                f"Return={node.expected_return * 100:+.1f}%"
            )
            for child in node.children:
                _collect(child, node.node_id)

        _collect(root)

        return {
            "ids": ids,
            "labels": labels,
            "parents": parents,
            "values": values,
            "marker_colors": colors,
            "text": texts,
            "type": "treemap",
        }


# ---------------------------------------------------------------------------
#  5.4  Counter-Factual Analysis
# ---------------------------------------------------------------------------

@dataclass
class CounterFactual:
    name: str
    description: str
    removed_event: str
    original_outcome: Dict[str, float]
    counterfactual_outcome: Dict[str, float]
    delta: Dict[str, float]
    causal_contribution: float  # how much the event "caused" the outcome
    confidence: float


class CounterFactualAnalyzer:
    """
    Generate "what if X hadn't happened?" analyses.
    
    Methodology:
    1. Take the realized market state
    2. Remove one event's estimated impact
    3. Recalculate expected returns using remaining scenario weights
    4. The difference = causal contribution of that event
    
    Use cases:
    - "What if the Fed hadn't raised rates?"
    - "What if the CEO hadn't resigned?"
    - "What if oil prices hadn't spiked?"
    """

    def __init__(self):
        self._event_impacts: Dict[str, Dict[str, float]] = {}

    def register_event_impact(self, event_id: str, impacts: Dict[str, float]) -> None:
        """
        Register an event and its estimated impact on various assets.
        impacts: {asset: estimated_price_impact}
        """
        self._event_impacts[event_id] = impacts

    def analyze_counterfactual(self, event_id: str,
                                 realized_returns: Dict[str, float],
                                 scenario_tree: Optional[ScenarioNode] = None) -> CounterFactual:
        """
        Compute what would have happened without the given event.
        
        event_id: ID of event to remove
        realized_returns: {asset: actual_return}
        """
        if event_id not in self._event_impacts:
            return CounterFactual(
                name=event_id,
                description=f"Counterfactual: without {event_id}",
                removed_event=event_id,
                original_outcome=realized_returns,
                counterfactual_outcome=realized_returns,
                delta={},
                causal_contribution=0.0,
                confidence=0.0,
            )

        impacts = self._event_impacts[event_id]
        counterfactual_returns = {}
        deltas = {}

        for asset, actual_return in realized_returns.items():
            event_impact = impacts.get(asset, 0)
            cf_return = actual_return - event_impact
            counterfactual_returns[asset] = round(cf_return, 4)
            deltas[asset] = round(event_impact, 4)

        # Causal contribution: fraction of total return explained by this event
        total_abs_return = sum(abs(v) for v in realized_returns.values()) or 1
        total_abs_impact = sum(abs(v) for v in impacts.values())
        causal = min(1.0, total_abs_impact / total_abs_return)

        # Confidence: based on how well-estimated the impact is
        confidence = min(1.0, 0.5 + 0.1 * len(impacts))

        return CounterFactual(
            name=f"without_{event_id}",
            description=f"What if '{event_id}' hadn't happened?",
            removed_event=event_id,
            original_outcome=realized_returns,
            counterfactual_outcome=counterfactual_returns,
            delta=deltas,
            causal_contribution=round(causal, 3),
            confidence=round(confidence, 3),
        )

    def compare_counterfactuals(self, event_ids: List[str],
                                  realized_returns: Dict[str, float]) -> List[CounterFactual]:
        """Run multiple counterfactual analyses and rank by causal contribution."""
        results = [
            self.analyze_counterfactual(eid, realized_returns) for eid in event_ids
        ]
        results.sort(key=lambda cf: cf.causal_contribution, reverse=True)
        return results

    def sensitivity_analysis(self, event_id: str,
                               realized_returns: Dict[str, float],
                               scale_range: Tuple[float, ...] = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
                               ) -> List[Dict]:
        """
        Vary the event's impact magnitude and show sensitivity.
        Useful for "what if the rate hike was 50bp instead of 75bp?"
        """
        if event_id not in self._event_impacts:
            return []

        base_impacts = self._event_impacts[event_id]
        results = []

        for scale in scale_range:
            scaled_impacts = {k: v * scale for k, v in base_impacts.items()}
            cf_returns = {}
            for asset, actual_return in realized_returns.items():
                cf_returns[asset] = round(actual_return - base_impacts.get(asset, 0) +
                                           scaled_impacts.get(asset, 0), 4)

            results.append({
                "scale": scale,
                "label": f"{scale * 100:.0f}% of actual impact",
                "counterfactual_returns": cf_returns,
                "portfolio_return_delta": round(
                    sum(cf_returns.values()) / max(1, len(cf_returns)) -
                    sum(realized_returns.values()) / max(1, len(realized_returns)), 4
                ),
            })

        return results


# ---------------------------------------------------------------------------
#  5.5  Scenario-Based Portfolio Optimization
# ---------------------------------------------------------------------------

@dataclass
class ScenarioWeight:
    scenario_name: str
    probability: float
    expected_returns: Dict[str, float]  # asset -> return under this scenario


@dataclass
class OptimizedPortfolio:
    weights: Dict[str, float]           # asset -> weight
    expected_return: float
    worst_case_return: float
    scenario_returns: Dict[str, float]  # scenario -> portfolio return
    optimization_method: str
    risk_budget: Dict[str, float]


class ScenarioPortfolioOptimizer:
    """
    Find portfolio weights that are robust across the full scenario distribution.

    Methods:
    1. Max worst-case (minimax): optimize for the worst scenario
    2. Expected utility: probability-weighted utility maximization
    3. Risk parity across scenarios: equal risk contribution from each scenario
    4. CVaR optimization: minimize conditional value at risk across scenarios
    """

    def __init__(self, risk_aversion: float = 2.0):
        self.risk_aversion = risk_aversion

    def optimize(self, scenarios: List[ScenarioWeight],
                 assets: List[str],
                 method: str = "minimax",
                 constraints: Optional[Dict] = None) -> OptimizedPortfolio:
        """
        Optimize portfolio weights across scenarios.
        
        method: 'minimax', 'expected_utility', 'risk_parity', 'cvar'
        constraints: {
            max_weight: 0.3,     # max weight per asset
            min_weight: 0.0,     # min weight per asset (0 = long only)
            max_leverage: 1.0,   # sum of abs weights
        }
        """
        constraints = constraints or {"max_weight": 0.3, "min_weight": 0.0, "max_leverage": 1.0}

        if method == "minimax":
            return self._minimax_optimize(scenarios, assets, constraints)
        elif method == "expected_utility":
            return self._expected_utility_optimize(scenarios, assets, constraints)
        elif method == "risk_parity":
            return self._risk_parity_optimize(scenarios, assets, constraints)
        elif method == "cvar":
            return self._cvar_optimize(scenarios, assets, constraints)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _minimax_optimize(self, scenarios: List[ScenarioWeight],
                            assets: List[str],
                            constraints: Dict) -> OptimizedPortfolio:
        """
        Maximize the minimum portfolio return across all scenarios.
        Simple grid search + refinement (no scipy dependency needed).
        """
        n_assets = len(assets)
        max_w = constraints.get("max_weight", 0.3)
        min_w = constraints.get("min_weight", 0.0)

        best_weights = {a: 1.0 / n_assets for a in assets}  # equal weight start
        best_worst = float("-inf")

        # Grid search over simplex
        step = 0.05
        candidates = self._generate_weight_candidates(assets, step, max_w, min_w)

        for weights in candidates:
            scenario_rets = {}
            worst = float("inf")
            for sc in scenarios:
                port_ret = sum(weights.get(a, 0) * sc.expected_returns.get(a, 0)
                               for a in assets)
                scenario_rets[sc.scenario_name] = port_ret
                worst = min(worst, port_ret)

            if worst > best_worst:
                best_worst = worst
                best_weights = weights.copy()
                best_scenario_rets = scenario_rets.copy()

        exp_ret = sum(
            sc.probability * sum(best_weights.get(a, 0) * sc.expected_returns.get(a, 0)
                                  for a in assets)
            for sc in scenarios
        )

        risk_budget = self._calculate_risk_budget(best_weights, scenarios, assets)

        return OptimizedPortfolio(
            weights={a: round(w, 4) for a, w in best_weights.items()},
            expected_return=round(exp_ret, 4),
            worst_case_return=round(best_worst, 4),
            scenario_returns={k: round(v, 4) for k, v in best_scenario_rets.items()},
            optimization_method="minimax",
            risk_budget=risk_budget,
        )

    def _expected_utility_optimize(self, scenarios: List[ScenarioWeight],
                                     assets: List[str],
                                     constraints: Dict) -> OptimizedPortfolio:
        """Maximize E[U(R)] = E[R] - (risk_aversion/2) * Var[R]."""
        max_w = constraints.get("max_weight", 0.3)
        min_w = constraints.get("min_weight", 0.0)

        best_weights = {a: 1.0 / len(assets) for a in assets}
        best_utility = float("-inf")
        best_scenario_rets = {}

        candidates = self._generate_weight_candidates(assets, 0.05, max_w, min_w)

        for weights in candidates:
            # E[R] and Var[R]
            rets = []
            probs = []
            for sc in scenarios:
                port_ret = sum(weights.get(a, 0) * sc.expected_returns.get(a, 0)
                               for a in assets)
                rets.append(port_ret)
                probs.append(sc.probability)

            exp_r = sum(r * p for r, p in zip(rets, probs))
            var_r = sum(p * (r - exp_r) ** 2 for r, p in zip(rets, probs))
            utility = exp_r - (self.risk_aversion / 2) * var_r

            if utility > best_utility:
                best_utility = utility
                best_weights = weights.copy()
                best_scenario_rets = {
                    sc.scenario_name: sum(weights.get(a, 0) * sc.expected_returns.get(a, 0)
                                           for a in assets)
                    for sc in scenarios
                }

        worst = min(best_scenario_rets.values()) if best_scenario_rets else 0
        exp_ret = sum(
            sc.probability * sum(best_weights.get(a, 0) * sc.expected_returns.get(a, 0)
                                  for a in assets)
            for sc in scenarios
        )

        return OptimizedPortfolio(
            weights={a: round(w, 4) for a, w in best_weights.items()},
            expected_return=round(exp_ret, 4),
            worst_case_return=round(worst, 4),
            scenario_returns={k: round(v, 4) for k, v in best_scenario_rets.items()},
            optimization_method="expected_utility",
            risk_budget=self._calculate_risk_budget(best_weights, scenarios, assets),
        )

    def _risk_parity_optimize(self, scenarios: List[ScenarioWeight],
                                assets: List[str],
                                constraints: Dict) -> OptimizedPortfolio:
        """Equal risk contribution from each asset across scenarios."""
        n = len(assets)
        # Start with inverse-volatility weights
        vol = {}
        for a in assets:
            asset_rets = [sc.expected_returns.get(a, 0) for sc in scenarios]
            probs = [sc.probability for sc in scenarios]
            mean = sum(r * p for r, p in zip(asset_rets, probs))
            variance = sum(p * (r - mean) ** 2 for r, p in zip(asset_rets, probs))
            vol[a] = max(0.001, math.sqrt(variance))

        inv_vol = {a: 1.0 / v for a, v in vol.items()}
        total_inv = sum(inv_vol.values())
        weights = {a: inv_vol[a] / total_inv for a in assets}

        # Enforce constraints
        max_w = constraints.get("max_weight", 0.3)
        for a in weights:
            weights[a] = min(weights[a], max_w)
        total = sum(weights.values())
        if total > 0:
            weights = {a: w / total for a, w in weights.items()}

        scenario_rets = {}
        for sc in scenarios:
            port_ret = sum(weights.get(a, 0) * sc.expected_returns.get(a, 0)
                           for a in assets)
            scenario_rets[sc.scenario_name] = port_ret

        exp_ret = sum(
            sc.probability * sum(weights.get(a, 0) * sc.expected_returns.get(a, 0)
                                  for a in assets)
            for sc in scenarios
        )
        worst = min(scenario_rets.values()) if scenario_rets else 0

        return OptimizedPortfolio(
            weights={a: round(w, 4) for a, w in weights.items()},
            expected_return=round(exp_ret, 4),
            worst_case_return=round(worst, 4),
            scenario_returns={k: round(v, 4) for k, v in scenario_rets.items()},
            optimization_method="risk_parity",
            risk_budget=self._calculate_risk_budget(weights, scenarios, assets),
        )

    def _cvar_optimize(self, scenarios: List[ScenarioWeight],
                         assets: List[str],
                         constraints: Dict) -> OptimizedPortfolio:
        """Minimize CVaR (Expected Shortfall at 5th percentile) across scenarios."""
        max_w = constraints.get("max_weight", 0.3)
        min_w = constraints.get("min_weight", 0.0)
        alpha = 0.05  # 5% CVaR

        best_weights = {a: 1.0 / len(assets) for a in assets}
        best_cvar = float("inf")
        best_scenario_rets = {}

        candidates = self._generate_weight_candidates(assets, 0.05, max_w, min_w)

        for weights in candidates:
            rets_probs = []
            for sc in scenarios:
                port_ret = sum(weights.get(a, 0) * sc.expected_returns.get(a, 0)
                               for a in assets)
                rets_probs.append((port_ret, sc.probability))

            rets_probs.sort(key=lambda x: x[0])

            # CVaR = average of returns in worst alpha quantile
            cum_prob = 0.0
            cvar_sum = 0.0
            cvar_weight = 0.0
            for ret, prob in rets_probs:
                if cum_prob >= alpha:
                    break
                contribution = min(prob, alpha - cum_prob)
                cvar_sum += ret * contribution
                cvar_weight += contribution
                cum_prob += prob

            cvar = cvar_sum / max(0.001, cvar_weight)

            if cvar > best_cvar * -1:  # less negative = better
                if -cvar < best_cvar:
                    best_cvar = -cvar
                    best_weights = weights.copy()
                    best_scenario_rets = {
                        sc.scenario_name: sum(
                            weights.get(a, 0) * sc.expected_returns.get(a, 0)
                            for a in assets
                        )
                        for sc in scenarios
                    }

        exp_ret = sum(
            sc.probability * sum(best_weights.get(a, 0) * sc.expected_returns.get(a, 0)
                                  for a in assets)
            for sc in scenarios
        )
        worst = min(best_scenario_rets.values()) if best_scenario_rets else 0

        return OptimizedPortfolio(
            weights={a: round(w, 4) for a, w in best_weights.items()},
            expected_return=round(exp_ret, 4),
            worst_case_return=round(worst, 4),
            scenario_returns={k: round(v, 4) for k, v in best_scenario_rets.items()},
            optimization_method="cvar_5pct",
            risk_budget=self._calculate_risk_budget(best_weights, scenarios, assets),
        )

    def _generate_weight_candidates(self, assets: List[str], step: float,
                                      max_w: float, min_w: float) -> List[Dict[str, float]]:
        """Generate candidate weight vectors on the simplex."""
        n = len(assets)
        candidates = []

        if n <= 4:
            # Full grid for small N
            self._grid_recurse(assets, 0, {}, step, max_w, min_w, 1.0, candidates)
        else:
            # Heuristic: random perturbations around equal weight
            import random
            base = 1.0 / n
            for _ in range(200):
                weights = {}
                for a in assets:
                    w = base + random.uniform(-0.15, 0.15)
                    w = max(min_w, min(max_w, w))
                    weights[a] = w
                total = sum(weights.values())
                if total > 0:
                    weights = {a: w / total for a, w in weights.items()}
                    candidates.append(weights)

        # Always include equal weight
        candidates.append({a: 1.0 / n for a in assets})

        return candidates

    def _grid_recurse(self, assets, idx, current, step, max_w, min_w, remaining, candidates):
        if idx == len(assets) - 1:
            w = max(min_w, min(max_w, remaining))
            current[assets[idx]] = round(w, 4)
            if abs(sum(current.values()) - 1.0) < 0.01:
                candidates.append(current.copy())
            return

        w = min_w
        while w <= min(max_w, remaining):
            current[assets[idx]] = round(w, 4)
            self._grid_recurse(assets, idx + 1, current, step, max_w, min_w, remaining - w, candidates)
            w += step

    def _calculate_risk_budget(self, weights: Dict[str, float],
                                 scenarios: List[ScenarioWeight],
                                 assets: List[str]) -> Dict[str, float]:
        """Calculate risk contribution of each asset."""
        risk_contrib = {}
        total_risk = 0.0

        for a in assets:
            w = weights.get(a, 0)
            asset_rets = [sc.expected_returns.get(a, 0) for sc in scenarios]
            probs = [sc.probability for sc in scenarios]
            mean = sum(r * p for r, p in zip(asset_rets, probs))
            variance = sum(p * (r - mean) ** 2 for r, p in zip(asset_rets, probs))
            marginal_risk = w * math.sqrt(max(0, variance))
            risk_contrib[a] = marginal_risk
            total_risk += marginal_risk

        if total_risk > 0:
            risk_contrib = {a: round(r / total_risk, 4) for a, r in risk_contrib.items()}

        return risk_contrib
