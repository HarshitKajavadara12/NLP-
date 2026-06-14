"""
NLP ENGINE - Deep Natural Language Processing

Replaces regex-based parsing with production NLP:
- spaCy for linguistic analysis, NER, dependency parsing
- Transformers for semantic understanding, NLI, intent detection
- Graceful fallback when models aren't available
"""

from .deep_nlp_parser import DeepNLPParser
from .entity_extraction import EntityExtractor
from .intent_detector import IntentDetector
from .contradiction_detector import ContradictionDetector
from .advanced_nlp import (
    MultiLingualFinancialNLP,
    FinancialEmbeddings,
    FinancialEventExtractor,
    AdvancedNLPEngine,
)

__all__ = [
    "DeepNLPParser",
    "EntityExtractor",
    "IntentDetector",
    "ContradictionDetector",
    "MultiLingualFinancialNLP",
    "FinancialEmbeddings",
    "FinancialEventExtractor",
    "AdvancedNLPEngine",
]
