"""
Advanced Hidden Truth Detection — Categories 4.1, 4.3, 4.4, 4.5, 4.6
=====================================================================
4.1  ML-Based Pattern Recognition — learn manipulation patterns from
     labeled data (pump-and-dump, wash trading, spoofing signatures)
4.3  SEC Filing Analysis — EDGAR integration, 10-K/10-Q/8-K parsing,
     risk factor comparison across filings
4.4  Insider Trading Correlation — cross-reference Form 4 insider
     transactions with sentiment events
4.5  Source Network Analysis — graph of sources, echo chamber detection,
     independence scoring
4.6  Regulatory Filing vs PR Comparison — detect divergence between
     what companies tell the SEC vs what they tell the press
"""
import re
import math
import time
import json
import logging
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta

logger = logging.getLogger("cme.hidden_truth.advanced")

# ---------------------------------------------------------------------------
#  4.1  ML-Based Pattern Recognition for Market Manipulation
# ---------------------------------------------------------------------------

@dataclass
class ManipulationSignal:
    pattern_type: str       # pump_and_dump, wash_trading, spoofing, layering
    confidence: float       # 0-1 from model
    features: Dict[str, float]
    evidence: List[str]
    timestamp: float = field(default_factory=time.time)
    asset: str = ""


class ManipulationPatternDetector:
    """
    ML-inspired detection of market manipulation patterns.
    Uses feature engineering + scoring (can be swapped with sklearn/xgboost later).

    Detectable patterns:
    - Pump-and-dump: sudden volume spike + social media surge + price reversal
    - Wash trading: correlated buy/sell at same price, circular order flow
    - Spoofing: large order placed + cancelled before execution
    - Layering: multiple orders at different levels, all cancelled
    - Front-running: suspicious order flow preceding large block trades
    """

    PATTERN_FEATURES = {
        "pump_and_dump": [
            "volume_spike_ratio",          # current vs 30-day avg volume
            "social_media_mention_spike",   # abnormal mention count
            "price_reversal_magnitude",     # % drop after spike
            "small_cap_flag",              # manipulation more likely in small caps
            "coordinated_posting_score",   # similar posts from multiple accounts
            "time_to_reversal_hours",      # faster = more likely manipulation
        ],
        "wash_trading": [
            "self_trade_ratio",            # fraction of trades with same counterparty
            "price_clustering",            # trades at identical prices
            "volume_without_price_impact", # high volume but no price movement
            "time_regularity_score",       # suspiciously regular trade timing
            "order_size_uniformity",       # same size orders
        ],
        "spoofing": [
            "cancel_rate",                 # order cancel / place ratio
            "time_to_cancel_ms",           # average time before cancellation
            "price_move_after_cancel",     # market moved after spoof
            "order_size_vs_typical",       # abnormally large orders
            "repeated_pattern_count",      # same behavior repeated
        ],
        "front_running": [
            "pre_block_activity_score",    # activity before large block
            "information_asymmetry_score", # trades anticipate non-public info
            "insider_proximity_score",     # trader connected to insiders
            "timing_precision_score",      # suspiciously well-timed
        ],
    }

    # Learned thresholds (would be trained from labeled data in production)
    THRESHOLDS = {
        "pump_and_dump": {
            "volume_spike_ratio": 3.0,
            "social_media_mention_spike": 5.0,
            "price_reversal_magnitude": 0.10,
            "small_cap_flag": 0.5,
            "coordinated_posting_score": 0.6,
            "time_to_reversal_hours": 48,
        },
        "wash_trading": {
            "self_trade_ratio": 0.3,
            "price_clustering": 0.7,
            "volume_without_price_impact": 0.6,
            "time_regularity_score": 0.8,
            "order_size_uniformity": 0.7,
        },
        "spoofing": {
            "cancel_rate": 0.9,
            "time_to_cancel_ms": 500,
            "price_move_after_cancel": 0.01,
            "order_size_vs_typical": 5.0,
            "repeated_pattern_count": 3,
        },
        "front_running": {
            "pre_block_activity_score": 0.7,
            "information_asymmetry_score": 0.6,
            "insider_proximity_score": 0.5,
            "timing_precision_score": 0.8,
        },
    }

    # Feature weights (logistic-regression-like)
    WEIGHTS = {
        "pump_and_dump": {
            "volume_spike_ratio": 0.20,
            "social_media_mention_spike": 0.25,
            "price_reversal_magnitude": 0.25,
            "small_cap_flag": 0.10,
            "coordinated_posting_score": 0.15,
            "time_to_reversal_hours": 0.05,
        },
        "wash_trading": {
            "self_trade_ratio": 0.30,
            "price_clustering": 0.20,
            "volume_without_price_impact": 0.25,
            "time_regularity_score": 0.10,
            "order_size_uniformity": 0.15,
        },
        "spoofing": {
            "cancel_rate": 0.30,
            "time_to_cancel_ms": 0.15,
            "price_move_after_cancel": 0.20,
            "order_size_vs_typical": 0.20,
            "repeated_pattern_count": 0.15,
        },
        "front_running": {
            "pre_block_activity_score": 0.30,
            "information_asymmetry_score": 0.25,
            "insider_proximity_score": 0.20,
            "timing_precision_score": 0.25,
        },
    }

    def __init__(self):
        self._history: List[ManipulationSignal] = []

    def detect(self, asset: str, features: Dict[str, float]) -> List[ManipulationSignal]:
        """
        Given market features for an asset, detect manipulation patterns.
        
        features: dict with keys matching PATTERN_FEATURES values
        """
        signals = []

        for pattern_type, feature_names in self.PATTERN_FEATURES.items():
            # Extract relevant features
            pattern_features = {}
            activated_features = []
            weighted_score = 0.0

            weights = self.WEIGHTS.get(pattern_type, {})
            thresholds = self.THRESHOLDS.get(pattern_type, {})

            for feat_name in feature_names:
                value = features.get(feat_name, 0)
                pattern_features[feat_name] = value
                threshold = thresholds.get(feat_name, 0)
                weight = weights.get(feat_name, 0)

                if threshold > 0:
                    # Normalize: how far above threshold
                    if feat_name == "time_to_reversal_hours":
                        # Inverse: shorter = more suspicious
                        norm = max(0, 1 - value / threshold) if value > 0 else 0
                    elif feat_name == "time_to_cancel_ms":
                        norm = max(0, 1 - value / threshold) if value > 0 else 0
                    else:
                        norm = min(1.0, value / threshold) if threshold > 0 else 0

                    weighted_score += norm * weight
                    if norm > 0.5:
                        activated_features.append(f"{feat_name}={value:.3f} (>{threshold})")

            # Sigmoid-like confidence
            confidence = 1 / (1 + math.exp(-10 * (weighted_score - 0.5)))

            if confidence > 0.3 and len(activated_features) >= 2:
                signal = ManipulationSignal(
                    pattern_type=pattern_type,
                    confidence=round(confidence, 3),
                    features=pattern_features,
                    evidence=activated_features,
                    asset=asset,
                )
                signals.append(signal)
                self._history.append(signal)
                logger.warning(
                    f"Manipulation signal: {pattern_type} on {asset} "
                    f"(confidence={confidence:.2f})"
                )

        return signals

    def get_history(self, asset: Optional[str] = None,
                    min_confidence: float = 0.0) -> List[ManipulationSignal]:
        results = self._history
        if asset:
            results = [s for s in results if s.asset == asset]
        if min_confidence > 0:
            results = [s for s in results if s.confidence >= min_confidence]
        return results


