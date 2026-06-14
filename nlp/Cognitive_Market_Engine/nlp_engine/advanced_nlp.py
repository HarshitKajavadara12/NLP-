"""
Advanced NLP Module
===================
Implements the 3 missing NLP concepts:
1. Multi-Lingual Support — process non-English financial news
2. Domain-Specific Embeddings — FinBERT/finance-tuned embeddings
3. Event Extraction — structured WHO/WHAT/WHOM/WHEN/RESULT extraction
"""
import re
import time
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

logger = logging.getLogger("cme.advanced_nlp")


# ─────────────────────────────────────────────────────────────
# 1. Multi-Lingual Financial NLP
# ─────────────────────────────────────────────────────────────

@dataclass
class TranslatedText:
    """Container for a translated/analyzed financial text."""
    original: str
    language: str
    translated: str
    confidence: float
    entities: List[Dict[str, str]] = field(default_factory=list)
    sentiment: float = 0.0


class MultiLingualFinancialNLP:
    """
    Processes non-English financial news and reports by:
    1. Detecting language
    2. Extracting financial entities regardless of language
    3. Translating / normalizing to English for downstream analysis
    4. Maintaining cross-language entity mappings

    Supports: English, Chinese (Mandarin), Japanese, German,
    French, Spanish, Portuguese, Korean, Arabic, Russian.
    """

    # Financial keywords in multiple languages for detection & extraction
    FINANCIAL_LEXICONS = {
        "zh": {
            "indicators": ["利率", "通胀", "GDP", "失业率", "贸易顺差", "汇率"],
            "actions": ["加息", "降息", "量化宽松", "紧缩", "收购", "合并", "上市"],
            "entities_prefix": ["央行", "人民银行", "证监会", "银保监会"],
            "sentiment_pos": ["上涨", "增长", "利好", "盈利", "突破"],
            "sentiment_neg": ["下跌", "衰退", "利空", "亏损", "暴跌"],
        },
        "ja": {
            "indicators": ["金利", "インフレ", "失業率", "貿易収支", "為替レート"],
            "actions": ["利上げ", "利下げ", "量的緩和", "買収", "合併", "上場"],
            "entities_prefix": ["日銀", "金融庁", "財務省"],
            "sentiment_pos": ["上昇", "成長", "好調", "増益"],
            "sentiment_neg": ["下落", "低迷", "不調", "減益", "暴落"],
        },
        "de": {
            "indicators": ["Zinssatz", "Inflation", "Arbeitslosenquote", "Handelsbilanz"],
            "actions": ["Zinserhöhung", "Zinssenkung", "Übernahme", "Fusion"],
            "entities_prefix": ["EZB", "Bundesbank", "BaFin"],
            "sentiment_pos": ["steigen", "Wachstum", "Gewinn", "Aufschwung"],
            "sentiment_neg": ["fallen", "Rezession", "Verlust", "Abschwung"],
        },
        "fr": {
            "indicators": ["taux d'intérêt", "inflation", "chômage", "balance commerciale"],
            "actions": ["hausse des taux", "baisse des taux", "acquisition", "fusion"],
            "entities_prefix": ["BCE", "Banque de France", "AMF"],
            "sentiment_pos": ["hausse", "croissance", "bénéfice"],
            "sentiment_neg": ["baisse", "récession", "perte", "effondrement"],
        },
        "es": {
            "indicators": ["tasa de interés", "inflación", "desempleo", "balanza comercial"],
            "actions": ["subida de tipos", "bajada de tipos", "adquisición", "fusión"],
            "entities_prefix": ["BCE", "Banco Central"],
            "sentiment_pos": ["subida", "crecimiento", "beneficio"],
            "sentiment_neg": ["caída", "recesión", "pérdida", "desplome"],
        },
        "ko": {
            "indicators": ["금리", "인플레이션", "실업률", "무역수지"],
            "actions": ["금리인상", "금리인하", "인수", "합병"],
            "entities_prefix": ["한국은행", "금융위원회", "금감원"],
            "sentiment_pos": ["상승", "성장", "호조", "흑자"],
            "sentiment_neg": ["하락", "침체", "부진", "적자"],
        },
        "en": {
            "indicators": ["interest rate", "inflation", "unemployment", "GDP", "trade balance"],
            "actions": ["rate hike", "rate cut", "acquisition", "merger", "IPO", "buyback"],
            "entities_prefix": ["Fed", "ECB", "BoJ", "SEC", "CFTC"],
            "sentiment_pos": ["rally", "surge", "gain", "growth", "beat", "upgrade"],
            "sentiment_neg": ["crash", "plunge", "loss", "recession", "miss", "downgrade"],
        },
    }

    # Common Unicode ranges for language detection
    _LANG_RANGES = {
        "zh": (0x4E00, 0x9FFF),   # CJK Unified Ideographs
        "ja": (0x3040, 0x30FF),   # Hiragana + Katakana
        "ko": (0xAC00, 0xD7AF),   # Hangul Syllables
        "ar": (0x0600, 0x06FF),   # Arabic
        "ru": (0x0400, 0x04FF),   # Cyrillic
    }

    def __init__(self):
        self._entity_map: Dict[str, str] = {}  # foreign → English entity mapping
        self._transformer = None
        self._try_load_transformer()

    def _try_load_transformer(self):
        """Attempt to load a multilingual transformer."""
        try:
            from transformers import pipeline
            self._transformer = pipeline(
                "text-classification",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                truncation=True,
                max_length=512
            )
            logger.info("Multilingual transformer loaded")
        except Exception:
            logger.info("Multilingual transformer not available; using lexicon fallback")
            self._transformer = None

    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect the language of financial text."""
        if not text:
            return "en", 0.0

        char_counts: Dict[str, int] = defaultdict(int)
        total = 0
        for char in text:
            cp = ord(char)
            for lang, (lo, hi) in self._LANG_RANGES.items():
                if lo <= cp <= hi:
                    char_counts[lang] += 1
            total += 1

        if total == 0:
            return "en", 0.5

        # Check script-based detection
        for lang, count in sorted(char_counts.items(), key=lambda x: -x[1]):
            ratio = count / total
            if ratio > 0.1:
                return lang, min(1.0, ratio * 3)

        # Latin-script language detection via keyword matching
        text_lower = text.lower()
        lang_scores: Dict[str, float] = {}
        for lang, lexicon in self.FINANCIAL_LEXICONS.items():
            score = 0
            for category in lexicon.values():
                for word in category:
                    if word.lower() in text_lower:
                        score += 1
            lang_scores[lang] = score

        if lang_scores:
            best_lang = max(lang_scores, key=lang_scores.get)
            best_score = lang_scores[best_lang]
            if best_score > 0:
                return best_lang, min(1.0, best_score / 5)

        return "en", 0.3  # default

    def extract_financial_entities(self, text: str, lang: str) -> List[Dict[str, str]]:
        """Extract financial entities regardless of language."""
        entities = []
        lexicon = self.FINANCIAL_LEXICONS.get(lang, self.FINANCIAL_LEXICONS["en"])

        for word in lexicon.get("entities_prefix", []):
            if word in text:
                entities.append({"text": word, "type": "ORG", "language": lang})

        for word in lexicon.get("indicators", []):
            if word.lower() in text.lower():
                entities.append({"text": word, "type": "INDICATOR", "language": lang})

        for word in lexicon.get("actions", []):
            if word.lower() in text.lower():
                entities.append({"text": word, "type": "ACTION", "language": lang})

        # Universal patterns: ticker symbols, monetary amounts
        tickers = re.findall(r'\b[A-Z]{1,5}\b', text)
        for t in tickers[:10]:
            if len(t) >= 2 and t not in ("THE", "AND", "FOR", "BUT", "WITH", "HAS"):
                entities.append({"text": t, "type": "TICKER", "language": "universal"})

        amounts = re.findall(r'[\$€£¥₹]\s*[\d,.]+\s*(?:[BMKbmk]illion|[BMK])?', text)
        for a in amounts[:10]:
            entities.append({"text": a.strip(), "type": "MONETARY", "language": "universal"})

        return entities

    def compute_sentiment(self, text: str, lang: str) -> float:
        """Compute sentiment using transformer (if available) or lexicon fallback."""
        if self._transformer and len(text) > 10:
            try:
                result = self._transformer(text[:512])
                if result:
                    label = result[0].get("label", "3 stars")
                    stars = int(label.split()[0])
                    return (stars - 3) / 2  # Normalize 1-5 → -1 to +1
            except Exception:
                pass

        # Lexicon fallback
        lexicon = self.FINANCIAL_LEXICONS.get(lang, self.FINANCIAL_LEXICONS["en"])
        text_lower = text.lower()
        pos = sum(1 for w in lexicon.get("sentiment_pos", []) if w.lower() in text_lower)
        neg = sum(1 for w in lexicon.get("sentiment_neg", []) if w.lower() in text_lower)
        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total

    def process_text(self, text: str) -> TranslatedText:
        """Full pipeline: detect language → extract entities → sentiment → translate."""
        lang, confidence = self.detect_language(text)
        entities = self.extract_financial_entities(text, lang)
        sentiment = self.compute_sentiment(text, lang)

        # Translation placeholder (in production, use DeepL/Google Translate API)
        translated = text if lang == "en" else f"[{lang}→en] {text}"

        return TranslatedText(
            original=text,
            language=lang,
            translated=translated,
            confidence=confidence,
            entities=entities,
            sentiment=sentiment,
        )

    def register_entity_mapping(self, foreign: str, english: str) -> None:
        """Register cross-language entity mapping (e.g., '日銀' → 'Bank of Japan')."""
        self._entity_map[foreign] = english

    def resolve_entity(self, text: str) -> str:
        """Resolve a foreign entity to its English equivalent."""
        return self._entity_map.get(text, text)


# ─────────────────────────────────────────────────────────────
# 2. Domain-Specific Financial Embeddings
# ─────────────────────────────────────────────────────────────

class FinancialEmbeddings:
    """
    Domain-specific embeddings for financial text using:
    - FinBERT (ProsusAI/finbert) for financial sentiment
    - Sentence-transformers for semantic similarity
    - Custom financial vocabulary expansion
    - Contextual embedding of financial terms
    """

    # Financial domain vocabulary not well captured by generic models
    FINANCIAL_VOCAB = {
        "hawkish": {"domain": "monetary_policy", "direction": "tightening", "intensity": 0.7},
        "dovish": {"domain": "monetary_policy", "direction": "easing", "intensity": 0.7},
        "taper": {"domain": "monetary_policy", "direction": "tightening", "intensity": 0.5},
        "QE": {"domain": "monetary_policy", "direction": "easing", "intensity": 0.9},
        "QT": {"domain": "monetary_policy", "direction": "tightening", "intensity": 0.9},
        "short squeeze": {"domain": "market_microstructure", "direction": "bullish", "intensity": 0.8},
        "dead cat bounce": {"domain": "technical", "direction": "bearish", "intensity": 0.6},
        "capitulation": {"domain": "sentiment", "direction": "extreme_bearish", "intensity": 0.9},
        "melt-up": {"domain": "market_dynamics", "direction": "extreme_bullish", "intensity": 0.85},
        "risk-off": {"domain": "cross_asset", "direction": "bearish", "intensity": 0.6},
        "risk-on": {"domain": "cross_asset", "direction": "bullish", "intensity": 0.6},
        "bid up": {"domain": "market_microstructure", "direction": "bullish", "intensity": 0.5},
        "margin call": {"domain": "forced_liquidation", "direction": "bearish", "intensity": 0.8},
        "blow-off top": {"domain": "technical", "direction": "bearish_reversal", "intensity": 0.9},
        "flight to quality": {"domain": "cross_asset", "direction": "risk_off", "intensity": 0.7},
        "basis trade": {"domain": "fixed_income", "direction": "neutral", "intensity": 0.4},
        "carry trade": {"domain": "fx", "direction": "neutral", "intensity": 0.4},
        "theta decay": {"domain": "options", "direction": "neutral", "intensity": 0.3},
        "gamma squeeze": {"domain": "options", "direction": "bullish", "intensity": 0.85},
        "delta hedging": {"domain": "options", "direction": "neutral", "intensity": 0.3},
        "window dressing": {"domain": "institutional", "direction": "bullish", "intensity": 0.3},
        "BTFD": {"domain": "retail_slang", "direction": "bullish", "intensity": 0.5},
        "priced in": {"domain": "efficiency", "direction": "neutral", "intensity": 0.2},
        "tail risk": {"domain": "risk", "direction": "bearish", "intensity": 0.7},
        "black swan": {"domain": "risk", "direction": "extreme_bearish", "intensity": 1.0},
    }

    def __init__(self):
        self._finbert = None
        self._sentence_model = None
        self._embedding_cache: Dict[str, List[float]] = {}
        self._try_load_models()

    def _try_load_models(self):
        """Attempt to load FinBERT and sentence-transformers."""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
            self._finbert = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                truncation=True,
                max_length=512,
            )
            logger.info("FinBERT loaded successfully")
        except Exception as e:
            logger.info(f"FinBERT not available: {e}")

        try:
            from sentence_transformers import SentenceTransformer
            self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Sentence transformer loaded")
        except Exception:
            logger.info("Sentence transformer not available; using TF-IDF fallback")

    def get_financial_sentiment(self, text: str) -> Dict[str, Any]:
        """Get FinBERT-based financial sentiment."""
        if self._finbert:
            try:
                result = self._finbert(text[:512])
                if result:
                    label = result[0]["label"].lower()
                    score = result[0]["score"]
                    direction = {"positive": 1, "negative": -1, "neutral": 0}.get(label, 0)
                    return {
                        "label": label,
                        "score": score,
                        "direction": direction,
                        "weighted_score": direction * score,
                        "model": "finbert",
                    }
            except Exception:
                pass

        # Lexicon-based fallback with financial vocab
        return self._lexicon_sentiment(text)

    def _lexicon_sentiment(self, text: str) -> Dict[str, Any]:
        """Financial domain lexicon-based sentiment."""
        text_lower = text.lower()
        bullish_score = 0.0
        bearish_score = 0.0
        matched_terms = []

        for term, properties in self.FINANCIAL_VOCAB.items():
            if term.lower() in text_lower:
                intensity = properties["intensity"]
                direction = properties["direction"]
                matched_terms.append(term)
                if "bullish" in direction or direction == "easing":
                    bullish_score += intensity
                elif "bearish" in direction or direction == "tightening":
                    bearish_score += intensity

        total = bullish_score + bearish_score
        if total == 0:
            return {"label": "neutral", "score": 0.5, "direction": 0,
                    "weighted_score": 0, "model": "lexicon", "terms": []}

        net = (bullish_score - bearish_score) / total
        label = "positive" if net > 0.1 else "negative" if net < -0.1 else "neutral"
        return {
            "label": label,
            "score": abs(net),
            "direction": 1 if net > 0 else -1 if net < 0 else 0,
            "weighted_score": net,
            "model": "lexicon",
            "terms": matched_terms,
        }

    def embed_text(self, text: str) -> List[float]:
        """Get dense embedding for financial text."""
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        if self._sentence_model:
            try:
                embedding = self._sentence_model.encode(text).tolist()
                self._embedding_cache[text] = embedding
                return embedding
            except Exception:
                pass

        # TF-IDF-style fallback (64-dim)
        embedding = self._tfidf_embedding(text)
        self._embedding_cache[text] = embedding
        return embedding

    def _tfidf_embedding(self, text: str, dim: int = 64) -> List[float]:
        """Simple TF-IDF-inspired fixed-dimension embedding fallback."""
        words = re.findall(r'\b\w+\b', text.lower())
        vec = [0.0] * dim
        for word in words:
            h = hash(word) % dim
            idf = 1.0 / (1 + math.log1p(len(word)))
            vec[h] += idf

            # Add financial domain boost
            if word in self.FINANCIAL_VOCAB:
                props = self.FINANCIAL_VOCAB[word]
                vec[(h + 1) % dim] += props["intensity"]

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Compute semantic similarity between two financial texts."""
        emb_a = self.embed_text(text_a)
        emb_b = self.embed_text(text_b)
        # Cosine similarity
        dot = sum(a * b for a, b in zip(emb_a, emb_b))
        norm_a = math.sqrt(sum(a * a for a in emb_a))
        norm_b = math.sqrt(sum(b * b for b in emb_b))
        if norm_a * norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def classify_domain(self, text: str) -> Dict[str, float]:
        """Classify text into financial sub-domains."""
        text_lower = text.lower()
        domain_scores: Dict[str, float] = defaultdict(float)

        for term, props in self.FINANCIAL_VOCAB.items():
            if term.lower() in text_lower:
                domain_scores[props["domain"]] += props["intensity"]

        total = sum(domain_scores.values())
        if total > 0:
            domain_scores = {k: v / total for k, v in domain_scores.items()}
        return dict(domain_scores)


