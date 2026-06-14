"""
ENTITY EXTRACTION — Advanced Named Entity Recognition

Extends spaCy NER with:
- Financial entity recognition (tickers, instruments, indices)
- Geopolitical entity linking
- Temporal expression normalization
- Monetary value normalization
- Relationship extraction between entities
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FinancialEntity:
    """A financial entity with normalized attributes."""
    text: str
    entity_type: str  # TICKER, INDEX, INSTRUMENT, CURRENCY, COMMODITY
    normalized_name: str = ""
    sector: str = ""
    country: str = ""
    confidence: float = 0.0


@dataclass
class GeopoliticalEntity:
    """A geopolitical entity with context."""
    text: str
    entity_type: str  # COUNTRY, REGION, BLOC, CITY
    iso_code: str = ""
    region: str = ""
    economic_bloc: List[str] = field(default_factory=list)


@dataclass
class EntityRelation:
    """Relationship between two entities."""
    source_entity: str
    target_entity: str
    relation_type: str  # "regulates", "invests_in", "sanctions", "trades_with"
    confidence: float = 0.0
    context: str = ""


class EntityExtractor:
    """
    Comprehensive entity extraction for financial news.
    
    Extracts:
    - Organizations (central banks, companies, regulators)
    - People (officials, executives)
    - Financial instruments (stocks, bonds, currencies)
    - Geopolitical entities (countries, blocs)
    - Monetary values (with normalization)
    - Temporal expressions (with normalization)
    - Relationships between entities
    """
    
    # Major central banks
    CENTRAL_BANKS = {
        "federal reserve": ("FED", "US"), "the fed": ("FED", "US"),
        "ecb": ("ECB", "EU"), "european central bank": ("ECB", "EU"),
        "boj": ("BOJ", "JP"), "bank of japan": ("BOJ", "JP"),
        "boe": ("BOE", "GB"), "bank of england": ("BOE", "GB"),
        "pboc": ("PBOC", "CN"), "people's bank of china": ("PBOC", "CN"),
        "rbi": ("RBI", "IN"), "reserve bank of india": ("RBI", "IN"),
        "rba": ("RBA", "AU"), "reserve bank of australia": ("RBA", "AU"),
        "snb": ("SNB", "CH"), "swiss national bank": ("SNB", "CH"),
        "boc": ("BOC", "CA"), "bank of canada": ("BOC", "CA"),
    }
    
    # Major indices
    INDICES = {
        "s&p 500": "SPX", "dow jones": "DJIA", "nasdaq": "IXIC",
        "ftse": "FTSE", "dax": "DAX", "nikkei": "N225",
        "hang seng": "HSI", "shanghai composite": "SSEC",
        "sensex": "SENSEX", "nifty": "NIFTY",
    }
    
    # Major currencies
    CURRENCIES = {
        "dollar": "USD", "euro": "EUR", "yen": "JPY",
        "pound": "GBP", "yuan": "CNY", "rupee": "INR",
        "franc": "CHF", "bitcoin": "BTC", "ethereum": "ETH",
    }
    
    # Commodities
    COMMODITIES = {
        "crude oil": "CL", "brent": "BZ", "gold": "GC",
        "silver": "SI", "natural gas": "NG", "copper": "HG",
        "wheat": "ZW", "corn": "ZC", "soybeans": "ZS",
    }
    
    # Economic indicators
    INDICATORS = {
        "gdp": "GDP", "cpi": "CPI", "ppi": "PPI",
        "pce": "PCE", "nonfarm payrolls": "NFP",
        "unemployment rate": "UNEMP", "jobless claims": "CLAIMS",
        "retail sales": "RETS", "industrial production": "IP",
        "pmi": "PMI", "ism": "ISM",
    }
    
    # Geopolitical blocs
    BLOCS = {
        "nato": ["US", "GB", "DE", "FR", "CA"],
        "eu": ["DE", "FR", "IT", "ES", "NL"],
        "brics": ["BR", "RU", "IN", "CN", "ZA"],
        "opec": ["SA", "IQ", "IR", "AE", "KW"],
        "g7": ["US", "GB", "DE", "FR", "JP", "CA", "IT"],
        "g20": ["US", "CN", "JP", "DE", "GB", "FR", "IN", "BR"],
        "asean": ["SG", "MY", "TH", "ID", "PH"],
    }
    
    # Relation patterns
    RELATION_PATTERNS = [
        (r'(\w+)\s+(?:sanction|penalize|restrict)s?\s+(\w+)', "sanctions"),
        (r'(\w+)\s+(?:invest|acquire|buy|purchase)s?\s+(?:in\s+)?(\w+)', "invests_in"),
        (r'(\w+)\s+(?:regulate|oversee|supervise)s?\s+(\w+)', "regulates"),
        (r'(\w+)\s+(?:trade|export|import)s?\s+(?:with|to|from)\s+(\w+)', "trades_with"),
        (r'(\w+)\s+(?:ally|support|back)s?\s+(\w+)', "allies_with"),
        (r'(\w+)\s+(?:oppose|reject|condemn)s?\s+(\w+)', "opposes"),
    ]
    
    def __init__(self, spacy_nlp=None):
        """Initialize with optional spaCy model for enhanced extraction."""
        self.nlp = spacy_nlp
    
    def extract_all(self, text: str) -> Dict:
        """
        Extract all entity types from text.
        
        Returns dict with keys:
        - financial_entities
        - geopolitical_entities
        - people
        - monetary_values
        - temporal_expressions
        - indicators
        - relations
        """
        text_lower = text.lower()
        
        result = {
            "financial_entities": self._extract_financial(text, text_lower),
            "geopolitical_entities": self._extract_geopolitical(text, text_lower),
            "people": self._extract_people(text),
            "monetary_values": self._extract_monetary(text),
            "temporal_expressions": self._extract_temporal(text, text_lower),
            "indicators": self._extract_indicators(text_lower),
            "relations": self._extract_relations(text),
        }
        
        # Use spaCy for additional entities
        if self.nlp:
            spacy_entities = self._spacy_extract(text)
            result["spacy_entities"] = spacy_entities
        
        return result
    
    def _extract_financial(self, text: str, text_lower: str) -> List[FinancialEntity]:
        """Extract financial entities."""
        entities = []
        
        # Central banks
        for name, (code, country) in self.CENTRAL_BANKS.items():
            if name in text_lower:
                entities.append(FinancialEntity(
                    text=name, entity_type="CENTRAL_BANK",
                    normalized_name=code, country=country,
                    confidence=0.95
                ))
        
        # Indices
        for name, code in self.INDICES.items():
            if name in text_lower:
                entities.append(FinancialEntity(
                    text=name, entity_type="INDEX",
                    normalized_name=code, confidence=0.9
                ))
        
        # Currencies
        for name, code in self.CURRENCIES.items():
            if name in text_lower:
                entities.append(FinancialEntity(
                    text=name, entity_type="CURRENCY",
                    normalized_name=code, confidence=0.85
                ))
        
        # Commodities
        for name, code in self.COMMODITIES.items():
            if name in text_lower:
                entities.append(FinancialEntity(
                    text=name, entity_type="COMMODITY",
                    normalized_name=code, confidence=0.85
                ))
        
        # Ticker symbols ($AAPL, $TSLA)
        ticker_pattern = r'\$([A-Z]{1,5})\b'
        for match in re.finditer(ticker_pattern, text):
            entities.append(FinancialEntity(
                text=match.group(0), entity_type="TICKER",
                normalized_name=match.group(1), confidence=0.9
            ))
        
        return entities
    
    def _extract_geopolitical(self, text: str, text_lower: str) -> List[GeopoliticalEntity]:
        """Extract geopolitical entities."""
        entities = []
        
        # Countries (extended list)
        countries = {
            "united states": ("US", "North America"), "china": ("CN", "Asia"),
            "russia": ("RU", "Europe/Asia"), "japan": ("JP", "Asia"),
            "germany": ("DE", "Europe"), "united kingdom": ("GB", "Europe"),
            "france": ("FR", "Europe"), "india": ("IN", "Asia"),
            "brazil": ("BR", "South America"), "canada": ("CA", "North America"),
            "australia": ("AU", "Oceania"), "south korea": ("KR", "Asia"),
            "mexico": ("MX", "North America"), "indonesia": ("ID", "Asia"),
            "turkey": ("TR", "Europe/Asia"), "saudi arabia": ("SA", "Middle East"),
            "iran": ("IR", "Middle East"), "israel": ("IL", "Middle East"),
            "ukraine": ("UA", "Europe"), "taiwan": ("TW", "Asia"),
            "switzerland": ("CH", "Europe"), "netherlands": ("NL", "Europe"),
            "italy": ("IT", "Europe"), "spain": ("ES", "Europe"),
            "poland": ("PL", "Europe"), "argentina": ("AR", "South America"),
            "nigeria": ("NG", "Africa"), "south africa": ("ZA", "Africa"),
            "egypt": ("EG", "Africa"), "singapore": ("SG", "Asia"),
        }
        
        for name, (iso, region) in countries.items():
            if name in text_lower:
                blocs = [b for b, members in self.BLOCS.items() if iso in members]
                entities.append(GeopoliticalEntity(
                    text=name, entity_type="COUNTRY",
                    iso_code=iso, region=region,
                    economic_bloc=blocs
                ))
        
        # Blocs
        for bloc_name in self.BLOCS:
            if bloc_name in text_lower:
                entities.append(GeopoliticalEntity(
                    text=bloc_name.upper(), entity_type="BLOC",
                    economic_bloc=[bloc_name]
                ))
        
        return entities
    
    def _extract_people(self, text: str) -> List[Dict]:
        """Extract person mentions with titles."""
        people = []
        
        title_pattern = r'(?:President|Chairman|Chair|CEO|CFO|Governor|Secretary|Minister|Director|Prime Minister|Chancellor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})'
        for match in re.finditer(title_pattern, text):
            people.append({
                "name": match.group(1),
                "title": match.group(0).replace(match.group(1), "").strip(),
                "full_mention": match.group(0),
                "confidence": 0.8,
            })
        
        return people
    
    def _extract_monetary(self, text: str) -> List[Dict]:
        """Extract and normalize monetary values."""
        values = []
        
        # $X billion/million/trillion
        pattern = r'\$\s*([\d,.]+)\s*(billion|million|trillion|bn|mn|tn|B|M|T)\b'
        multipliers = {
            "billion": 1e9, "bn": 1e9, "B": 1e9,
            "million": 1e6, "mn": 1e6, "M": 1e6,
            "trillion": 1e12, "tn": 1e12, "T": 1e12,
        }
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw = match.group(1).replace(",", "")
            mult = multipliers.get(match.group(2), 1)
            try:
                normalized = float(raw) * mult
                values.append({
                    "raw_text": match.group(0),
                    "value": normalized,
                    "currency": "USD",
                    "unit": match.group(2),
                })
            except ValueError:
                pass
        
        # Percentage/basis points
        pct_pattern = r'([\d,.]+)\s*(?:percent|%|basis points|bps)\b'
        for match in re.finditer(pct_pattern, text, re.IGNORECASE):
            try:
                value = float(match.group(1).replace(",", ""))
                unit = "bps" if "basis" in match.group(0).lower() or "bps" in match.group(0) else "percent"
                values.append({
                    "raw_text": match.group(0),
                    "value": value,
                    "currency": "N/A",
                    "unit": unit,
                })
            except ValueError:
                pass
        
        return values
    
    def _extract_temporal(self, text: str, text_lower: str) -> List[Dict]:
        """Extract and normalize temporal expressions."""
        expressions = []
        
        patterns = [
            (r'\b(today|yesterday|tomorrow)\b', "relative_day"),
            (r'\bnext\s+(week|month|quarter|year)\b', "relative_future"),
            (r'\blast\s+(week|month|quarter|year)\b', "relative_past"),
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b', "absolute_date"),
            (r'\bQ[1-4]\s+\d{4}\b', "quarter"),
            (r'\bFY\s*\d{4}\b', "fiscal_year"),
            (r'\b\d{4}\b', "year"),
            (r'\b(short-term|medium-term|long-term|near-term)\b', "horizon"),
            (r'\b(intraday|overnight|end of day|close)\b', "trading_time"),
        ]
        
        for pattern, expr_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                expressions.append({
                    "text": match.group(0),
                    "type": expr_type,
                    "position": match.start(),
                })
        
        return expressions
    
    def _extract_indicators(self, text_lower: str) -> List[Dict]:
        """Extract economic indicators."""
        indicators = []
        for name, code in self.INDICATORS.items():
            if name in text_lower:
                indicators.append({
                    "name": name.upper(),
                    "code": code,
                    "confidence": 0.9,
                })
        return indicators
    
    def _extract_relations(self, text: str) -> List[EntityRelation]:
        """Extract relationships between entities."""
        relations = []
        for pattern, rel_type in self.RELATION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                relations.append(EntityRelation(
                    source_entity=match.group(1),
                    target_entity=match.group(2),
                    relation_type=rel_type,
                    confidence=0.6,
                    context=match.group(0),
                ))
        return relations
    
    def _spacy_extract(self, text: str) -> List[Dict]:
        """Use spaCy for additional NER."""
        entities = []
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                })
        return entities
