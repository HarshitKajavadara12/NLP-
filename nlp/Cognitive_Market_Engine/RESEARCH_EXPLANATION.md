# Complete Research Explanation: Cognitive Market Engine (NLP-)

## What This Project Is

This is a **Cognitive Finance System** — an advanced NLP-driven platform that models how different market participants (banks, hedge funds, retail traders, HFTs, market makers) **interpret the same news differently** and how those different interpretations create market movements.

**Core Thesis:** "News does NOT move markets. INTERPRETATION moves markets."

This is NOT a simple sentiment analyzer. It models the actual cognitive processes of 5 different market participant types and predicts how their conflicting interpretations create price dynamics.

---

## The Researcher's Thinking & Motivation

### Why This Was Built:
1. Traditional NLP systems give a single sentiment score (positive/negative) — this is WRONG because different market players read the same headline differently
2. A bank reads "Fed signals patience on rate cuts" as a balance sheet risk signal
3. An HFT reads it as a volatility opportunity
4. A retail trader reads it as fear/excitement
5. The COLLISION between these different interpretations is what actually moves markets

### What Makes This Different From Other NLP Systems:
| Traditional NLP | This System |
|----------------|-------------|
| Single sentiment score | 5 different cognitive interpretations |
| News → positive/negative | News → linguistic shock → expectation collision → market stress |
| Predicts price direction | Models market behavior dynamics |
| One pipeline | Dual pipeline (Cognitive + Operational) unified by bridge |

---

## System Architecture (What Was Built)

### Scale:
| Metric | Value |
|--------|-------|
| Total Python files | ~78 |
| Total lines of code | ~42,000 |
| Classes | 120+ |
| Dataclasses | 80+ |
| Modules/Packages | 30+ |
| Test checks | 463 (100% pass rate) |

### The Dual Pipeline Architecture:

```
NEWS INPUT → [Pipeline A: 5-Layer Cognitive Engine]
           → [Pipeline B: 7-Phase Operational Pipeline]
           → [Pipeline C: Bridge merges both]
           → TRADING SIGNAL / RESEARCH OUTPUT
```

---

## Pipeline A: 5-Layer Cognitive Engine

**Purpose:** Deep cognitive modeling of how news creates market dynamics

| Layer | What It Does | Output |
|-------|-------------|--------|
| Layer 1: NLP Parser | Converts raw text → Linguistic Shock Vector | magnitude, direction, uncertainty, temporal_focus, narrative_shift |
| Layer 2: Participant Models | 5 different agents interpret the same news | 5 different ParticipantResponses |
| Layer 3: Expectation Collision | Measures disagreement between interpretations | MarketStressVector (9-step computation) |
| Layer 4: Signal Translator | Converts stress into actionable signals | TradableSignal (direction, confidence, size) |
| Layer 5: Knowledge Graph | Updates persistent entity relationships | Entity-relationship graph (36+ nodes) |

### The 5 Participant Models:

| Participant | How They Think | Time Horizon | Risk Focus |
|-------------|---------------|-------------|-----------|
| **Retail Trader** | Emotional, headline-driven, momentum-chasing | Short (days) | Low sophistication |
| **HFT (High Frequency)** | Speed-focused, volatility-seeking, statistical | Microseconds | Volatility opportunity |
| **Hedge Fund** | Multi-factor, contrarian, alpha-seeking | Weeks-months | Asymmetric risk/reward |
| **Bank** | Balance sheet, regulatory, systemic risk | Quarters-years | Capital adequacy |
| **Market Maker** | Liquidity provision, spread management, inventory | Intraday | Inventory balance |

---

## Pipeline B: 7-Phase Operational Pipeline

**Purpose:** Production operational flow from news to execution

| Phase | Module | What It Does |
|-------|--------|-------------|
| Phase 1: News Parsing | `news_model/` | Raw text → structured NewsEvent (actors, temporal markers, uncertainty, contradictions) |
| Phase 2: Cognitive Interpretation | `participant_cognition/` | 5 participants interpret → belief_shift, urgency, action_likelihoods |
| Phase 3: Behavior Translation | `market_response/` | Interpretations → behavioral postures (risk, liquidity, exposure intent) |
| Phase 4: Market Impact | `market_impact/` | Aggregate behaviors → 6D impact profile (liquidity, volatility, spread, order flow, price, regime) |
| Phase 5: Reality Validation | `reality_validation/` | Compare predictions vs actual market data (5 dimensions) |
| Phase 6: Signal Authorization | `signal_auth/` | Trust scoring, filtering (>0.6 threshold), signal normalization, 4-hour expiry |
| Phase 7: Execution | `execution/` | Kelly-inspired sizing, paper trading, $100K capital, risk management |

