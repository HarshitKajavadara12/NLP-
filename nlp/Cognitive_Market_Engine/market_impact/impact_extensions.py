"""
Market Impact Extensions — Categories 7.3, 7.4, 2.6
====================================================
7.3  Impact Attribution — decompose a price move into contributing factors
     (news impact, technical factors, order flow, macro, sentiment)
7.4  Cross-Asset Impact Cascade — model how impact propagates:
     company → suppliers → competitors → sector ETF → related sectors
2.6  Sector / ETF Flow Data — track fund flow data as a sentiment proxy
"""
import time
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

logger = logging.getLogger("cme.market_impact.extensions")

# ---------------------------------------------------------------------------
#  7.3  Impact Attribution — Decompose Price Move By Factor
# ---------------------------------------------------------------------------

@dataclass
class PriceFactor:
    name: str
    contribution_pct: float      # % of total price move explained
    contribution_bps: float      # basis points
    confidence: float            # 0-1
    evidence: List[str]
    direction: str               # positive / negative / neutral


@dataclass
class ImpactAttribution:
    asset: str
    total_move_pct: float
    period_start: str
    period_end: str
    factors: List[PriceFactor]
    unexplained_pct: float       # residual not attributable
    r_squared: float             # goodness of fit
    dominant_factor: str


class ImpactAttributionEngine:
    """
    Decompose an observed price move into contributing factors.

    Factor catalog:
    - news_sentiment: impact from news articles
    - earnings_surprise: earnings beat/miss
    - macro_rates: interest rate / yield curve changes
    - sector_momentum: sector-level flows
    - technical_signal: breakout / breakdown signals
    - order_flow: buy/sell imbalance
    - options_flow: unusual options activity
    - analyst_revision: upgrades / downgrades
    - insider_activity: Form 4 transactions
    - social_sentiment: Reddit/Twitter/StockTwits sentiment shift
    """

    FACTOR_REGISTRY = {
        "news_sentiment": {"default_impact_range": (-0.05, 0.05), "weight": 0.20},
        "earnings_surprise": {"default_impact_range": (-0.10, 0.10), "weight": 0.15},
        "macro_rates": {"default_impact_range": (-0.03, 0.03), "weight": 0.15},
        "sector_momentum": {"default_impact_range": (-0.02, 0.02), "weight": 0.10},
        "technical_signal": {"default_impact_range": (-0.02, 0.02), "weight": 0.10},
        "order_flow": {"default_impact_range": (-0.03, 0.03), "weight": 0.10},
        "options_flow": {"default_impact_range": (-0.02, 0.02), "weight": 0.05},
        "analyst_revision": {"default_impact_range": (-0.05, 0.05), "weight": 0.05},
        "insider_activity": {"default_impact_range": (-0.02, 0.02), "weight": 0.05},
        "social_sentiment": {"default_impact_range": (-0.02, 0.02), "weight": 0.05},
    }

    def __init__(self):
        self._history: List[ImpactAttribution] = []

    def attribute(self, asset: str, total_move_pct: float,
                  factor_observations: Dict[str, Dict],
                  period_start: str = "", period_end: str = "") -> ImpactAttribution:
        """
        Decompose a price move into factors.
        
        factor_observations: {
            "news_sentiment": {"value": 0.7, "confidence": 0.8, "evidence": ["headline"]},
            "earnings_surprise": {"value": 0.05, "confidence": 0.9, "evidence": ["beat by 5%"]},
            ...
        }
        value: normalized signal strength (-1 to 1)
        """
        factors = []
        attributed_total = 0.0

        for factor_name, registry in self.FACTOR_REGISTRY.items():
            obs = factor_observations.get(factor_name, {})
            signal = obs.get("value", 0)
            confidence = obs.get("confidence", 0)
            evidence = obs.get("evidence", [])

            if signal == 0 and confidence == 0:
                continue

            # Map signal to impact
            low, high = registry["default_impact_range"]
            impact_range = high - low
            estimated_impact = signal * impact_range * registry["weight"]

            # Scale to total move
            contribution_pct = (estimated_impact / total_move_pct * 100) if total_move_pct != 0 else 0
            contribution_bps = estimated_impact * 10000

            direction = "positive" if estimated_impact > 0 else "negative" if estimated_impact < 0 else "neutral"

            factors.append(PriceFactor(
                name=factor_name,
                contribution_pct=round(contribution_pct, 2),
                contribution_bps=round(contribution_bps, 2),
                confidence=round(confidence, 3),
                evidence=evidence,
                direction=direction,
            ))
            attributed_total += abs(contribution_pct)

        # Sort by absolute contribution
        factors.sort(key=lambda f: abs(f.contribution_pct), reverse=True)

        unexplained = max(0, 100 - attributed_total)
        r_squared = min(1.0, attributed_total / 100) if attributed_total > 0 else 0

        dominant = factors[0].name if factors else "unknown"

        result = ImpactAttribution(
            asset=asset,
            total_move_pct=total_move_pct,
            period_start=period_start,
            period_end=period_end,
            factors=factors,
            unexplained_pct=round(unexplained, 2),
            r_squared=round(r_squared, 3),
            dominant_factor=dominant,
        )
        self._history.append(result)
        return result