# ---------------------------------------------------------------------------
#  4.3 + 4.6  SEC Filing Analysis + Regulatory vs PR Comparison
# ---------------------------------------------------------------------------

@dataclass
class FilingSection:
    section_name: str       # e.g. "Risk Factors", "MD&A", "Business"
    text: str
    word_count: int
    risk_keywords: List[str]
    sentiment_score: float
    new_language_pct: float  # % of text that's new vs prior filing


@dataclass
class FilingAnalysis:
    company: str
    filing_type: str        # 10-K, 10-Q, 8-K
    filing_date: str
    sections: List[FilingSection]
    risk_factor_changes: List[Dict[str, str]]
    new_risk_factors: List[str]
    removed_risk_factors: List[str]
    language_complexity_score: float  # Fog index
    overall_tone: float
    pr_vs_filing_divergence: float   # 4.6: how much PR differs from filing
    divergence_details: List[str]


RISK_KEYWORDS = [
    "material adverse", "significant risk", "may not", "cannot assure",
    "no guarantee", "subject to", "litigation", "investigation",
    "impairment", "going concern", "restatement", "covenant",
    "default", "cybersecurity", "data breach", "regulatory action",
    "class action", "write-off", "write-down", "goodwill impairment",
]


class SECFilingAnalyzer:
    """
    Parse and analyze SEC filings (10-K, 10-Q, 8-K).
    Compare successive filings for new/removed risk factors.
    Compare filing language with public PR statements (4.6).
    """

    SECTION_HEADERS = {
        "10-K": [
            "Business", "Risk Factors", "Properties",
            "Legal Proceedings", "Management's Discussion and Analysis",
            "Financial Statements", "Changes in and Disagreements",
        ],
        "10-Q": [
            "Financial Statements", "Management's Discussion and Analysis",
            "Risk Factors", "Controls and Procedures",
        ],
        "8-K": [
            "Entry into a Material Definitive Agreement",
            "Termination of a Material Definitive Agreement",
            "Bankruptcy or Receivership",
            "Changes in Registrant's Certifying Accountant",
            "Financial Statements and Exhibits",
            "Regulation FD Disclosure",
        ],
    }

    def __init__(self):
        self._filing_cache: Dict[str, Dict] = {}  # company -> latest filing data
        self._pr_cache: Dict[str, List[str]] = {}  # company -> recent PR statements

    def analyze_filing(self, text: str, company: str,
                       filing_type: str = "10-K",
                       filing_date: str = "",
                       prior_filing_text: Optional[str] = None,
                       pr_statements: Optional[List[str]] = None) -> FilingAnalysis:
        """Full analysis of an SEC filing."""
        # Parse sections
        sections = self._parse_sections(text, filing_type)

        # Risk factor changes
        risk_changes = []
        new_risks = []
        removed_risks = []

        if prior_filing_text:
            prior_sections = self._parse_sections(prior_filing_text, filing_type)
            new_risks, removed_risks, risk_changes = self._compare_risk_factors(
                prior_sections, sections
            )

        # Calculate new language percentage for each section
        if prior_filing_text:
            prior_text_set = set(prior_filing_text.lower().split())
            for section in sections:
                words = section.text.lower().split()
                if words:
                    new_words = [w for w in words if w not in prior_text_set]
                    section.new_language_pct = round(len(new_words) / len(words), 3)
                else:
                    section.new_language_pct = 0.0

        # Language complexity (Gunning Fog Index approximation)
        complexity = self._gunning_fog(text)

        # Overall tone
        overall_tone = self._calculate_tone(text)

        # PR vs Filing divergence (4.6)
        pr_divergence = 0.0
        divergence_details = []
        if pr_statements:
            pr_divergence, divergence_details = self._compare_pr_vs_filing(
                text, pr_statements
            )

        # Cache
        self._filing_cache[company] = {
            "text": text, "filing_type": filing_type, "date": filing_date,
        }
        if pr_statements:
            self._pr_cache[company] = pr_statements

        return FilingAnalysis(
            company=company,
            filing_type=filing_type,
            filing_date=filing_date,
            sections=sections,
            risk_factor_changes=risk_changes,
            new_risk_factors=new_risks,
            removed_risk_factors=removed_risks,
            language_complexity_score=round(complexity, 2),
            overall_tone=round(overall_tone, 3),
            pr_vs_filing_divergence=round(pr_divergence, 3),
            divergence_details=divergence_details,
        )

    def _parse_sections(self, text: str, filing_type: str) -> List[FilingSection]:
        """Split filing into labeled sections."""
        headers = self.SECTION_HEADERS.get(filing_type, [])
        sections = []

        for i, header in enumerate(headers):
            pattern = re.compile(re.escape(header), re.IGNORECASE)
            match = pattern.search(text)
            if match:
                start = match.end()
                # Find next section header
                end = len(text)
                for next_header in headers[i + 1:]:
                    next_match = re.compile(re.escape(next_header), re.IGNORECASE).search(
                        text, start
                    )
                    if next_match:
                        end = next_match.start()
                        break

                section_text = text[start:end].strip()[:5000]  # cap at 5K chars
                risk_kw = [kw for kw in RISK_KEYWORDS if kw.lower() in section_text.lower()]
                tone = self._calculate_tone(section_text)

                sections.append(FilingSection(
                    section_name=header,
                    text=section_text,
                    word_count=len(section_text.split()),
                    risk_keywords=risk_kw,
                    sentiment_score=round(tone, 3),
                    new_language_pct=0.0,
                ))

        return sections

    def _compare_risk_factors(self, prior: List[FilingSection],
                               current: List[FilingSection]) -> Tuple[List[str], List[str], List[Dict]]:
        """Compare risk factors between two filings."""
        prior_risks = []
        current_risks = []

        for s in prior:
            if "risk" in s.section_name.lower():
                prior_risks = [p.strip() for p in s.text.split("\n") if len(p.strip()) > 30]
        for s in current:
            if "risk" in s.section_name.lower():
                current_risks = [p.strip() for p in s.text.split("\n") if len(p.strip()) > 30]

        # Simple diff: use first 50 chars as fingerprint
        prior_fps = {r[:50].lower(): r for r in prior_risks}
        current_fps = {r[:50].lower(): r for r in current_risks}

        new_risks = [current_fps[fp] for fp in current_fps if fp not in prior_fps]
        removed_risks = [prior_fps[fp] for fp in prior_fps if fp not in current_fps]

        changes = []
        for fp in current_fps:
            if fp in prior_fps:
                old = prior_fps[fp]
                new = current_fps[fp]
                if old != new:
                    changes.append({
                        "type": "modified",
                        "prior_excerpt": old[:200],
                        "current_excerpt": new[:200],
                    })

        return (
            [r[:200] for r in new_risks[:10]],
            [r[:200] for r in removed_risks[:10]],
            changes[:10],
        )

    def _compare_pr_vs_filing(self, filing_text: str,
                               pr_statements: List[str]) -> Tuple[float, List[str]]:
        """
        Category 4.6: Compare regulatory filing language with PR language.
        Detect divergence (positive PR spin vs cautious filing language).
        """
        filing_tone = self._calculate_tone(filing_text)
        pr_tone = sum(self._calculate_tone(pr) for pr in pr_statements) / max(1, len(pr_statements))

        details = []
        divergence = abs(pr_tone - filing_tone)

        if pr_tone > filing_tone + 0.3:
            details.append(
                f"PR significantly more positive (PR={pr_tone:.2f}) than filing "
                f"(filing={filing_tone:.2f}). Company may be spinning negative "
                f"fundamentals for public consumption."
            )

        # Check for risks mentioned in filing but absent from PR
        filing_lower = filing_text.lower()
        for kw in RISK_KEYWORDS:
            if kw in filing_lower:
                pr_combined = " ".join(pr_statements).lower()
                if kw not in pr_combined:
                    details.append(
                        f"Risk '{kw}' disclosed in filing but absent from PR statements"
                    )

        # Check for forward-looking qualifier differences
        filing_qualifiers = len(re.findall(
            r'\b(may|might|could|uncertain|no assurance|cannot predict)\b',
            filing_text, re.IGNORECASE
        ))
        pr_qualifiers = sum(
            len(re.findall(
                r'\b(may|might|could|uncertain|no assurance|cannot predict)\b',
                pr, re.IGNORECASE
            )) for pr in pr_statements
        )

        filing_qual_density = filing_qualifiers / max(1, len(filing_text.split()) / 100)
        pr_qual_density = pr_qualifiers / max(1, sum(len(p.split()) for p in pr_statements) / 100)

        if filing_qual_density > pr_qual_density * 2:
            details.append(
                f"Filing uses {filing_qual_density:.1f}x more qualifiers per 100 words "
                f"than PR ({pr_qual_density:.1f}x). Regulatory caution vs PR confidence."
            )

        return divergence, details

    @staticmethod
    def _calculate_tone(text: str) -> float:
        words = text.lower().split()
        positive = {"strong", "growth", "improving", "record", "exceeded",
                     "robust", "momentum", "confident", "favorable", "resilient"}
        negative = {"decline", "risk", "adverse", "uncertain", "challenging",
                     "impairment", "loss", "weakness", "concern", "deteriorating"}
        pos = sum(1 for w in words if w in positive)
        neg = sum(1 for w in words if w in negative)
        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total

    @staticmethod
    def _gunning_fog(text: str) -> float:
        """Approximate Gunning Fog Index."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        if not sentences:
            return 0.0
        words = text.split()
        if not words:
            return 0.0

        avg_sentence_length = len(words) / len(sentences)
        complex_words = sum(1 for w in words if len(w) > 12)
        complex_ratio = complex_words / len(words)

        return 0.4 * (avg_sentence_length + 100 * complex_ratio)


# ---------------------------------------------------------------------------
#  4.4  Insider Trading Correlation
# ---------------------------------------------------------------------------

@dataclass
class InsiderTransaction:
    """Represents a Form 4 insider transaction."""
    insider_name: str
    title: str              # CEO, CFO, Director, VP, etc.
    transaction_type: str   # P (Purchase), S (Sale), A (Award), M (Exercise)
    shares: int
    price: float
    total_value: float
    date: str               # YYYY-MM-DD
    ownership_type: str     # D (Direct), I (Indirect)
    shares_after: int


@dataclass
class InsiderSentimentCorrelation:
    insider_name: str
    transaction_type: str
    transaction_date: str
    transaction_value: float
    correlated_events: List[Dict[str, str]]
    suspicion_score: float  # 0-1
    interpretation: str


class InsiderCorrelationAnalyzer:
    """
    Cross-reference Form 4 insider transactions with news sentiment
    and price events to detect suspicious patterns.

    Red flags:
    - Insider selling before negative news break
    - Insider buying before positive catalysts
    - Cluster of insiders all selling within short window
    - Insider transactions timed around earnings/announcements
    """

    def __init__(self, lookback_days: int = 30, lookahead_days: int = 14):
        self.lookback = lookback_days
        self.lookahead = lookahead_days
        self._transactions: Dict[str, List[InsiderTransaction]] = defaultdict(list)
        self._events: Dict[str, List[Dict]] = defaultdict(list)  # asset -> events

    def add_transaction(self, asset: str, tx: InsiderTransaction) -> None:
        self._transactions[asset].append(tx)

    def add_event(self, asset: str, event: Dict) -> None:
        """event: {date, type, sentiment, headline, magnitude}"""
        self._events[asset].append(event)

    def analyze(self, asset: str) -> List[InsiderSentimentCorrelation]:
        """Find suspicious correlations between insider trades and events."""
        results = []
        transactions = self._transactions.get(asset, [])
        events = self._events.get(asset, [])

        if not transactions or not events:
            return results

        for tx in transactions:
            try:
                tx_date = datetime.strptime(tx.date, "%Y-%m-%d")
            except ValueError:
                continue

            correlated = []
            suspicion = 0.0

            for evt in events:
                try:
                    evt_date = datetime.strptime(evt.get("date", ""), "%Y-%m-%d")
                except ValueError:
                    continue

                days_diff = (evt_date - tx_date).days

                # Look for events within lookahead window after transaction
                if 0 < days_diff <= self.lookahead:
                    evt_sentiment = evt.get("sentiment", 0)
                    evt_type = evt.get("type", "")

                    # Insider SOLD and negative news follows
                    if tx.transaction_type == "S" and evt_sentiment < -0.3:
                        suspicion += 0.4
                        correlated.append({
                            "event": evt.get("headline", ""),
                            "days_after_trade": days_diff,
                            "sentiment": evt_sentiment,
                            "flag": "sale_before_bad_news",
                        })

                    # Insider BOUGHT and positive news follows
                    elif tx.transaction_type == "P" and evt_sentiment > 0.3:
                        suspicion += 0.3
                        correlated.append({
                            "event": evt.get("headline", ""),
                            "days_after_trade": days_diff,
                            "sentiment": evt_sentiment,
                            "flag": "purchase_before_good_news",
                        })

                    # Insider transacted right before earnings
                    if evt_type in ("earnings", "guidance_update"):
                        suspicion += 0.2
                        correlated.append({
                            "event": evt.get("headline", ""),
                            "days_after_trade": days_diff,
                            "type": evt_type,
                            "flag": "transaction_before_earnings",
                        })

            # Cluster detection: multiple insiders selling in same window
            cluster_count = sum(
                1 for other_tx in transactions
                if other_tx.insider_name != tx.insider_name
                and other_tx.transaction_type == tx.transaction_type
                and abs(self._date_diff(tx.date, other_tx.date)) <= 5
            )
            if cluster_count >= 2 and tx.transaction_type == "S":
                suspicion += 0.3 * min(cluster_count, 3)
                correlated.append({
                    "flag": "insider_cluster",
                    "count": cluster_count + 1,
                    "note": f"{cluster_count + 1} insiders sold within 5 days",
                })

            # C-suite weight
            if tx.title.upper() in ("CEO", "CFO", "COO", "CTO"):
                suspicion *= 1.5

            # Large transactions
            if tx.total_value > 1_000_000:
                suspicion *= 1.3

            suspicion = min(1.0, suspicion)

            if correlated:
                interpretation = self._interpret(tx, correlated, suspicion)
                results.append(InsiderSentimentCorrelation(
                    insider_name=tx.insider_name,
                    transaction_type=tx.transaction_type,
                    transaction_date=tx.date,
                    transaction_value=tx.total_value,
                    correlated_events=correlated,
                    suspicion_score=round(suspicion, 3),
                    interpretation=interpretation,
                ))

        results.sort(key=lambda r: r.suspicion_score, reverse=True)
        return results

    def _interpret(self, tx: InsiderTransaction,
                   correlated: List[Dict], score: float) -> str:
        flags = [c.get("flag", "") for c in correlated]
        parts = []
        if "sale_before_bad_news" in flags:
            parts.append(
                f"{tx.insider_name} ({tx.title}) sold "
                f"${tx.total_value:,.0f} worth of shares before negative news."
            )
        if "purchase_before_good_news" in flags:
            parts.append(
                f"{tx.insider_name} ({tx.title}) purchased shares before positive catalyst."
            )
        if "insider_cluster" in flags:
            cluster_info = [c for c in correlated if c.get("flag") == "insider_cluster"]
            if cluster_info:
                parts.append(cluster_info[0].get("note", ""))
        if "transaction_before_earnings" in flags:
            parts.append("Transaction timed suspiciously close to earnings.")

        if score > 0.7:
            parts.append("HIGH SUSPICION — warrants investigation.")
        elif score > 0.4:
            parts.append("MODERATE SUSPICION — monitor closely.")

        return " ".join(parts) if parts else "Low concern."

    @staticmethod
    def _date_diff(date1: str, date2: str) -> int:
        try:
            d1 = datetime.strptime(date1, "%Y-%m-%d")
            d2 = datetime.strptime(date2, "%Y-%m-%d")
            return (d2 - d1).days
        except ValueError:
            return 999


# ---------------------------------------------------------------------------
#  4.5  Source Network Analysis
# ---------------------------------------------------------------------------

@dataclass
class SourceNode:
    source_id: str
    name: str
    type: str              # newswire, blog, social, analyst, company_pr, regulator
    credibility_score: float  # 0-1
    total_articles: int = 0
    accuracy_rate: float = 0.0
    avg_sentiment_bias: float = 0.0


@dataclass
class SourceEdge:
    source_a: str
    source_b: str
    co_coverage_count: int     # how often they cover same story
    timing_correlation: float  # do they publish at same time?
    sentiment_correlation: float  # do they have same sentiment?
    is_echo_chamber: bool


class SourceNetworkAnalyzer:
    """
    Build a graph of information sources and detect:
    - Echo chambers (sources that always agree / copy each other)
    - Independence scores (how original is each source)
    - Credibility rankings (based on prediction accuracy)
    - Coordinated information campaigns (simultaneous similar posts)
    """

    def __init__(self):
        self._sources: Dict[str, SourceNode] = {}
        self._edges: Dict[str, SourceEdge] = {}
        self._articles: List[Dict] = []

    def add_source(self, source: SourceNode) -> None:
        self._sources[source.source_id] = source

    def add_article(self, article: Dict) -> None:
        """
        article: {
            source_id, headline, published_at, sentiment, topics, asset, text
        }
        """
        self._articles.append(article)

    def build_network(self) -> Dict[str, any]:
        """Build source relationship graph from article co-coverage."""
        # Index articles by topic/asset
        topic_sources: Dict[str, List[Dict]] = defaultdict(list)

        for article in self._articles:
            asset = article.get("asset", "")
            topics = article.get("topics", [])
            for topic in topics + [asset]:
                if topic:
                    topic_sources[topic].append(article)

        # Build edges: find co-coverage
        pair_stats: Dict[str, Dict] = defaultdict(
            lambda: {"count": 0, "sentiment_pairs": [], "timing_pairs": []}
        )

        for topic, articles in topic_sources.items():
            if len(articles) < 2:
                continue
            # Compare pairs within topic
            for i, a in enumerate(articles):
                for b in articles[i + 1:]:
                    src_a = a.get("source_id", "")
                    src_b = b.get("source_id", "")
                    if src_a == src_b:
                        continue
                    pair_key = tuple(sorted([src_a, src_b]))
                    pair_str = f"{pair_key[0]}|{pair_key[1]}"

                    pair_stats[pair_str]["count"] += 1
                    pair_stats[pair_str]["sentiment_pairs"].append(
                        (a.get("sentiment", 0), b.get("sentiment", 0))
                    )

                    # Timing correlation
                    try:
                        t_a = a.get("published_at", 0)
                        t_b = b.get("published_at", 0)
                        if isinstance(t_a, (int, float)) and isinstance(t_b, (int, float)):
                            pair_stats[pair_str]["timing_pairs"].append(abs(t_a - t_b))
                    except (TypeError, ValueError):
                        pass

        # Create edges
        for pair_str, stats in pair_stats.items():
            parts = pair_str.split("|")
            if len(parts) != 2:
                continue
            src_a, src_b = parts

            # Sentiment correlation
            sent_pairs = stats["sentiment_pairs"]
            if sent_pairs:
                sent_corr = self._correlation(
                    [p[0] for p in sent_pairs],
                    [p[1] for p in sent_pairs]
                )
            else:
                sent_corr = 0.0

            # Timing correlation (fraction published within 1 hour)
            timing_pairs = stats["timing_pairs"]
            if timing_pairs:
                near_simultaneous = sum(1 for t in timing_pairs if t < 3600) / len(timing_pairs)
            else:
                near_simultaneous = 0.0

            # Echo chamber: high co-coverage + high sentiment correlation + near-simultaneous
            is_echo = (
                stats["count"] >= 5
                and sent_corr > 0.8
                and near_simultaneous > 0.6
            )

            edge = SourceEdge(
                source_a=src_a,
                source_b=src_b,
                co_coverage_count=stats["count"],
                timing_correlation=round(near_simultaneous, 3),
                sentiment_correlation=round(sent_corr, 3),
                is_echo_chamber=is_echo,
            )
            self._edges[pair_str] = edge

        # Update source credibility based on network position
        independence_scores = self._calculate_independence()

        return {
            "sources": len(self._sources),
            "edges": len(self._edges),
            "echo_chambers": self.get_echo_chambers(),
            "independence_scores": independence_scores,
        }

    def get_echo_chambers(self) -> List[Dict]:
        """Return detected echo chamber clusters."""
        chambers = []
        processed: Set[str] = set()

        for key, edge in self._edges.items():
            if not edge.is_echo_chamber:
                continue
            if key in processed:
                continue

            chamber = {
                "sources": [edge.source_a, edge.source_b],
                "co_coverage": edge.co_coverage_count,
                "sentiment_correlation": edge.sentiment_correlation,
                "timing_correlation": edge.timing_correlation,
            }
            chambers.append(chamber)
            processed.add(key)

        return chambers

    def _calculate_independence(self) -> Dict[str, float]:
        """Score each source's independence (low echo = high independence)."""
        scores = {}
        for sid in self._sources:
            echo_edges = 0
            total_edges = 0
            for key, edge in self._edges.items():
                if edge.source_a == sid or edge.source_b == sid:
                    total_edges += 1
                    if edge.is_echo_chamber:
                        echo_edges += 1

            if total_edges == 0:
                scores[sid] = 1.0  # No connections = fully independent
            else:
                scores[sid] = round(1 - echo_edges / total_edges, 3)

        return scores

    def get_credibility_ranking(self) -> List[Dict]:
        """Rank sources by credibility."""
        ranking = []
        for sid, source in self._sources.items():
            independence = self._calculate_independence().get(sid, 1.0)
            combined = (
                0.4 * source.credibility_score
                + 0.3 * source.accuracy_rate
                + 0.3 * independence
            )
            ranking.append({
                "source_id": sid,
                "name": source.name,
                "type": source.type,
                "credibility": round(source.credibility_score, 3),
                "accuracy": round(source.accuracy_rate, 3),
                "independence": independence,
                "combined_score": round(combined, 3),
            })
        ranking.sort(key=lambda x: x["combined_score"], reverse=True)
        return ranking

    @staticmethod
    def _correlation(x: List[float], y: List[float]) -> float:
        """Pearson correlation coefficient."""
        n = len(x)
        if n < 2:
            return 0.0
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        var_x = sum((xi - mean_x) ** 2 for xi in x)
        var_y = sum((yi - mean_y) ** 2 for yi in y)
        if var_x == 0 or var_y == 0:
            return 0.0
        cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        return cov / math.sqrt(var_x * var_y)
