"""
NLP Extensions — Categories 3.5, 3.6, 3.8
==========================================
3.5  Aspect-Based Sentiment Analysis (ABSA)  — per-aspect sentiment for
     revenue, guidance, margins, competition, market conditions
3.6  Sarcasm & Irony Detection — detect inverted sentiment in financial text
3.8  Earnings Call Transcript Analysis — tone shift detection, hedging
     language patterns, forward guidance extraction, Q&A vs prepared remarks
"""
import re
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger("cme.nlp_extensions")

# ---------------------------------------------------------------------------
#  3.5  Aspect-Based Sentiment Analysis (ABSA)
# ---------------------------------------------------------------------------

# Financial aspects and their keyword clusters
FINANCIAL_ASPECTS = {
    "revenue": {
        "keywords": [
            "revenue", "sales", "top line", "top-line", "turnover",
            "bookings", "orders", "demand", "growth",
        ],
        "weight": 1.0,
    },
    "guidance": {
        "keywords": [
            "guidance", "outlook", "forecast", "expect", "projection",
            "full-year", "full year", "next quarter", "forward-looking",
            "anticipate", "target",
        ],
        "weight": 1.2,
    },
    "margins": {
        "keywords": [
            "margin", "gross margin", "operating margin", "ebitda",
            "profitability", "cost structure", "efficiency", "expense",
            "opex", "capex", "cost reduction",
        ],
        "weight": 1.0,
    },
    "competition": {
        "keywords": [
            "market share", "competitive", "competitor", "moat",
            "differentiation", "pricing power", "disruption",
        ],
        "weight": 0.8,
    },
    "market_conditions": {
        "keywords": [
            "macro", "interest rate", "inflation", "recession", "demand",
            "consumer", "supply chain", "headwind", "tailwind",
            "economic environment",
        ],
        "weight": 0.7,
    },
    "innovation": {
        "keywords": [
            "r&d", "pipeline", "product launch", "innovation", "patent",
            "technology", "ai", "machine learning", "platform",
        ],
        "weight": 0.6,
    },
    "capital_allocation": {
        "keywords": [
            "buyback", "dividend", "share repurchase", "acquisition",
            "m&a", "balance sheet", "debt", "leverage", "free cash flow",
        ],
        "weight": 0.9,
    },
}

# Sentiment lexicon (finance-tuned)
POSITIVE_WORDS = {
    "beat", "exceeded", "strong", "growth", "improving", "record",
    "upside", "robust", "accelerating", "outperform", "raise",
    "upgrade", "tailwind", "confident", "optimistic", "resilient",
    "expand", "favorable", "uptick", "momentum", "solid",
}
NEGATIVE_WORDS = {
    "miss", "missed", "decline", "declining", "weak", "softening",
    "headwind", "deteriorating", "downside", "risk", "concern",
    "challenging", "pressure", "contraction", "underperform",
    "downgrade", "cut", "slowdown", "uncertain", "disappointing",
    "cautious", "worsen",
}
INTENSIFIERS = {"very", "significantly", "substantially", "extremely", "massive"}
NEGATORS = {"not", "no", "never", "neither", "nor", "n't", "don't", "doesn't",
            "didn't", "wasn't", "weren't", "isn't", "aren't", "hardly", "barely"}


@dataclass
class AspectSentiment:
    aspect: str
    sentiment_score: float  # -1.0 to 1.0
    confidence: float
    evidence_sentences: List[str]
    keyword_hits: List[str]
    weight: float = 1.0

    @property
    def weighted_score(self) -> float:
        return self.sentiment_score * self.weight * self.confidence


