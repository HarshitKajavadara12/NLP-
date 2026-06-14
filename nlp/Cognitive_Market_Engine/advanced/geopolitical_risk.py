"""
GEOPOLITICAL RISK SCORER — Geopolitical risk assessment framework.

Scores geopolitical events and maps them to market impact:
- Regional conflict risk levels
- Sanctions and trade war escalation
- Political instability indices
- Supply chain disruption risk
- Energy security assessment
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class GeopoliticalEvent:
    """A geopolitical event with risk scores."""
    event_type: str
    region: str
    description: str
    severity: float  # 0-1
    escalation_risk: float  # 0-1 probability of escalation
    market_relevance: float  # 0-1
    affected_assets: List[str] = None
    affected_sectors: List[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if self.affected_assets is None:
            self.affected_assets = []
        if self.affected_sectors is None:
            self.affected_sectors = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def composite_risk(self) -> float:
        """Overall risk score."""
        return (self.severity * 0.4 +
                self.escalation_risk * 0.3 +
                self.market_relevance * 0.3)
    
    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type,
            "region": self.region,
            "description": self.description,
            "severity": round(self.severity, 3),
            "escalation_risk": round(self.escalation_risk, 3),
            "market_relevance": round(self.market_relevance, 3),
            "composite_risk": round(self.composite_risk(), 3),
            "affected_assets": self.affected_assets,
            "affected_sectors": self.affected_sectors,
        }


class GeopoliticalRiskScorer:
    """
    Geopolitical risk scoring framework.
    
    Maps geopolitical events to risk levels and market impacts.
    Uses keyword-based classification with regional risk profiles.
    """
    
    # Event type classifications
    EVENT_TYPES = {
        "military_conflict": {
            "keywords": ["war", "military", "invasion", "troops", "airstrike",
                        "missile", "attack", "conflict", "combat", "offensive"],
            "base_severity": 0.85,
            "default_assets": ["GLD", "UST", "XLE", "VIX"],
        },
        "sanctions": {
            "keywords": ["sanction", "embargo", "ban", "restrict", "blacklist",
                        "freeze assets", "trade ban", "tariff"],
            "base_severity": 0.6,
            "default_assets": ["USD", "EUR", "commodities"],
        },
        "trade_war": {
            "keywords": ["tariff", "trade war", "import duty", "trade deficit",
                        "retaliation", "trade restriction", "decoupling"],
            "base_severity": 0.55,
            "default_assets": ["SPY", "FXI", "EEM", "USD"],
        },
        "political_instability": {
            "keywords": ["coup", "protest", "revolution", "election crisis",
                        "impeachment", "government collapse", "civil unrest"],
            "base_severity": 0.5,
            "default_assets": ["EEM", "FX-local", "VIX"],
        },
        "terrorism": {
            "keywords": ["terror", "bombing", "terrorist", "attack",
                        "hostage", "extremist"],
            "base_severity": 0.7,
            "default_assets": ["VIX", "GLD", "UST"],
        },
        "cyber_attack": {
            "keywords": ["cyber attack", "hack", "ransomware", "data breach",
                        "infrastructure attack", "cyber warfare"],
            "base_severity": 0.5,
            "default_assets": ["QQQ", "HACK", "VIX"],
        },
        "energy_crisis": {
            "keywords": ["oil embargo", "pipeline", "OPEC cut", "energy crisis",
                        "gas shortage", "oil supply", "refinery"],
            "base_severity": 0.65,
            "default_assets": ["XLE", "CL", "NG", "USO"],
        },
        "nuclear": {
            "keywords": ["nuclear", "uranium", "enrichment", "warhead",
                        "nuclear test", "ICBM"],
            "base_severity": 0.95,
            "default_assets": ["GLD", "VIX", "UST", "JPY"],
        },
    }
    
    # Regional risk profiles
    REGIONS = {
        "middle_east": {
            "keywords": ["iran", "iraq", "syria", "saudi", "israel",
                        "yemen", "lebanon", "gaza", "strait of hormuz"],
            "energy_sensitivity": 0.9,
            "base_risk_premium": 0.3,
            "key_assets": ["XLE", "CL", "GLD"],
        },
        "east_asia": {
            "keywords": ["china", "taiwan", "north korea", "south china sea",
                        "japan", "korea"],
            "energy_sensitivity": 0.4,
            "base_risk_premium": 0.25,
            "key_assets": ["FXI", "EWJ", "TSM", "USD/CNY"],
        },
        "europe": {
            "keywords": ["russia", "ukraine", "nato", "eu", "brexit",
                        "european", "baltics"],
            "energy_sensitivity": 0.7,
            "base_risk_premium": 0.2,
            "key_assets": ["EUR", "EWG", "TTF"],
        },
        "americas": {
            "keywords": ["us", "canada", "mexico", "brazil", "venezuela",
                        "latin america", "usmca"],
            "energy_sensitivity": 0.5,
            "base_risk_premium": 0.15,
            "key_assets": ["SPY", "EWZ", "USD/MXN"],
        },
        "africa": {
            "keywords": ["africa", "nigeria", "south africa", "ethiopia",
                        "congo", "sahel"],
            "energy_sensitivity": 0.3,
            "base_risk_premium": 0.1,
            "key_assets": ["EZA", "commodities"],
        },
        "south_asia": {
            "keywords": ["india", "pakistan", "kashmir", "sri lanka",
                        "bangladesh"],
            "energy_sensitivity": 0.3,
            "base_risk_premium": 0.15,
            "key_assets": ["INDA", "INR"],
        },
    }
    
    def __init__(self):
        self.active_risks: List[GeopoliticalEvent] = []
        self.risk_history: List[Dict] = []
        print("[GEOPOLITICAL] Risk scorer initialized")
    
    def score_event(self, text: str, source: str = "") -> GeopoliticalEvent:
        """
        Score a geopolitical event from text.
        
        Args:
            text: Event description
            source: Source of the information
            
        Returns:
            GeopoliticalEvent with risk scores
        """
        text_lower = text.lower()
        
        # Classify event type
        event_type, type_score = self._classify_event_type(text_lower)
        
        # Identify region
        region, region_data = self._identify_region(text_lower)
        
        # Compute severity
        severity = self._compute_severity(text_lower, event_type, type_score)
        
        # Escalation risk
        escalation = self._assess_escalation(text_lower, event_type)
        
        # Market relevance
        relevance = self._assess_market_relevance(text_lower, region_data)
        
        # Affected assets
        type_data = self.EVENT_TYPES.get(event_type, {})
        assets = list(set(
            type_data.get("default_assets", []) +
            region_data.get("key_assets", [])
        ))
        
        # Affected sectors
        sectors = self._identify_sectors(text_lower, event_type)
        
        event = GeopoliticalEvent(
            event_type=event_type,
            region=region,
            description=text[:300],
            severity=severity,
            escalation_risk=escalation,
            market_relevance=relevance,
            affected_assets=assets,
            affected_sectors=sectors,
        )
        
        self.active_risks.append(event)
        self.risk_history.append(event.to_dict())
        
        return event
    
    def get_global_risk_index(self) -> Dict:
        """
        Compute global geopolitical risk index from active risks.
        """
        if not self.active_risks:
            return {
                "risk_index": 0.0,
                "level": "low",
                "active_events": 0,
                "hotspots": [],
            }
        
        # Weighted average of recent risks
        max_risk = max(e.composite_risk() for e in self.active_risks)
        avg_risk = sum(e.composite_risk() for e in self.active_risks) / len(self.active_risks)
        
        # Global index: blend of max and average
        index = 0.6 * max_risk + 0.4 * avg_risk
        
        # Determine level
        if index > 0.8:
            level = "critical"
        elif index > 0.6:
            level = "high"
        elif index > 0.4:
            level = "elevated"
        elif index > 0.2:
            level = "moderate"
        else:
            level = "low"
        
        # Hotspots
        regions = {}
        for e in self.active_risks:
            if e.region not in regions:
                regions[e.region] = []
            regions[e.region].append(e.composite_risk())
        
        hotspots = [
            {"region": r, "risk": round(max(scores), 3), "events": len(scores)}
            for r, scores in sorted(regions.items(),
                                     key=lambda x: -max(x[1]))
        ]
        
        return {
            "risk_index": round(index, 3),
            "level": level,
            "active_events": len(self.active_risks),
            "hotspots": hotspots,
            "most_affected_assets": self._get_most_affected_assets(),
        }
    
    def _classify_event_type(self, text: str) -> tuple:
        """Classify the type of geopolitical event."""
        best_type = "political_instability"
        best_score = 0
        
        for etype, config in self.EVENT_TYPES.items():
            score = sum(1 for kw in config["keywords"] if kw in text)
            if score > best_score:
                best_score = score
                best_type = etype
        
        return best_type, best_score
    
    def _identify_region(self, text: str) -> tuple:
        """Identify the geographic region."""
        best_region = "global"
        best_score = 0
        best_data = {}
        
        for region, config in self.REGIONS.items():
            score = sum(1 for kw in config["keywords"] if kw in text)
            if score > best_score:
                best_score = score
                best_region = region
                best_data = config
        
        return best_region, best_data
    
    def _compute_severity(self, text: str, event_type: str,
                          keyword_score: int) -> float:
        """Compute event severity."""
        base = self.EVENT_TYPES.get(event_type, {}).get("base_severity", 0.5)
        
        # Severity modifiers
        escalation_words = ["escalat", "intensif", "expand", "spread",
                           "worst", "unprecedented", "emergency"]
        deescalation_words = ["ceasefire", "negotiate", "peace", "de-escalat",
                             "withdraw", "resolve", "calm"]
        
        esc = sum(1 for w in escalation_words if w in text) * 0.05
        deesc = sum(1 for w in deescalation_words if w in text) * 0.05
        
        severity = base + esc - deesc
        
        # Keyword density bonus
        if keyword_score > 3:
            severity += 0.1
        
        return max(0.0, min(1.0, severity))
    
    def _assess_escalation(self, text: str, event_type: str) -> float:
        """Assess probability of escalation."""
        base = 0.3
        
        escalation_signals = [
            "threat", "ultimatum", "deadline", "mobiliz", "deploy",
            "retaliat", "response", "counter", "warn", "prepar",
        ]
        
        deescalation_signals = [
            "talk", "diplomat", "negotiat", "agree", "compromise",
            "ceasefire", "withdraw", "peaceful",
        ]
        
        esc = sum(1 for w in escalation_signals if w in text) * 0.08
        deesc = sum(1 for w in deescalation_signals if w in text) * 0.08
        
        if event_type in ("nuclear", "military_conflict"):
            base += 0.15
        
        return max(0.0, min(1.0, base + esc - deesc))
    
    def _assess_market_relevance(self, text: str, region_data: Dict) -> float:
        """Assess market relevance of the event."""
        base = region_data.get("base_risk_premium", 0.2)
        
        market_words = ["market", "stock", "oil", "energy", "trade",
                       "supply chain", "inflation", "currency", "bond",
                       "investor", "economic"]
        
        relevance = base + sum(1 for w in market_words if w in text) * 0.07
        
        # Energy sensitivity boost
        energy_words = ["oil", "gas", "energy", "pipeline", "opec", "refinery"]
        if any(w in text for w in energy_words):
            relevance += region_data.get("energy_sensitivity", 0.3) * 0.2
        
        return max(0.0, min(1.0, relevance))
    
    def _identify_sectors(self, text: str, event_type: str) -> List[str]:
        """Identify affected market sectors."""
        sectors = []
        
        sector_keywords = {
            "energy": ["oil", "gas", "energy", "pipeline", "refinery", "opec"],
            "defense": ["military", "weapons", "defense", "arms", "missile"],
            "technology": ["tech", "semiconductor", "chip", "cyber", "ai"],
            "financial": ["bank", "currency", "bond", "interest rate"],
            "agriculture": ["food", "grain", "wheat", "agriculture", "famine"],
            "shipping": ["shipping", "supply chain", "cargo", "port", "strait"],
            "mining": ["mining", "rare earth", "metals", "gold", "uranium"],
        }
        
        for sector, keywords in sector_keywords.items():
            if any(kw in text for kw in keywords):
                sectors.append(sector)
        
        if not sectors:
            sectors = ["broad_market"]
        
        return sectors
    
    def _get_most_affected_assets(self) -> List[str]:
        """Get most frequently affected assets across active risks."""
        asset_counts = {}
        for e in self.active_risks:
            risk = e.composite_risk()
            for a in e.affected_assets:
                asset_counts[a] = asset_counts.get(a, 0) + risk
        
        return sorted(asset_counts, key=asset_counts.get, reverse=True)[:10]
