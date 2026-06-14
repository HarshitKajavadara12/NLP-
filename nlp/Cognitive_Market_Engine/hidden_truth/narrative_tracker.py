"""
NARRATIVE TRACKER — Track how stories evolve over time

Detects:
- Narrative shifts (story changing direction)
- Story amplification/suppression patterns
- New framing of old events
- Consensus formation/breakdown
- Source leadership (who drives the narrative)
"""

import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque


@dataclass
class NarrativeSnapshot:
    """A snapshot of a narrative at a point in time."""
    timestamp: str = ""
    dominant_framing: str = ""
    sentiment: float = 0.0
    source_count: int = 0
    leading_source: str = ""
    key_claims: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)


@dataclass 
class NarrativeEvolution:
    """Track how a narrative evolves."""
    narrative_id: str = ""
    topic: str = ""
    first_seen: str = ""
    last_updated: str = ""
    
    # Evolution metrics
    snapshots: List[NarrativeSnapshot] = field(default_factory=list)
    direction_changes: int = 0
    amplification_trend: str = "stable"  # growing, stable, fading
    
    # Current state
    current_sentiment: float = 0.0
    current_intensity: float = 0.0       # 0-1
    source_coverage: int = 0
    
    # Manipulation signals
    framing_shifts: List[Dict] = field(default_factory=list)
    consensus_score: float = 0.5
    credibility: float = 0.5
    
    def to_dict(self) -> Dict:
        return {
            "narrative_id": self.narrative_id,
            "topic": self.topic,
            "first_seen": self.first_seen,
            "last_updated": self.last_updated,
            "direction_changes": self.direction_changes,
            "amplification_trend": self.amplification_trend,
            "current_sentiment": round(self.current_sentiment, 3),
            "current_intensity": round(self.current_intensity, 3),
            "source_coverage": self.source_coverage,
            "framing_shifts": self.framing_shifts,
            "consensus_score": round(self.consensus_score, 3),
            "credibility": round(self.credibility, 3),
            "snapshot_count": len(self.snapshots),
        }