class AspectBasedSentimentAnalyzer:
    """
    Extract per-aspect sentiment from financial text.
    Uses window-based keyword detection + lexicon scoring.
    """

    def __init__(self, aspects: Optional[Dict] = None, window_size: int = 50):
        self.aspects = aspects or FINANCIAL_ASPECTS
        self.window = window_size

    def analyze(self, text: str) -> Dict[str, AspectSentiment]:
        """Return per-aspect sentiment for the financial text."""
        text_lower = text.lower()
        sentences = self._split_sentences(text)
        results: Dict[str, AspectSentiment] = {}

        for aspect_name, aspect_cfg in self.aspects.items():
            evidence = []
            keyword_hits = []

            for sent in sentences:
                sent_lower = sent.lower()
                for kw in aspect_cfg["keywords"]:
                    if kw in sent_lower:
                        evidence.append(sent)
                        keyword_hits.append(kw)
                        break

            if not evidence:
                results[aspect_name] = AspectSentiment(
                    aspect=aspect_name, sentiment_score=0.0,
                    confidence=0.0, evidence_sentences=[],
                    keyword_hits=[], weight=aspect_cfg["weight"],
                )
                continue

            sentiment, confidence = self._score_sentences(evidence)
            results[aspect_name] = AspectSentiment(
                aspect=aspect_name,
                sentiment_score=sentiment,
                confidence=confidence,
                evidence_sentences=evidence[:5],
                keyword_hits=list(set(keyword_hits)),
                weight=aspect_cfg["weight"],
            )

        return results

    def get_composite_score(self, results: Dict[str, AspectSentiment]) -> float:
        """Weighted average across all aspects."""
        total_weight = 0.0
        weighted_sum = 0.0
        for asp in results.values():
            if asp.confidence > 0:
                weighted_sum += asp.weighted_score
                total_weight += asp.weight * asp.confidence
        if total_weight == 0:
            return 0.0
        return weighted_sum / total_weight

    def _score_sentences(self, sentences: List[str]) -> Tuple[float, float]:
        """Calculate sentiment and confidence for a set of sentences."""
        all_scores = []
        for sent in sentences:
            tokens = sent.lower().split()
            pos_count = 0
            neg_count = 0
            has_negator = False
            has_intensifier = False

            for i, tok in enumerate(tokens):
                clean = tok.strip(".,;:!?\"'()")
                if clean in NEGATORS:
                    has_negator = True
                if clean in INTENSIFIERS:
                    has_intensifier = True
                if clean in POSITIVE_WORDS:
                    # Check for negation in preceding 3 words
                    window_tokens = [t.strip(".,;:!?\"'()") for t in tokens[max(0, i - 3):i]]
                    if any(w in NEGATORS for w in window_tokens):
                        neg_count += 1
                    else:
                        pos_count += 1
                elif clean in NEGATIVE_WORDS:
                    window_tokens = [t.strip(".,;:!?\"'()") for t in tokens[max(0, i - 3):i]]
                    if any(w in NEGATORS for w in window_tokens):
                        pos_count += 1
                    else:
                        neg_count += 1

            total = pos_count + neg_count
            if total == 0:
                continue
            raw = (pos_count - neg_count) / total
            if has_intensifier:
                raw *= 1.3
            all_scores.append(max(-1, min(1, raw)))

        if not all_scores:
            return 0.0, 0.0

        avg_score = sum(all_scores) / len(all_scores)
        # Confidence: consistency of signal + evidence count
        if len(all_scores) == 1:
            confidence = 0.5
        else:
            variance = sum((s - avg_score) ** 2 for s in all_scores) / len(all_scores)
            consistency = max(0, 1 - math.sqrt(variance))
            evidence_factor = min(1.0, len(all_scores) / 5)
            confidence = 0.5 * consistency + 0.5 * evidence_factor

        return avg_score, confidence

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        parts = re.split(r'(?<=[.!?])\s+', text)
        return [p.strip() for p in parts if len(p.strip()) > 10]


# ---------------------------------------------------------------------------
#  3.6  Sarcasm & Irony Detection
# ---------------------------------------------------------------------------

SARCASM_INDICATORS = [
    r"\byeah right\b", r"\bsure\b.*\bthat'?ll work\b",
    r"\bwhat could (possibly )?go wrong\b",
    r"\b(clearly|obviously|totally)\b.*\b(fine|great|wonderful|perfect)\b",
    r"\bgenius\b", r"\bbrilliant\b",  # often sarcastic in context
    r"\bshocker\b", r"\bsurprise surprise\b",
    r'"[^"]*"',  # air quotes
    r"\b(so|very) (helpful|useful|insightful|reassuring)\b",
    r"\b(another|yet another) (great|brilliant)\b",
]

