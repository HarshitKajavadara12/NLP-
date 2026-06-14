"""
CROSS-SOURCE ANALYZER — Verify claims across multiple news sources

Detects:
- Stories reported by only one source (unverified)
- Conflicting claims between sources
- Coordinated narratives (suspiciously similar wording)
- Source reliability tracking
- Embedding-based semantic similarity (when NLP engine available)

Trust score = f(source_count, source_diversity, consistency)
"""

import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter

# Try to import NLP engine for embedding-based similarity
try:
    from nlp_engine.deep_nlp_parser import DeepNLPParser
    _NLP_AVAILABLE = True
except ImportError:
    _NLP_AVAILABLE = False


@dataclass
class SourceReport:
    """A single source's version of a story."""
    source: str = ""
    text: str = ""
    timestamp: str = ""
    key_claims: List[str] = field(default_factory=list)
    sentiment: float = 0.0  # -1 to 1
    entities_mentioned: List[str] = field(default_factory=list)
    numbers_mentioned: List[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Result of cross-source verification."""
    story_hash: str = ""
    source_count: int = 0
    source_diversity: float = 0.0  # 0-1 (how different are the sources)
    
    # Verification scores
    claim_consistency: float = 0.5
    narrative_alignment: float = 0.5
    cross_source_trust: float = 0.5
    
    # Flags
    single_source_only: bool = False
    conflicting_claims: List[Dict] = field(default_factory=list)
    coordinated_narrative: bool = False
    suspicious_timing: bool = False
    
    # Detail
    sources: List[str] = field(default_factory=list)
    common_claims: List[str] = field(default_factory=list)
    disputed_claims: List[str] = field(default_factory=list)
    missing_from_sources: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "story_hash": self.story_hash,
            "source_count": self.source_count,
            "source_diversity": round(self.source_diversity, 3),
            "claim_consistency": round(self.claim_consistency, 3),
            "narrative_alignment": round(self.narrative_alignment, 3),
            "cross_source_trust": round(self.cross_source_trust, 3),
            "single_source_only": self.single_source_only,
            "conflicting_claims": self.conflicting_claims,
            "coordinated_narrative": self.coordinated_narrative,
            "suspicious_timing": self.suspicious_timing,
            "sources": self.sources,
            "common_claims": self.common_claims,
            "disputed_claims": self.disputed_claims,
        }


class CrossSourceAnalyzer:
    """
    Analyzes the same story across multiple news sources to
    verify claims, detect conflicts, and build trust scores.
    """
    
    # Source categories for diversity measurement
    SOURCE_CATEGORIES = {
        "wire": {"reuters", "ap", "afp", "bloomberg"},
        "financial": {"wsj", "ft", "cnbc", "marketwatch", "barrons"},
        "mainstream": {"bbc", "cnn", "nytimes", "guardian", "wapo"},
        "official": {"fed", "ecb", "boe", "treasury", "imf", "worldbank"},
        "alternative": {"zerohedge", "seekingalpha", "reddit", "twitter"},
        "regional": {"scmp", "nikkei", "handelsblatt"},
    }
    
    # Source credibility priors (0-1)
    SOURCE_CREDIBILITY = {
        "reuters": 0.95, "bloomberg": 0.93, "ap": 0.94, "afp": 0.92,
        "wsj": 0.90, "ft": 0.91, "bbc": 0.88, "cnbc": 0.82,
        "fed": 0.99, "ecb": 0.98, "boe": 0.98, "imf": 0.95,
        "zerohedge": 0.40, "seekingalpha": 0.55, "reddit": 0.30,
    }
    
    def __init__(self):
        """Initialize cross-source analyzer."""
        self.story_buffer = defaultdict(list)  # story_hash -> [SourceReports]
        self.source_track_record = defaultdict(lambda: {"correct": 0, "total": 0})
        
        # Try to initialize NLP-based similarity
        self._nlp_parser = None
        if _NLP_AVAILABLE:
            try:
                self._nlp_parser = DeepNLPParser()
                print("[CROSS_SOURCE] Analyzer initialized with NLP-based similarity")
            except Exception:
                print("[CROSS_SOURCE] Analyzer initialized (NLP unavailable, using keyword fallback)")
        else:
            print("[CROSS_SOURCE] Analyzer initialized (keyword-based)")
    
    def add_report(self, source: str, text: str, timestamp: str = None,
                   entities: List[str] = None):
        """
        Add a source report for potential cross-referencing.
        
        Args:
            source: Source name (e.g., "reuters", "bloomberg")
            text: Full text of the report
            timestamp: Publication time
            entities: Pre-extracted entities
        """
        report = SourceReport(
            source=source.lower(),
            text=text,
            timestamp=timestamp or datetime.now().isoformat(),
            key_claims=self._extract_claims(text),
            sentiment=self._estimate_sentiment(text),
            entities_mentioned=entities or self._extract_simple_entities(text),
            numbers_mentioned=self._extract_numbers(text),
        )
        
        story_hash = self._compute_story_hash(report)
        self.story_buffer[story_hash].append(report)
    
    def verify(self, text: str = None, story_hash: str = None) -> VerificationResult:
        """
        Verify a story across available sources.
        
        Args:
            text: Story text to verify (will find matching reports)
            story_hash: Direct story hash if known
            
        Returns:
            VerificationResult with trust scores
        """
        if text:
            story_hash = self._compute_story_hash(
                SourceReport(text=text, key_claims=self._extract_claims(text))
            )
        
        reports = self.story_buffer.get(story_hash, [])
        
        result = VerificationResult(story_hash=story_hash or "")
        
        if not reports:
            result.single_source_only = True
            result.cross_source_trust = 0.3
            return result
        
        result.source_count = len(reports)
        result.sources = list(set(r.source for r in reports))
        result.single_source_only = (len(set(r.source for r in reports)) <= 1)
        
        # Source diversity
        result.source_diversity = self._compute_source_diversity(result.sources)
        
        # Claim consistency
        consistency, common, disputed = self._check_claim_consistency(reports)
        result.claim_consistency = consistency
        result.common_claims = common
        result.disputed_claims = disputed
        
        # Narrative alignment (are they telling the same story?)
        result.narrative_alignment = self._check_narrative_alignment(reports)
        
        # Coordinated narrative detection
        result.coordinated_narrative = self._detect_coordination(reports)
        
        # Suspicious timing
        result.suspicious_timing = self._check_timing(reports)
        
        # Conflicting claims
        result.conflicting_claims = self._find_conflicts(reports)
        
        # Compute overall trust
        result.cross_source_trust = self._compute_trust_score(result)
        
        return result
    
    def verify_batch(self, reports_list: List[Dict]) -> List[VerificationResult]:
        """
        Verify multiple stories at once.
        
        Args:
            reports_list: List of {source, text, timestamp} dicts
        """
        # Add all reports
        for r in reports_list:
            self.add_report(
                source=r.get("source", "unknown"),
                text=r.get("text", ""),
                timestamp=r.get("timestamp"),
                entities=r.get("entities"),
            )
        
        # Verify each unique story
        results = []
        verified_hashes = set()
        
        for story_hash in self.story_buffer:
            if story_hash not in verified_hashes:
                result = self.verify(story_hash=story_hash)
                results.append(result)
                verified_hashes.add(story_hash)
        
        return results
    
    def _compute_story_hash(self, report: SourceReport) -> str:
        """Compute hash to group reports about the same story."""
        # Use key claims and entities for matching, not exact text
        key_elements = sorted(report.key_claims[:5] + report.entities_mentioned[:5])
        hash_input = " ".join(key_elements).lower().strip()
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract key factual claims from text."""
        claims = []
        sentences = text.replace(".", ".\n").split("\n")
        
        claim_indicators = [
            "said", "announced", "stated", "reported", "confirmed",
            "decided", "raised", "cut", "increased", "decreased",
            "expects", "forecasts", "predicts", "warns", "revealed",
            "will", "plan to", "agreed", "rejected", "approved",
        ]
        
        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 10:
                continue
            
            for indicator in claim_indicators:
                if indicator in sent.lower():
                    # Normalize the claim
                    claim = sent.strip().lower()
                    # Remove common filler words for comparison
                    for filler in ["the", "a", "an", "and", "or", "but", "in", "on", "at"]:
                        claim = claim.replace(f" {filler} ", " ")
                    claims.append(claim[:200])
                    break
        
        return claims[:10]
    
    def _extract_simple_entities(self, text: str) -> List[str]:
        """Quick entity extraction without NLP models."""
        entities = []
        
        known_entities = {
            "fed", "federal reserve", "ecb", "boj", "boe", "pboc",
            "s&p 500", "nasdaq", "dow", "ftse", "dax", "nikkei",
            "usd", "eur", "jpy", "gbp", "cny",
            "gold", "oil", "wti", "brent", "copper", "bitcoin",
            "powell", "lagarde", "yellen", "trump", "biden",
            "gdp", "cpi", "inflation", "unemployment", "nonfarm",
        }
        
        text_lower = text.lower()
        for entity in known_entities:
            if entity in text_lower:
                entities.append(entity)
        
        return entities
    
    def _extract_numbers(self, text: str) -> List[str]:
        """Extract numeric values (key for fact-checking)."""
        import re
        pattern = r'[-+]?\d+\.?\d*\s*%?'
        matches = re.findall(pattern, text)
        return [m.strip() for m in matches[:10]]
    
    def _estimate_sentiment(self, text: str) -> float:
        """Quick sentiment estimate (-1 to 1). Uses expanded financial lexicon."""
        positive = [
            "rally", "gain", "surge", "rise", "strong", "boost", "beat", "growth",
            "soar", "jump", "upgrade", "bullish", "outperform", "recovery", "expansion",
            "accelerate", "exceed", "upside", "optimism", "robust"
        ]
        negative = [
            "crash", "plunge", "fall", "decline", "weak", "miss", "fear", "crisis",
            "slump", "drop", "downgrade", "bearish", "underperform", "contraction",
            "decelerate", "disappoint", "downside", "pessimism", "fragile", "default"
        ]
        
        text_lower = text.lower()
        pos_count = sum(1 for w in positive if w in text_lower)
        neg_count = sum(1 for w in negative if w in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        return (pos_count - neg_count) / total
    
    def _compute_source_diversity(self, sources: List[str]) -> float:
        """Measure how diverse the sources are (0-1)."""
        if len(sources) <= 1:
            return 0.0
        
        categories_represented = set()
        for source in sources:
            for category, members in self.SOURCE_CATEGORIES.items():
                if source in members:
                    categories_represented.add(category)
                    break
            else:
                categories_represented.add(f"unknown_{source}")
        
        max_categories = min(len(sources), len(self.SOURCE_CATEGORIES))
        return min(1.0, len(categories_represented) / max(1, max_categories))
    
    def _check_claim_consistency(self, reports: List[SourceReport]) -> Tuple[float, List, List]:
        """Check if sources make consistent claims."""
        all_claims = defaultdict(int)
        source_claims = defaultdict(set)
        
        for report in reports:
            for claim in report.key_claims:
                all_claims[claim] += 1
                source_claims[report.source].add(claim)
        
        if not all_claims:
            return 0.5, [], []
        
        n_sources = len(reports)
        
        # Common claims = mentioned by >50% of sources
        common = [claim for claim, count in all_claims.items() 
                 if count > n_sources * 0.5]
        
        # Disputed = mentioned by only one source
        disputed = [claim for claim, count in all_claims.items() 
                   if count == 1 and n_sources > 1]
        
        # Consistency = ratio of common to total
        total_claims = len(all_claims)
        consistency = len(common) / max(1, total_claims) if total_claims > 0 else 0.5
        
        return round(consistency, 3), common[:5], disputed[:5]
    
    def _check_narrative_alignment(self, reports: List[SourceReport]) -> float:
        """Check if sources tell the same narrative direction."""
        if len(reports) <= 1:
            return 0.5
        
        sentiments = [r.sentiment for r in reports]
        
        # Check if all sentiments are in the same direction
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        if all(s > 0 for s in sentiments) or all(s < 0 for s in sentiments):
            alignment = 0.9  # All agree
        elif all(abs(s) < 0.1 for s in sentiments):
            alignment = 0.7  # All neutral
        else:
            # Mixed signals
            variance = sum((s - avg_sentiment) ** 2 for s in sentiments) / len(sentiments)
            alignment = max(0.1, 1.0 - variance * 2)
        
        return round(alignment, 3)
    
    def _detect_coordination(self, reports: List[SourceReport]) -> bool:
        """Detect suspiciously coordinated reporting."""
        if len(reports) <= 1:
            return False
        
        # Check for very similar wording (copy-paste detection)
        texts = [r.text.lower() for r in reports]
        
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similarity = self._text_similarity(texts[i], texts[j])
                if similarity > 0.8 and reports[i].source != reports[j].source:
                    return True  # Different sources, nearly identical text
        
        return False
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Semantic similarity — uses NLP embeddings if available, falls back to Jaccard."""
        # Try embedding-based cosine similarity first
        if self._nlp_parser is not None:
            try:
                return self._nlp_parser.compute_similarity(text1, text2)
            except Exception:
                pass
        
        # Fallback: Jaccard similarity on words (stopwords removed)
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
                      "for", "of", "with", "is", "was", "are", "were", "be", "been",
                      "have", "has", "had", "do", "does", "did", "will", "would",
                      "could", "should", "may", "might", "it", "its", "this", "that"}
        words1 = set(text1.split()) - stopwords
        words2 = set(text2.split()) - stopwords
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _check_timing(self, reports: List[SourceReport]) -> bool:
        """Check for suspicious timing patterns."""
        if len(reports) <= 1:
            return False
        
        # Check if reports cluster too tightly (potential coordinated release)
        timestamps = []
        for r in reports:
            try:
                ts = datetime.fromisoformat(r.timestamp.replace("Z", "+00:00"))
                timestamps.append(ts)
            except (ValueError, AttributeError):
                continue
        
        if len(timestamps) < 2:
            return False
        
        timestamps.sort()
        
        # If all reports within 30 seconds of each other from different sources
        time_span = (timestamps[-1] - timestamps[0]).total_seconds()
        unique_sources = len(set(r.source for r in reports))
        
        if time_span < 30 and unique_sources > 2:
            return True  # Suspiciously synchronized
        
        return False
    
    def _find_conflicts(self, reports: List[SourceReport]) -> List[Dict]:
        """Find directly conflicting claims between sources."""
        conflicts = []
        
        for i, r1 in enumerate(reports):
            for j, r2 in enumerate(reports):
                if i >= j or r1.source == r2.source:
                    continue
                
                # Check sentiment conflict
                if (r1.sentiment > 0.3 and r2.sentiment < -0.3) or \
                   (r1.sentiment < -0.3 and r2.sentiment > 0.3):
                    conflicts.append({
                        "type": "sentiment_conflict",
                        "source_a": r1.source,
                        "source_b": r2.source,
                        "detail": f"Sentiment: {r1.source}={r1.sentiment:.2f} vs {r2.source}={r2.sentiment:.2f}"
                    })
                
                # Check number conflicts
                nums1 = set(r1.numbers_mentioned)
                nums2 = set(r2.numbers_mentioned)
                if nums1 and nums2 and not nums1 & nums2:
                    conflicts.append({
                        "type": "number_conflict",
                        "source_a": r1.source,
                        "source_b": r2.source,
                        "detail": f"Numbers differ: {r1.source}={nums1} vs {r2.source}={nums2}"
                    })
        
        return conflicts[:10]
    
    def _compute_trust_score(self, result: VerificationResult) -> float:
        """Compute overall cross-source trust score."""
        if result.single_source_only:
            # Single source: lower trust, adjusted by source credibility
            source = result.sources[0] if result.sources else "unknown"
            base = self.SOURCE_CREDIBILITY.get(source, 0.5)
            return round(base * 0.5, 3)  # Halved for single source
        
        components = [
            result.source_diversity * 0.25,
            result.claim_consistency * 0.30,
            result.narrative_alignment * 0.20,
            (1.0 - min(1.0, len(result.conflicting_claims) * 0.15)) * 0.15,
            (0.0 if result.coordinated_narrative else 0.5) * 0.10,
        ]
        
        # Source credibility bonus
        avg_credibility = 0
        for source in result.sources:
            avg_credibility += self.SOURCE_CREDIBILITY.get(source, 0.5)
        avg_credibility /= max(1, len(result.sources))
        
        trust = sum(components) + avg_credibility * 0.2
        
        # Penalties
        if result.suspicious_timing:
            trust *= 0.85
        if result.coordinated_narrative:
            trust *= 0.80
        
        return round(min(1.0, max(0.0, trust)), 3)

    # ====================================================================
    # HISTORICAL PATTERN DATABASE
    # ====================================================================
    
    def _init_pattern_db(self):
        """Initialize SQLite-based historical pattern database."""
        import sqlite3
        import os
        
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "hidden_truth_patterns.db")
        
        self._pattern_db = sqlite3.connect(db_path, check_same_thread=False)
        self._pattern_db.execute("PRAGMA journal_mode=WAL")
        
        self._pattern_db.executescript("""
            CREATE TABLE IF NOT EXISTS manipulation_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                description TEXT,
                source_fingerprint TEXT,
                narrative_fingerprint TEXT,
                timing_fingerprint TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                market_impact_direction TEXT,
                market_impact_magnitude REAL,
                confidence REAL DEFAULT 0.5,
                was_confirmed INTEGER DEFAULT 0,
                metadata TEXT
            );
            
            CREATE TABLE IF NOT EXISTS source_reliability_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                claim_text TEXT,
                was_accurate INTEGER,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_pattern_type 
                ON manipulation_patterns(pattern_type);
            CREATE INDEX IF NOT EXISTS idx_source_name 
                ON source_reliability_history(source_name);
        """)
        self._pattern_db.commit()
        self._pattern_db_initialized = True
    
    def record_pattern(self, pattern_type: str, description: str,
                       sources: list = None, narrative_key: str = "",
                       timing_key: str = "", confidence: float = 0.5,
                       market_impact: dict = None):
        """
        Record a detected manipulation pattern for future learning.
        
        Args:
            pattern_type: e.g., 'coordinated_narrative', 'strategic_timing',
                         'manufactured_consensus', 'omission', 'conflicting_claims'
            description: Human-readable description
            sources: List of sources involved
            narrative_key: Key phrases identifying the narrative
            timing_key: Timing characteristics (e.g., 'friday_dump', 'pre_fomc')
            confidence: Confidence this is actually manipulation
            market_impact: Dict with 'direction' and 'magnitude'
        """
        if not self._pattern_db_initialized:
            self._init_pattern_db()
        
        import json
        
        source_fp = ",".join(sorted(sources)) if sources else ""
        impact_dir = market_impact.get("direction", "") if market_impact else ""
        impact_mag = market_impact.get("magnitude", 0.0) if market_impact else 0.0
        
        self._pattern_db.execute(
            """INSERT INTO manipulation_patterns 
               (pattern_type, description, source_fingerprint, 
                narrative_fingerprint, timing_fingerprint, 
                market_impact_direction, market_impact_magnitude, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (pattern_type, description, source_fp, narrative_key,
             timing_key, impact_dir, impact_mag, confidence)
        )
        self._pattern_db.commit()
    
    def record_source_accuracy(self, source_name: str, claim: str,
                                was_accurate: bool, context: str = ""):
        """Record whether a source's claim was accurate (for reliability tracking)."""
        if not self._pattern_db_initialized:
            self._init_pattern_db()
        
        self._pattern_db.execute(
            """INSERT INTO source_reliability_history 
               (source_name, claim_text, was_accurate, context)
               VALUES (?, ?, ?, ?)""",
            (source_name, claim[:500], 1 if was_accurate else 0, context)
        )
        self._pattern_db.commit()
    
    def get_source_reliability(self, source_name: str, days: int = 90) -> dict:
        """
        Get historical reliability stats for a source.
        
        Returns:
            Dict with total_claims, accurate_count, accuracy_rate, trend
        """
        if not self._pattern_db_initialized:
            self._init_pattern_db()
        
        rows = self._pattern_db.execute(
            """SELECT was_accurate, checked_at FROM source_reliability_history
               WHERE source_name = ? 
               AND checked_at > datetime('now', ?)
               ORDER BY checked_at""",
            (source_name, f"-{days} days")
        ).fetchall()
        
        if not rows:
            return {"total_claims": 0, "accuracy_rate": None, "trend": "unknown"}
        
        total = len(rows)
        accurate = sum(1 for r in rows if r[0])
        rate = accurate / total
        
        # Trend: compare first half vs second half
        mid = total // 2
        first_half_rate = sum(1 for r in rows[:mid] if r[0]) / max(1, mid) if mid > 0 else rate
        second_half_rate = sum(1 for r in rows[mid:] if r[0]) / max(1, total - mid)
        
        if second_half_rate > first_half_rate + 0.05:
            trend = "improving"
        elif second_half_rate < first_half_rate - 0.05:
            trend = "degrading"
        else:
            trend = "stable"
        
        return {
            "total_claims": total,
            "accurate_count": accurate,
            "accuracy_rate": round(rate, 3),
            "trend": trend,
        }
    
    def find_similar_patterns(self, pattern_type: str, 
                               narrative_key: str = "",
                               limit: int = 10) -> list:
        """
        Find historical patterns similar to the current detection.
        
        Returns list of past patterns with their market impact outcomes.
        """
        if not self._pattern_db_initialized:
            self._init_pattern_db()
        
        if narrative_key:
            rows = self._pattern_db.execute(
                """SELECT pattern_type, description, market_impact_direction,
                          market_impact_magnitude, confidence, was_confirmed,
                          detected_at
                   FROM manipulation_patterns
                   WHERE pattern_type = ? AND narrative_fingerprint LIKE ?
                   ORDER BY detected_at DESC LIMIT ?""",
                (pattern_type, f"%{narrative_key[:50]}%", limit)
            ).fetchall()
        else:
            rows = self._pattern_db.execute(
                """SELECT pattern_type, description, market_impact_direction,
                          market_impact_magnitude, confidence, was_confirmed,
                          detected_at
                   FROM manipulation_patterns
                   WHERE pattern_type = ?
                   ORDER BY detected_at DESC LIMIT ?""",
                (pattern_type, limit)
            ).fetchall()
        
        return [
            {
                "pattern_type": r[0],
                "description": r[1],
                "market_impact_direction": r[2],
                "market_impact_magnitude": r[3],
                "confidence": r[4],
                "was_confirmed": bool(r[5]),
                "detected_at": r[6],
            }
            for r in rows
        ]
    
    def confirm_pattern(self, pattern_id: int, market_impact: dict = None):
        """Confirm that a detected pattern was indeed manipulation."""
        if not self._pattern_db_initialized:
            self._init_pattern_db()
        
        if market_impact:
            self._pattern_db.execute(
                """UPDATE manipulation_patterns 
                   SET was_confirmed = 1, 
                       market_impact_direction = ?,
                       market_impact_magnitude = ?
                   WHERE id = ?""",
                (market_impact.get("direction", ""),
                 market_impact.get("magnitude", 0.0),
                 pattern_id)
            )
        else:
            self._pattern_db.execute(
                "UPDATE manipulation_patterns SET was_confirmed = 1 WHERE id = ?",
                (pattern_id,)
            )
        self._pattern_db.commit()
