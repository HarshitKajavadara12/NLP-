"""
DEEP NLP PARSER — Replaces regex-based news parsing

Uses spaCy for:
- Sentence segmentation, tokenization
- Dependency parsing (subject-verb-object extraction)
- Part-of-speech tagging
- Linguistic feature extraction

Uses Transformers for:
- Contextual embeddings (sentence meaning)
- Zero-shot classification (narrative type)
- Semantic similarity (for deduplication)

Falls back to rule-based parsing if models unavailable.
"""

import re
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Graceful imports
try:
    import spacy
    from spacy.tokens import Doc, Span
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class SemanticRole(str, Enum):
    """Semantic roles in a clause."""
    AGENT = "agent"           # Who does the action
    ACTION = "action"         # What is done
    PATIENT = "patient"       # What is affected
    INSTRUMENT = "instrument" # By what means
    LOCATION = "location"     # Where
    TEMPORAL = "temporal"     # When
    CAUSE = "cause"           # Why
    CONDITION = "condition"   # Under what condition


class NarrativeIntent(str, Enum):
    """Detected intent behind the news."""
    INFORM = "inform"
    WARN = "warn"
    REASSURE = "reassure"
    DEFLECT = "deflect"
    SIGNAL_POLICY = "signal_policy"
    MARKET_MOVE = "market_move"
    CRISIS_MANAGE = "crisis_manage"
    PROPAGANDA = "propaganda"
    LEAK = "leak"
    TRIAL_BALLOON = "trial_balloon"


@dataclass
class SemanticTriple:
    """Subject-Predicate-Object triple with confidence."""
    subject: str
    predicate: str
    object_: str
    confidence: float = 0.0
    source_text: str = ""
    negated: bool = False
    conditional: bool = False
    modality: str = "declarative"  # declarative, possible, necessary, hypothetical


@dataclass
class EntityMention:
    """Named entity with context."""
    text: str
    label: str          # PERSON, ORG, GPE, MONEY, DATE, EVENT, LAW, etc.
    start: int
    end: int
    confidence: float = 0.0
    linked_id: str = ""  # Wikidata/knowledge base ID
    context: str = ""    # Surrounding text


@dataclass
class SentenceAnalysis:
    """Deep analysis of a single sentence."""
    text: str
    index: int
    
    # Linguistic
    tokens: List[str] = field(default_factory=list)
    pos_tags: List[str] = field(default_factory=list)
    dependencies: List[Tuple[str, str, str]] = field(default_factory=list)
    
    # Semantic
    triples: List[SemanticTriple] = field(default_factory=list)
    entities: List[EntityMention] = field(default_factory=list)
    
    # Properties
    is_conditional: bool = False
    is_negated: bool = False
    is_question: bool = False
    is_quotation: bool = False
    tense: str = "present"
    voice: str = "active"
    
    # Embedding
    embedding: Optional[List[float]] = None
    
    # Uncertainty
    certainty_score: float = 0.5  # 0=very uncertain, 1=very certain
    hedging_words: List[str] = field(default_factory=list)
    boosting_words: List[str] = field(default_factory=list)


@dataclass
class DeepParseResult:
    """Complete deep NLP parse of a news article."""
    raw_text: str
    text_hash: str
    timestamp: datetime
    
    # Sentence-level analysis
    sentences: List[SentenceAnalysis] = field(default_factory=list)
    
    # Document-level
    all_entities: List[EntityMention] = field(default_factory=list)
    all_triples: List[SemanticTriple] = field(default_factory=list)
    
    # Classifications
    narrative_types: List[Tuple[str, float]] = field(default_factory=list)
    detected_intent: NarrativeIntent = NarrativeIntent.INFORM
    intent_confidence: float = 0.0
    
    # Document properties
    overall_certainty: float = 0.5
    overall_subjectivity: float = 0.5
    complexity_score: float = 0.5
    
    # Key phrases
    key_phrases: List[str] = field(default_factory=list)
    
    # Embedding
    document_embedding: Optional[List[float]] = None
    
    # Metadata
    language: str = "en"
    word_count: int = 0
    parse_method: str = "unknown"  # "spacy+transformers", "spacy", "fallback"


# ============================================================================
# DEEP NLP PARSER
# ============================================================================