---

## NLP Engine: The Brain (5 Modules)

### Module 1: DeepNLPParser (1,303 lines)
**3-tier fallback:** Transformers → spaCy → Rule-based

What it extracts:
- Sentences with POS tags, dependencies, entities
- SVO triples (Subject-Verb-Object)
- Tense detection (past/present/future)
- Voice detection (active/passive)
- Certainty scoring (hedge words vs. boosting words)
- 12 narrative categories (classified via zero-shot BART-MNLI)
- Document embeddings (all-MiniLM-L6-v2)

### Module 2: Entity Extraction
Financial dictionaries:
- 18 central banks, 10 market indices, 9 currencies
- 9 commodities, 11 economic indicators
- 28 countries + 7 geopolitical blocs
- Monetary value normalization ($1.5B → 1,500,000,000)

### Module 3: Intent Detector (464 lines)
4-dimensional intent analysis:
- **Communication Intent:** INFORM, WARN, REASSURE, SIGNAL_POLICY, LEAK, DEFLECT
- **Strategic Intent:** MARKET_PREPARATION, DAMAGE_CONTROL, COMPETITIVE_POSITIONING
- **Target Audience:** GENERAL_PUBLIC, INSTITUTIONAL, RETAIL, POLICYMAKERS
- **Source Credibility:** Weighted by source reliability

### Module 4: Contradiction Detector (381 lines)
5 manipulation pattern types using NLI (Natural Language Inference):
- Direct contradiction between statements
- Hedging patterns (saying X while implying NOT X)
- Temporal contradictions
- Source credibility conflicts
- Narrative-vs-data mismatches

### Module 5: Advanced NLP (801 lines)
- Earnings call analysis
- Aspect-based sentiment
- Sarcasm/irony detection
- Multi-lingual financial NLP
- Financial embeddings

---

## Hidden Truth Detection System (4 Modules)

**Purpose:** Detect manipulation, lies, and hidden agendas in news

| Module | What It Detects | How |
|--------|----------------|-----|
| Cross-Source Verification | Conflicting narratives across sources | NLP-based similarity + trust scoring |
| Omission Detection | What's NOT being reported (strategic silence) | 7 event templates of expected coverage |
| Timing Analyzer | Suspicious timing patterns | 11 recurring event templates, news dump detection |
| Narrative Tracker | Manufactured consensus | >80% identical framing = manufactured |

---

## Scenario Engine

**Purpose:** Generate ALL possible outcomes from a news event

Components:
- **7 event templates** with 3-level branching (2nd/3rd order effects)
- **Monte Carlo Simulator:** 10,000 simulations → VaR, CVaR, max drawdown
- **Causal Chain Builder:** Multi-order causal effect propagation
- **Knowledge Graph Integration:** 36+ entities, 31+ edges

---

## Decision Engine (622 lines)

**8-Step Decision Pipeline:**
1. Collect signals from 8 sources (NLP, cognitive, behavior, impact, scenario, hidden_truth, reality, cross-asset)
2. Score each signal
3. Aggregate with regime-adaptive weights
4. Apply Risk Gates (max position %, max drawdown, max daily trades, min confidence)
5. Apply Hidden Truth filters
6. Determine action
7. Calculate position size (Kelly-inspired)
8. Set risk levels (stops, targets)

**7 Possible Actions:** BUY, SELL, HOLD, REDUCE, HEDGE, WATCH, EMERGENCY_EXIT

**5 Market Regimes (auto-detected):** CALM, TRENDING, VOLATILE, CRISIS, TRANSITIONING

---

## Execution Engine

| Parameter | Value |
|-----------|-------|
| Capital | $100,000 (paper trading) |
| Max Position | 15% of portfolio |
| Stop Loss | 2% |
| Take Profit | 3-4% |
| Sizing | Kelly-inspired formula |
| Circuit Breaker | Auto-halt on excessive losses |