IRONY_CONTRAST_PAIRS = [
    (POSITIVE_WORDS, NEGATIVE_WORDS),
]


@dataclass
class SarcasmResult:
    is_sarcastic: bool
    sarcasm_probability: float
    detected_patterns: List[str]
    sentiment_inversion: bool
    original_sentiment: float
    adjusted_sentiment: float


class SarcasmIronyDetector:
    """
    Detect sarcasm/irony in financial text and invert sentiment when found.
    
    Approaches:
    1. Pattern matching (sarcastic phrases)
    2. Sentiment-context contrast (positive words in negative context)
    3. Punctuation signals (excessive caps, exclamation marks)
    4. Hyperbole detection
    """

    def __init__(self):
        self._patterns = [re.compile(p, re.IGNORECASE) for p in SARCASM_INDICATORS]

    def detect(self, text: str, context_sentiment: float = 0.0) -> SarcasmResult:
        """
        Analyze text for sarcasm/irony.
        context_sentiment: known sentiment of surrounding text (-1..1)
        """
        scores = []
        detected = []

        # 1. Pattern matching
        for pattern in self._patterns:
            if pattern.search(text):
                detected.append(f"pattern: {pattern.pattern}")
                scores.append(0.6)

        # 2. Punctuation signals
        exclamation_density = text.count("!") / max(1, len(text.split()))
        if exclamation_density > 0.15:
            detected.append("excessive_exclamation")
            scores.append(0.3)

        caps_words = [w for w in text.split() if w.isupper() and len(w) > 2]
        caps_ratio = len(caps_words) / max(1, len(text.split()))
        if caps_ratio > 0.2:
            detected.append("excessive_caps")
            scores.append(0.3)

        # 3. Sentiment-context contrast
        words_lower = set(text.lower().split())
        pos_in_text = words_lower & POSITIVE_WORDS
        neg_in_text = words_lower & NEGATIVE_WORDS

        sentiment_inversion = False
        if pos_in_text and context_sentiment < -0.3:
            detected.append("positive_in_negative_context")
            scores.append(0.5)
            sentiment_inversion = True
        elif neg_in_text and context_sentiment > 0.3 and not pos_in_text:
            detected.append("negative_in_positive_context")
            scores.append(0.4)

        # 4. Quotation marks around positive words (air quotes)
        airquote_pattern = re.compile(r'"(\w+)"')
        airquotes = airquote_pattern.findall(text)
        for aq in airquotes:
            if aq.lower() in POSITIVE_WORDS:
                detected.append(f"airquote_{aq}")
                scores.append(0.6)
                sentiment_inversion = True

        # Calculate probability
        if not scores:
            probability = 0.0
        else:
            # Combine evidence (noisy-OR)
            prob_not_sarcasm = 1.0
            for s in scores:
                prob_not_sarcasm *= (1 - s)
            probability = 1 - prob_not_sarcasm

        is_sarcastic = probability > 0.45

        # Calculate adjusted sentiment
        original_sent = self._quick_sentiment(text)
        adjusted_sent = -original_sent * 0.7 if is_sarcastic and sentiment_inversion else original_sent

        return SarcasmResult(
            is_sarcastic=is_sarcastic,
            sarcasm_probability=round(probability, 3),
            detected_patterns=detected,
            sentiment_inversion=sentiment_inversion,
            original_sentiment=round(original_sent, 3),
            adjusted_sentiment=round(adjusted_sent, 3),
        )

    @staticmethod
    def _quick_sentiment(text: str) -> float:
        words = set(text.lower().split())
        pos = len(words & POSITIVE_WORDS)
        neg = len(words & NEGATIVE_WORDS)
        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total


# ---------------------------------------------------------------------------
#  3.8  Earnings Call Transcript Analysis
# ---------------------------------------------------------------------------

