"""
CONTRADICTION DETECTOR — Natural Language Inference

Detects contradictions between:
- Claims within the same article
- Claims across different articles about the same topic
- Current claims vs historical statements
- Official statements vs leaked information

Uses NLI (Natural Language Inference) when transformer models available.
Falls back to rule-based contradiction detection.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class ContradictionType:
    """Types of contradictions detected."""
    DIRECT = "direct"           # "A is true" vs "A is false"
    TEMPORAL = "temporal"       # "X will happen" vs "X won't happen"
    NUMERIC = "numeric"         # "growth is 3%" vs "growth is 1%"
    STANCE = "stance"           # "supportive of X" vs "against X"
    OMISSION = "omission"       # Source A mentions X, Source B omits X
    FRAMING = "framing"         # Same fact, opposite framing


@dataclass
class ContradictionResult:
    """A detected contradiction between two claims."""
    claim_a: str
    claim_b: str
    source_a: str
    source_b: str
    contradiction_type: str
    confidence: float  # 0.0-1.0
    reasoning: str = ""
    severity: float = 0.0  # 0=minor, 1=critical
    resolution_hint: str = ""  # Which claim is likely more accurate


@dataclass
class ConsistencyReport:
    """Complete consistency analysis across claims."""
    total_claims_analyzed: int = 0
    contradictions_found: List[ContradictionResult] = field(default_factory=list)
    consistency_score: float = 1.0  # 0=all contradictions, 1=fully consistent
    key_disagreements: List[str] = field(default_factory=list)
    reliable_claims: List[str] = field(default_factory=list)
    unreliable_claims: List[str] = field(default_factory=list)


class ContradictionDetector:
    """
    Detects contradictions and inconsistencies in news claims.
    
    Methods:
    1. NLI-based: Uses transformer model for entailment/contradiction
    2. Rule-based: Pattern matching for numeric and stance contradictions
    3. Cross-source: Compares claims across different sources
    4. Temporal: Tracks how claims evolve over time
    """
    
    # Antonym pairs for rule-based detection
    ANTONYMS = {
        "increase": "decrease", "rise": "fall", "grow": "shrink",
        "expand": "contract", "strengthen": "weaken", "improve": "deteriorate",
        "accelerate": "decelerate", "tighten": "ease", "hawk": "dove",
        "bullish": "bearish", "optimistic": "pessimistic", "surplus": "deficit",
        "gain": "loss", "profit": "loss", "support": "oppose",
        "approve": "reject", "confirm": "deny", "raise": "cut",
        "upgrade": "downgrade", "buy": "sell", "long": "short",
        "inflation": "deflation", "boom": "bust", "recovery": "recession",
    }
    
    # Negation patterns
    NEGATION_PATTERNS = [
        r"\bnot\s+", r"\bno\s+", r"\bnever\s+", r"\bneither\s+",
        r"\bnor\s+", r"\bwon't\s+", r"\bcan't\s+", r"\bdon't\s+",
        r"\bdoesn't\s+", r"\bdidn't\s+", r"\bisn't\s+", r"\baren't\s+",
        r"\bwouldn't\s+", r"\bcouldn't\s+", r"\bshouldn't\s+",
        r"\bdeny\b", r"\bdenied\b", r"\brefute\b", r"\brefuted\b",
    ]
    
    def __init__(self, use_nli_model: bool = True):
        """
        Initialize contradiction detector.
        
        Args:
            use_nli_model: Whether to load NLI transformer model
        """
        self.nli_pipeline = None
        
        if use_nli_model and TRANSFORMERS_AVAILABLE:
            try:
                self.nli_pipeline = pipeline(
                    "text-classification",
                    model="cross-encoder/nli-deberta-v3-small",
                    device=-1  # CPU
                )
                print("[NLI] Contradiction detector loaded (transformer)")
            except Exception as e:
                print(f"[NLI] Transformer unavailable: {e}. Using rule-based.")
        
        # Build reverse antonyms
        self._antonyms_full = {}
        for k, v in self.ANTONYMS.items():
            self._antonyms_full[k] = v
            self._antonyms_full[v] = k
    
    # ========================================================================
    # MAIN API
    # ========================================================================
    
    def check_contradiction(self, claim_a: str, claim_b: str,
                           source_a: str = "", source_b: str = "") -> ContradictionResult:
        """
        Check if two claims contradict each other.
        
        Uses NLI if available, falls back to rule-based.
        """
        # Try NLI first
        if self.nli_pipeline:
            return self._nli_check(claim_a, claim_b, source_a, source_b)
        
        # Fall back to rule-based
        return self._rule_based_check(claim_a, claim_b, source_a, source_b)
    
    def analyze_consistency(self, claims: List[Dict[str, str]]) -> ConsistencyReport:
        """
        Analyze consistency across multiple claims.
        
        Args:
            claims: List of {"text": "...", "source": "...", "timestamp": "..."}
        
        Returns:
            ConsistencyReport with all contradictions found
        """
        report = ConsistencyReport(total_claims_analyzed=len(claims))
        
        # Pairwise comparison
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                result = self.check_contradiction(
                    claims[i].get("text", ""),
                    claims[j].get("text", ""),
                    claims[i].get("source", f"source_{i}"),
                    claims[j].get("source", f"source_{j}"),
                )
                
                if result.confidence > 0.5:
                    report.contradictions_found.append(result)
        
        # Compute consistency score
        if claims:
            max_pairs = len(claims) * (len(claims) - 1) / 2
            contradiction_ratio = len(report.contradictions_found) / max(max_pairs, 1)
            report.consistency_score = max(0.0, 1.0 - contradiction_ratio)
        
        # Identify key disagreements
        for c in sorted(report.contradictions_found, key=lambda x: x.severity, reverse=True)[:5]:
            report.key_disagreements.append(
                f"{c.source_a} vs {c.source_b}: {c.reasoning}"
            )
        
        # Identify reliable vs unreliable claims
        contradiction_counts = {}
        for c in report.contradictions_found:
            contradiction_counts[c.claim_a] = contradiction_counts.get(c.claim_a, 0) + 1
            contradiction_counts[c.claim_b] = contradiction_counts.get(c.claim_b, 0) + 1
        
        for claim_dict in claims:
            text = claim_dict.get("text", "")
            if text in contradiction_counts and contradiction_counts[text] > 1:
                report.unreliable_claims.append(text[:100])
            else:
                report.reliable_claims.append(text[:100])
        
        return report
    
    def detect_omissions(self, source_claims: Dict[str, List[str]]) -> List[Dict]:
        """
        Detect what one source mentions that others omit.
        
        Args:
            source_claims: {"reuters": ["claim1", ...], "cnbc": ["claim2", ...]}
        
        Returns:
            List of omission detections
        """
        omissions = []
        all_sources = list(source_claims.keys())
        
        for source, claims in source_claims.items():
            other_sources = [s for s in all_sources if s != source]
            
            for claim in claims:
                # Check if this claim appears (semantically) in other sources
                claim_words = set(claim.lower().split())
                found_in_others = False
                
                for other_source in other_sources:
                    for other_claim in source_claims[other_source]:
                        other_words = set(other_claim.lower().split())
                        overlap = len(claim_words & other_words) / max(len(claim_words), 1)
                        if overlap > 0.4:  # 40% word overlap = similar topic
                            found_in_others = True
                            break
                    if found_in_others:
                        break
                
                if not found_in_others:
                    omissions.append({
                        "claim": claim,
                        "mentioned_by": source,
                        "omitted_by": other_sources,
                        "significance": "high" if len(other_sources) > 2 else "medium",
                    })
        
        return omissions
    
    # ========================================================================
    # NLI-BASED DETECTION
    # ========================================================================
    
    def _nli_check(self, claim_a: str, claim_b: str,
                   source_a: str, source_b: str) -> ContradictionResult:
        """Use NLI model to check for contradiction."""
        try:
            # NLI input format: premise + hypothesis
            result = self.nli_pipeline(f"{claim_a} [SEP] {claim_b}")
            
            label = result[0]["label"].lower()
            score = result[0]["score"]
            
            if "contradiction" in label:
                return ContradictionResult(
                    claim_a=claim_a, claim_b=claim_b,
                    source_a=source_a, source_b=source_b,
                    contradiction_type=ContradictionType.DIRECT,
                    confidence=score,
                    reasoning=f"NLI detected contradiction (score: {score:.2f})",
                    severity=score,
                )
            elif "entailment" in label:
                return ContradictionResult(
                    claim_a=claim_a, claim_b=claim_b,
                    source_a=source_a, source_b=source_b,
                    contradiction_type="entailment",
                    confidence=1.0 - score,
                    reasoning=f"Claims are consistent (entailment score: {score:.2f})",
                    severity=0.0,
                )
            else:
                return ContradictionResult(
                    claim_a=claim_a, claim_b=claim_b,
                    source_a=source_a, source_b=source_b,
                    contradiction_type="neutral",
                    confidence=0.3,
                    reasoning="Claims are unrelated (neutral)",
                    severity=0.1,
                )
        except Exception as e:
            return self._rule_based_check(claim_a, claim_b, source_a, source_b)
    
    # ========================================================================
    # RULE-BASED DETECTION
    # ========================================================================
    
    def _rule_based_check(self, claim_a: str, claim_b: str,
                          source_a: str, source_b: str) -> ContradictionResult:
        """Rule-based contradiction detection."""
        a_lower = claim_a.lower()
        b_lower = claim_b.lower()
        
        # Check 1: Negation contradiction
        neg_result = self._check_negation_contradiction(a_lower, b_lower)
        if neg_result:
            return ContradictionResult(
                claim_a=claim_a, claim_b=claim_b,
                source_a=source_a, source_b=source_b,
                contradiction_type=ContradictionType.DIRECT,
                confidence=neg_result[0],
                reasoning=neg_result[1],
                severity=neg_result[0] * 0.8,
            )
        
        # Check 2: Antonym contradiction
        ant_result = self._check_antonym_contradiction(a_lower, b_lower)
        if ant_result:
            return ContradictionResult(
                claim_a=claim_a, claim_b=claim_b,
                source_a=source_a, source_b=source_b,
                contradiction_type=ContradictionType.STANCE,
                confidence=ant_result[0],
                reasoning=ant_result[1],
                severity=ant_result[0] * 0.7,
            )
        
        # Check 3: Numeric contradiction
        num_result = self._check_numeric_contradiction(a_lower, b_lower)
        if num_result:
            return ContradictionResult(
                claim_a=claim_a, claim_b=claim_b,
                source_a=source_a, source_b=source_b,
                contradiction_type=ContradictionType.NUMERIC,
                confidence=num_result[0],
                reasoning=num_result[1],
                severity=num_result[0] * 0.6,
            )
        
        # No contradiction found
        return ContradictionResult(
            claim_a=claim_a, claim_b=claim_b,
            source_a=source_a, source_b=source_b,
            contradiction_type="consistent",
            confidence=0.1,
            reasoning="No contradiction detected",
            severity=0.0,
        )
    
    def _check_negation_contradiction(self, a: str, b: str) -> Optional[Tuple[float, str]]:
        """Check if one claim negates the other."""
        for pattern in self.NEGATION_PATTERNS:
            # If A has negation but B doesn't (or vice versa) on same topic
            a_has_neg = bool(re.search(pattern, a))
            b_has_neg = bool(re.search(pattern, b))
            
            if a_has_neg != b_has_neg:
                # Check topic overlap
                a_words = set(re.sub(r'[^\w\s]', '', a).split())
                b_words = set(re.sub(r'[^\w\s]', '', b).split())
                overlap = len(a_words & b_words) / max(min(len(a_words), len(b_words)), 1)
                
                if overlap > 0.3:
                    return (
                        min(1.0, overlap + 0.3),
                        f"Negation detected: one claim negates the other (overlap: {overlap:.0%})"
                    )
        return None
    
    def _check_antonym_contradiction(self, a: str, b: str) -> Optional[Tuple[float, str]]:
        """Check if claims use antonymous language."""
        for word, antonym in self._antonyms_full.items():
            if re.search(r'\b' + word + r'\b', a) and re.search(r'\b' + antonym + r'\b', b):
                return (
                    0.7,
                    f"Antonym contradiction: '{word}' vs '{antonym}'"
                )
        return None
    
    def _check_numeric_contradiction(self, a: str, b: str) -> Optional[Tuple[float, str]]:
        """Check if claims have conflicting numbers for same topic."""
        # Extract numbers
        a_numbers = re.findall(r'(\d+\.?\d*)\s*(%|percent|bps|billion|million)', a)
        b_numbers = re.findall(r'(\d+\.?\d*)\s*(%|percent|bps|billion|million)', b)
        
        if a_numbers and b_numbers:
            for a_num, a_unit in a_numbers:
                for b_num, b_unit in b_numbers:
                    if a_unit == b_unit:
                        try:
                            diff = abs(float(a_num) - float(b_num))
                            avg = (float(a_num) + float(b_num)) / 2
                            if avg > 0 and diff / avg > 0.2:  # >20% difference
                                return (
                                    min(1.0, diff / avg),
                                    f"Numeric disagreement: {a_num}{a_unit} vs {b_num}{b_unit}"
                                )
                        except ValueError:
                            pass
        return None
