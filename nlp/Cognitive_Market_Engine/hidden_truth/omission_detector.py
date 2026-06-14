"""
OMISSION DETECTOR — Detect what's NOT being said

The most powerful lies are told through silence.

Detects:
- Expected information that's missing from a statement
- Topics that should be addressed but aren't
- Data points that are conspicuously absent
- Hedging language that avoids commitment
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Omission:
    """A detected omission."""
    category: str = ""         # "data", "topic", "qualifier", "timeline"
    expected: str = ""         # What was expected
    significance: float = 0.0  # How important this omission is (0-1)
    explanation: str = ""      # Why this matters
    manipulation_risk: float = 0.0  # How likely this is deliberate


@dataclass
class OmissionReport:
    """Full omission analysis of a text."""
    total_omissions: int = 0
    critical_omissions: int = 0
    overall_omission_score: float = 0.0  # Higher = more sus
    omissions: List[Omission] = field(default_factory=list)
    hedging_score: float = 0.0
    specificity_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "total_omissions": self.total_omissions,
            "critical_omissions": self.critical_omissions,
            "overall_omission_score": round(self.overall_omission_score, 3),
            "hedging_score": round(self.hedging_score, 3),
            "specificity_score": round(self.specificity_score, 3),
            "omissions": [
                {
                    "category": o.category,
                    "expected": o.expected,
                    "significance": round(o.significance, 3),
                    "explanation": o.explanation,
                    "manipulation_risk": round(o.manipulation_risk, 3),
                }
                for o in self.omissions
            ]
        }


class OmissionDetector:
    """
    Detects what's missing from financial statements and reports.
    
    Key principle: When someone carefully controls their words,
    what they DON'T say is often more important than what they do.
    """
    
    # What should be mentioned when discussing these topics
    TOPIC_EXPECTATIONS = {
        "rate_decision": {
            "required": ["inflation", "employment", "growth", "forward guidance"],
            "expected": ["balance sheet", "financial conditions", "data dependent",
                        "risks", "outlook", "unanimous", "dissent"],
            "optional": ["housing", "credit", "wage growth", "productivity"],
        },
        "inflation": {
            "required": ["core inflation", "headline inflation", "expectations"],
            "expected": ["food", "energy", "shelter", "services", "goods",
                        "wage", "supply chain", "transitory", "persistent"],
            "optional": ["pce", "cpi", "producer prices"],
        },
        "gdp": {
            "required": ["growth rate", "quarter", "year-over-year"],
            "expected": ["consumer spending", "investment", "government",
                        "trade", "inventories", "revision"],
            "optional": ["potential gdp", "output gap", "productivity"],
        },
        "earnings": {
            "required": ["revenue", "earnings per share", "guidance"],
            "expected": ["margins", "costs", "competition", "market share",
                        "backlog", "restructuring"],
            "optional": ["capex", "r&d", "headcount", "acquisitions"],
        },
        "employment": {
            "required": ["jobs added", "unemployment rate"],
            "expected": ["participation rate", "wage growth", "hours worked",
                        "underemployment", "job openings"],
            "optional": ["sector breakdown", "temporary", "part-time"],
        },
        "banking": {
            "required": ["capital ratios", "provisions", "assets"],
            "expected": ["loan growth", "deposits", "net interest margin",
                        "non-performing loans", "stress tests"],
            "optional": ["trading revenue", "advisory fees"],
        },
        "geopolitical": {
            "required": ["parties involved", "actions taken"],
            "expected": ["timeline", "consequences", "diplomatic channels",
                        "economic impact", "sanctions"],
            "optional": ["military details", "intelligence"],
        },
    }
    
    # Hedging language patterns
    HEDGING_PATTERNS = [
        "may", "might", "could", "possibly", "potentially",
        "approximately", "roughly", "about", "around",
        "somewhat", "to some extent", "in some ways",
        "it appears", "it seems", "it is believed",
        "not necessarily", "not entirely", "not exactly",
        "subject to change", "depending on",
        "we continue to monitor", "remains to be seen",
        "appropriate", "measured", "prudent", "calibrated",
        "optionality", "flexibility", "data dependent",
    ]
    
    # Evasion patterns
    EVASION_PATTERNS = [
        "i can't comment on", "no comment",
        "not going to speculate", "hypothetical",
        "let me redirect", "the real question is",
        "as i said before", "i've already addressed",
        "that's outside my purview", "premature to say",
        "we'll cross that bridge", "time will tell",
    ]
    
    def __init__(self):
        """Initialize OmissionDetector."""
        print("[OMISSION] Detector initialized")
    
    def analyze(self, text: str, event_type: str = None, 
                source: str = None) -> OmissionReport:
        """
        Analyze text for omissions.
        
        Args:
            text: Text to analyze
            event_type: Expected event type for context
            source: Source of the text
            
        Returns:
            OmissionReport with detected omissions
        """
        report = OmissionReport()
        
        # Detect event type if not provided
        if not event_type:
            event_type = self._detect_event_type(text)
        
        # Check topic-specific omissions
        topic_omissions = self._check_topic_omissions(text, event_type)
        report.omissions.extend(topic_omissions)
        
        # Check for hedging language
        hedging_omissions, hedging_score = self._analyze_hedging(text)
        report.omissions.extend(hedging_omissions)
        report.hedging_score = hedging_score
        
        # Check for evasion
        evasion_omissions = self._detect_evasion(text)
        report.omissions.extend(evasion_omissions)
        
        # Check specificity
        report.specificity_score = self._measure_specificity(text)
        if report.specificity_score < 0.3:
            report.omissions.append(Omission(
                category="specificity",
                expected="Specific data points and numbers",
                significance=0.6,
                explanation="Statement lacks specific, verifiable claims",
                manipulation_risk=0.4,
            ))
        
        # Check for timeline omissions
        timeline_omissions = self._check_timeline_omissions(text, event_type)
        report.omissions.extend(timeline_omissions)
        
        # Check for comparison omissions
        comparison_omissions = self._check_comparison_omissions(text)
        report.omissions.extend(comparison_omissions)
        
        # Compute scores
        report.total_omissions = len(report.omissions)
        report.critical_omissions = sum(
            1 for o in report.omissions if o.significance > 0.7
        )
        
        if report.omissions:
            report.overall_omission_score = (
                sum(o.significance for o in report.omissions) / 
                max(1, len(report.omissions))
            )
        
        return report
    
    def _detect_event_type(self, text: str) -> str:
        """Auto-detect event type from text."""
        text_lower = text.lower()
        
        type_keywords = {
            "rate_decision": ["rate", "basis point", "fomc", "monetary policy", "interest rate"],
            "inflation": ["inflation", "cpi", "consumer prices", "price index"],
            "gdp": ["gdp", "gross domestic product", "economic growth", "output"],
            "earnings": ["earnings", "revenue", "profit", "quarterly results", "eps"],
            "employment": ["jobs", "employment", "unemployment", "nonfarm", "payroll"],
            "banking": ["bank", "capital", "lending", "deposits", "credit"],
            "geopolitical": ["war", "conflict", "sanctions", "military", "diplomatic"],
        }
        
        best = "rate_decision"
        best_score = 0
        for event_type, keywords in type_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best = event_type
        
        return best
    
    def _check_topic_omissions(self, text: str, event_type: str) -> List[Omission]:
        """Check for missing expected topics."""
        omissions = []
        expectations = self.TOPIC_EXPECTATIONS.get(event_type, {})
        text_lower = text.lower()
        
        # Required topics (high significance if missing)
        for topic in expectations.get("required", []):
            if topic.lower() not in text_lower:
                # Check for synonyms
                if not self._has_synonym(text_lower, topic):
                    omissions.append(Omission(
                        category="required_topic",
                        expected=topic,
                        significance=0.85,
                        explanation=f"'{topic}' is a required topic for {event_type} but was not mentioned",
                        manipulation_risk=0.6,
                    ))
        
        # Expected topics (medium significance)
        for topic in expectations.get("expected", []):
            if topic.lower() not in text_lower:
                if not self._has_synonym(text_lower, topic):
                    omissions.append(Omission(
                        category="expected_topic",
                        expected=topic,
                        significance=0.5,
                        explanation=f"'{topic}' is typically discussed in {event_type} contexts but absent",
                        manipulation_risk=0.3,
                    ))
        
        return omissions
    
    def _has_synonym(self, text: str, topic: str) -> bool:
        """Check if a topic's synonym exists in text."""
        synonyms = {
            "inflation": ["prices", "cpi", "pce"],
            "employment": ["jobs", "labor", "workforce"],
            "growth": ["expansion", "gdp", "output"],
            "forward guidance": ["outlook", "projection", "forecast", "path forward"],
            "risks": ["uncertainties", "headwinds", "challenges", "downside"],
            "wage growth": ["compensation", "earnings growth", "pay"],
            "balance sheet": ["quantitative", "qt", "qe", "asset purchases"],
            "dissent": ["disagreement", "minority view", "voted against"],
        }
        
        topic_synonyms = synonyms.get(topic.lower(), [])
        return any(syn in text for syn in topic_synonyms)
    
    def _analyze_hedging(self, text: str) -> tuple:
        """Analyze hedging language usage."""
        text_lower = text.lower()
        words = text_lower.split()
        total_words = len(words)
        
        hedge_count = 0
        hedging_omissions = []
        
        for pattern in self.HEDGING_PATTERNS:
            if pattern in text_lower:
                hedge_count += text_lower.count(pattern)
        
        hedging_score = min(1.0, hedge_count / max(1, total_words) * 20)
        
        if hedging_score > 0.5:
            hedging_omissions.append(Omission(
                category="hedging",
                expected="Clear, committed statements",
                significance=0.6,
                explanation=f"Excessive hedging language ({hedge_count} instances). "
                           f"Speaker may be avoiding commitment to specific claims.",
                manipulation_risk=0.5,
            ))
        
        return hedging_omissions, round(hedging_score, 3)
    
    def _detect_evasion(self, text: str) -> List[Omission]:
        """Detect explicit evasion patterns."""
        omissions = []
        text_lower = text.lower()
        
        for pattern in self.EVASION_PATTERNS:
            if pattern in text_lower:
                omissions.append(Omission(
                    category="evasion",
                    expected="Direct answer to implied question",
                    significance=0.7,
                    explanation=f"Evasion detected: '{pattern}'. "
                               f"Speaker actively avoiding a topic.",
                    manipulation_risk=0.7,
                ))
        
        return omissions
    
    def _measure_specificity(self, text: str) -> float:
        """Measure how specific/vague the text is (0=vague, 1=specific)."""
        import re
        
        # Count numeric data points
        numbers = len(re.findall(r'\d+\.?\d*\s*%?', text))
        
        # Count specific entity mentions
        entities = len(re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+|[A-Z]{2,}', text))
        
        # Count dates/times
        dates = len(re.findall(r'\d{4}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|Q[1-4]', text))
        
        words = len(text.split())
        if words == 0:
            return 0.0
        
        specificity = min(1.0, (numbers * 3 + entities * 2 + dates * 2) / max(1, words) * 10)
        
        return round(specificity, 3)
    
    def _check_timeline_omissions(self, text: str, event_type: str) -> List[Omission]:
        """Check if temporal context is missing."""
        import re
        omissions = []
        
        # Check for time references
        has_time = bool(re.search(
            r'\d{4}|Q[1-4]|next\s+(?:month|quarter|year)|'
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)',
            text
        ))
        
        if not has_time and event_type in ("rate_decision", "gdp", "inflation", "earnings"):
            omissions.append(Omission(
                category="timeline",
                expected="Temporal context (dates, quarters, projections)",
                significance=0.5,
                explanation="No timeline or date references found. Statements without "
                           "temporal context can be used to mislead.",
                manipulation_risk=0.4,
            ))
        
        # Check for forward-looking omissions in policy statements
        forward_words = ["will", "expect", "plan", "forecast", "target", "project"]
        has_forward = any(w in text.lower() for w in forward_words)
        
        if event_type in ("rate_decision", "gdp") and not has_forward:
            omissions.append(Omission(
                category="forward_guidance",
                expected="Forward-looking statements or projections",
                significance=0.6,
                explanation="No forward guidance provided. Policy makers typically "
                           "signal future intentions.",
                manipulation_risk=0.5,
            ))
        
        return omissions
    
    def _check_comparison_omissions(self, text: str) -> List[Omission]:
        """Check if comparison context is missing."""
        omissions = []
        import re
        
        # If numbers are present but no comparison context
        has_numbers = bool(re.search(r'\d+\.?\d*\s*%', text))
        comparison_words = ["compared to", "versus", "vs", "from", "changed",
                          "increased from", "decreased from", "previous",
                          "year-over-year", "month-over-month", "yoy", "mom"]
        
        has_comparison = any(w in text.lower() for w in comparison_words)
        
        if has_numbers and not has_comparison:
            omissions.append(Omission(
                category="comparison",
                expected="Comparison context (vs previous, vs expectations)",
                significance=0.5,
                explanation="Numbers presented without comparison baseline. "
                           "Without context, numbers can be misleading.",
                manipulation_risk=0.4,
            ))
        
        return omissions