HEDGING_PHRASES = [
    r"\b(we believe|we think)\b",
    r"\b(may|might|could|possibly|potentially)\b",
    r"\b(to some extent|somewhat|relatively)\b",
    r"\b(it depends|depends on|subject to)\b",
    r"\b(uncertain|uncertainty|unclear)\b",
    r"\b(cautiously optimistic)\b",
    r"\b(going forward|at this time|at this point)\b",
    r"\b(we'?re not in a position to)\b",
    r"\b(we'?ll have to see|remains to be seen)\b",
    r"\b(challenging environment|headwinds)\b",
]

FORWARD_GUIDANCE_PATTERNS = [
    r"\b(guidance|expect|forecast|outlook|target|plan|project) (for|of|is|at|to be)\b",
    r"\b(next quarter|next year|full[- ]year|fiscal \d{4})\b",
    r"\b(we (expect|anticipate|project|target|plan))\b",
    r"\b(revenue (guidance|outlook|expectation))\b",
    r"\b(eps (guidance|outlook|range))\b",
    r"\b(between \$[\d.]+ and \$[\d.]+)\b",
    r"\b(approximately \$[\d.]+)\b",
    r"\b(raise|lower|reiterate|maintain|narrow)\b.*\b(guidance|outlook|range)\b",
]


@dataclass
class EarningsCallSection:
    section_type: str  # "prepared_remarks" | "qa"
    speaker: str
    text: str
    sentiment_score: float
    hedging_density: float
    forward_guidance_count: int


@dataclass
class ToneShift:
    from_section: str
    to_section: str
    sentiment_delta: float
    hedging_delta: float
    interpretation: str


@dataclass
class EarningsCallAnalysis:
    overall_sentiment: float
    prepared_remarks_sentiment: float
    qa_sentiment: float
    tone_shift: Optional[ToneShift]
    hedging_score: float  # 0-1
    hedging_phrases_found: List[str]
    forward_guidance: List[Dict[str, str]]
    guidance_direction: str  # "raised" | "lowered" | "maintained" | "unclear"
    key_metrics_mentioned: Dict[str, float]
    speaker_sentiments: Dict[str, float]
    risk_signals: List[str]
    sections: List[EarningsCallSection]


