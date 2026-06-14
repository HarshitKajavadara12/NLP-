"""
PHASE 1: NEWS EVENT PARSER

Converts raw news text into structured NewsEvent objects.

Key principle: This parser does NOT produce trading signals.
It only decomposes linguistic structure and extracts semantic meaning.

Rules:
- Preserve ambiguity, never resolve it
- Store raw text unchanged
- Extract facts, not sentiment
- No market interpretation
"""

import re
from datetime import datetime
from typing import List, Tuple, Optional
from news_model.news_event import (
    NewsEvent, NarrativeType, TemporalType, ConfidenceLevel, Actor
)


class NewsEventParser:
    """
    Parses raw news text into structured NewsEvent objects.
    
    This is a linguistic and semantic parser, NOT a sentiment analyzer.
    It preserves ambiguity and uncertainty without resolving them.
    """
    
    # Uncertainty markers (things that reduce certainty)
    UNCERTAINTY_WORDS = {
        "may", "might", "could", "can", "appears", "seems", "possibly",
        "probably", "arguably", "suggest", "signal", "potentially",
        "reportedly", "if", "likely", "alleged", "purportedly", "rumored"
    }
    
    # Authority markers (things that increase certainty)
    AUTHORITY_WORDS = {
        "confirmed", "official", "announced", "stated", "declared",
        "will", "shall", "must", "definitively"
    }
    
    # Contradiction markers (indicate conflicts with prior news)
    CONTRADICTION_WORDS = {
        "contrasts", "unlike", "opposite", "contrary", "despite",
        "however", "but", "yet", "reversed", "flip", "U-turn", "reversal"
    }
    
    # Policy-related keywords for narrative classification
    POLICY_KEYWORDS = {
        "fed", "central bank", "ecb", "boj", "rate", "interest", "monetary",
        "taper", "pivot", "hawkish", "dovish", "policy", "reserve"
    }
    
    # Growth-related keywords
    GROWTH_KEYWORDS = {
        "growth", "gdp", "earnings", "revenue", "guidance", "profit",
        "expansion", "recession", "slowdown"
    }
    
    # Credit-related keywords
    CREDIT_KEYWORDS = {
        "credit", "spread", "default", "downgrade", "rating", "debt",
        "bankruptcy", "collateral"
    }
    
    # Crisis keywords
    CRISIS_KEYWORDS = {
        "crisis", "collapse", "crash", "panic", "emergency", "breakdown",
        "failed", "systemic", "contagion"
    }
    
    def parse(self, 
              timestamp_utc: datetime,
              source: str,
              raw_text: str) -> NewsEvent:
        """
        Parse raw news text into a NewsEvent.
        
        Args:
            timestamp_utc: When the news became public
            source: Source/publisher name
            raw_text: The exact, unaltered raw news text
        
        Returns:
            NewsEvent: Structured news event
        
        Note: This does NOT produce sentiment or trading signals.
        """
        
        # Create base event
        event = NewsEvent.create(
            timestamp_utc=timestamp_utc,
            source=source,
            raw_text=raw_text
        )
        
        # Decompose into sentences
        self._extract_sentences(event, raw_text)
        
        # Extract linguistic clauses
        self._extract_clauses(event, raw_text)
        
        # Extract modality markers (uncertainty, authority)
        self._extract_modality_markers(event, raw_text)
        
        # Extract temporal markers
        self._extract_temporal_markers(event, raw_text)
        
        # Extract actors (who is acting)
        self._extract_actors(event, raw_text)
        
        # Extract semantic claims (what are they claiming)
        self._extract_semantic_claims(event, raw_text)
        
        # Classify narratives
        self._classify_narratives(event, raw_text)
        
        # Calculate uncertainty metrics
        self._calculate_uncertainty_metrics(event, raw_text)
        
        return event
    
    def _extract_sentences(self, event: NewsEvent, text: str):
        """Decompose text into sentences."""
        # Simple sentence splitting on periods, exclamation, question marks
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence_text in sentences:
            event.add_sentence(sentence_text)
    
    def _extract_clauses(self, event: NewsEvent, text: str):
        """Extract logical clauses from the text."""
        text_lower = text.lower()
        
        # Find conditional clauses
        conditional_pattern = r'(if|when|unless|provided that)\s+([^,\.]+)'
        for match in re.finditer(conditional_pattern, text_lower):
            clause_text = match.group(0)
            event.add_clause(clause_text, conditional=True)
        
        # Find clauses with negation
        negation_pattern = r'(not|no|never|neither)\s+(\w+\s+\w+[^,\.]*)'
        for match in re.finditer(negation_pattern, text_lower):
            clause_text = match.group(0)
            event.add_clause(clause_text, negated=True)
    
    def _extract_modality_markers(self, event: NewsEvent, text: str):
        """Extract markers of certainty, uncertainty, and authority."""
        text_lower = text.lower()
        
        # Uncertainty markers
        for word in self.UNCERTAINTY_WORDS:
            if re.search(r'\b' + word + r'\b', text_lower):
                event.add_modality_marker(
                    text=word,
                    marker_type="uncertainty",
                    strength=0.6
                )
        
        # Authority markers
        for word in self.AUTHORITY_WORDS:
            if re.search(r'\b' + word + r'\b', text_lower):
                event.add_modality_marker(
                    text=word,
                    marker_type="authority",
                    strength=0.8
                )
        
        # Contradiction markers
        for word in self.CONTRADICTION_WORDS:
            if re.search(r'\b' + word + r'\b', text_lower):
                event.add_modality_marker(
                    text=word,
                    marker_type="contradiction",
                    strength=0.7
                )
                event.contradicts_prior_news = True
    
    def _extract_temporal_markers(self, event: NewsEvent, text: str):
        """Extract temporal information."""
        text_lower = text.lower()
        
        # Now/immediate
        if re.search(r'\b(today|now|immediately|currently)\b', text_lower):
            event.add_temporal_marker(
                TemporalType.NOW,
                explicit_time="today"
            )
        
        # Future
        future_patterns = [
            (r'\bnext\s+(quarter|year|month|week)\b', 'next_period'),
            (r'\bfuture\b', 'future'),
            (r'\bcoming\b', 'coming'),
        ]
        
        for pattern, label in future_patterns:
            if re.search(pattern, text_lower):
                match = re.search(pattern, text_lower)
                event.add_temporal_marker(
                    TemporalType.FUTURE,
                    explicit_time=match.group(0) if match else label
                )
        
        # Conditional future (coupled with "if", "when")
        if 'if' in text_lower or 'when' in text_lower:
            event.add_temporal_marker(
                TemporalType.CONDITIONAL
            )
    
    def _extract_actors(self, event: NewsEvent, text: str):
        """Extract identified actors (who is acting)."""
        text_lower = text.lower()
        
        # Central banks
        if 'fed' in text_lower or 'federal reserve' in text_lower:
            event.add_actor("Federal Reserve", "central_bank")
        
        if 'ecb' in text_lower or 'european central bank' in text_lower:
            event.add_actor("ECB", "central_bank")
        
        if 'boj' in text_lower or 'bank of japan' in text_lower:
            event.add_actor("Bank of Japan", "central_bank")
        
        # Government
        if re.search(r'\b(government|administration|treasury|congress)\b', text_lower):
            event.add_actor("Government", "government")
        
        # Company/Corporation (generic)
        if re.search(r'\b(company|corporation|firm|bank|financial|institution)\b', text_lower):
            # Try to find specific names — search original text (not lowered) for capitalized words
            proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', text)
            for noun in proper_nouns[:3]:  # Limit to first 3
                if len(noun) > 3:  # Skip short words
                    event.add_actor(noun, "company")
        
        # Anonymous source
        if 'source' in text_lower or 'reportedly' in text_lower:
            event.add_actor("Unnamed Source", "source")
    
    def _extract_semantic_claims(self, event: NewsEvent, text: str):
        """Extract semantic claims (factual claims from the news)."""
        text_lower = text.lower()
        
        # Simple pattern: Actor + Action + Object
        # Example: "Fed raises rates" = Federal Reserve + raise + interest rates
        
        action_patterns = [
            (r'(fed|federal reserve).*?(raise|increase|hike).*?(rate|interest)', 
             "Federal Reserve", "raise rates", "interest rates"),
            (r'(fed|federal reserve).*?(cut|lower).*?(rate|interest)', 
             "Federal Reserve", "cut rates", "interest rates"),
            (r'(fed|federal reserve).*?(signal|suggest|indicate).*?(patience|dovish)', 
             "Federal Reserve", "signal patience", "interest rates"),
            (r'(company|earnings).*?(beat|exceed|miss)', 
             "Company", "beat/miss earnings", "earnings"),
        ]
        
        for pattern, actor_name, action, obj in action_patterns:
            if re.search(pattern, text_lower):
                # Find or create the actor
                actor = None
                for a in event.actors:
                    if actor_name.lower() in a.name.lower():
                        actor = a
                        break
                
                if actor is None:
                    actor = event.add_actor(actor_name, "entity")
                
                # Determine confidence based on modality
                confidence = ConfidenceLevel.HIGH
                if event.has_uncertainty():
                    confidence = ConfidenceLevel.MEDIUM
                
                event.add_semantic_claim(
                    actor=actor,
                    action=action,
                    object_=obj,
                    confidence=confidence,
                    raw_source=text[:100]
                )
    
    def _classify_narratives(self, event: NewsEvent, text: str):
        """Classify what type(s) of narrative this event represents."""
        text_lower = text.lower()
        
        # Check for each narrative type
        if any(kw in text_lower for kw in self.POLICY_KEYWORDS):
            event.add_narrative_type(NarrativeType.MACRO_POLICY)
        
        if any(kw in text_lower for kw in self.GROWTH_KEYWORDS):
            event.add_narrative_type(NarrativeType.GROWTH)
        
        if any(kw in text_lower for kw in self.CREDIT_KEYWORDS):
            event.add_narrative_type(NarrativeType.CREDIT_RISK)
        
        if any(kw in text_lower for kw in self.CRISIS_KEYWORDS):
            event.add_narrative_type(NarrativeType.CRISIS_SHOCK)
        
        if event.contradicts_prior_news:
            event.add_narrative_type(NarrativeType.NARRATIVE_CONTRADICTION)
        else:
            event.add_narrative_type(NarrativeType.NARRATIVE_REINFORCEMENT)
    
    def _calculate_uncertainty_metrics(self, event: NewsEvent, text: str):
        """Calculate ambiguity and confidence metrics."""
        
        # Ambiguity score based on uncertainty markers and vague language
        uncertainty_count = len([m for m in event.modality_markers 
                                if m.marker_type == "uncertainty"])
        authority_count = len([m for m in event.modality_markers 
                              if m.marker_type == "authority"])
        
        # Base ambiguity on uncertainty vs authority
        if authority_count > uncertainty_count:
            event.ambiguity_score = 0.2
            event.confidence_level = ConfidenceLevel.HIGH
        elif uncertainty_count > authority_count:
            event.ambiguity_score = 0.7
            event.confidence_level = ConfidenceLevel.LOW
        else:
            event.ambiguity_score = 0.5
            event.confidence_level = ConfidenceLevel.MEDIUM
        
        # Increase ambiguity if conditional
        if any(m.temporal_type == TemporalType.CONDITIONAL 
               for m in event.temporal_markers):
            event.ambiguity_score = min(1.0, event.ambiguity_score + 0.2)
        
        # Check for contradictions
        if any(m.marker_type == "contradiction" for m in event.modality_markers):
            event.ambiguity_score = min(1.0, event.ambiguity_score + 0.1)


if __name__ == "__main__":
    parser = NewsEventParser()
    
    # Test parse
    event = parser.parse(
        timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
        source="Reuters",
        raw_text="""
        The Federal Reserve signaled patience on interest rate cuts today.
        Chair Powell stated that the central bank may hold rates steady if 
        inflation persists above target. Markets reacted with uncertainty,
        as this contrasts with previous dovish signals from last week.
        """
    )
    
    print(event.get_summary())
    print(f"\nActors: {[a.name for a in event.actors]}")
    print(f"Narratives: {[n.value for n in event.narrative_types]}")
    print(f"Semantic Claims: {len(event.semantic_claims)}")
    print(f"Modality Markers: {len(event.modality_markers)}")
    print(f"Temporal Markers: {len(event.temporal_markers)}")