# ---------------------------------------------------------------------------
#  7.4  Cross-Asset Impact Cascade
# ---------------------------------------------------------------------------

@dataclass
class CascadeStep:
    from_asset: str
    to_asset: str
    relationship: str       # supplier, competitor, sector_peer, etf_component, macro_link
    transmission_delay_hours: float
    impact_decay: float     # fraction of impact transmitted (0-1)
    estimated_impact_pct: float
    confidence: float


@dataclass
class CascadeResult:
    origin_asset: str
    origin_event: str
    origin_impact_pct: float
    cascade_steps: List[CascadeStep]
    total_affected_assets: int
    total_cascade_impact: float   # sum of all secondary impacts
    max_depth: int


class CrossAssetCascadeModel:
    """
    Model how an event's impact propagates through an asset network:
    Company → Suppliers → Competitors → Sector ETF → Related Sectors

    Graph edges have:
    - relationship_type (supplier, customer, competitor, sector_peer, etf)
    - correlation (historical co-movement)
    - transmission_delay (hours)
    - decay_factor (how much impact is lost at each hop)
    """

    def __init__(self, max_depth: int = 4, min_impact_threshold: float = 0.001):
        self.max_depth = max_depth
        self.min_impact = min_impact_threshold
        # asset -> [(related_asset, relationship, correlation, delay_hours, decay)]
        self._graph: Dict[str, List[Tuple]] = defaultdict(list)
        self._asset_sectors: Dict[str, str] = {}  # asset -> sector

    def add_relationship(self, asset_a: str, asset_b: str,
                          relationship: str, correlation: float = 0.5,
                          delay_hours: float = 2.0, decay: float = 0.5) -> None:
        """Add a directed relationship edge."""
        self._graph[asset_a].append((asset_b, relationship, correlation, delay_hours, decay))

    def add_sector(self, asset: str, sector: str) -> None:
        self._asset_sectors[asset] = sector

    def build_common_graph(self, supply_chain: Dict[str, List[str]],
                            competitors: Dict[str, List[str]],
                            etf_components: Dict[str, List[str]]) -> None:
        """
        Build from structured data sources.
        supply_chain: {company: [supplier1, supplier2, ...]}
        competitors: {company: [competitor1, ...]}
        etf_components: {etf: [component1, component2, ...]}
        """
        for company, suppliers in supply_chain.items():
            for supplier in suppliers:
                self.add_relationship(company, supplier, "supplier",
                                       correlation=0.4, delay_hours=4, decay=0.4)
                self.add_relationship(supplier, company, "customer",
                                       correlation=0.3, delay_hours=6, decay=0.3)

        for company, comps in competitors.items():
            for comp in comps:
                self.add_relationship(company, comp, "competitor",
                                       correlation=-0.3, delay_hours=1, decay=0.5)

        for etf, components in etf_components.items():
            for comp in components:
                self.add_relationship(comp, etf, "etf_component",
                                       correlation=0.6, delay_hours=0.5, decay=0.6)
                self.add_relationship(etf, comp, "etf_holding",
                                       correlation=0.3, delay_hours=1, decay=0.3)

    def simulate_cascade(self, origin_asset: str, event_name: str,
                           origin_impact_pct: float) -> CascadeResult:
        """
        Simulate how an impact cascades through the asset network.
        Uses BFS with decay.
        """
        visited: Set[str] = {origin_asset}
        cascade_steps: List[CascadeStep] = []
        queue = [(origin_asset, origin_impact_pct, 0)]  # (asset, impact, depth)

        while queue:
            current_asset, current_impact, depth = queue.pop(0)

            if depth >= self.max_depth:
                continue

            neighbors = self._graph.get(current_asset, [])
            for (next_asset, relationship, correlation, delay, decay) in neighbors:
                if next_asset in visited:
                    continue

                transmitted_impact = current_impact * decay * abs(correlation)

                if relationship == "competitor":
                    transmitted_impact *= -1 * abs(correlation)  # inverse for competitors

                if abs(transmitted_impact) < self.min_impact:
                    continue

                step = CascadeStep(
                    from_asset=current_asset,
                    to_asset=next_asset,
                    relationship=relationship,
                    transmission_delay_hours=delay,
                    impact_decay=decay,
                    estimated_impact_pct=round(transmitted_impact, 4),
                    confidence=round(abs(correlation) * (0.9 ** depth), 3),
                )
                cascade_steps.append(step)
                visited.add(next_asset)
                queue.append((next_asset, transmitted_impact, depth + 1))

        cascade_steps.sort(key=lambda s: abs(s.estimated_impact_pct), reverse=True)

        total_cascade = sum(abs(s.estimated_impact_pct) for s in cascade_steps)
        max_d = max((s.confidence for s in cascade_steps), default=0)

        return CascadeResult(
            origin_asset=origin_asset,
            origin_event=event_name,
            origin_impact_pct=origin_impact_pct,
            cascade_steps=cascade_steps,
            total_affected_assets=len(cascade_steps),
            total_cascade_impact=round(total_cascade, 4),
            max_depth=self.max_depth,
        )