class EarningsCallAnalyzer:
    """
    Analyze earnings call transcripts for:
    - Tone shifts between prepared remarks vs Q&A
    - Hedging language density (management uncertainty)
    - Forward guidance extraction and direction
    - Per-speaker sentiment tracking
    """

    SECTION_SEPARATORS = [
        r"(?i)(operator|moderator)[:\s]",
        r"(?i)question[- ]and[- ]answer",
        r"(?i)q\s*&\s*a\s*(session|portion|segment)?",
        r"(?i)opening remarks",
        r"(?i)prepared remarks",
        r"(?i)closing remarks",
    ]

    def __init__(self):
        self._hedging_patterns = [re.compile(p, re.IGNORECASE) for p in HEDGING_PHRASES]
        self._guidance_patterns = [re.compile(p, re.IGNORECASE) for p in FORWARD_GUIDANCE_PATTERNS]
        self._absa = AspectBasedSentimentAnalyzer()

    def analyze_transcript(self, transcript: str) -> EarningsCallAnalysis:
        """Full analysis of an earnings call transcript."""
        # Split into prepared remarks + Q&A
        prepared, qa = self._split_prepared_qa(transcript)

        # Section-level analysis
        prepared_sections = self._analyze_section(prepared, "prepared_remarks")
        qa_sections = self._analyze_section(qa, "qa")

        # Overall metrics
        prep_sent = self._section_avg_sentiment(prepared_sections) if prepared_sections else 0
        qa_sent = self._section_avg_sentiment(qa_sections) if qa_sections else 0
        overall_sent = (prep_sent + qa_sent) / 2

        # Tone shift detection
        tone_shift = None
        if prepared_sections and qa_sections:
            sent_delta = qa_sent - prep_sent
            hedging_prep = self._avg_hedging(prepared_sections)
            hedging_qa = self._avg_hedging(qa_sections)
            hedge_delta = hedging_qa - hedging_prep

            if abs(sent_delta) > 0.15 or abs(hedge_delta) > 0.1:
                if sent_delta < -0.15:
                    interp = "Management more cautious in Q&A than prepared remarks — potential hidden concerns"
                elif sent_delta > 0.15:
                    interp = "Management more positive in Q&A — responding well to scrutiny"
                elif hedge_delta > 0.1:
                    interp = "Hedging language increases in Q&A — management uncertain on specifics"
                else:
                    interp = "Minor tone shift between sections"

                tone_shift = ToneShift(
                    from_section="prepared_remarks",
                    to_section="qa",
                    sentiment_delta=round(sent_delta, 3),
                    hedging_delta=round(hedge_delta, 3),
                    interpretation=interp,
                )

        # Hedging analysis
        all_text = transcript
        hedging_hits = self._detect_hedging(all_text)
        hedging_score = min(1.0, len(hedging_hits) / max(1, len(transcript.split()) / 100))

        # Forward guidance extraction
        guidance_items = self._extract_guidance(all_text)
        guidance_dir = self._determine_guidance_direction(all_text)

        # Per-speaker sentiment
        speakers = self._extract_speakers(transcript)

        # Risk signals
        risks = self._detect_risk_signals(all_text)

        # Key metrics via ABSA
        absa_results = self._absa.analyze(all_text)
        key_metrics = {name: asp.sentiment_score for name, asp in absa_results.items()
                       if asp.confidence > 0.2}

        return EarningsCallAnalysis(
            overall_sentiment=round(overall_sent, 3),
            prepared_remarks_sentiment=round(prep_sent, 3),
            qa_sentiment=round(qa_sent, 3),
            tone_shift=tone_shift,
            hedging_score=round(hedging_score, 3),
            hedging_phrases_found=hedging_hits[:20],
            forward_guidance=guidance_items,
            guidance_direction=guidance_dir,
            key_metrics_mentioned=key_metrics,
            speaker_sentiments=speakers,
            risk_signals=risks,
            sections=prepared_sections + qa_sections,
        )

    def _split_prepared_qa(self, transcript: str) -> Tuple[str, str]:
        """Split transcript into prepared remarks and Q&A sections."""
        qa_patterns = [
            r"(?i)question[- ]and[- ]answer",
            r"(?i)q\s*&\s*a\s*(session|portion|segment)?",
            r"(?i)(now|let'?s)\s*(open|turn|move)\s*(it\s*)?(up\s*)?(for|to)\s*questions?",
        ]
        for pattern in qa_patterns:
            match = re.search(pattern, transcript)
            if match:
                return transcript[:match.start()], transcript[match.start():]
        # If no clear split, use 60/40 heuristic
        split_point = int(len(transcript) * 0.6)
        return transcript[:split_point], transcript[split_point:]

    def _analyze_section(self, text: str, section_type: str) -> List[EarningsCallSection]:
        """Analyze a section of the transcript."""
        if not text.strip():
            return []
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 10]
        if not sentences:
            return []

        # Group into chunks of ~5 sentences
        chunks = []
        for i in range(0, len(sentences), 5):
            chunk_text = " ".join(sentences[i:i + 5])
            hedging = len(self._detect_hedging(chunk_text))
            word_count = len(chunk_text.split())
            hedging_density = hedging / max(1, word_count / 20)

            guidance_count = sum(1 for p in self._guidance_patterns if p.search(chunk_text))

            # Sentiment
            words = set(chunk_text.lower().split())
            pos = len(words & POSITIVE_WORDS)
            neg = len(words & NEGATIVE_WORDS)
            total = pos + neg
            sent = (pos - neg) / max(1, total)

            chunks.append(EarningsCallSection(
                section_type=section_type,
                speaker="",
                text=chunk_text[:200],
                sentiment_score=round(sent, 3),
                hedging_density=round(min(1.0, hedging_density), 3),
                forward_guidance_count=guidance_count,
            ))

        return chunks

    def _detect_hedging(self, text: str) -> List[str]:
        """Find hedging language in text."""
        hits = []
        for pattern in self._hedging_patterns:
            matches = pattern.findall(text)
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0]
                hits.append(m.lower())
        return hits

    def _extract_guidance(self, text: str) -> List[Dict[str, str]]:
        """Extract forward guidance statements."""
        guidance = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for sent in sentences:
            for pattern in self._guidance_patterns:
                if pattern.search(sent):
                    # Extract any numerical values
                    numbers = re.findall(r'\$[\d,.]+[BMK]?|\d+\.?\d*%', sent)
                    guidance.append({
                        "statement": sent.strip()[:300],
                        "numerical_values": numbers,
                        "type": "forward_guidance",
                    })
                    break
        return guidance[:15]

    def _determine_guidance_direction(self, text: str) -> str:
        """Determine if guidance was raised, lowered, or maintained."""
        text_lower = text.lower()
        raise_signals = ["raise", "raised", "increase", "increased", "higher",
                         "above prior", "upward revision", "beat"]
        lower_signals = ["lower", "lowered", "reduce", "reduced", "cut",
                         "below prior", "downward revision", "miss"]
        maintain_signals = ["reiterate", "reaffirm", "maintain", "unchanged",
                            "consistent with prior"]

        raise_count = sum(1 for w in raise_signals if w in text_lower)
        lower_count = sum(1 for w in lower_signals if w in text_lower)
        maintain_count = sum(1 for w in maintain_signals if w in text_lower)

        if raise_count > lower_count and raise_count > maintain_count:
            return "raised"
        elif lower_count > raise_count and lower_count > maintain_count:
            return "lowered"
        elif maintain_count > 0:
            return "maintained"
        return "unclear"

    def _extract_speakers(self, transcript: str) -> Dict[str, float]:
        """Extract per-speaker sentiment."""
        speaker_pattern = re.compile(r'^([A-Z][a-z]+ [A-Z][a-z]+)\s*[-–:]\s*(.+)', re.MULTILINE)
        speaker_texts: Dict[str, List[str]] = defaultdict(list)

        for match in speaker_pattern.finditer(transcript):
            name = match.group(1)
            text = match.group(2)
            speaker_texts[name].append(text)

        results = {}
        for speaker, texts in speaker_texts.items():
            combined = " ".join(texts)
            words = set(combined.lower().split())
            pos = len(words & POSITIVE_WORDS)
            neg = len(words & NEGATIVE_WORDS)
            total = pos + neg
            results[speaker] = round((pos - neg) / max(1, total), 3)

        return results

    def _detect_risk_signals(self, text: str) -> List[str]:
        """Identify risk-related statements."""
        risk_patterns = [
            (r"(?i)material weakness", "material_weakness"),
            (r"(?i)restat(e|ed|ement)", "restatement"),
            (r"(?i)going concern", "going_concern"),
            (r"(?i)sec (investigation|inquiry|subpoena)", "sec_investigation"),
            (r"(?i)class action|lawsuit|litigation", "litigation"),
            (r"(?i)covenant (breach|violation)", "covenant_breach"),
            (r"(?i)impairment|write[- ]?down", "impairment"),
            (r"(?i)departure.{0,30}(ceo|cfo|cto|officer)", "executive_departure"),
            (r"(?i)supply chain (disruption|issue|challenge)", "supply_chain_risk"),
            (r"(?i)cybersecurity (incident|breach|attack)", "cybersecurity"),
        ]
        signals = []
        for pattern, name in risk_patterns:
            if re.search(pattern, text):
                signals.append(name)
        return signals

    @staticmethod
    def _section_avg_sentiment(sections: List[EarningsCallSection]) -> float:
        if not sections:
            return 0.0
        return sum(s.sentiment_score for s in sections) / len(sections)

    @staticmethod
    def _avg_hedging(sections: List[EarningsCallSection]) -> float:
        if not sections:
            return 0.0
        return sum(s.hedging_density for s in sections) / len(sections)
