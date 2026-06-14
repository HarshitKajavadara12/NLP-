# Market Cognition System

## Purpose

This system proves that **the same news produces different interpretations for different market participants**, and models how those differences express themselves in market behavior.

This is NOT a sentiment analyzer.
This is NOT a price predictor.
This is a **cognitive finance system** that studies how markets interpret information.

---

## Core Hypothesis

**News does not move markets. Interpretation moves markets.**

Different agents interpret the same news differently:
- Banks see balance sheet risk
- HFTs see volatility opportunity
- Hedge funds see portfolio implications
- Retail traders see fear or excitement

We model these different interpretations and prove they lead to different behaviors.

---

## System Architecture

### Phase 1: News Event Data Model (  COMPLETE)
- Converts raw news text into structured linguistic objects
- Preserves ambiguity and uncertainty
- NO sentiment, NO trading signals, NO market interpretation
- **Status:** 12/12 tests pass

### Phase 2: Participant Cognitive Models (Next)
- Models how different agent types interpret the same news
- Banks vs HFTs vs Hedge Funds vs Retail
- Maps interpretation → expected behavior
- **Status:** Design locked, implementation pending

### Phase 3: Market Response Analysis (Later)
- Measures actual market behavior after news
- Validates whether interpretation models predict behavior
- Identifies which participants acted and when
- **Status:** Pending Phase 2 completion

### Phase 4: Decision System (Final)
- Research mode: Prove causality
- Trading mode (optional): Use validated models for trading
- **Status:** Pending Phase 3 validation

---

## Quick Start

### Run Phase 1 Tests
```bash
cd market_cognition_system
python tests/test_phase_1.py
```

Expected output:
```
RESULTS: 12 passed, 0 failed
  PHASE 1 COMPLETE AND VERIFIED
```

### Create a News Event
```python
from phase_1_news_model.parser import NewsEventParser
from datetime import datetime

parser = NewsEventParser()

event = parser.parse(
    timestamp_utc=datetime(2026, 1, 10, 14, 30, 0),
    source="Reuters",
    raw_text="The Federal Reserve signaled patience on rate cuts."
)

print(event.get_summary())
print(f"Actors: {[a.name for a in event.actors]}")
print(f"Ambiguity: {event.ambiguity_score:.2f}")
print(f"Uncertainty: {event.has_uncertainty()}")
```

---

## Key Files

| File | Purpose |
|------|---------|
| `phase_1_news_model/news_event.py` | NewsEvent data model |
| `phase_1_news_model/parser.py` | Raw text → NewsEvent parser |
| `tests/test_phase_1.py` | 12 comprehensive tests |
| `PHASE_1_COMPLETE.md` | Detailed Phase 1 documentation |

---

## Design Principles

### 1. News ≠ Market Reaction
- News is linguistic (text)
- Market reaction is behavioral (price, volume, order flow)
- These are studied separately, never mixed

### 2. Raw Text is Sacred
- Never altered, truncated, or cleaned
- Can be re-interpreted with new models
- Original always retrievable

### 3. Ambiguity is Preserved
- Captured, not resolved
- Different agents interpret ambiguity differently
- Ambiguity can be the source of trading opportunity

### 4. No Premature Interpretation
- No sentiment scoring
- No buy/sell signals
- No market direction labels
- Interpretation comes from participant models (Phase 2)

### 5. Reproducibility
- Deterministic parsing
- Same input → same output
- Can validate with real data

---

## Example: Fed Rate Decision

### Raw News
```
"The Federal Reserve signaled patience on interest rate cuts today.
 Chair Powell stated the central bank may hold rates steady if 
 inflation persists above target."
```

### Phase 1 Output (NewsEvent)

```
event.raw_text
  → Exact original text, unchanged

event.actors
  → [Actor("Federal Reserve", "central_bank")]

event.semantic_claims
  → [Claim(Fed, "signal patience", "rates")]

event.modality_markers
  → ["may", "if"] (uncertainty markers)

event.ambiguity_score
  → 0.7 (somewhat vague due to "may" and "if")

event.narrative_types
  → [NarrativeType.MACRO_POLICY]

event.participant_interpretations
  → {} (empty, will be filled in Phase 2)
```

### Phase 2 Output (Different Interpretations)

```
Bank interpretation:
  "Rates stay higher longer → margin compression risk"
  Expected behavior: Reduce duration exposure

HFT interpretation:
  "Ambiguous signal → volatility spike expected"
  Expected behavior: Deploy vol-trading algorithms

Hedge Fund interpretation:
  "Supports my rate-duration thesis"
  Expected behavior: Maintain positioning

Retail interpretation:
  "Market confused → scary → sell"
  Expected behavior: Panic sell
```

### Phase 3 Output (Market Reality)

```
Observed market behavior:
  • Duration selling by banks   (predicted)
  • Vol spike in rates   (predicted)
  • Equity rally   (predicted from hedge fund positioning)
  • Retail selling   (predicted)
  
Conclusion: Interpretation models predict behavior accurately
```

---

## How This Differs From Traditional NLP

### Traditional Sentiment Analysis
```
Text → Sentiment Score (0 to 1) → Trading Signal

Problem: Same score, different meanings for different agents
```

### This System
```
Text → NewsEvent (linguistic container)
     → Bank Model → Bank Interpretation
     → HFT Model → HFT Interpretation
     → Hedge Fund Model → Hedge Fund Interpretation
     → Retail Model → Retail Interpretation

Insight: Same news, different meanings, different behaviors
```

---

## Requirements

```
Python >= 3.8
(No heavy dependencies for Phase 1)
```

---

## Status

**Phase 1:**   COMPLETE AND LOCKED
- 12/12 tests passing
- End-to-end working
- Ready for Phase 2

**Phase 2:**   DESIGNED, IMPLEMENTATION PENDING
- Participant cognitive models
- Interpretation frameworks
- Behavior prediction

---

## Contact

This is research-grade code.
Built from first principles for accuracy and clarity.

Key principle: **Prove interpretation matters. Then trade.**

---

## License

Research use. No warranties. Use at your own risk.
