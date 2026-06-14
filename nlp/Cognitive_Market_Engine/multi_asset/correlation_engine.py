"""
CORRELATION ENGINE — Cross-asset correlation analysis

Tracks and analyzes correlations between:
- Equities, bonds, currencies, commodities, crypto
- Regime-dependent correlation shifts
- Correlation breakdown detection (crisis indicator)
- Rolling correlation windows

Key insight: Correlations are NOT constant — they change during
different market regimes (risk-on, risk-off, crisis).
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime


@dataclass
class CorrelationPair:
    """Correlation between two assets."""
    asset_a: str = ""
    asset_b: str = ""
    correlation: float = 0.0
    rolling_30d: float = 0.0
    rolling_90d: float = 0.0
    regime: str = "normal"     # normal, risk_on, risk_off, crisis
    
    # Historical
    mean_correlation: float = 0.0
    std_correlation: float = 0.0
    current_z_score: float = 0.0   # How unusual current correlation is
    
    # Breakdown detection
    is_breaking_down: bool = False
    breakdown_severity: float = 0.0


@dataclass
class CorrelationMatrix:
    """Full cross-asset correlation snapshot."""
    timestamp: str = ""
    regime: str = "normal"
    pairs: List[CorrelationPair] = field(default_factory=list)
    
    # Aggregate metrics
    avg_correlation: float = 0.0
    correlation_dispersion: float = 0.0
    n_breakdowns: int = 0
    systemic_risk_indicator: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "regime": self.regime,
            "avg_correlation": round(self.avg_correlation, 4),
            "correlation_dispersion": round(self.correlation_dispersion, 4),
            "n_breakdowns": self.n_breakdowns,
            "systemic_risk_indicator": round(self.systemic_risk_indicator, 4),
            "top_correlations": [
                {
                    "pair": f"{p.asset_a}/{p.asset_b}",
                    "correlation": round(p.correlation, 4),
                    "regime": p.regime,
                    "z_score": round(p.current_z_score, 2),
                    "breaking_down": p.is_breaking_down,
                }
                for p in sorted(self.pairs, key=lambda x: abs(x.correlation), reverse=True)[:15]
            ]
        }


class CorrelationEngine:
    """
    Tracks cross-asset correlations and detects regime changes.
    
    Maintains rolling correlation windows and compares to historical norms.
    """
    
    # Pre-defined asset pairs with expected normal correlations
    BASELINE_CORRELATIONS = {
        ("SPX", "NASDAQ"): 0.92,
        ("SPX", "DJIA"): 0.95,
        ("SPX", "US_10Y"): -0.30,
        ("SPX", "GOLD"): -0.10,
        ("SPX", "VIX"): -0.80,
        ("SPX", "USD"): -0.15,
        ("SPX", "OIL_WTI"): 0.20,
        ("SPX", "BTC"): 0.35,
        
        ("US_10Y", "US_2Y"): 0.80,
        ("US_10Y", "GOLD"): -0.25,
        ("US_10Y", "USD"): 0.30,
        
        ("USD", "GOLD"): -0.45,
        ("USD", "EUR"): -0.90,
        ("USD", "JPY"): -0.55,
        ("USD", "OIL_WTI"): -0.35,
        ("USD", "BTC"): -0.25,
        
        ("GOLD", "SILVER"): 0.88,
        ("GOLD", "BTC"): 0.20,
        
        ("OIL_WTI", "OIL_BRENT"): 0.98,
        ("BTC", "ETH"): 0.85,
        
        ("EUR", "GBP"): 0.70,
        ("EUR", "CHF"): 0.65,
    }
    
    # Regime-specific correlation adjustments
    REGIME_ADJUSTMENTS = {
        "risk_off": {
            ("SPX", "GOLD"): 0.3,       # Gold de-correlates from equities
            ("SPX", "US_10Y"): -0.2,     # Flight to safety
            ("SPX", "VIX"): -0.1,        # VIX spikes more
            ("USD", "GOLD"): -0.1,       # Both safe havens
            ("SPX", "BTC"): -0.3,        # Crypto sells off with risk
        },
        "crisis": {
            ("SPX", "GOLD"): 0.5,        # Everything correlates in crisis
            ("SPX", "US_10Y"): 0.5,       # Correlations converge to 1
            ("SPX", "BTC"): 0.4,          # All risk assets dump
            ("USD", "GOLD"): 0.3,         # Even safe havens diverge
        },
        "risk_on": {
            ("SPX", "BTC"): 0.2,          # Risk assets rally together
            ("SPX", "OIL_WTI"): 0.1,
            ("USD", "GOLD"): -0.1,        # USD weakens, gold neutral
        },
    }
    
    def __init__(self):
        """Initialize CorrelationEngine."""
        self.price_history = defaultdict(lambda: deque(maxlen=252))  # 1 year of daily
        self.correlation_history = defaultdict(lambda: deque(maxlen=100))
        self.current_regime = "normal"
        print("[CORRELATION] Engine initialized")
    
    def update_prices(self, asset: str, price: float, timestamp: str = None):
        """
        Feed price data for correlation tracking.
        
        Args:
            asset: Asset identifier
            price: Current price
            timestamp: Timestamp of price
        """
        self.price_history[asset].append({
            "price": price,
            "timestamp": timestamp or datetime.now().isoformat(),
        })
    
    def compute_matrix(self, regime: str = None) -> CorrelationMatrix:
        """
        Compute full cross-asset correlation matrix.
        
        Args:
            regime: Override detected regime (normal, risk_on, risk_off, crisis)
            
        Returns:
            CorrelationMatrix with all pairs
        """
        regime = regime or self.current_regime
        
        matrix = CorrelationMatrix(
            timestamp=datetime.now().isoformat(),
            regime=regime,
        )
        
        # Compute correlations for all tracked pairs
        for (asset_a, asset_b), baseline in self.BASELINE_CORRELATIONS.items():
            pair = self._compute_pair(asset_a, asset_b, baseline, regime)
            matrix.pairs.append(pair)
        
        # Aggregate metrics
        if matrix.pairs:
            correlations = [p.correlation for p in matrix.pairs]
            matrix.avg_correlation = sum(abs(c) for c in correlations) / len(correlations)
            
            mean_c = sum(correlations) / len(correlations)
            matrix.correlation_dispersion = math.sqrt(
                sum((c - mean_c) ** 2 for c in correlations) / len(correlations)
            )
            
            matrix.n_breakdowns = sum(1 for p in matrix.pairs if p.is_breaking_down)
            
            # Systemic risk: all correlations moving toward 1
            matrix.systemic_risk_indicator = self._compute_systemic_risk(matrix)
        
        return matrix
    
    def detect_regime(self, market_data: Dict = None) -> str:
        """
        Detect current market regime from correlations and data.
        
        Args:
            market_data: Optional dict with VIX, SPX change, etc.
            
        Returns:
            Regime string: "normal", "risk_on", "risk_off", "crisis"
        """
        if not market_data:
            return self.current_regime
        
        vix = market_data.get("vix", 20)
        spx_change = market_data.get("spx_change_pct", 0)
        
        if vix > 40 or spx_change < -3:
            regime = "crisis"
        elif vix > 25 or spx_change < -1:
            regime = "risk_off"
        elif vix < 15 and spx_change > 0.5:
            regime = "risk_on"
        else:
            regime = "normal"
        
        self.current_regime = regime
        return regime
    
    def get_impact_map(self, event_entity: str) -> List[Dict]:
        """
        Given an entity affected by news, map expected cross-asset impact.
        
        Args:
            event_entity: The primary entity affected (e.g., "USD", "SPX")
            
        Returns:
            List of {asset, expected_direction, correlation, confidence}
        """
        impacts = []
        
        for (a, b), baseline in self.BASELINE_CORRELATIONS.items():
            if a == event_entity:
                impacts.append({
                    "asset": b,
                    "correlation": baseline,
                    "expected_direction": "same" if baseline > 0 else "opposite",
                    "confidence": abs(baseline),
                })
            elif b == event_entity:
                impacts.append({
                    "asset": a,
                    "correlation": baseline,
                    "expected_direction": "same" if baseline > 0 else "opposite",
                    "confidence": abs(baseline),
                })
        
        impacts.sort(key=lambda x: x["confidence"], reverse=True)
        return impacts
    
    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalous correlation behavior."""
        anomalies = []
        
        matrix = self.compute_matrix()
        
        for pair in matrix.pairs:
            if pair.is_breaking_down:
                anomalies.append({
                    "type": "correlation_breakdown",
                    "pair": f"{pair.asset_a}/{pair.asset_b}",
                    "expected": round(pair.mean_correlation, 3),
                    "actual": round(pair.correlation, 3),
                    "z_score": round(pair.current_z_score, 2),
                    "severity": round(pair.breakdown_severity, 3),
                })
            
            if abs(pair.current_z_score) > 2:
                anomalies.append({
                    "type": "unusual_correlation",
                    "pair": f"{pair.asset_a}/{pair.asset_b}",
                    "z_score": round(pair.current_z_score, 2),
                    "explanation": "Correlation significantly deviates from historical norm",
                })
        
        anomalies.sort(key=lambda x: abs(x.get("z_score", 0)), reverse=True)
        return anomalies
    
    def _compute_pair(self, asset_a: str, asset_b: str, 
                      baseline: float, regime: str) -> CorrelationPair:
        """Compute correlation for a single pair."""
        pair = CorrelationPair(asset_a=asset_a, asset_b=asset_b)
        
        # Try to compute from actual price data
        prices_a = list(self.price_history.get(asset_a, []))
        prices_b = list(self.price_history.get(asset_b, []))
        
        if len(prices_a) >= 30 and len(prices_b) >= 30:
            # Compute rolling correlations from actual data
            returns_a = self._compute_returns([p["price"] for p in prices_a])
            returns_b = self._compute_returns([p["price"] for p in prices_b])
            
            min_len = min(len(returns_a), len(returns_b))
            if min_len >= 20:
                pair.rolling_30d = self._pearson_correlation(
                    returns_a[-30:], returns_b[-30:]
                )
                pair.rolling_90d = self._pearson_correlation(
                    returns_a[-90:], returns_b[-90:]
                ) if min_len >= 90 else pair.rolling_30d
                
                pair.correlation = pair.rolling_30d
            else:
                pair.correlation = baseline
        else:
            # Use baseline with regime adjustment
            adjustment = self.REGIME_ADJUSTMENTS.get(regime, {}).get(
                (asset_a, asset_b), 0
            )
            pair.correlation = max(-1.0, min(1.0, baseline + adjustment))
            pair.rolling_30d = pair.correlation
            pair.rolling_90d = baseline
        
        pair.mean_correlation = baseline
        pair.std_correlation = 0.15  # Default
        
        # Z-score
        if pair.std_correlation > 0:
            pair.current_z_score = (pair.correlation - baseline) / pair.std_correlation
        
        # Breakdown detection
        if abs(pair.current_z_score) > 2:
            pair.is_breaking_down = True
            pair.breakdown_severity = min(1.0, abs(pair.current_z_score) / 4)
        
        pair.regime = regime
        
        return pair
    
    def _compute_returns(self, prices: List[float]) -> List[float]:
        """Compute log returns from prices."""
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0 and prices[i] > 0:
                returns.append(math.log(prices[i] / prices[i-1]))
            else:
                returns.append(0.0)
        return returns
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Compute Pearson correlation coefficient."""
        n = min(len(x), len(y))
        if n < 2:
            return 0.0
        
        x = x[:n]
        y = y[:n]
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
        std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
        std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)
        
        if std_x * std_y == 0:
            return 0.0
        
        return max(-1.0, min(1.0, cov / (std_x * std_y)))
    
    def _compute_systemic_risk(self, matrix: CorrelationMatrix) -> float:
        """
        Compute systemic risk indicator.
        
        When all correlations move toward 1, systemic risk is high.
        """
        if not matrix.pairs:
            return 0.0
        
        # Measure how many pairs have unusual correlations
        unusual = sum(1 for p in matrix.pairs if abs(p.current_z_score) > 1.5)
        breakdown = matrix.n_breakdowns
        
        risk = (unusual / max(1, len(matrix.pairs))) * 0.5
        risk += (breakdown / max(1, len(matrix.pairs))) * 0.3
        risk += (matrix.avg_correlation - 0.4) * 0.5 if matrix.avg_correlation > 0.4 else 0
        
        return round(min(1.0, max(0.0, risk)), 4)