---

## News Ingestion (3 Sources)

| Source | Type | Status |
|--------|------|--------|
| NewsAPI | API (requires key) | Configurable via .env |
| GDELT | Free global events API | Ready |
| RSS Reader | 15+ pre-configured financial feeds | Ready |

- Polling: 60-second intervals
- Deduplication: Content hash + 70% title overlap detection
- Async fetching with ThreadPoolExecutor

---

## Data Storage

### SQLite Database (9 tables):
- news_events, signals, trading_signals, decisions, executions, validation_records, feedback, models, metrics

### Knowledge Graph (NetworkX):
- 36+ seed entities (Federal Reserve, ECB, S&P 500, etc.)
- 31+ relationships (controls, influences, correlates_with)
- Updated dynamically from news events

---

## Alpha Models (31 Signal Generators)

| Category | Signals |
|----------|---------|
| Market Microstructure | OrderFlow, VolSurface, Positioning |
| Macro | CreditMarket, MacroSurprise, CentralBankBalance |
| Cross-Asset | LeadLag, Contagion, Correlation |
| NLP-derived | SentimentExtremes, NarrativeShift, Hidden Truth |
| Alternative | Insider Trading, CalendarEffects, EarningsRevisions |
| Behavioral | Crowding, FlowOfFunds |

---

## Market Intelligence Hub (9 Models)

Regime detection, correlation tracking, contagion modeling, volatility forecasting, liquidity monitoring, positioning analysis, flow tracking, cross-asset analysis, stress testing.

---

## What Results This System Produces

For every news event processed, the system outputs:

1. **Linguistic Shock Vector** — magnitude (0-1), direction, uncertainty level
2. **5 Participant Interpretations** — each with belief_shift, urgency, action_likelihoods
3. **Expectation Collision Metrics** — disagreement level, concentration, stress
4. **Market Impact Profile** — 6 dimensions (liquidity, volatility, spread, order flow, price, regime)
5. **Scenarios** — branching tree of possible outcomes with probabilities
6. **Hidden Truth Flags** — manipulation/deception warnings
7. **Trading Signal** — direction, confidence, recommended size, stops, targets
8. **Decision Packet** — action + reasoning trace + dissenting signals

---

## Technologies Used

| Technology | Purpose |
|-----------|---------|
| spaCy (en_core_web_sm) | NER, POS tagging, dependency parsing |
| Transformers (BART-MNLI) | Zero-shot narrative classification |
| Transformers (MiniLM) | Sentence embeddings for similarity |
| Transformers (DeBERTa-NLI) | Contradiction detection |
| NetworkX | Knowledge graph |
| SQLite (WAL mode) | Persistent storage |
| Streamlit | 7-page monitoring dashboard |
| NumPy/SciPy | Monte Carlo simulations, statistical analysis |
| CoinGecko API | Live cryptocurrency prices |
| NewsAPI / GDELT / RSS | News data ingestion |

---

## Design Principles

1. **Graceful Degradation:** Every module has fallbacks. No API key? Use demo data. No GPU? Use rule-based parsing.
2. **Event-Driven:** EventBus with pub/sub connects all modules
3. **Self-Learning:** FeedbackLoop with EMA (α=0.15) tracks accuracy, adjusts weights
4. **Deterministic:** Same input → same output (enforced by tests)
5. **Inaction is meaningful:** HOLD/WATCH are valid decisions, not failures

---

## How to Run

```bash
cd Cognitive_Market_Engine/

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Interactive demo
python main.py

# Process single news
python main.py --news "Federal Reserve signals patience on rate cuts"

# Live monitoring (60-second polling)
python main.py --live

# Dashboard
python main.py --dashboard

# Run tests
python main.py --test

# 7-Phase pipeline only
python legacy_main.py

# Unified bridge
python pipeline_bridge.py
```

---

## Conclusion

This is a **production-grade cognitive finance research system** (~42,000 lines) that goes far beyond traditional sentiment analysis. It models the actual cognitive diversity of market participants and proves that interpretation conflicts — not news itself — drive market behavior. The architecture is fully wired end-to-end with graceful degradation, self-learning, and paper trading execution.
