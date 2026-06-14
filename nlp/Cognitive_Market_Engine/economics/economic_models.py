"""
ECONOMIC MODELING MODULE — Cognitive Market Engine

Purpose:
Calculates economic effects of news events by modeling macroeconomic
relationships. Fills the "Calculates economic effects" requirement
that was previously only partially addressed via causal chains.

Models:
1. Phillips Curve — Inflation ↔ Unemployment relationship
2. Yield Curve — Term structure analysis and inversion signals
3. GDP Impact — News event → GDP growth rate impact estimation
4. Taylor Rule — Implied policy rate from inflation + output gap
5. Fiscal Multiplier — Government spending → GDP effect
6. Exchange Rate Impact — Interest rate differential → currency moves

All models are simplified approximations for research/analysis,
not full econometric implementations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math
import logging

logger = logging.getLogger("cme.economics")


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class EconomicState:
    """Current macroeconomic state (inputs to models)."""
    # Inflation
    cpi_yoy: float = 3.0          # Year-over-year CPI %
    core_cpi_yoy: float = 2.8     # Core CPI (ex food/energy) %
    inflation_expectation: float = 2.5  # Market-implied expected inflation %
    
    # Employment
    unemployment_rate: float = 4.0    # %
    nfp_change: int = 200_000        # Non-farm payrolls monthly change
    wage_growth_yoy: float = 3.5     # Average hourly earnings YoY %
    
    # Growth
    gdp_growth_yoy: float = 2.5      # Real GDP growth %
    gdp_potential: float = 2.0       # Potential GDP growth %
    output_gap: float = 0.5          # Actual - Potential GDP %
    
    # Rates
    fed_funds_rate: float = 5.0      # Current federal funds rate %
    ten_year_yield: float = 4.5      # 10-year Treasury yield %
    two_year_yield: float = 4.8      # 2-year Treasury yield %
    
    # Fiscal
    government_spending_change: float = 0.0  # Change in G as % of GDP
    
    # External
    oil_price_change_pct: float = 0.0   # % change in crude oil
    usd_dxy_level: float = 104.0        # Dollar index


@dataclass
class EconomicImpact:
    """Output: estimated economic effects of an event."""
    event_description: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # GDP effects
    gdp_impact_pct: float = 0.0          # Estimated GDP impact in %
    gdp_impact_direction: str = "neutral"  # positive / negative / neutral
    
    # Inflation effects
    inflation_impact_pct: float = 0.0     # Estimated CPI change in %
    inflation_direction: str = "neutral"
    
    # Rates effects
    implied_policy_rate: float = 0.0      # Taylor Rule implied rate
    rate_change_probability: float = 0.0  # Probability of rate change
    
    # Yield curve
    yield_curve_slope: float = 0.0        # 10y - 2y spread
    recession_signal: bool = False        # Inverted curve = recession risk
    
    # Currency
    usd_impact: str = "neutral"           # bullish / bearish / neutral
    
    # Overall assessment
    severity: str = "low"     # low / moderate / high / extreme
    confidence: float = 0.5
    reasoning: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "event": self.event_description,
            "gdp_impact": f"{self.gdp_impact_pct:+.2f}%",
            "gdp_direction": self.gdp_impact_direction,
            "inflation_impact": f"{self.inflation_impact_pct:+.2f}%",
            "implied_policy_rate": f"{self.implied_policy_rate:.2f}%",
            "yield_curve_slope": f"{self.yield_curve_slope:.2f}%",
            "recession_signal": self.recession_signal,
            "usd_impact": self.usd_impact,
            "severity": self.severity,
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
        }


# ============================================================
# ECONOMIC MODELS
# ============================================================

class PhillipsCurveModel:
    """
    Models the inverse relationship between inflation and unemployment.
    
    Uses a simplified expectations-augmented Phillips Curve:
    π = πe - β(U - U*) + ε
    
    Where:
    - π = actual inflation
    - πe = expected inflation  
    - β = slope coefficient (how much unemployment affects inflation)
    - U = unemployment rate
    - U* = natural rate of unemployment (NAIRU)
    - ε = supply shocks (oil, etc.)
    """
    
    def __init__(self, nairu: float = 4.5, beta: float = 0.5):
        self.nairu = nairu  # Natural rate of unemployment
        self.beta = beta    # Slope coefficient
    
    def estimate_inflation(self, state: EconomicState) -> Tuple[float, str]:
        """
        Estimate implied inflation from labor market conditions.
        
        Returns: (estimated_inflation, reasoning)
        """
        unemployment_gap = state.unemployment_rate - self.nairu
        supply_shock = state.oil_price_change_pct * 0.03  # Oil pass-through
        
        implied_inflation = (
            state.inflation_expectation
            - self.beta * unemployment_gap
            + supply_shock
        )
        
        reasoning = (
            f"Phillips Curve: πe={state.inflation_expectation:.1f}% "
            f"- {self.beta}×(U={state.unemployment_rate:.1f}% - NAIRU={self.nairu:.1f}%) "
            f"+ oil_shock={supply_shock:+.2f}% "
            f"→ implied inflation = {implied_inflation:.2f}%"
        )
        
        return round(implied_inflation, 3), reasoning
    
    def unemployment_impact(
        self,
        nfp_surprise: int,
        state: EconomicState
    ) -> Tuple[float, str]:
        """
        Estimate unemployment rate change from NFP surprise.
        
        Args:
            nfp_surprise: actual NFP - expected NFP
        """
        # Okun's Law approximation: 100K jobs ≈ 0.06% unemployment change
        unemployment_change = -nfp_surprise / 100_000 * 0.06
        new_rate = state.unemployment_rate + unemployment_change
        
        reasoning = (
            f"NFP surprise {nfp_surprise:+,} → "
            f"unemployment {state.unemployment_rate:.1f}% → {new_rate:.1f}% "
            f"(Δ{unemployment_change:+.2f}%)"
        )
        
        return round(unemployment_change, 4), reasoning


class YieldCurveModel:
    """
    Analyzes yield curve for recession signals and rate expectations.
    
    Key signals:
    - Normal: 10y > 2y (positive slope) → growth expected
    - Flat: 10y ≈ 2y → slowdown ahead
    - Inverted: 10y < 2y (negative slope) → recession warning
    
    Historical: Every US recession since 1955 preceded by 2y/10y inversion.
    """
    
    def analyze(self, state: EconomicState) -> Dict:
        """Analyze current yield curve state."""
        spread = state.ten_year_yield - state.two_year_yield
        
        # Classification
        if spread > 0.50:
            shape = "normal"
            recession_probability = max(0, 0.15 - spread * 0.05)
        elif spread > 0.0:
            shape = "flat"
            recession_probability = 0.20 + (0.50 - spread) * 0.40
        elif spread > -0.50:
            shape = "mildly_inverted"
            recession_probability = 0.40 + abs(spread) * 0.40
        else:
            shape = "deeply_inverted"
            recession_probability = min(0.85, 0.60 + abs(spread) * 0.30)
        
        # Term premium decomposition (simplified)
        # Real rate ≈ fed_funds - expected_inflation
        real_rate = state.fed_funds_rate - state.inflation_expectation
        
        # Implied growth expectation from long end
        implied_growth = state.ten_year_yield - state.inflation_expectation - 0.5  # 0.5% term premium
        
        return {
            "spread_2y_10y": round(spread, 3),
            "shape": shape,
            "recession_probability": round(recession_probability, 3),
            "real_rate": round(real_rate, 3),
            "implied_growth": round(implied_growth, 3),
            "reasoning": (
                f"2y={state.two_year_yield:.2f}%, 10y={state.ten_year_yield:.2f}%, "
                f"spread={spread:+.2f}% → {shape}. "
                f"Recession probability: {recession_probability:.0%}. "
                f"Real rate: {real_rate:.2f}%. "
                f"Implied growth: {implied_growth:.2f}%"
            )
        }
    
    def rate_change_impact(
        self,
        rate_change_bps: int,
        state: EconomicState
    ) -> Dict:
        """
        Estimate yield curve impact from a rate change.
        
        Args:
            rate_change_bps: basis points change (e.g., +25, -50)
        """
        change_pct = rate_change_bps / 100
        
        # Short end moves more than long end (typical response)
        two_year_move = change_pct * 0.85  # 85% pass-through
        ten_year_move = change_pct * 0.40  # 40% pass-through
        
        new_2y = state.two_year_yield + two_year_move
        new_10y = state.ten_year_yield + ten_year_move
        new_spread = new_10y - new_2y
        
        return {
            "rate_change_bps": rate_change_bps,
            "new_2y_yield": round(new_2y, 3),
            "new_10y_yield": round(new_10y, 3),
            "new_spread": round(new_spread, 3),
            "curve_flattening": new_spread < (state.ten_year_yield - state.two_year_yield),
            "inversion_risk": new_spread < 0,
        }


class TaylorRuleModel:
    """
    Taylor Rule — estimates the appropriate policy interest rate.
    
    i* = r* + π + 0.5(π - π*) + 0.5(y - y*)
    
    Where:
    - i* = implied policy rate
    - r* = equilibrium real rate (typically 0.5-2.0%)
    - π = current inflation
    - π* = target inflation (2%)
    - y = actual GDP growth
    - y* = potential GDP growth (output gap)
    """
    
    def __init__(
        self,
        equilibrium_real_rate: float = 1.0,
        target_inflation: float = 2.0,
        inflation_coefficient: float = 0.5,
        output_gap_coefficient: float = 0.5
    ):
        self.r_star = equilibrium_real_rate
        self.pi_star = target_inflation
        self.alpha = inflation_coefficient
        self.beta = output_gap_coefficient
    
    def compute(self, state: EconomicState) -> Dict:
        """Compute Taylor Rule implied rate."""
        inflation_gap = state.cpi_yoy - self.pi_star
        output_gap = state.gdp_growth_yoy - state.gdp_potential
        
        implied_rate = (
            self.r_star
            + state.cpi_yoy
            + self.alpha * inflation_gap
            + self.beta * output_gap
        )
        
        rate_diff = implied_rate - state.fed_funds_rate
        
        if rate_diff > 0.25:
            policy_stance = "too_loose"
            recommendation = "hike"
        elif rate_diff < -0.25:
            policy_stance = "too_tight"
            recommendation = "cut"
        else:
            policy_stance = "appropriate"
            recommendation = "hold"
        
        return {
            "implied_rate": round(implied_rate, 3),
            "current_rate": state.fed_funds_rate,
            "rate_gap": round(rate_diff, 3),
            "policy_stance": policy_stance,
            "recommendation": recommendation,
            "reasoning": (
                f"Taylor Rule: r*={self.r_star}% + π={state.cpi_yoy:.1f}% "
                f"+ {self.alpha}×(π-π*)={self.alpha}×{inflation_gap:+.1f}% "
                f"+ {self.beta}×(y-y*)={self.beta}×{output_gap:+.1f}% "
                f"= {implied_rate:.2f}%. "
                f"Current={state.fed_funds_rate:.2f}%. "
                f"Gap={rate_diff:+.2f}% → {recommendation}"
            )
        }


class GDPImpactModel:
    """
    Estimates GDP impact of various economic events.
    
    Uses simplified multiplier/elasticity models for:
    - Rate changes → GDP (monetary policy transmission)
    - Oil shocks → GDP (supply-side effect)
    - Government spending → GDP (fiscal multiplier)
    - NFP surprises → GDP (labor market signal)
    """
    
    def __init__(self):
        # Elasticities (simplified)
        self.rate_to_gdp = -0.3   # 100bps hike → -0.3% GDP (with lag)
        self.oil_to_gdp = -0.02   # 10% oil hike → -0.2% GDP
        self.fiscal_multiplier = 1.2  # $1 spending → $1.20 GDP
        self.nfp_to_gdp = 0.001   # Per 10K NFP → 0.01% GDP
    
    def rate_change_impact(self, rate_change_bps: int) -> Dict:
        """Estimate GDP impact of a rate change."""
        impact = (rate_change_bps / 100) * self.rate_to_gdp
        
        return {
            "gdp_impact_pct": round(impact, 4),
            "direction": "negative" if impact < 0 else "positive" if impact > 0 else "neutral",
            "lag_quarters": "3-6",  # Monetary policy operates with a lag
            "reasoning": f"{rate_change_bps:+d}bps rate change → {impact:+.3f}% GDP impact (3-6 quarter lag)"
        }
    
    def oil_shock_impact(self, oil_change_pct: float) -> Dict:
        """Estimate GDP impact of oil price changes."""
        impact = oil_change_pct * self.oil_to_gdp
        
        return {
            "gdp_impact_pct": round(impact, 4),
            "direction": "negative" if impact < 0 else "positive",
            "inflation_pass_through": round(oil_change_pct * 0.03, 3),
            "reasoning": f"{oil_change_pct:+.1f}% oil → {impact:+.3f}% GDP, {oil_change_pct * 0.03:+.2f}% CPI"
        }
    
    def fiscal_impact(self, spending_change_pct_gdp: float) -> Dict:
        """Estimate GDP impact of fiscal spending changes."""
        impact = spending_change_pct_gdp * self.fiscal_multiplier
        
        return {
            "gdp_impact_pct": round(impact, 4),
            "fiscal_multiplier_used": self.fiscal_multiplier,
            "reasoning": f"{spending_change_pct_gdp:+.2f}% GDP spending × {self.fiscal_multiplier} multiplier → {impact:+.3f}% GDP"
        }


class ExchangeRateModel:
    """
    Models USD impact from interest rate differentials and capital flows.
    
    Simplified interest rate parity + risk premium approach.
    """
    
    def rate_differential_impact(
        self,
        us_rate_change_bps: int,
        foreign_rate_change_bps: int = 0
    ) -> Dict:
        """
        Estimate USD impact from rate differential changes.
        
        A wider US rate advantage → stronger USD (capital inflows).
        """
        net_differential = us_rate_change_bps - foreign_rate_change_bps
        
        # Approximate: 25bps differential → ~0.5-1% USD move
        usd_impact_pct = net_differential / 25 * 0.7
        
        if net_differential > 0:
            direction = "bullish"
        elif net_differential < 0:
            direction = "bearish"
        else:
            direction = "neutral"
        
        return {
            "net_rate_differential_bps": net_differential,
            "usd_impact_pct": round(usd_impact_pct, 3),
            "direction": direction,
            "reasoning": (
                f"Rate differential {net_differential:+d}bps → "
                f"USD {direction} ({usd_impact_pct:+.2f}% estimated DXY move)"
            )
        }


# ============================================================
# UNIFIED ECONOMIC ANALYZER
# ============================================================

class EconomicAnalyzer:
    """
    Unified interface for economic analysis.
    
    Combines all economic models to produce comprehensive
    economic impact assessments from news events.
    
    Usage:
        analyzer = EconomicAnalyzer()
        impact = analyzer.analyze_rate_decision(+25, state)
        impact = analyzer.analyze_event("gdp_miss", {"miss_pct": -0.3}, state)
    """
    
    def __init__(self):
        self.phillips = PhillipsCurveModel()
        self.yield_curve = YieldCurveModel()
        self.taylor = TaylorRuleModel()
        self.gdp = GDPImpactModel()
        self.fx = ExchangeRateModel()
    
    def analyze_rate_decision(
        self,
        rate_change_bps: int,
        state: EconomicState
    ) -> EconomicImpact:
        """Full economic analysis of a rate decision."""
        impact = EconomicImpact(
            event_description=f"Rate {'hike' if rate_change_bps > 0 else 'cut'} of {abs(rate_change_bps)}bps"
        )
        
        # GDP impact
        gdp_result = self.gdp.rate_change_impact(rate_change_bps)
        impact.gdp_impact_pct = gdp_result["gdp_impact_pct"]
        impact.gdp_impact_direction = gdp_result["direction"]
        impact.reasoning.append(gdp_result["reasoning"])
        
        # Taylor Rule
        taylor_result = self.taylor.compute(state)
        impact.implied_policy_rate = taylor_result["implied_rate"]
        impact.reasoning.append(taylor_result["reasoning"])
        
        # Yield curve
        yield_result = self.yield_curve.rate_change_impact(rate_change_bps, state)
        yc_analysis = self.yield_curve.analyze(state)
        impact.yield_curve_slope = yc_analysis["spread_2y_10y"]
        impact.recession_signal = yc_analysis["recession_probability"] > 0.5
        impact.reasoning.append(yc_analysis["reasoning"])
        
        # Inflation via Phillips Curve
        inflation_est, inflation_reason = self.phillips.estimate_inflation(state)
        impact.inflation_impact_pct = inflation_est - state.cpi_yoy
        impact.inflation_direction = "up" if impact.inflation_impact_pct > 0 else "down"
        impact.reasoning.append(inflation_reason)
        
        # USD impact
        fx_result = self.fx.rate_differential_impact(rate_change_bps)
        impact.usd_impact = fx_result["direction"]
        impact.reasoning.append(fx_result["reasoning"])
        
        # Severity assessment
        impact.severity = self._assess_severity(abs(rate_change_bps), {
            25: "low", 50: "moderate", 75: "high", 100: "extreme"
        })
        impact.confidence = 0.75
        
        return impact
    
    def analyze_inflation_data(
        self,
        cpi_actual: float,
        cpi_expected: float,
        state: EconomicState
    ) -> EconomicImpact:
        """Analyze inflation data surprise."""
        surprise = cpi_actual - cpi_expected
        
        impact = EconomicImpact(
            event_description=f"CPI {cpi_actual:.1f}% vs expected {cpi_expected:.1f}%"
        )
        
        impact.inflation_impact_pct = surprise
        impact.inflation_direction = "up" if surprise > 0 else "down" if surprise < 0 else "neutral"
        
        # Taylor Rule with updated inflation
        updated_state = EconomicState(
            cpi_yoy=cpi_actual,
            core_cpi_yoy=state.core_cpi_yoy,
            inflation_expectation=state.inflation_expectation,
            unemployment_rate=state.unemployment_rate,
            gdp_growth_yoy=state.gdp_growth_yoy,
            gdp_potential=state.gdp_potential,
            fed_funds_rate=state.fed_funds_rate,
            ten_year_yield=state.ten_year_yield,
            two_year_yield=state.two_year_yield,
        )
        taylor_result = self.taylor.compute(updated_state)
        impact.implied_policy_rate = taylor_result["implied_rate"]
        impact.rate_change_probability = min(1.0, abs(taylor_result["rate_gap"]) / 0.5)
        impact.reasoning.append(taylor_result["reasoning"])
        
        # Rate expectation → GDP
        implied_rate_change = round((taylor_result["implied_rate"] - state.fed_funds_rate) * 100)
        gdp_result = self.gdp.rate_change_impact(implied_rate_change)
        impact.gdp_impact_pct = gdp_result["gdp_impact_pct"]
        impact.gdp_impact_direction = gdp_result["direction"]
        impact.reasoning.append(f"Inflation surprise {surprise:+.1f}% → {gdp_result['reasoning']}")
        
        # USD
        fx_result = self.fx.rate_differential_impact(
            max(-50, min(50, int(surprise * 25)))  # Surprise → implied rate change
        )
        impact.usd_impact = fx_result["direction"]
        impact.reasoning.append(fx_result["reasoning"])
        
        impact.severity = self._assess_severity(abs(surprise), {
            0.1: "low", 0.3: "moderate", 0.5: "high", 1.0: "extreme"
        })
        impact.confidence = 0.70
        
        return impact
    
    def analyze_employment_data(
        self,
        nfp_actual: int,
        nfp_expected: int,
        state: EconomicState
    ) -> EconomicImpact:
        """Analyze employment data (NFP) surprise."""
        surprise = nfp_actual - nfp_expected
        
        impact = EconomicImpact(
            event_description=f"NFP {nfp_actual:+,} vs expected {nfp_expected:+,}"
        )
        
        # Unemployment impact
        u_change, u_reason = self.phillips.unemployment_impact(surprise, state)
        impact.reasoning.append(u_reason)
        
        # Inflation implications
        updated_state = EconomicState(
            cpi_yoy=state.cpi_yoy,
            unemployment_rate=state.unemployment_rate + u_change,
            inflation_expectation=state.inflation_expectation,
            gdp_growth_yoy=state.gdp_growth_yoy,
            gdp_potential=state.gdp_potential,
            fed_funds_rate=state.fed_funds_rate,
            ten_year_yield=state.ten_year_yield,
            two_year_yield=state.two_year_yield,
        )
        inflation_est, inflation_reason = self.phillips.estimate_inflation(updated_state)
        impact.inflation_impact_pct = inflation_est - state.cpi_yoy
        impact.inflation_direction = "up" if impact.inflation_impact_pct > 0 else "down"
        impact.reasoning.append(inflation_reason)
        
        # GDP signal
        gdp_signal = surprise * 0.001 / 10  # Very rough approximation
        impact.gdp_impact_pct = round(gdp_signal, 4)
        impact.gdp_impact_direction = "positive" if surprise > 0 else "negative"
        
        # Taylor Rule
        taylor = self.taylor.compute(updated_state)
        impact.implied_policy_rate = taylor["implied_rate"]
        impact.reasoning.append(taylor["reasoning"])
        
        impact.severity = self._assess_severity(abs(surprise), {
            50_000: "low", 100_000: "moderate", 200_000: "high", 300_000: "extreme"
        })
        impact.confidence = 0.65
        
        return impact
    
    def analyze_geopolitical_event(
        self,
        event_type: str,
        severity_score: float,
        state: EconomicState
    ) -> EconomicImpact:
        """
        Analyze geopolitical event's economic impact.
        
        Args:
            event_type: "conflict", "sanctions", "trade_war", "political_crisis"
            severity_score: 0.0 to 1.0
        """
        impact = EconomicImpact(
            event_description=f"Geopolitical: {event_type} (severity {severity_score:.1f})"
        )
        
        # Supply-side GDP shock
        gdp_shock_map = {
            "conflict": -0.5,
            "sanctions": -0.3,
            "trade_war": -0.4,
            "political_crisis": -0.2,
        }
        base_gdp_impact = gdp_shock_map.get(event_type, -0.2) * severity_score
        impact.gdp_impact_pct = round(base_gdp_impact, 4)
        impact.gdp_impact_direction = "negative"
        
        # Oil/commodity shock
        oil_shock_map = {
            "conflict": 15.0,
            "sanctions": 10.0,
            "trade_war": 5.0,
            "political_crisis": 3.0,
        }
        estimated_oil_change = oil_shock_map.get(event_type, 5.0) * severity_score
        oil_impact = self.gdp.oil_shock_impact(estimated_oil_change)
        impact.inflation_impact_pct = oil_impact["inflation_pass_through"]
        impact.inflation_direction = "up"
        impact.reasoning.append(oil_impact["reasoning"])
        
        # Safe haven flows → USD
        if severity_score > 0.5:
            impact.usd_impact = "bullish"  # Flight to safety
            impact.reasoning.append(f"High severity ({severity_score:.1f}) → USD safe haven flows")
        else:
            impact.usd_impact = "neutral"
        
        # Yield curve: flight to quality → lower long rates
        if severity_score > 0.6:
            impact.yield_curve_slope = state.ten_year_yield - state.two_year_yield - severity_score * 0.3
            impact.reasoning.append("Flight to quality → curve flattening")
        
        impact.severity = self._assess_severity(severity_score, {
            0.3: "low", 0.5: "moderate", 0.7: "high", 0.9: "extreme"
        })
        impact.confidence = 0.55  # Geopolitical has high uncertainty
        
        impact.reasoning.append(
            f"Geopolitical {event_type}: GDP {base_gdp_impact:+.2f}%, "
            f"oil {estimated_oil_change:+.1f}%, severity={severity_score:.1f}"
        )
        
        return impact
    
    def get_macro_snapshot(self, state: EconomicState) -> Dict:
        """Get a comprehensive macro snapshot with all models."""
        taylor = self.taylor.compute(state)
        yield_analysis = self.yield_curve.analyze(state)
        inflation_est, _ = self.phillips.estimate_inflation(state)
        
        return {
            "taylor_rule": taylor,
            "yield_curve": yield_analysis,
            "phillips_curve_inflation": inflation_est,
            "output_gap": state.output_gap,
            "real_rate": round(state.fed_funds_rate - state.cpi_yoy, 3),
            "recession_probability": yield_analysis["recession_probability"],
            "policy_stance": taylor["policy_stance"],
        }
    
    @staticmethod
    def _assess_severity(value: float, thresholds: Dict[float, str]) -> str:
        """Map a numeric value to a severity label using thresholds."""
        result = "low"
        for threshold, label in sorted(thresholds.items()):
            if value >= threshold:
                result = label
        return result
