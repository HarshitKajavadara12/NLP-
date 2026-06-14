"""
LLM ANALYZER — Deep text analysis using OpenAI GPT models.

Provides sophisticated linguistic analysis beyond what spaCy/BERT can do:
- Nuanced sentiment with reasoning
- Strategic intent detection
- Hidden message extraction
- Scenario narrative generation
- Market psychology analysis
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional


# Graceful import
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class LLMAnalyzer:
    """
    Deep text analysis using OpenAI GPT models.
    
    Falls back to rule-based analysis if OpenAI is not available.
    """
    
    SYSTEM_PROMPT = """You are a senior financial analyst with expertise in:
- Central bank communications and forward guidance
- Macro-economic data interpretation
- Corporate earnings analysis
- Geopolitical risk assessment
- Market psychology and behavioral finance

Analyze the provided text and respond in JSON format as instructed."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Args:
            api_key: OpenAI API key (reads OPENAI_API_KEY env if None)
            model: Model to use
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.available = HAS_OPENAI and bool(self.api_key)
        
        if self.available:
            self.client = openai.OpenAI(api_key=self.api_key)
            print(f"[LLM] Initialized with model {model}")
        else:
            self.client = None
            reason = "openai not installed" if not HAS_OPENAI else "no API key"
            print(f"[LLM] Fallback mode ({reason})")
    
    def analyze_deep_sentiment(self, text: str) -> Dict:
        """
        Deep sentiment analysis with reasoning chain.
        
        Returns:
            {sentiment, confidence, reasoning, nuances, hidden_sentiment}
        """
        if not self.available:
            return self._fallback_sentiment(text)
        
        prompt = f"""Analyze this financial news text for sentiment.

TEXT: {text}

Return JSON:
{{
    "sentiment": "bullish" | "bearish" | "neutral" | "mixed",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "nuances": ["list of subtle sentiment indicators"],
    "hidden_sentiment": "any sentiment the text tries to hide or downplay",
    "market_implications": "what this means for markets",
    "time_horizon": "immediate" | "short_term" | "medium_term" | "long_term"
}}"""
        
        return self._call_llm(prompt)
    
    def detect_strategic_intent(self, text: str, source: str = "") -> Dict:
        """
        Detect strategic communication intent.
        
        Returns:
            {intent, target_audience, desired_effect, manipulation_risk}
        """
        if not self.available:
            return self._fallback_intent(text)
        
        prompt = f"""Analyze the strategic communication intent of this text.
Source: {source}

TEXT: {text}

Return JSON:
{{
    "primary_intent": "inform" | "reassure" | "warn" | "manipulate" | "deflect" | "signal",
    "target_audience": "who this is aimed at",
    "desired_market_effect": "what market reaction the author wants",
    "manipulation_risk": 0.0-1.0,
    "credibility_assessment": 0.0-1.0,
    "key_phrases": ["phrases revealing intent"],
    "what_is_unsaid": "important omissions"
}}"""
        
        return self._call_llm(prompt)
    
    def generate_scenario_narrative(self, event_summary: str,
                                    scenarios: List[Dict]) -> Dict:
        """
        Generate rich narrative descriptions for scenarios.
        """
        if not self.available:
            return {"narratives": scenarios}
        
        prompt = f"""Given this market event and scenarios, create rich narratives.

EVENT: {event_summary}

SCENARIOS: {json.dumps(scenarios[:5], indent=2)}

For each scenario, return JSON:
{{
    "narratives": [
        {{
            "scenario_name": "name",
            "narrative": "2-3 sentence story of how this plays out",
            "key_drivers": ["what drives this outcome"],
            "warning_signs": ["early indicators this scenario is unfolding"],
            "recommended_positioning": "how to position for this"
        }}
    ]
}}"""
        
        return self._call_llm(prompt)
    
    def analyze_fed_language(self, text: str) -> Dict:
        """
        Specialized analysis for central bank communications.
        """
        if not self.available:
            return self._fallback_fed(text)
        
        prompt = f"""Analyze this central bank / Fed communication.

TEXT: {text}

Return JSON:
{{
    "hawkish_dovish_score": -1.0 to 1.0 (negative=dovish, positive=hawkish),
    "policy_direction": "tightening" | "easing" | "holding" | "unclear",
    "forward_guidance_strength": 0.0-1.0,
    "dissent_signals": ["any hints of internal disagreement"],
    "key_phrase_changes": ["notable language changes from previous"],
    "data_dependency": "what data they're watching",
    "market_rate_implications": "what this means for rates",
    "confidence_in_outlook": 0.0-1.0
}}"""
        
        return self._call_llm(prompt)
    
    def _call_llm(self, user_prompt: str) -> Dict:
        """Call the LLM and parse JSON response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response", "raw": content}
        except Exception as e:
            return {"error": str(e)}
    
    # ================================================================
    # FALLBACK (rule-based when no API key)
    # ================================================================
    
    def _fallback_sentiment(self, text: str) -> Dict:
        text_lower = text.lower()
        
        bullish = sum(1 for w in ["growth", "surge", "rally", "beat",
                                   "strong", "optimism", "upgrade", "buy"]
                      if w in text_lower)
        bearish = sum(1 for w in ["decline", "crash", "fear", "miss",
                                   "weak", "recession", "downgrade", "sell"]
                      if w in text_lower)
        
        if bullish > bearish:
            sentiment = "bullish"
        elif bearish > bullish:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "confidence": 0.4,
            "reasoning": "Rule-based fallback (no LLM)",
            "nuances": [],
            "hidden_sentiment": "unknown",
            "market_implications": "requires deeper analysis",
            "time_horizon": "short_term",
            "_fallback": True,
        }
    
    def _fallback_intent(self, text: str) -> Dict:
        return {
            "primary_intent": "inform",
            "target_audience": "general market",
            "desired_market_effect": "unknown",
            "manipulation_risk": 0.3,
            "credibility_assessment": 0.5,
            "key_phrases": [],
            "what_is_unsaid": "unknown without LLM",
            "_fallback": True,
        }
    
    def _fallback_fed(self, text: str) -> Dict:
        text_lower = text.lower()
        
        hawkish = sum(1 for w in ["inflation", "tightening", "hike",
                                   "restrictive", "vigilant"]
                      if w in text_lower)
        dovish = sum(1 for w in ["employment", "easing", "cut",
                                  "accommodative", "patient"]
                     if w in text_lower)
        
        score = (hawkish - dovish) / max(hawkish + dovish, 1)
        
        return {
            "hawkish_dovish_score": round(score, 2),
            "policy_direction": "unclear",
            "forward_guidance_strength": 0.3,
            "dissent_signals": [],
            "key_phrase_changes": [],
            "data_dependency": "unknown",
            "market_rate_implications": "requires LLM analysis",
            "confidence_in_outlook": 0.5,
            "_fallback": True,
        }