# ─────────────────────────────────────────────────────────────
# 3. Structured Event Extraction
# ─────────────────────────────────────────────────────────────

@dataclass
class ExtractedEvent:
    """Structured event extracted from financial text."""
    event_type: str
    who: str              # Actor / subject
    what: str             # Action / verb phrase
    whom: str             # Target / object
    when: str             # Temporal expression
    result: str           # Outcome / consequence
    confidence: float
    raw_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class FinancialEventExtractor:
    """
    Structured event extraction from financial text:
    WHO did WHAT to WHOM, WHEN, with what RESULT.

    Uses dependency parsing (spaCy) and pattern matching to extract
    structured events from unstructured financial news.
    """

    # Event type patterns
    EVENT_PATTERNS = {
        "rate_decision": {
            "triggers": ["rate hike", "rate cut", "raised rates", "lowered rates",
                         "held rates", "paused", "cut by", "hiked by",
                         "basis points", "bps", "rate decision"],
            "who_patterns": ["Federal Reserve", "Fed", "ECB", "BoJ", "BoE",
                             "central bank", "FOMC", "RBA", "RBNZ", "SNB", "PBoC"],
        },
        "earnings": {
            "triggers": ["reported earnings", "beat estimates", "missed estimates",
                         "revenue of", "EPS of", "guidance", "raised guidance",
                         "lowered guidance", "profit warning", "earnings surprise"],
            "who_patterns": [],  # Will be NER-detected companies
        },
        "merger_acquisition": {
            "triggers": ["acquired", "to acquire", "merger with", "to merge",
                         "buyout", "takeover", "bid for", "offer for",
                         "deal worth", "all-cash deal", "all-stock deal"],
            "who_patterns": [],
        },
        "regulatory": {
            "triggers": ["SEC charged", "fined", "investigation", "subpoena",
                         "regulatory action", "compliance", "antitrust",
                         "approved", "rejected", "sanctioned", "banned"],
            "who_patterns": ["SEC", "CFTC", "DOJ", "FTC", "EU Commission",
                             "regulators"],
        },
        "geopolitical": {
            "triggers": ["sanctions", "tariff", "trade war", "embargo",
                         "conflict", "invasion", "alliance", "treaty",
                         "diplomatic", "military"],
            "who_patterns": [],
        },
        "labor": {
            "triggers": ["layoffs", "hiring", "strike", "workforce reduction",
                         "job cuts", "restructuring", "downsizing",
                         "new positions", "hiring freeze"],
            "who_patterns": [],
        },
        "product_launch": {
            "triggers": ["launched", "unveiled", "announced", "introduced",
                         "released", "new product", "next generation",
                         "breakthrough", "patent"],
            "who_patterns": [],
        },
        "macro_data": {
            "triggers": ["GDP", "CPI", "PPI", "NFP", "payrolls", "jobless claims",
                         "unemployment rate", "PMI", "ISM", "retail sales",
                         "housing starts", "consumer confidence"],
            "who_patterns": ["Bureau of Labor Statistics", "BLS", "Commerce Department",
                             "Census Bureau"],
        },
    }

    def __init__(self):
        self._nlp = None
        self._try_load_spacy()

    def _try_load_spacy(self):
        """Attempt to load spaCy for dependency parsing."""
        try:
            import spacy
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                self._nlp = spacy.load("en_core_web_md") if hasattr(spacy, 'load') else None
            logger.info("spaCy loaded for event extraction")
        except Exception:
            logger.info("spaCy not available; using pattern-based extraction")

    def extract_events(self, text: str) -> List[ExtractedEvent]:
        """Extract all financial events from text."""
        events = []

        # Determine event type
        text_lower = text.lower()
        matched_types = []
        for event_type, patterns in self.EVENT_PATTERNS.items():
            for trigger in patterns["triggers"]:
                if trigger.lower() in text_lower:
                    matched_types.append((event_type, trigger))
                    break

        for event_type, trigger in matched_types:
            event = self._extract_single_event(text, event_type, trigger)
            if event:
                events.append(event)

        if not events:
            # Try generic extraction
            generic = self._generic_extraction(text)
            if generic:
                events.append(generic)

        return events

    def _extract_single_event(self, text: str, event_type: str,
                               trigger: str) -> Optional[ExtractedEvent]:
        """Extract a single structured event."""
        who = self._extract_who(text, event_type)
        what = self._extract_what(text, trigger)
        whom = self._extract_whom(text, event_type, who)
        when = self._extract_when(text)
        result = self._extract_result(text, event_type)

        confidence = 0.3
        if who:
            confidence += 0.15
        if what:
            confidence += 0.15
        if when:
            confidence += 0.1
        if result:
            confidence += 0.1
        if whom:
            confidence += 0.1

        return ExtractedEvent(
            event_type=event_type,
            who=who or "Unknown",
            what=what or trigger,
            whom=whom or "",
            when=when or "now",
            result=result or "",
            confidence=min(1.0, confidence),
            raw_text=text,
        )

    def _extract_who(self, text: str, event_type: str) -> str:
        """Extract the subject / actor."""
        # Try spaCy NER first
        if self._nlp:
            try:
                doc = self._nlp(text[:512])
                orgs = [ent.text for ent in doc.ents if ent.label_ in ("ORG", "GPE")]
                persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
                if orgs:
                    return orgs[0]
                if persons:
                    return persons[0]
            except Exception:
                pass

        # Pattern-based fallback
        who_patterns = self.EVENT_PATTERNS.get(event_type, {}).get("who_patterns", [])
        for pattern in who_patterns:
            if pattern in text:
                return pattern

        # Generic org extraction
        org_match = re.search(
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|Co|Group|Bank)\.?))\b',
            text
        )
        if org_match:
            return org_match.group(1)

        return ""

    def _extract_what(self, text: str, trigger: str) -> str:
        """Extract the action/verb phrase."""
        # Find sentence containing trigger
        sentences = re.split(r'[.!?]+', text)
        for sent in sentences:
            if trigger.lower() in sent.lower():
                # Return the sentence as the action context
                return sent.strip()[:200]
        return trigger

    def _extract_whom(self, text: str, event_type: str, who: str) -> str:
        """Extract the target/object of the action."""
        if self._nlp:
            try:
                doc = self._nlp(text[:512])
                orgs = [ent.text for ent in doc.ents if ent.label_ in ("ORG", "GPE")]
                # Whom is the second organization (not the who)
                for org in orgs:
                    if org != who:
                        return org
            except Exception:
                pass

        # For M&A, look for "acquired X" or "merger with X"
        if event_type == "merger_acquisition":
            patterns = [
                r'acquir(?:ed|ing|e)\s+([A-Z][a-zA-Z\s]+?)(?:\s+for|\s+in|\.|,)',
                r'merger\s+with\s+([A-Z][a-zA-Z\s]+?)(?:\s+for|\s+in|\.|,)',
                r'bid\s+for\s+([A-Z][a-zA-Z\s]+?)(?:\s+for|\s+in|\.|,)',
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip()

        return ""

    def _extract_when(self, text: str) -> str:
        """Extract temporal expression."""
        # Try spaCy
        if self._nlp:
            try:
                doc = self._nlp(text[:512])
                dates = [ent.text for ent in doc.ents if ent.label_ in ("DATE", "TIME")]
                if dates:
                    return dates[0]
            except Exception:
                pass

        # Pattern-based
        patterns = [
            r'(?:on\s+)?(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
            r'(?:on\s+)?\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}',
            r'(?:today|yesterday|last\s+week|this\s+(?:morning|afternoon|week))',
            r'(?:Q[1-4]\s+\d{4})',
            r'(?:\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return ""

    def _extract_result(self, text: str, event_type: str) -> str:
        """Extract the outcome/consequence."""
        result_keywords = {
            "rate_decision": [
                r'(?:sending|pushing|drove|causing)\s+(.+?)(?:\.|,|$)',
                r'(?:stocks|bonds|markets?)\s+(?:rose|fell|dropped|surged|plunged)(.+?)(?:\.|$)',
            ],
            "earnings": [
                r'(?:shares|stock)\s+(?:rose|fell|jumped|dropped|surged)\s+(.+?)(?:\.|$)',
                r'(?:beat|missed)\s+(?:estimates|expectations)\s+by\s+(.+?)(?:\.|$)',
            ],
            "merger_acquisition": [
                r'deal\s+(?:valued|worth)\s+(.+?)(?:\.|$)',
                r'(?:premium|discount)\s+of\s+(.+?)(?:\.|$)',
            ],
        }

        patterns = result_keywords.get(event_type, [])
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]

        # Generic "resulted in" / "leading to"
        generic = re.search(
            r'(?:result(?:ed|ing)\s+in|lead(?:ing|s)\s+to|caus(?:ed|ing))\s+(.+?)(?:\.|$)',
            text, re.IGNORECASE
        )
        if generic:
            return generic.group(1).strip()[:200]

        return ""

    def _generic_extraction(self, text: str) -> Optional[ExtractedEvent]:
        """Fallback generic event extraction."""
        who = self._extract_who(text, "")
        when = self._extract_when(text)

        if not who and not when:
            return None

        # First sentence as what
        sentences = re.split(r'[.!?]+', text)
        what = sentences[0].strip()[:200] if sentences else text[:200]

        return ExtractedEvent(
            event_type="generic",
            who=who or "Unknown",
            what=what,
            whom="",
            when=when or "unspecified",
            result="",
            confidence=0.3,
            raw_text=text,
        )

    def extract_event_chain(self, texts: List[str]) -> List[ExtractedEvent]:
        """Extract events from multiple texts and link them chronologically."""
        all_events = []
        for text in texts:
            events = self.extract_events(text)
            all_events.extend(events)

        # Sort by temporal expression (rudimentary)
        return sorted(all_events, key=lambda e: e.when or "zzz")


# ─────────────────────────────────────────────────────────────
# Unified Advanced NLP Interface
# ─────────────────────────────────────────────────────────────

class AdvancedNLPEngine:
    """Orchestrates all three advanced NLP capabilities."""

    def __init__(self):
        self.multilingual = MultiLingualFinancialNLP()
        self.embeddings = FinancialEmbeddings()
        self.event_extractor = FinancialEventExtractor()

    def full_analysis(self, text: str) -> Dict[str, Any]:
        """Run the complete advanced NLP pipeline on text."""
        # 1. Language detection & translation
        translated = self.multilingual.process_text(text)

        # 2. Domain-specific sentiment (on English text)
        analysis_text = translated.translated if translated.language != "en" else text
        sentiment = self.embeddings.get_financial_sentiment(analysis_text)
        domain = self.embeddings.classify_domain(analysis_text)

        # 3. Event extraction
        events = self.event_extractor.extract_events(analysis_text)

        return {
            "language": translated.language,
            "language_confidence": translated.confidence,
            "translated": translated.translated,
            "entities": translated.entities,
            "sentiment": sentiment,
            "domains": domain,
            "events": [
                {
                    "type": e.event_type,
                    "who": e.who,
                    "what": e.what,
                    "whom": e.whom,
                    "when": e.when,
                    "result": e.result,
                    "confidence": e.confidence,
                }
                for e in events
            ],
        }