class NarrativeTracker:
    """
    Tracks narratives over time, detecting evolution, shifts,
    coordinated amplification, and manufactured consensus.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize NarrativeTracker.
        
        Args:
            max_history: Max events to track per narrative
        """
        self.narratives = {}            # narrative_id -> NarrativeEvolution
        self.topic_index = defaultdict(set)   # topic -> {narrative_ids}
        self.entity_index = defaultdict(set)  # entity -> {narrative_ids}
        self.max_history = max_history
        self.event_count = 0
        print("[NARRATIVE] Tracker initialized")
    
    def track(self, text: str, source: str = "", 
              timestamp: str = None,
              entities: List[str] = None,
              sentiment: float = None) -> NarrativeEvolution:
        """
        Track a new piece of a narrative.
        
        Args:
            text: Article/statement text
            source: Source name
            timestamp: Publication time
            entities: Pre-extracted entities
            sentiment: Pre-computed sentiment (-1 to 1)
            
        Returns:
            The narrative this text belongs to, with evolution data
        """
        timestamp = timestamp or datetime.now().isoformat()
        entities = entities or self._extract_entities(text)
        sentiment = sentiment if sentiment is not None else self._estimate_sentiment(text)
        
        # Find or create narrative
        narrative_id = self._find_matching_narrative(text, entities)
        
        if narrative_id and narrative_id in self.narratives:
            narrative = self.narratives[narrative_id]
        else:
            narrative_id = self._generate_narrative_id(text, entities)
            topic = self._extract_topic(text, entities)
            narrative = NarrativeEvolution(
                narrative_id=narrative_id,
                topic=topic,
                first_seen=timestamp,
            )
            self.narratives[narrative_id] = narrative
            self.topic_index[topic].add(narrative_id)
            for ent in entities:
                self.entity_index[ent].add(narrative_id)
        
        # Create snapshot
        snapshot = NarrativeSnapshot(
            timestamp=timestamp,
            dominant_framing=self._detect_framing(text),
            sentiment=sentiment,
            source_count=narrative.source_coverage + 1,
            leading_source=source,
            key_claims=self._extract_claims(text),
            entities=entities,
        )
        
        # Check for narrative shifts before adding
        if narrative.snapshots:
            self._detect_shifts(narrative, snapshot)
        
        narrative.snapshots.append(snapshot)
        if len(narrative.snapshots) > self.max_history:
            narrative.snapshots = narrative.snapshots[-self.max_history:]
        
        # Update current state
        narrative.last_updated = timestamp
        narrative.current_sentiment = sentiment
        narrative.source_coverage = len(set(
            s.leading_source for s in narrative.snapshots if s.leading_source
        ))
        narrative.current_intensity = self._compute_intensity(narrative)
        narrative.amplification_trend = self._compute_trend(narrative)
        narrative.consensus_score = self._compute_consensus(narrative)
        narrative.credibility = self._compute_credibility(narrative)
        
        self.event_count += 1
        return narrative
    
    def get_narrative(self, narrative_id: str) -> Optional[NarrativeEvolution]:
        """Get a narrative by ID."""
        return self.narratives.get(narrative_id)
    
    def get_narratives_for_entity(self, entity: str) -> List[NarrativeEvolution]:
        """Get all narratives involving an entity."""
        narrative_ids = self.entity_index.get(entity, set())
        return [self.narratives[nid] for nid in narrative_ids if nid in self.narratives]
    
    def get_active_narratives(self, hours: int = 24) -> List[NarrativeEvolution]:
        """Get narratives updated within the last N hours."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        active = [
            n for n in self.narratives.values()
            if n.last_updated >= cutoff
        ]
        active.sort(key=lambda x: x.current_intensity, reverse=True)
        return active
    
    def get_trending(self, top_n: int = 10) -> List[Dict]:
        """Get trending narratives by intensity."""
        all_narratives = sorted(
            self.narratives.values(),
            key=lambda x: x.current_intensity,
            reverse=True
        )
        
        return [
            {
                "narrative_id": n.narrative_id,
                "topic": n.topic,
                "intensity": round(n.current_intensity, 3),
                "sentiment": round(n.current_sentiment, 3),
                "trend": n.amplification_trend,
                "sources": n.source_coverage,
                "credibility": round(n.credibility, 3),
            }
            for n in all_narratives[:top_n]
        ]
    
    def detect_manufactured_consensus(self) -> List[Dict]:
        """
        Detect narratives that show signs of manufactured consensus.
        
        Signs:
        - Sudden appearance across many sources
        - Very similar framing across sources
        - Topics that benefit specific actors
        """
        suspicious = []
        
        for nid, narrative in self.narratives.items():
            risk_score = 0.0
            reasons = []
            
            # Check for sudden multi-source appearance
            if len(narrative.snapshots) >= 3:
                first_3 = narrative.snapshots[:3]
                sources_in_first_3 = len(set(s.leading_source for s in first_3))
                if sources_in_first_3 >= 3:
                    risk_score += 0.3
                    reasons.append("Appeared across 3+ sources simultaneously")
            
            # Check for high sentiment consensus
            if narrative.consensus_score > 0.9 and narrative.source_coverage >= 3:
                risk_score += 0.2
                reasons.append("Unusually high consensus across sources")
            
            # Check for zero direction changes with many updates
            if narrative.direction_changes == 0 and len(narrative.snapshots) >= 5:
                risk_score += 0.2
                reasons.append("No narrative pushback despite many reports")
            
            # Check for rapid intensification
            if narrative.amplification_trend == "growing" and narrative.current_intensity > 0.7:
                risk_score += 0.2
                reasons.append("Rapid narrative intensification")
            
            if risk_score > 0.3:
                suspicious.append({
                    "narrative_id": nid,
                    "topic": narrative.topic,
                    "risk_score": round(risk_score, 3),
                    "reasons": reasons,
                })
        
        suspicious.sort(key=lambda x: x["risk_score"], reverse=True)
        return suspicious
    
    # ================================================================
    # INTERNAL METHODS
    # ================================================================
    
    def _find_matching_narrative(self, text: str, entities: List[str]) -> Optional[str]:
        """Find existing narrative that this text belongs to."""
        best_match = None
        best_score = 0.0
        
        text_words = set(text.lower().split())
        entity_set = set(e.lower() for e in entities)
        
        for nid, narrative in self.narratives.items():
            # Entity overlap
            narrative_entities = set()
            for s in narrative.snapshots[-5:]:
                narrative_entities.update(e.lower() for e in s.entities)
            
            entity_overlap = len(entity_set & narrative_entities) / max(1, len(entity_set | narrative_entities))
            
            # Claim overlap
            claim_overlap = 0
            if narrative.snapshots:
                recent_claims = set()
                for s in narrative.snapshots[-3:]:
                    recent_claims.update(c.lower() for c in s.key_claims)
                
                current_claims = set(c.lower() for c in self._extract_claims(text))
                if recent_claims and current_claims:
                    claim_overlap = len(current_claims & recent_claims) / max(1, len(current_claims | recent_claims))
            
            score = entity_overlap * 0.6 + claim_overlap * 0.4
            
            if score > 0.3 and score > best_score:
                best_score = score
                best_match = nid
        
        return best_match
    
    def _generate_narrative_id(self, text: str, entities: List[str]) -> str:
        """Generate unique narrative ID."""
        content = " ".join(sorted(entities[:5])) + " " + text[:100]
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _extract_topic(self, text: str, entities: List[str]) -> str:
        """Extract the main topic."""
        if entities:
            return entities[0]
        
        words = text.split()[:5]
        return " ".join(words)
    
    def _detect_framing(self, text: str) -> str:
        """Detect the framing/angle of the narrative."""
        text_lower = text.lower()
        
        framings = {
            "crisis": ["crisis", "crash", "collapse", "panic", "meltdown"],
            "recovery": ["recover", "rebound", "bounce", "improve", "upturn"],
            "policy": ["policy", "regulation", "reform", "legislation", "intervention"],
            "opportunity": ["opportunity", "growth", "potential", "upside", "promising"],
            "risk": ["risk", "threat", "danger", "warning", "concern", "vulnerability"],
            "uncertainty": ["uncertain", "unclear", "unknown", "volatile", "unpredictable"],
            "blame": ["blame", "responsible", "fault", "caused by", "due to"],
            "neutral": [],
        }
        
        best_framing = "neutral"
        best_score = 0
        
        for framing, keywords in framings.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_framing = framing
        
        return best_framing
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract key claims."""
        claims = []
        sentences = text.replace(". ", ".\n").split("\n")
        
        for sent in sentences[:5]:
            sent = sent.strip()
            if len(sent) > 20:
                claims.append(sent[:150])
        
        return claims
    
    def _extract_entities(self, text: str) -> List[str]:
        """Simple entity extraction."""
        entities = []
        known = [
            "Fed", "ECB", "BOJ", "BOE", "IMF",
            "S&P", "Nasdaq", "Dow", "FTSE", "DAX",
            "USD", "EUR", "JPY", "GBP",
            "gold", "oil", "bitcoin",
        ]
        
        for entity in known:
            if entity.lower() in text.lower():
                entities.append(entity)
        
        return entities
    
    def _estimate_sentiment(self, text: str) -> float:
        """Quick sentiment estimate."""
        positive = ["rally", "gain", "surge", "rise", "strong", "boost", "beat"]
        negative = ["crash", "plunge", "fall", "decline", "weak", "miss", "fear"]
        
        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        
        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total
    
    def _detect_shifts(self, narrative: NarrativeEvolution, 
                       new_snapshot: NarrativeSnapshot):
        """Detect narrative direction shifts."""
        prev = narrative.snapshots[-1]
        
        # Sentiment reversal
        if (prev.sentiment > 0.2 and new_snapshot.sentiment < -0.2) or \
           (prev.sentiment < -0.2 and new_snapshot.sentiment > 0.2):
            narrative.direction_changes += 1
            narrative.framing_shifts.append({
                "timestamp": new_snapshot.timestamp,
                "from_sentiment": round(prev.sentiment, 3),
                "to_sentiment": round(new_snapshot.sentiment, 3),
                "from_framing": prev.dominant_framing,
                "to_framing": new_snapshot.dominant_framing,
            })
        
        # Framing change
        if prev.dominant_framing != new_snapshot.dominant_framing and \
           prev.dominant_framing != "neutral" and new_snapshot.dominant_framing != "neutral":
            narrative.framing_shifts.append({
                "timestamp": new_snapshot.timestamp,
                "type": "framing_change",
                "from": prev.dominant_framing,
                "to": new_snapshot.dominant_framing,
            })
    
    def _compute_intensity(self, narrative: NarrativeEvolution) -> float:
        """Compute current narrative intensity (0-1)."""
        if not narrative.snapshots:
            return 0.0
        
        # Factors: recency, frequency, source count, sentiment magnitude
        recent = narrative.snapshots[-10:]
        
        recency = min(1.0, len(recent) / 10)
        source_factor = min(1.0, narrative.source_coverage / 5)
        sentiment_mag = abs(narrative.current_sentiment)
        
        return round(min(1.0, recency * 0.4 + source_factor * 0.3 + sentiment_mag * 0.3), 3)
    
    def _compute_trend(self, narrative: NarrativeEvolution) -> str:
        """Compute amplification trend."""
        if len(narrative.snapshots) < 3:
            return "new"
        
        recent = narrative.snapshots[-5:]
        older = narrative.snapshots[-10:-5] if len(narrative.snapshots) >= 10 else narrative.snapshots[:5]
        
        recent_intensity = len(recent) / 5
        older_intensity = len(older) / max(1, len(older))
        
        if recent_intensity > older_intensity * 1.5:
            return "growing"
        elif recent_intensity < older_intensity * 0.5:
            return "fading"
        else:
            return "stable"
    
    def _compute_consensus(self, narrative: NarrativeEvolution) -> float:
        """Compute how much consensus exists across sources."""
        if len(narrative.snapshots) < 2:
            return 0.5
        
        sentiments = [s.sentiment for s in narrative.snapshots[-10:]]
        
        if not sentiments:
            return 0.5
        
        avg = sum(sentiments) / len(sentiments)
        variance = sum((s - avg) ** 2 for s in sentiments) / len(sentiments)
        
        consensus = max(0.0, 1.0 - variance * 2)
        return round(consensus, 3)
    
    def _compute_credibility(self, narrative: NarrativeEvolution) -> float:
        """Compute narrative credibility."""
        factors = []
        
        # Multi-source = more credible
        factors.append(min(1.0, narrative.source_coverage / 3) * 0.4)
        
        # Consistency = more credible
        factors.append(narrative.consensus_score * 0.3)
        
        # Stability (fewer direction changes) = more credible
        stability = max(0.0, 1.0 - narrative.direction_changes * 0.2)
        factors.append(stability * 0.3)
        
        return round(min(1.0, sum(factors)), 3)
    
    def get_summary(self) -> Dict:
        """Get tracker summary."""
        return {
            "total_narratives": len(self.narratives),
            "total_events_tracked": self.event_count,
            "active_narratives": len(self.get_active_narratives(24)),
            "trending": self.get_trending(5),
            "suspicious": self.detect_manufactured_consensus()[:3],
        }