# ---------------------------------------------------------------------------
#  2.6  Sector / ETF Flow Data Tracking
# ---------------------------------------------------------------------------

@dataclass
class FlowDataPoint:
    date: str
    sector_or_etf: str
    net_flow_millions: float      # positive = inflow, negative = outflow
    total_aum_millions: float
    flow_pct_of_aum: float
    creation_units: int           # ETF creation/redemption units
    source: str                   # ICI, ETF.com, Bloomberg


@dataclass
class FlowAnalysis:
    sector_or_etf: str
    period_days: int
    total_net_flow: float
    avg_daily_flow: float
    flow_streak_days: int          # consecutive days of same direction
    flow_momentum: float           # acceleration of flows
    flow_vs_returns_correlation: float
    signal: str                    # "strong_inflow", "strong_outflow", "neutral"
    contrarian_signal: str         # when everyone is buying = potential top


class SectorFlowTracker:
    """
    Track sector/ETF fund flow data as a sentiment and positioning proxy.
    
    Features:
    - Net flow tracking (creation/redemption units for ETFs)
    - Flow momentum (are flows accelerating or decelerating?)
    - Contrarian signals (extreme flows = potential reversal)
    - Flow-return correlation (does money follow or lead performance?)
    """

    SIGNAL_THRESHOLDS = {
        "strong_inflow": 0.02,     # 2% AUM daily inflow
        "moderate_inflow": 0.005,
        "moderate_outflow": -0.005,
        "strong_outflow": -0.02,
    }

    def __init__(self, lookback_days: int = 63):
        self.lookback = lookback_days
        self._flows: Dict[str, List[FlowDataPoint]] = defaultdict(list)
        self._returns: Dict[str, List[Tuple[str, float]]] = defaultdict(list)

    def add_flow(self, flow: FlowDataPoint) -> None:
        self._flows[flow.sector_or_etf].append(flow)
        # Keep sorted by date
        self._flows[flow.sector_or_etf].sort(key=lambda f: f.date)

    def add_return(self, sector_or_etf: str, date: str, return_pct: float) -> None:
        self._returns[sector_or_etf].append((date, return_pct))

    def analyze(self, sector_or_etf: str,
                period_days: int = 30) -> FlowAnalysis:
        """Analyze flow patterns for a sector/ETF."""
        flows = self._flows.get(sector_or_etf, [])
        if not flows:
            return FlowAnalysis(
                sector_or_etf=sector_or_etf, period_days=period_days,
                total_net_flow=0, avg_daily_flow=0, flow_streak_days=0,
                flow_momentum=0, flow_vs_returns_correlation=0,
                signal="no_data", contrarian_signal="no_data",
            )

        recent = flows[-period_days:]
        if not recent:
            recent = flows

        total_flow = sum(f.net_flow_millions for f in recent)
        avg_flow = total_flow / len(recent)
        avg_aum = sum(f.total_aum_millions for f in recent) / len(recent)
        flow_pct = total_flow / avg_aum if avg_aum > 0 else 0

        # Flow streak
        streak = 0
        if recent:
            last_dir = 1 if recent[-1].net_flow_millions > 0 else -1
            for f in reversed(recent):
                curr_dir = 1 if f.net_flow_millions > 0 else -1
                if curr_dir == last_dir:
                    streak += 1
                else:
                    break

        # Flow momentum (2nd half vs 1st half)
        mid = len(recent) // 2
        first_half = sum(f.net_flow_millions for f in recent[:mid])
        second_half = sum(f.net_flow_millions for f in recent[mid:])
        momentum = (second_half - first_half) / max(1, abs(first_half) + abs(second_half))

        # Flow-return correlation
        flow_return_corr = self._flow_return_correlation(sector_or_etf, period_days)

        # Signal classification
        daily_pct = avg_flow / avg_aum if avg_aum > 0 else 0
        if daily_pct > self.SIGNAL_THRESHOLDS["strong_inflow"]:
            signal = "strong_inflow"
        elif daily_pct > self.SIGNAL_THRESHOLDS["moderate_inflow"]:
            signal = "moderate_inflow"
        elif daily_pct < self.SIGNAL_THRESHOLDS["strong_outflow"]:
            signal = "strong_outflow"
        elif daily_pct < self.SIGNAL_THRESHOLDS["moderate_outflow"]:
            signal = "moderate_outflow"
        else:
            signal = "neutral"

        # Contrarian: extreme + extended streak
        contrarian = "neutral"
        if signal == "strong_inflow" and streak > 10:
            contrarian = "potential_top_crowded_long"
        elif signal == "strong_outflow" and streak > 10:
            contrarian = "potential_bottom_capitulation"

        return FlowAnalysis(
            sector_or_etf=sector_or_etf,
            period_days=period_days,
            total_net_flow=round(total_flow, 2),
            avg_daily_flow=round(avg_flow, 2),
            flow_streak_days=streak,
            flow_momentum=round(momentum, 3),
            flow_vs_returns_correlation=round(flow_return_corr, 3),
            signal=signal,
            contrarian_signal=contrarian,
        )

    def get_sector_rotation_map(self) -> Dict[str, str]:
        """Show which sectors money is flowing into/out of."""
        rotation = {}
        for sector in self._flows:
            analysis = self.analyze(sector, period_days=20)
            rotation[sector] = analysis.signal
        return rotation

    def _flow_return_correlation(self, sector_or_etf: str, period_days: int) -> float:
        """Calculate correlation between flows and returns."""
        flows = self._flows.get(sector_or_etf, [])[-period_days:]
        returns = self._returns.get(sector_or_etf, [])[-period_days:]

        if len(flows) < 5 or len(returns) < 5:
            return 0.0

        flow_vals = [f.net_flow_millions for f in flows[:min(len(flows), len(returns))]]
        ret_vals = [r[1] for r in returns[:len(flow_vals)]]

        return self._pearson(flow_vals, ret_vals)

    @staticmethod
    def _pearson(x: List[float], y: List[float]) -> float:
        n = len(x)
        if n < 2:
            return 0.0
        mx = sum(x) / n
        my = sum(y) / n
        vx = sum((xi - mx) ** 2 for xi in x)
        vy = sum((yi - my) ** 2 for yi in y)
        if vx == 0 or vy == 0:
            return 0.0
        cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
        return cov / math.sqrt(vx * vy)