class DeepNLPParser:
    """
    Production NLP parser using spaCy + Transformers.
    
    Capabilities:
    1. Deep linguistic analysis (syntax, semantics, pragmatics)
    2. Named entity recognition with linking
    3. Semantic triple extraction (who did what to whom)
    4. Narrative classification (what type of news)
    5. Certainty/hedging detection
    6. Document and sentence embeddings
    7. Zero-shot topic classification
    
    Falls back to rule-based parsing if models unavailable.
    """
    
    # Hedging language (reduces certainty)
    HEDGE_WORDS = {
        "may", "might", "could", "can", "possibly", "perhaps", "probably",
        "reportedly", "allegedly", "apparently", "seemingly", "suggests",
        "indicates", "appears", "likely", "unlikely", "potential",
        "expected", "anticipated", "estimated", "projected", "forecast",
        "if", "unless", "whether", "uncertain", "unclear", "ambiguous"
    }
    
    # Boosting language (increases certainty)
    BOOST_WORDS = {
        "confirmed", "announced", "declared", "stated", "will", "shall",
        "must", "definitely", "certainly", "absolutely", "official",
        "unanimous", "decisive", "unequivocal", "undeniable", "proven",
        "guaranteed", "committed", "mandated", "enacted", "signed"
    }
    
    # Narrative type keywords for zero-shot classification
    NARRATIVE_LABELS = [
        "monetary policy and central banking",
        "economic growth and recession",
        "geopolitical conflict and diplomacy",
        "corporate earnings and business",
        "financial crisis and systemic risk",
        "regulatory and legal action",
        "technology and innovation",
        "trade and tariffs",
        "inflation and prices",
        "employment and labor market",
        "energy and commodities",
        "real estate and housing",
    ]
    
    def __init__(self, 
                 spacy_model: str = "en_core_web_sm",
                 use_transformers: bool = True,
                 device: str = "cpu"):
        """
        Initialize the deep NLP parser.
        
        Args:
            spacy_model: spaCy model to load (en_core_web_sm, en_core_web_trf)
            use_transformers: Whether to use transformer models
            device: Device for transformers ("cpu" or "cuda")
        """
        self.device = device
        self.nlp = None
        self.zero_shot_classifier = None
        self.embedding_model = None
        self.ner_pipeline = None
        self.parse_method = "fallback"
        
        # Load spaCy
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(spacy_model)
                self.parse_method = "spacy"
                print(f"[NLP] spaCy loaded: {spacy_model}")
            except OSError:
                try:
                    # Try downloading
                    spacy.cli.download(spacy_model)
                    self.nlp = spacy.load(spacy_model)
                    self.parse_method = "spacy"
                    print(f"[NLP] spaCy downloaded and loaded: {spacy_model}")
                except Exception as e:
                    print(f"[NLP] spaCy unavailable: {e}. Using fallback.")
        
        # Load Transformers
        if use_transformers and TRANSFORMERS_AVAILABLE:
            try:
                # Zero-shot classification for narrative types
                self.zero_shot_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1 if device == "cpu" else 0
                )
                self.parse_method = "spacy+transformers" if self.nlp else "transformers"
                print("[NLP] Zero-shot classifier loaded")
            except Exception as e:
                print(f"[NLP] Zero-shot classifier unavailable: {e}")
            
            try:
                # Sentence embeddings
                self.embedding_model = pipeline(
                    "feature-extraction",
                    model="sentence-transformers/all-MiniLM-L6-v2",
                    device=-1 if device == "cpu" else 0
                )
                print("[NLP] Embedding model loaded")
            except Exception as e:
                print(f"[NLP] Embedding model unavailable: {e}")
        
        print(f"[NLP] Parser ready. Method: {self.parse_method}")
    
    # ========================================================================
    # MAIN PARSE METHOD
    # ========================================================================
    
    def parse(self, text: str, source: str = "", timestamp: datetime = None) -> DeepParseResult:
        """
        Perform deep NLP parsing on raw text.
        
        Args:
            text: Raw news text
            source: News source identifier
            timestamp: When news was published
        
        Returns:
            DeepParseResult with full linguistic analysis
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        result = DeepParseResult(
            raw_text=text,
            text_hash=text_hash,
            timestamp=timestamp,
            word_count=len(text.split()),
            parse_method=self.parse_method,
        )
        
        # Step 1: Sentence-level analysis
        if self.nlp:
            self._spacy_parse(text, result)
        else:
            self._fallback_parse(text, result)
        
        # Step 2: Narrative classification
        self._classify_narrative(text, result)
        
        # Step 3: Intent detection
        self._detect_intent(text, result)
        
        # Step 4: Document-level metrics
        self._compute_document_metrics(result)
        
        # Step 5: Key phrase extraction
        self._extract_key_phrases(result)
        
        # Step 6: Embeddings (if available)
        self._compute_embeddings(text, result)
        
        return result
    
    # ========================================================================
    # SPACY PARSING
    # ========================================================================
    
    def _spacy_parse(self, text: str, result: DeepParseResult):
        """Parse using spaCy for deep linguistic analysis."""
        doc = self.nlp(text)
        
        for sent_idx, sent in enumerate(doc.sents):
            analysis = SentenceAnalysis(
                text=sent.text.strip(),
                index=sent_idx,
            )
            
            # Tokenization and POS
            analysis.tokens = [token.text for token in sent]
            analysis.pos_tags = [token.pos_ for token in sent]
            
            # Dependencies
            analysis.dependencies = [
                (token.text, token.dep_, token.head.text)
                for token in sent
            ]
            
            # Named entities in sentence
            for ent in sent.ents:
                entity = EntityMention(
                    text=ent.text,
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.85,
                    context=sent.text,
                )
                analysis.entities.append(entity)
                result.all_entities.append(entity)
            
            # Extract semantic triples (SVO)
            triples = self._extract_svo_triples(sent)
            analysis.triples = triples
            result.all_triples.extend(triples)
            
            # Detect properties
            sent_lower = sent.text.lower()
            analysis.is_conditional = any(
                tok.text.lower() in ("if", "unless", "provided", "assuming", "whether")
                for tok in sent
            )
            analysis.is_negated = any(
                tok.dep_ == "neg" for tok in sent
            )
            analysis.is_question = sent.text.strip().endswith("?")
            analysis.is_quotation = '"' in sent.text or "'" in sent.text
            
            # Tense detection
            analysis.tense = self._detect_tense(sent)
            analysis.voice = self._detect_voice(sent)
            
            # Certainty scoring
            hedge_found = [w for w in self.HEDGE_WORDS if w in sent_lower]
            boost_found = [w for w in self.BOOST_WORDS if w in sent_lower]
            analysis.hedging_words = hedge_found
            analysis.boosting_words = boost_found
            
            hedge_score = len(hedge_found) * 0.15
            boost_score = len(boost_found) * 0.15
            analysis.certainty_score = max(0.0, min(1.0, 0.5 - hedge_score + boost_score))
            
            result.sentences.append(analysis)
    
    def _extract_svo_triples(self, sent) -> List[SemanticTriple]:
        """Extract Subject-Verb-Object triples from a spaCy sentence.
        
        Enhanced to handle:
        - Coordinated subjects/objects (A and B announced...)
        - Clausal complements (said that X would Y)
        - Indirect objects (gave X to Y)
        - Non-root verbs with their own subjects
        """
        triples = []
        
        for token in sent:
            if token.pos_ == "VERB":
                # Find subjects — include coordinated subjects (conj)
                direct_subjects = [
                    child for child in token.children
                    if child.dep_ in ("nsubj", "nsubjpass", "agent")
                ]
                subjects = []
                for subj in direct_subjects:
                    subjects.append(subj)
                    # Add coordinated subjects: "A and B announced"
                    for conj in subj.children:
                        if conj.dep_ == "conj":
                            subjects.append(conj)
                
                # Find objects — include coordinated objects and indirect objects
                direct_objects = [
                    child for child in token.children
                    if child.dep_ in ("dobj", "pobj", "attr", "oprd", "dative")
                ]
                objects = []
                for obj in direct_objects:
                    objects.append(obj)
                    # Add coordinated objects: "announced X, Y, and Z"
                    for conj in obj.children:
                        if conj.dep_ == "conj":
                            objects.append(conj)
                
                # Also find prepositional objects ("gave X to Y")
                for child in token.children:
                    if child.dep_ == "prep":
                        for pobj in child.children:
                            if pobj.dep_ == "pobj":
                                objects.append(pobj)
                
                # Find clausal complements ("said that X would Y")
                for child in token.children:
                    if child.dep_ in ("ccomp", "xcomp"):
                        # Recursively extract from the complement clause
                        sub_triples = self._extract_svo_triples_from_token(child)
                        triples.extend(sub_triples)
                
                # Check for negation
                negated = any(child.dep_ == "neg" for child in token.children)
                
                # Check for modality
                modals = [
                    child.text.lower() for child in token.children
                    if child.dep_ == "aux" and child.text.lower() in (
                        "may", "might", "could", "would", "should", "can"
                    )
                ]
                modality = "possible" if modals else "declarative"
                
                # Check for conditional
                conditional = any(
                    child.text.lower() in ("if", "unless", "whether")
                    for child in token.children
                    if child.dep_ == "mark"
                )
                
                for subj in subjects:
                    subj_text = self._get_full_phrase(subj)
                    for obj in objects:
                        obj_text = self._get_full_phrase(obj)
                        # Compute confidence based on parse quality
                        conf = 0.85 if token.dep_ == "ROOT" else 0.65
                        if any(child.dep_ == "neg" for child in token.children):
                            conf *= 0.9  # Slightly lower for negated
                        triple = SemanticTriple(
                            subject=subj_text,
                            predicate=token.lemma_,
                            object_=obj_text,
                            confidence=conf,
                            source_text=sent.text,
                            negated=any(child.dep_ == "neg" for child in token.children),
                            conditional=any(
                                child.text.lower() in ("if", "unless", "whether")
                                for child in token.children
                                if child.dep_ == "mark"
                            ),
                            modality="possible" if any(
                                child.text.lower() in ("may", "might", "could", "would", "should", "can")
                                for child in token.children if child.dep_ == "aux"
                            ) else "declarative",
                        )
                        triples.append(triple)
                    
                    # If no objects found, use the verb itself
                    if not objects:
                        triple = SemanticTriple(
                            subject=subj_text,
                            predicate=token.lemma_,
                            object_="[intransitive]",
                            confidence=0.5,
                            source_text=sent.text,
                            negated=any(child.dep_ == "neg" for child in token.children),
                            conditional=any(
                                child.text.lower() in ("if", "unless", "whether")
                                for child in token.children
                                if child.dep_ == "mark"
                            ),
                            modality="possible" if any(
                                child.text.lower() in ("may", "might", "could", "would", "should", "can")
                                for child in token.children if child.dep_ == "aux"
                            ) else "declarative",
                        )
                        triples.append(triple)
        
        return triples
    
    def _extract_svo_triples_from_token(self, verb_token) -> List[SemanticTriple]:
        """Extract SVO triples from a specific verb token (for clausal complements)."""
        triples = []
        subjects = [
            child for child in verb_token.children
            if child.dep_ in ("nsubj", "nsubjpass", "agent")
        ]
        objects = [
            child for child in verb_token.children
            if child.dep_ in ("dobj", "pobj", "attr", "oprd")
        ]
        negated = any(child.dep_ == "neg" for child in verb_token.children)
        
        for subj in subjects:
            subj_text = self._get_full_phrase(subj)
            for obj in objects:
                obj_text = self._get_full_phrase(obj)
                triples.append(SemanticTriple(
                    subject=subj_text,
                    predicate=verb_token.lemma_,
                    object_=obj_text,
                    confidence=0.60,  # Lower confidence for complement clauses
                    source_text=verb_token.sent.text,
                    negated=negated,
                    conditional=False,
                    modality="declarative",
                ))
        return triples
    
    def _get_full_phrase(self, token) -> str:
        """Get the full noun phrase for a token."""
        subtree = list(token.subtree)
        return " ".join(t.text for t in sorted(subtree, key=lambda x: x.i))
    
    def _detect_tense(self, sent) -> str:
        """Detect the dominant tense of a sentence."""
        for token in sent:
            if token.pos_ == "VERB":
                if token.tag_ in ("VBD", "VBN"):
                    return "past"
                elif token.tag_ in ("VBZ", "VBP", "VBG"):
                    return "present"
                elif token.tag_ == "MD":
                    return "future"
        return "present"
    
    def _detect_voice(self, sent) -> str:
        """Detect active vs passive voice."""
        for token in sent:
            if token.dep_ == "nsubjpass":
                return "passive"
        return "active"
    
    # ========================================================================
    # FALLBACK PARSING (when spaCy unavailable)
    # ========================================================================
    
    def _fallback_parse(self, text: str, result: DeepParseResult):
        """Rule-based fallback parsing without spaCy."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for idx, sent_text in enumerate(sentences):
            sent_text = sent_text.strip()
            if not sent_text:
                continue
            
            analysis = SentenceAnalysis(
                text=sent_text,
                index=idx,
                tokens=sent_text.split(),
                pos_tags=["UNK"] * len(sent_text.split()),
            )
            
            sent_lower = sent_text.lower()
            
            # Basic property detection
            analysis.is_conditional = any(
                w in sent_lower for w in ["if ", "unless ", "provided ", "assuming "]
            )
            analysis.is_negated = any(
                w in sent_lower for w in [" not ", " no ", " never ", "n't "]
            )
            analysis.is_question = sent_text.endswith("?")
            
            # Basic entity extraction via patterns
            entities = self._fallback_entity_extraction(sent_text)
            analysis.entities = entities
            result.all_entities.extend(entities)
            
            # Certainty scoring
            hedge_found = [w for w in self.HEDGE_WORDS if re.search(r'\b' + w + r'\b', sent_lower)]
            boost_found = [w for w in self.BOOST_WORDS if re.search(r'\b' + w + r'\b', sent_lower)]
            analysis.hedging_words = hedge_found
            analysis.boosting_words = boost_found
            analysis.certainty_score = max(0.0, min(1.0, 
                0.5 - len(hedge_found) * 0.15 + len(boost_found) * 0.15
            ))
            
            result.sentences.append(analysis)
    
    def _fallback_entity_extraction(self, text: str) -> List[EntityMention]:
        """Basic entity extraction using patterns."""
        entities = []
        
        # Organization patterns
        org_patterns = [
            (r'\b(Federal Reserve|Fed|ECB|BOJ|BOE|PBOC|RBI|IMF|World Bank)\b', "ORG"),
            (r'\b(SEC|CFTC|FDIC|OCC|FINRA|FSB|BIS)\b', "ORG"),
            (r'\b(Goldman Sachs|JPMorgan|Morgan Stanley|Citigroup|HSBC|Deutsche Bank)\b', "ORG"),
            (r'\b(Apple|Google|Microsoft|Amazon|Meta|Tesla|NVIDIA|OpenAI)\b', "ORG"),
            (r'\b(NATO|UN|EU|OPEC|G7|G20|BRICS)\b', "ORG"),
        ]
        
        # Person title patterns (simplified)
        person_patterns = [
            (r'\b(Chairman|Chair|President|CEO|CFO|Governor|Secretary|Minister)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', "PERSON"),
        ]
        
        # Currency/Money patterns
        money_patterns = [
            (r'\$[\d,.]+\s*(?:billion|million|trillion|B|M|T)\b', "MONEY"),
            (r'[\d,.]+\s*(?:percent|%|basis points|bps)\b', "PERCENT"),
        ]
        
        # Geopolitical
        geo_patterns = [
            (r'\b(United States|China|Russia|Japan|Germany|UK|India|Brazil|EU|Europe)\b', "GPE"),
        ]
        
        all_patterns = org_patterns + money_patterns + geo_patterns
        
        for pattern, label in all_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(EntityMention(
                    text=match.group(0),
                    label=label,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.7,
                    context=text,
                ))
        
        # Person patterns (special handling)
        for pattern, label in person_patterns:
            for match in re.finditer(pattern, text):
                entities.append(EntityMention(
                    text=match.group(0),
                    label=label,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.6,
                    context=text,
                ))
        
        return entities
    
    # ========================================================================
    # NARRATIVE CLASSIFICATION
    # ========================================================================
    
    def _classify_narrative(self, text: str, result: DeepParseResult):
        """Classify the narrative type using zero-shot classification or rules."""
        
        if self.zero_shot_classifier:
            try:
                classification = self.zero_shot_classifier(
                    text[:2048],  # ~512 tokens ≈ ~2048 chars (BART tokenizer limit)
                    candidate_labels=self.NARRATIVE_LABELS,
                    multi_label=True,
                )
                result.narrative_types = list(zip(
                    classification["labels"],
                    classification["scores"]
                ))
                return
            except Exception:
                pass
        
        # Fallback: keyword-based classification
        text_lower = text.lower()
        scores = []
        
        keyword_map = {
            "monetary policy and central banking": [
                "fed", "rate", "monetary", "central bank", "ecb", "boj",
                "hawkish", "dovish", "taper", "quantitative", "reserve"
            ],
            "economic growth and recession": [
                "gdp", "growth", "recession", "slowdown", "expansion",
                "economic", "output", "productivity"
            ],
            "geopolitical conflict and diplomacy": [
                "war", "conflict", "sanctions", "treaty", "diplomacy",
                "military", "tension", "alliance", "invasion"
            ],
            "corporate earnings and business": [
                "earnings", "revenue", "profit", "guidance", "quarterly",
                "CEO", "company", "shares", "stock"
            ],
            "financial crisis and systemic risk": [
                "crisis", "collapse", "contagion", "systemic", "default",
                "bankruptcy", "bailout", "panic", "crash"
            ],
            "regulatory and legal action": [
                "regulation", "SEC", "lawsuit", "fine", "compliance",
                "enforcement", "antitrust", "investigation"
            ],
            "technology and innovation": [
                "AI", "technology", "innovation", "digital", "crypto",
                "blockchain", "quantum", "cybersecurity"
            ],
            "trade and tariffs": [
                "tariff", "trade", "import", "export", "customs",
                "supply chain", "trade war", "protectionism"
            ],
            "inflation and prices": [
                "inflation", "CPI", "prices", "deflation", "cost",
                "purchasing power", "consumer prices"
            ],
            "employment and labor market": [
                "jobs", "unemployment", "labor", "hiring", "payroll",
                "workforce", "wages", "employment"
            ],
            "energy and commodities": [
                "oil", "gas", "energy", "commodity", "OPEC", "crude",
                "renewable", "mining", "gold"
            ],
            "real estate and housing": [
                "housing", "real estate", "mortgage", "property",
                "construction", "home sales", "rent"
            ],
        }
        
        for label, keywords in keyword_map.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            normalized = min(1.0, score / max(len(keywords) * 0.3, 1))
            if normalized > 0.1:
                scores.append((label, normalized))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        result.narrative_types = scores[:5]
    
    # ========================================================================
    # INTENT DETECTION
    # ========================================================================
    
    def _detect_intent(self, text: str, result: DeepParseResult):
        """Detect the underlying intent of the news article."""
        text_lower = text.lower()
        
        intent_signals = {
            NarrativeIntent.WARN: [
                "warns", "warning", "caution", "risk", "danger",
                "threat", "vulnerable", "concerns", "alarming"
            ],
            NarrativeIntent.REASSURE: [
                "stable", "confidence", "resilient", "strong",
                "recovery", "improving", "optimistic", "robust"
            ],
            NarrativeIntent.SIGNAL_POLICY: [
                "considering", "exploring", "reviewing", "assessing",
                "evaluating", "weighing options", "deliberating"
            ],
            NarrativeIntent.CRISIS_MANAGE: [
                "emergency", "unprecedented", "intervention", "bailout",
                "extraordinary measures", "crisis response"
            ],
            NarrativeIntent.DEFLECT: [
                "blame", "attributed to", "external factors",
                "beyond control", "inherited", "previously"
            ],
            NarrativeIntent.TRIAL_BALLOON: [
                "sources say", "reportedly", "considering",
                "unnamed officials", "floating", "gauging reaction"
            ],
            NarrativeIntent.LEAK: [
                "leaked", "confidential", "internal document",
                "whistleblower", "exclusive", "obtained by"
            ],
            NarrativeIntent.PROPAGANDA: [
                "historic achievement", "unprecedented success",
                "revolutionary", "world-leading", "best ever"
            ],
        }
        
        best_intent = NarrativeIntent.INFORM
        best_score = 0.0
        
        for intent, keywords in intent_signals.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            normalized = score / len(keywords)
            if normalized > best_score:
                best_score = normalized
                best_intent = intent
        
        result.detected_intent = best_intent
        result.intent_confidence = min(1.0, best_score * 3)
    
    # ========================================================================
    # DOCUMENT METRICS
    # ========================================================================
    
    def _compute_document_metrics(self, result: DeepParseResult):
        """Compute document-level metrics."""
        if not result.sentences:
            return
        
        # Overall certainty: weighted average of sentence certainties
        result.overall_certainty = sum(
            s.certainty_score for s in result.sentences
        ) / len(result.sentences)
        
        # Subjectivity: ratio of hedging/boosting to total words
        total_hedge = sum(len(s.hedging_words) for s in result.sentences)
        total_boost = sum(len(s.boosting_words) for s in result.sentences)
        total_words = max(result.word_count, 1)
        result.overall_subjectivity = min(1.0, (total_hedge + total_boost) / total_words * 10)
        
        # Complexity: average sentence length + entity density
        avg_sent_len = sum(len(s.tokens) for s in result.sentences) / len(result.sentences)
        entity_density = len(result.all_entities) / max(total_words, 1)
        result.complexity_score = min(1.0, (avg_sent_len / 40) + entity_density * 5)
    
    # ========================================================================
    # KEY PHRASE EXTRACTION
    # ========================================================================
    
    def _extract_key_phrases(self, result: DeepParseResult):
        """Extract key phrases from the document."""
        phrases = set()
        
        # From entities
        for entity in result.all_entities:
            phrases.add(entity.text)
        
        # From triples
        for triple in result.all_triples:
            phrases.add(f"{triple.subject} {triple.predicate}")
            if triple.object_ != "[intransitive]":
                phrases.add(f"{triple.predicate} {triple.object_}")
        
        # From spaCy noun chunks (if available)
        if self.nlp:
            try:
                doc = self.nlp(result.raw_text)
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) >= 2:
                        phrases.add(chunk.text)
            except Exception:
                pass
        
        result.key_phrases = list(phrases)[:30]
    
    # ========================================================================
    # EMBEDDINGS
    # ========================================================================
    
    def _compute_embeddings(self, text: str, result: DeepParseResult):
        """Compute document embedding using transformer model."""
        if self.embedding_model and NUMPY_AVAILABLE:
            try:
                # Document embedding
                features = self.embedding_model(text[:2048], return_tensors=False)
                # Mean pooling
                embedding = np.mean(features[0], axis=0).tolist()
                result.document_embedding = embedding
                
                # Sentence embeddings (first 10)
                for sent in result.sentences[:10]:
                    try:
                        sent_features = self.embedding_model(sent.text, return_tensors=False)
                        sent.embedding = np.mean(sent_features[0], axis=0).tolist()
                    except Exception:
                        pass
            except Exception:
                pass
    
    # ========================================================================
    # COREFERENCE RESOLUTION
    # ========================================================================
    
    def resolve_coreferences(self, text: str) -> Dict[str, Any]:
        """
        Resolve pronominal coreferences in text.
        
        Maps pronouns (he, she, they, it, etc.) back to their most likely
        antecedent entity using a combination of:
        - Recency heuristic (nearest preceding entity)
        - Gender/number agreement
        - Syntactic role matching (subject pronouns → subject entities)
        
        Returns:
            Dict with 'resolved_text', 'coreference_chains', 'resolution_count'
        """
        if not self.nlp:
            return {"resolved_text": text, "coreference_chains": [], "resolution_count": 0}
        
        doc = self.nlp(text)
        
        # Step 1: Collect all named entities with positions
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start,
                "end": ent.end,
                "gender": self._infer_gender(ent.text, ent.label_),
                "number": "plural" if ent.label_ in ("NORP", "ORG") else "singular",
            })
        
        # Also collect noun-phrase subjects as potential antecedents
        for token in doc:
            if token.dep_ in ("nsubj", "nsubjpass") and token.pos_ in ("NOUN", "PROPN"):
                if not any(e["start"] <= token.i < e["end"] for e in entities):
                    entities.append({
                        "text": token.text,
                        "label": "NOUN",
                        "start": token.i,
                        "end": token.i + 1,
                        "gender": self._infer_gender(token.text, "NOUN"),
                        "number": "plural" if token.tag_ in ("NNS", "NNPS") else "singular",
                    })
        
        # Step 2: Find pronouns and resolve
        PERSONAL_PRONOUNS = {
            "he": ("singular", "masculine"), "him": ("singular", "masculine"),
            "his": ("singular", "masculine"), "himself": ("singular", "masculine"),
            "she": ("singular", "feminine"), "her": ("singular", "feminine"),
            "hers": ("singular", "feminine"), "herself": ("singular", "feminine"),
            "it": ("singular", "neutral"), "its": ("singular", "neutral"),
            "itself": ("singular", "neutral"),
            "they": ("plural", "neutral"), "them": ("plural", "neutral"),
            "their": ("plural", "neutral"), "theirs": ("plural", "neutral"),
            "themselves": ("plural", "neutral"),
        }
        
        coref_chains = []  # List of {pronoun, antecedent, pronoun_pos, confidence}
        resolved_tokens = list(doc)
        
        for token in doc:
            lower = token.text.lower()
            if lower not in PERSONAL_PRONOUNS:
                continue
            
            pron_number, pron_gender = PERSONAL_PRONOUNS[lower]
            
            # Find best antecedent: nearest preceding entity with agreement
            best_antecedent = None
            best_distance = float("inf")
            
            for ent in entities:
                if ent["end"] > token.i:
                    continue  # Must precede pronoun
                
                distance = token.i - ent["end"]
                
                # Check number agreement
                if pron_number == "plural" and ent["number"] != "plural":
                    # Organizations can be "they"
                    if ent["label"] not in ("ORG", "NORP", "GPE"):
                        continue
                
                # Check gender agreement (if inferable)
                if pron_gender != "neutral" and ent["gender"] != "neutral":
                    if pron_gender != ent["gender"]:
                        continue
                
                # Prefer closer antecedents, with preference for PERSON/ORG
                effective_distance = distance
                if ent["label"] in ("PERSON", "ORG", "GPE"):
                    effective_distance *= 0.7  # Boost named entities
                
                if effective_distance < best_distance:
                    best_distance = effective_distance
                    best_antecedent = ent
            
            if best_antecedent and best_distance < 50:
                confidence = max(0.3, 1.0 - (best_distance / 50))
                coref_chains.append({
                    "pronoun": token.text,
                    "pronoun_position": token.i,
                    "antecedent": best_antecedent["text"],
                    "antecedent_label": best_antecedent["label"],
                    "confidence": round(confidence, 2),
                })
        
        # Step 3: Build resolved text
        resolved_text = text
        for chain in reversed(coref_chains):  # Reverse to preserve positions
            if chain["confidence"] >= 0.5:
                pron = chain["pronoun"]
                ant = chain["antecedent"]
                # Replace in text (simple replacement of first occurrence after position)
                resolved_text = resolved_text.replace(
                    f" {pron} ", f" {ant} ({pron}) ", 1
                )
        
        return {
            "resolved_text": resolved_text,
            "coreference_chains": coref_chains,
            "resolution_count": len(coref_chains),
        }
    
    def _infer_gender(self, text: str, label: str) -> str:
        """Infer gender from entity text and label."""
        if label == "PERSON":
            # Common name-based heuristic
            male_titles = {"mr", "mr.", "sir", "lord", "king", "chairman", "president"}
            female_titles = {"ms", "ms.", "mrs", "mrs.", "miss", "madam", "queen", "chairwoman"}
            first_word = text.split()[0].lower() if text else ""
            if first_word in male_titles:
                return "masculine"
            if first_word in female_titles:
                return "feminine"
        return "neutral"
    
    # ========================================================================
    # TEMPORAL REASONING
    # ========================================================================
    
    def extract_temporal_timeline(self, texts: List[str], 
                                   sources: List[str] = None) -> Dict[str, Any]:
        """
        Build a temporal timeline from multiple event texts.
        
        Extracts temporal expressions, orders events chronologically,
        detects acceleration/deceleration patterns, and identifies
        temporal clusters.
        
        Args:
            texts: List of news article texts (in any order)
            sources: Optional list of source names (parallel to texts)
            
        Returns:
            Dict with timeline, temporal_patterns, event_velocity,
            acceleration_detected, clusters
        """
        import re
        
        if sources is None:
            sources = [f"source_{i}" for i in range(len(texts))]
        
        # Step 1: Extract temporal expressions from each text
        TEMPORAL_PATTERNS = [
            # Absolute dates
            (r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', "absolute_date"),
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{0,4}\b', "absolute_date"),
            # Relative time
            (r'\b(yesterday|today|tomorrow|last\s+week|this\s+week|next\s+week|last\s+month|this\s+month|next\s+month)\b', "relative_time"),
            (r'\b(\d+)\s+(minutes?|hours?|days?|weeks?|months?|years?)\s+(ago|from now|later|earlier)\b', "relative_offset"),
            # Temporal anchors
            (r'\b(before|after|during|since|until|prior to|following)\s+the\b', "temporal_anchor"),
            # Frequency/recurrence
            (r'\b(daily|weekly|monthly|quarterly|annually|every\s+\w+)\b', "frequency"),
            # Sequence markers
            (r'\b(first|then|next|subsequently|finally|meanwhile|simultaneously|earlier|later|previously)\b', "sequence_marker"),
            # Duration
            (r'\bfor\s+(\d+)\s+(minutes?|hours?|days?|weeks?|months?|years?)\b', "duration"),
            # Deadline/urgency
            (r'\b(deadline|by\s+end\s+of|no\s+later\s+than|within\s+\d+)\b', "deadline"),
        ]
        
        timeline_events = []
        
        for idx, text in enumerate(texts):
            text_lower = text.lower()
            event_temporals = []
            
            for pattern, temporal_type in TEMPORAL_PATTERNS:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    event_temporals.append({
                        "expression": match.group(0),
                        "type": temporal_type,
                        "position": match.start(),
                    })
            
            # Extract the dominant temporal anchor for ordering
            order_score = self._compute_temporal_order(text_lower, event_temporals)
            
            timeline_events.append({
                "text_index": idx,
                "source": sources[idx],
                "text_preview": text[:150],
                "temporal_expressions": event_temporals,
                "temporal_count": len(event_temporals),
                "order_score": order_score,
                "has_past_reference": any(t["type"] == "relative_time" and 
                    any(w in t["expression"] for w in ("yesterday", "last", "ago", "earlier", "previously"))
                    for t in event_temporals),
                "has_future_reference": any(t["type"] == "relative_time" and 
                    any(w in t["expression"] for w in ("tomorrow", "next", "from now", "later"))
                    for t in event_temporals),
            })
        
        # Step 2: Sort by temporal order
        timeline_events.sort(key=lambda e: e["order_score"])
        
        # Step 3: Detect patterns
        patterns = self._detect_temporal_patterns(timeline_events)
        
        # Step 4: Detect clusters (events with similar temporal references)
        clusters = self._detect_temporal_clusters(timeline_events)
        
        # Step 5: Compute event velocity (how quickly events are unfolding)
        velocity = self._compute_event_velocity(timeline_events)
        
        return {
            "timeline": timeline_events,
            "event_count": len(timeline_events),
            "temporal_patterns": patterns,
            "event_velocity": velocity,
            "acceleration_detected": velocity.get("acceleration", False),
            "clusters": clusters,
        }
    
    def _compute_temporal_order(self, text: str, temporals: list) -> float:
        """Assign a relative temporal order score to a text."""
        score = 0.5  # Default: present
        
        past_words = ["was", "were", "had", "did", "announced", "reported", 
                       "said", "stated", "revealed", "previously", "ago", "yesterday"]
        future_words = ["will", "would", "shall", "plan", "expect", "forecast",
                         "predict", "tomorrow", "upcoming", "next"]
        present_words = ["is", "are", "has", "does", "today", "currently", "now"]
        
        text_words = text.split()
        past_count = sum(1 for w in text_words if w in past_words)
        future_count = sum(1 for w in text_words if w in future_words)
        present_count = sum(1 for w in text_words if w in present_words)
        
        total = max(1, past_count + future_count + present_count)
        score = (future_count - past_count) / total * 0.5 + 0.5
        
        # Adjust by explicit temporal expressions
        for t in temporals:
            if t["type"] == "relative_offset" and "ago" in t["expression"]:
                score -= 0.1
            elif t["type"] == "relative_offset" and "from now" in t["expression"]:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _detect_temporal_patterns(self, events: list) -> Dict[str, Any]:
        """Detect acceleration, deceleration, and clustering patterns."""
        if len(events) < 2:
            return {"pattern": "insufficient_data", "details": "Need 2+ events"}
        
        # Count sequence markers
        escalation_words = {"escalating", "intensifying", "accelerating", "surging", "mounting"}
        deescalation_words = {"easing", "moderating", "slowing", "stabilizing", "cooling"}
        
        escalation_count = 0
        deescalation_count = 0
        for ev in events:
            text = ev["text_preview"].lower()
            escalation_count += sum(1 for w in escalation_words if w in text)
            deescalation_count += sum(1 for w in deescalation_words if w in text)
        
        if escalation_count > deescalation_count + 1:
            pattern = "accelerating"
        elif deescalation_count > escalation_count + 1:
            pattern = "decelerating"
        else:
            pattern = "stable"
        
        # Temporal density (how many temporal refs per event)
        avg_temporal_density = sum(e["temporal_count"] for e in events) / len(events)
        
        return {
            "pattern": pattern,
            "escalation_signals": escalation_count,
            "deescalation_signals": deescalation_count,
            "avg_temporal_density": round(avg_temporal_density, 2),
            "events_with_future_ref": sum(1 for e in events if e["has_future_reference"]),
            "events_with_past_ref": sum(1 for e in events if e["has_past_reference"]),
        }
    
    def _detect_temporal_clusters(self, events: list) -> List[Dict]:
        """Group events that reference the same time period."""
        clusters = []
        
        # Simple clustering: group by shared temporal expressions
        from collections import defaultdict
        expression_to_events = defaultdict(list)
        
        for ev in events:
            for t in ev["temporal_expressions"]:
                expr_key = t["expression"].strip()
                if len(expr_key) > 3:  # Skip very short expressions
                    expression_to_events[expr_key].append(ev["text_index"])
        
        for expr, event_indices in expression_to_events.items():
            if len(event_indices) >= 2:
                clusters.append({
                    "temporal_anchor": expr,
                    "event_indices": event_indices,
                    "cluster_size": len(event_indices),
                })
        
        return clusters
    
    def _compute_event_velocity(self, events: list) -> Dict[str, Any]:
        """Compute how quickly events are unfolding."""
        if len(events) < 3:
            return {"velocity": "unknown", "acceleration": False}
        
        # Use temporal density as proxy for velocity
        densities = [e["temporal_count"] for e in events]
        
        # Check if density is increasing (acceleration)
        first_half = densities[:len(densities)//2]
        second_half = densities[len(densities)//2:]
        
        avg_first = sum(first_half) / max(1, len(first_half))
        avg_second = sum(second_half) / max(1, len(second_half))
        
        acceleration = avg_second > avg_first * 1.3
        
        # Future-reference ratio increasing = events speeding up
        future_refs = [1 if e["has_future_reference"] else 0 for e in events]
        future_ratio = sum(future_refs) / len(future_refs)
        
        if future_ratio > 0.5:
            velocity = "forward_looking"
        elif future_ratio < 0.2:
            velocity = "retrospective"
        else:
            velocity = "mixed"
        
        return {
            "velocity": velocity,
            "acceleration": acceleration,
            "temporal_density_trend": "increasing" if acceleration else "stable",
            "future_reference_ratio": round(future_ratio, 2),
        }
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two texts."""
        if self.embedding_model and NUMPY_AVAILABLE:
            try:
                feat1 = self.embedding_model(text1[:2048], return_tensors=False)
                feat2 = self.embedding_model(text2[:2048], return_tensors=False)
                emb1 = np.mean(feat1[0], axis=0)
                emb2 = np.mean(feat2[0], axis=0)
                
                # Cosine similarity
                dot = np.dot(emb1, emb2)
                norm = np.linalg.norm(emb1) * np.linalg.norm(emb2)
                return float(dot / max(norm, 1e-10))
            except Exception:
                pass
        
        # Fallback: Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / max(len(union), 1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get parser status."""
        return {
            "parse_method": self.parse_method,
            "spacy_available": self.nlp is not None,
            "zero_shot_available": self.zero_shot_classifier is not None,
            "embedding_available": self.embedding_model is not None,
            "device": self.device,
        }
