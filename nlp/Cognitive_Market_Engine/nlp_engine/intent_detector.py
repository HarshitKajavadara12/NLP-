"""
INTENT DETECTOR — Uncover the PURPOSE behind news

Goes beyond "what happened" to answer "WHY was this published?"

Detects:
- Communication intent (inform, warn, reassure, deflect)
- Strategic intent (trial balloon, market manipulation, narrative control)
- Timing intent (why now? pre-emptive? reactive?)
- Audience targeting (retail investors, institutions, regulators, public)
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CommunicationIntent(str, Enum):
    """Primary communication purpose."""
    INFORM = "inform"
    WARN = "warn"
    REASSURE = "reassure"
    DEFLECT = "deflect"
    PERSUADE = "persuade"
    CONFUSE = "confuse"
    DISTRACT = "distract"


class StrategicIntent(str, Enum):
    """Strategic purpose behind publication."""
    TRIAL_BALLOON = "trial_balloon"       # Testing public reaction
    NARRATIVE_CONTROL = "narrative_control" # Shaping the story
    MARKET_MANIPULATION = "market_manipulation"  # Moving prices
    POLITICAL_LEVERAGE = "political_leverage"   # Gaining political advantage
    REGULATORY_SIGNAL = "regulatory_signal"     # Signaling future regulation
    LEAK_STRATEGIC = "leak_strategic"            # Intentional leak
    LEAK_WHISTLEBLOWER = "leak_whistleblower"   # Unauthorized disclosure
    ROUTINE = "routine"                          # Standard reporting


class TargetAudience(str, Enum):
    """Intended audience."""
    GENERAL_PUBLIC = "general_public"
    INSTITUTIONAL_INVESTORS = "institutional_investors"
    RETAIL_INVESTORS = "retail_investors"
    REGULATORS = "regulators"
    POLICYMAKERS = "policymakers"
    INDUSTRY_INSIDERS = "industry_insiders"
    FOREIGN_GOVERNMENTS = "foreign_governments"


class TimingIntent(str, Enum):
    """Why was this published NOW?"""
    BREAKING = "breaking"              # Just happened
    PRE_EMPTIVE = "pre_emptive"        # Before something expected
    REACTIVE = "reactive"              # In response to events
    FRIDAY_DUMP = "friday_dump"        # Bad news on Friday
    MARKET_HOURS = "market_hours"      # During trading
    AFTER_HOURS = "after_hours"        # After market close
    WEEKEND = "weekend"                # Weekend release
    HOLIDAY = "holiday"                # Holiday timing
    DISTRACTION = "distraction"        # During other major events


@dataclass
class IntentAnalysis:
    """Complete intent analysis of a news article."""
    # Primary intents
    communication_intent: CommunicationIntent = CommunicationIntent.INFORM
    communication_confidence: float = 0.0
    
    strategic_intent: StrategicIntent = StrategicIntent.ROUTINE
    strategic_confidence: float = 0.0
    
    target_audiences: List[Tuple[TargetAudience, float]] = field(default_factory=list)
    
    timing_intent: TimingIntent = TimingIntent.BREAKING
    timing_confidence: float = 0.0
    
    # Manipulation indicators
    manipulation_score: float = 0.0  # 0=genuine, 1=highly manipulative
    manipulation_signals: List[str] = field(default_factory=list)
    
    # Credibility assessment
    source_credibility: float = 0.5
    claim_verifiability: float = 0.5
    
    # Hidden agenda indicators
    hidden_agenda_score: float = 0.0
    hidden_agenda_signals: List[str] = field(default_factory=list)
    
    # Who benefits
    likely_beneficiaries: List[str] = field(default_factory=list)
    likely_harmed: List[str] = field(default_factory=list)
    
    # Reasoning
    reasoning: str = ""


class IntentDetector:
    """
    Detects the underlying intent and purpose behind news publication.
    
    This is the "WHY" detector — the layer that finds hidden truths.
    """
    
    # Source credibility tiers
    SOURCE_CREDIBILITY = {
        # Tier 1: Primary sources
        "reuters": 0.95, "bloomberg": 0.95, "associated press": 0.95,
        "federal reserve": 0.99, "ecb": 0.99, "sec": 0.95,
        
        # Tier 2: Major outlets
        "wsj": 0.90, "ft": 0.90, "nyt": 0.85, "cnbc": 0.80,
        "bbc": 0.88, "economist": 0.90,
        
        # Tier 3: Analysis/opinion
        "seeking alpha": 0.60, "zerohedge": 0.45, "motley fool": 0.55,
        
        # Tier 4: Social/unverified
        "twitter": 0.35, "reddit": 0.30, "telegram": 0.25,
        "blog": 0.40, "unknown": 0.30,
    }
    
    # Manipulation signal patterns
    MANIPULATION_PATTERNS = {
        "urgency_pressure": [
            r"\b(act now|don't miss|last chance|limited time|urgent)\b",
            r"\b(once in a lifetime|never before|historic opportunity)\b",
        ],
        "false_authority": [
            r"\b(experts say|insiders reveal|sources confirm)\b",
            r"\b(everyone knows|it's obvious|clearly|undeniably)\b",
        ],
        "emotional_manipulation": [
            r"\b(shocking|devastating|terrifying|incredible|unbelievable)\b",
            r"\b(panic|fear|greed|euphoria|mania)\b",
        ],
        "selective_framing": [
            r"\b(despite|while ignoring|overlooking|failing to mention)\b",
            r"\b(cherry-picked|misleading|out of context)\b",
        ],
        "anonymous_sourcing": [
            r"\b(anonymous sources|people familiar|sources say|reportedly)\b",
            r"\b(unnamed officials|people close to|whispers|rumor)\b",
        ],
    }
    
    # Beneficiary detection patterns
    BENEFICIARY_PATTERNS = {
        "rate_hike": {
            "beneficiaries": ["banks", "savers", "USD holders"],
            "harmed": ["borrowers", "growth stocks", "emerging markets"],
        },
        "rate_cut": {
            "beneficiaries": ["borrowers", "growth stocks", "real estate"],
            "harmed": ["savers", "banks (margins)", "USD holders"],
        },
        "sanctions": {
            "beneficiaries": ["sanctioning country allies", "alternative suppliers"],
            "harmed": ["sanctioned country", "dependent trading partners"],
        },
        "deregulation": {
            "beneficiaries": ["regulated industry", "industry investors"],
            "harmed": ["consumers", "competitors", "environment"],
        },
        "tariff_increase": {
            "beneficiaries": ["domestic producers", "protectionist politicians"],
            "harmed": ["importers", "consumers", "exporting countries"],
        },
        "stimulus": {
            "beneficiaries": ["asset holders", "banks", "construction"],
            "harmed": ["future taxpayers", "inflation-sensitive"],
        },
        "crypto_regulation": {
            "beneficiaries": ["traditional finance", "compliant exchanges"],
            "harmed": ["DeFi protocols", "privacy coins", "unregulated exchanges"],
        },
    }
    
    def __init__(self):
        """Initialize the intent detector."""
        pass
    
    def analyze(self, text: str, source: str = "",
                publish_time: datetime = None,
                market_hours: bool = True) -> IntentAnalysis:
        """
        Perform complete intent analysis on news text.
        
        Args:
            text: Raw news text
            source: News source/publisher
            publish_time: When the news was published
            market_hours: Whether published during market hours
        """
        analysis = IntentAnalysis()
        text_lower = text.lower()
        
        # 1. Communication intent
        self._detect_communication_intent(text_lower, analysis)
        
        # 2. Strategic intent
        self._detect_strategic_intent(text_lower, source, analysis)
        
        # 3. Target audience
        self._detect_target_audience(text_lower, source, analysis)
        
        # 4. Timing intent
        self._detect_timing_intent(text_lower, publish_time, market_hours, analysis)
        
        # 5. Manipulation detection
        self._detect_manipulation(text, text_lower, analysis)
        
        # 6. Source credibility
        self._assess_credibility(text_lower, source, analysis)
        
        # 7. Beneficiary analysis
        self._detect_beneficiaries(text_lower, analysis)
        
        # 8. Hidden agenda
        self._detect_hidden_agenda(text_lower, source, analysis)
        
        # 9. Generate reasoning
        analysis.reasoning = self._generate_reasoning(analysis)
        
        return analysis
    
    def _detect_communication_intent(self, text: str, analysis: IntentAnalysis):
        """Detect the communication purpose."""
        intent_scores = {}
        
        intent_keywords = {
            CommunicationIntent.WARN: [
                "warn", "caution", "risk", "danger", "threat", "concern",
                "vulnerable", "alarming", "worrisome", "deteriorat"
            ],
            CommunicationIntent.REASSURE: [
                "stable", "confident", "resilient", "strong", "recovery",
                "improving", "optimistic", "robust", "healthy", "solid"
            ],
            CommunicationIntent.DEFLECT: [
                "external factors", "beyond control", "inherited",
                "previously", "blame", "attributed to", "not responsible"
            ],
            CommunicationIntent.PERSUADE: [
                "must", "should", "need to", "imperative", "essential",
                "critical", "vital", "necessary", "recommend"
            ],
            CommunicationIntent.CONFUSE: [
                "complex", "nuanced", "multifaceted", "on one hand",
                "however", "but also", "simultaneously", "paradoxically"
            ],
        }
        
        for intent, keywords in intent_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            intent_scores[intent] = score / len(keywords)
        
        if intent_scores:
            best = max(intent_scores, key=intent_scores.get)
            if intent_scores[best] > 0.1:
                analysis.communication_intent = best
                analysis.communication_confidence = min(1.0, intent_scores[best] * 3)
    
    def _detect_strategic_intent(self, text: str, source: str, analysis: IntentAnalysis):
        """Detect strategic purpose."""
        source_lower = source.lower()
        
        # Trial balloon detection
        trial_balloon_signals = [
            "considering", "exploring options", "floating",
            "gauging", "sources say", "could potentially",
            "one option", "among the ideas"
        ]
        tb_score = sum(1 for s in trial_balloon_signals if s in text) / len(trial_balloon_signals)
        
        # Leak detection
        leak_signals = [
            "leaked", "obtained by", "confidential", "internal",
            "exclusive", "whistleblower", "not authorized"
        ]
        leak_score = sum(1 for s in leak_signals if s in text) / len(leak_signals)
        
        # Narrative control
        nc_signals = [
            "our position is", "we want to make clear", "contrary to reports",
            "the truth is", "let me be clear", "official statement"
        ]
        nc_score = sum(1 for s in nc_signals if s in text) / len(nc_signals)
        
        scores = {
            StrategicIntent.TRIAL_BALLOON: tb_score,
            StrategicIntent.LEAK_STRATEGIC: leak_score,
            StrategicIntent.NARRATIVE_CONTROL: nc_score,
        }
        
        best = max(scores, key=scores.get)
        if scores[best] > 0.1:
            analysis.strategic_intent = best
            analysis.strategic_confidence = min(1.0, scores[best] * 5)
        else:
            analysis.strategic_intent = StrategicIntent.ROUTINE
            analysis.strategic_confidence = 0.5
    
    def _detect_target_audience(self, text: str, source: str, analysis: IntentAnalysis):
        """Detect intended audience."""
        audiences = []
        source_lower = source.lower()
        
        # Retail markers
        retail_words = ["investors should", "your portfolio", "how to invest",
                       "what this means for you", "average investor"]
        retail_score = sum(1 for w in retail_words if w in text) / len(retail_words)
        if retail_score > 0 or source_lower in ("cnbc", "motley fool", "seeking alpha"):
            audiences.append((TargetAudience.RETAIL_INVESTORS, min(1.0, retail_score * 5 + 0.3)))
        
        # Institutional markers
        inst_words = ["institutional", "portfolio allocation", "risk-adjusted",
                     "basis points", "credit spread", "duration"]
        inst_score = sum(1 for w in inst_words if w in text) / len(inst_words)
        if inst_score > 0 or source_lower in ("bloomberg", "ft", "wsj"):
            audiences.append((TargetAudience.INSTITUTIONAL_INVESTORS, min(1.0, inst_score * 5 + 0.3)))
        
        # Policy maker markers
        policy_words = ["congress", "legislation", "bipartisan", "bill",
                       "regulation", "executive order", "policy framework"]
        policy_score = sum(1 for w in policy_words if w in text) / len(policy_words)
        if policy_score > 0:
            audiences.append((TargetAudience.POLICYMAKERS, min(1.0, policy_score * 5)))
        
        if not audiences:
            audiences.append((TargetAudience.GENERAL_PUBLIC, 0.5))
        
        analysis.target_audiences = sorted(audiences, key=lambda x: x[1], reverse=True)
    
    def _detect_timing_intent(self, text: str, publish_time: datetime,
                              market_hours: bool, analysis: IntentAnalysis):
        """Detect timing-related intent."""
        if publish_time:
            hour = publish_time.hour
            weekday = publish_time.weekday()
            
            if weekday == 4 and hour >= 17:  # Friday evening
                analysis.timing_intent = TimingIntent.FRIDAY_DUMP
                analysis.timing_confidence = 0.7
            elif weekday >= 5:  # Weekend
                analysis.timing_intent = TimingIntent.WEEKEND
                analysis.timing_confidence = 0.6
            elif not market_hours:
                analysis.timing_intent = TimingIntent.AFTER_HOURS
                analysis.timing_confidence = 0.5
            else:
                analysis.timing_intent = TimingIntent.MARKET_HOURS
                analysis.timing_confidence = 0.5
        
        # Breaking news detection
        if any(w in text for w in ["breaking", "just in", "developing"]):
            analysis.timing_intent = TimingIntent.BREAKING
            analysis.timing_confidence = 0.8
    
    def _detect_manipulation(self, text: str, text_lower: str, analysis: IntentAnalysis):
        """Detect potential manipulation signals."""
        total_signals = 0
        signals = []
        
        for category, patterns in self.MANIPULATION_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    total_signals += len(matches)
                    signals.append(f"{category}: {', '.join(matches[:3])}")
        
        analysis.manipulation_score = min(1.0, total_signals / 10)
        analysis.manipulation_signals = signals
    
    def _assess_credibility(self, text: str, source: str, analysis: IntentAnalysis):
        """Assess source and claim credibility."""
        source_lower = source.lower()
        
        # Source credibility
        analysis.source_credibility = self.SOURCE_CREDIBILITY.get(source_lower, 0.5)
        
        # Claim verifiability
        verifiable_markers = ["data shows", "according to", "report finds",
                            "statistics indicate", "survey results", "published"]
        unverifiable_markers = ["sources say", "reportedly", "rumored",
                              "believed to", "speculation", "could be"]
        
        v_score = sum(1 for m in verifiable_markers if m in text)
        u_score = sum(1 for m in unverifiable_markers if m in text)
        analysis.claim_verifiability = min(1.0, max(0.0, 0.5 + v_score * 0.1 - u_score * 0.1))
    
    def _detect_beneficiaries(self, text: str, analysis: IntentAnalysis):
        """Detect who benefits and who is harmed by this news."""
        for topic, bh in self.BENEFICIARY_PATTERNS.items():
            topic_words = topic.replace("_", " ").split()
            if any(w in text for w in topic_words):
                analysis.likely_beneficiaries.extend(bh["beneficiaries"])
                analysis.likely_harmed.extend(bh["harmed"])
        
        # Deduplicate
        analysis.likely_beneficiaries = list(set(analysis.likely_beneficiaries))
        analysis.likely_harmed = list(set(analysis.likely_harmed))
    
    def _detect_hidden_agenda(self, text: str, source: str, analysis: IntentAnalysis):
        """Detect potential hidden agendas."""
        signals = []
        score = 0.0
        
        # High manipulation + anonymous sources
        if analysis.manipulation_score > 0.3:
            signals.append("High manipulation indicators detected")
            score += 0.2
        
        # Low credibility source with strong claims
        if analysis.source_credibility < 0.5 and analysis.communication_confidence > 0.5:
            signals.append("Low credibility source making strong claims")
            score += 0.2
        
        # Strategic leak detection
        if analysis.strategic_intent in (StrategicIntent.LEAK_STRATEGIC, StrategicIntent.TRIAL_BALLOON):
            signals.append(f"Detected {analysis.strategic_intent.value} pattern")
            score += 0.2
        
        # Timing suspicious
        if analysis.timing_intent in (TimingIntent.FRIDAY_DUMP, TimingIntent.DISTRACTION):
            signals.append("Suspicious timing detected")
            score += 0.15
        
        # Unverifiable claims
        if analysis.claim_verifiability < 0.3:
            signals.append("Claims are largely unverifiable")
            score += 0.15
        
        analysis.hidden_agenda_score = min(1.0, score)
        analysis.hidden_agenda_signals = signals
    
    def _generate_reasoning(self, analysis: IntentAnalysis) -> str:
        """Generate human-readable reasoning about detected intent."""
        parts = []
        
        parts.append(f"Communication intent: {analysis.communication_intent.value} "
                     f"(confidence: {analysis.communication_confidence:.0%})")
        parts.append(f"Strategic intent: {analysis.strategic_intent.value} "
                     f"(confidence: {analysis.strategic_confidence:.0%})")
        
        if analysis.target_audiences:
            audiences = ", ".join(f"{a.value}" for a, _ in analysis.target_audiences[:3])
            parts.append(f"Target audience: {audiences}")
        
        if analysis.manipulation_score > 0.3:
            parts.append(f"WARNING: Manipulation score {analysis.manipulation_score:.0%}")
        
        if analysis.hidden_agenda_signals:
            parts.append(f"Hidden agenda signals: {'; '.join(analysis.hidden_agenda_signals)}")
        
        if analysis.likely_beneficiaries:
            parts.append(f"Beneficiaries: {', '.join(analysis.likely_beneficiaries[:5])}")
        
        return " | ".join(parts)
