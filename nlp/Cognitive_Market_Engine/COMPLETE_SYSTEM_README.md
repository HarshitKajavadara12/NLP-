# Cognitive Market Engine — Complete System Explanation

## What This System Is

This is a **Cognitive Finance System** — not a sentiment analysis bot, not a price predictor. It simulates how **5 different types of market participants think about the same news differently**, finds where they disagree, and generates trading signals from that structural disagreement.

**~38,000 lines of Python | 78 files | 120+ classes | 3 pipelines | 22+ alpha signal generators**

---

## How to Run It (Input → Output)

### Running the System

```bash
# Basic demo — processes 3 hardcoded financial news events
python main.py

# Live mode — fetches real news every 60 seconds
python main.py --live

# Dashboard UI — Streamlit at localhost:8501
python main.py --dashboard

# Process single news text
python main.py --news "Federal Reserve signals unexpected dovish pivot"

# Backtest on historical events (2024-2025)
python run_cognitive_backtest.py

# Quick pipeline test
python simple_test.py
```

### What You Give It (Input)

| Parameter | Type | Example |
|-----------|------|---------|
| `raw_text` | string | "Federal Reserve signals unexpected dovish pivot amid rising unemployment" |
| `source_id` | string | "Reuters", "Bloomberg", "CNBC" |
| `asset_scope` | list | `["BTC", "ETH", "SPY"]` |
| `macro_scope` | list | `["rates", "monetary-policy", "inflation"]` |

You feed it **raw financial news text**. That's it. The system does everything else.

### What You Get Back (Output)

A **TradableSignal** — not just "buy/sell" but a complete execution plan:

```
Signal Type:             liquidity_arbitrage / volatility_capture / passive_accumulation / 
                         regime_fade / aggressive_mean_reversion / liquidity_provision / no_trade
Direction:               BUY / SELL / NEUTRAL
Strength:                0.0 – 1.0
Confidence:              VERY_LOW / LOW / MEDIUM / HIGH / VERY_HIGH
Execution Mode:          passive / algorithmic / aggressive
Position Size:           1% – 10% of account
Stop Loss:               2% – 10% (volatility-adjusted)
Profit Target:           1.5% – 7%
Entry Window:            0 – 300 seconds (when to enter)
Hold Duration:           2 minutes – 1 hour
Reason:                  "High expectation collision between retail panic sellers and 
                         institutional liquidity providers creates structural opportunity"
Who Drove It:            [retail_panic, market_maker_withdrawal, hedge_fund_conviction]
What Kills It:           [conditions that would invalidate this signal]
```

---

## What Happens Inside (The Full Process)

### Step 1: Linguistic Shock Detection

The system doesn't ask "is this news good or bad?" — it asks "how SHOCKING is this news structurally?"

```
Raw Text → LinguisticShockVector:
  ├── surprise_level      [0,1]  — how unexpected is this?
  ├── ambiguity_level     [0,1]  — how unclear is the meaning?
  ├── certainty_level     [0,1]  — how definitive is the language?
  ├── authority_strength   [0,1]  — how credible is the source?
  ├── novelty_score       [0,1]  — is this new information?
  ├── temporal_focus       — PAST / PRESENT / FUTURE / AMBIGUOUS
  ├── narrative_shift      — NONE / WEAK / STRONG / REGIME_CHANGE
  ├── is_macro            — true/false
  └── is_asset_specific   — true/false
```

Uses **spaCy** for linguistic parsing (sentence structure, entities, verb tense, voice detection) + **BART-MNLI** for zero-shot classification into 12 narrative categories.

### Step 2: Five Participant Models Think Differently

The same LinguisticShockVector gets processed by 5 different cognitive models — each simulating a different type of market participant:

| Participant | Reaction Time | What They Care About | Behavior |
|-------------|---------------|---------------------|----------|
| **Retail Trader** | 3 minutes | Narrative tone, fear/excitement | uncertainty + novelty → PANIC or FOMO |
| **HFT Algorithm** | 0.001 seconds | Other participants' reactions | `belief_shift = 0.0` (doesn't believe news at all) |
| **Hedge Fund** | 10 minutes | Thesis validation/invalidation | certainty + authority → conviction trade |
| **Bank/Institution** | 1 hour | Regulatory keywords, balance sheet risk | authority + regulation → slow rebalancing |
| **Market Maker** | 0.01 seconds | Ambiguity → risk | ambiguity → widen spreads → reduce inventory |

Each produces:
- **CognitiveState**: belief_shift, risk_perception, confidence, urgency, uncertainty
- **ExpectationVector**: where they think volatility/liquidity/spreads/direction are going
- **BehaviorIntention**: how aggressively they'll act, patience, size, execution style

### Step 3: Expectation Collision (Where Alpha Lives)

This is the **core insight** of the entire system. Alpha doesn't come from predicting price — it comes from predicting **where participants disagree**.

The `ExpectationCollisionEngine` computes:

```
1. Expectation Variance     = How much do participants disagree on volatility/liquidity/spreads?
2. Direction Disagreement   = |buyers - sellers| / total (0 = half buying half selling)
3. Timing Disagreement      = std(when they think peak impact happens)
4. Magnitude Disagreement   = std(how big they think the move will be)
5. Liquidity Stress         = total_provision - total_consumption  (negative = danger)
6. Reaction Sequencing      = Who acts first? (HFT > Market Maker > Retail > Hedge Fund > Bank)

→ Market Stress Index = 0.25×variance + 0.25×|liquidity_stress| + 0.25×mean_vol + 0.25×(MM_withdrawing?)
```

**Key Formula:**
```
If Market Makers are WITHDRAWING liquidity (spread_expectation > 0.6)
  AND Retail is PANICKING (belief_shift > 0.5)
  AND Hedge Funds are BUYING (direction_bias < -0.3)
→ This is a "retail panic window" = buy opportunity
```

### Step 4: Signal Translation

The `TradableSignalTranslator` applies safety gates before generating signals:

```
Gate 1: confidence_in_assessment ≥ 0.5   (else NO_TRADE)
Gate 2: structural_opportunity ≥ 0.4     (else NO_TRADE)
```

Then selects signal type based on market stress:

| Condition | Signal Type |
|-----------|-------------|
| Retail panic + liquidity drain | `aggressive_mean_reversion` |
| High disagreement + vol spike | `volatility_capture` |
| Liquidity providers withdrawing | `liquidity_provision` |
| Regime fragility high | `regime_fade` |
| Gradual accumulation opportunity | `passive_accumulation` / `passive_distribution` |
| Spread/flow mismatch | `liquidity_arbitrage` |

**Position Sizing**: `strength × 10%` of account (halved if urgent)  
**Stop Loss**: `volatility_stress × 8% + 2%` (range: 2-10%)

---

## The Three Pipelines

```
┌─────────────────────────────────────────────────────────────┐
│  Pipeline A: 4-Phase Cognitive Engine (engine/ folder)       │
│  ┌─────────────┐ → ┌──────────────┐ → ┌──────────┐ → ┌────────┐  │
│  │ Linguistic  │   │ 5 Participant│   │Collision │   │ Signal │  │
│  │ Shock       │   │ Cognition    │   │ Engine   │   │Translate│  │
│  └─────────────┘   └──────────────┘   └──────────┘   └────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Pipeline B: 7-Phase Operational (legacy, separate modules)  │
│  News → Cognition → Behavior → Impact → Reality → Auth → Exec │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Pipeline C: Unified Bridge (pipeline_bridge.py)             │
│  Modes: engine_only | phase_only | hybrid (default)         │
│  Hybrid = Engine for analysis + Phases 3-7 for execution    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Sources

| Source | What It Provides | API Key? |
|--------|-----------------|----------|
| **NewsAPI** | 80,000+ news sources, headlines, articles | Yes |
| **GDELT** | Global events in 100+ languages, entity tone, Goldstein scale | No (free) |
| **RSS Feeds** | Custom financial RSS (Reuters, Bloomberg, etc.) | No |
| **Reddit** | Subreddit sentiment (r/wallstreetbets, r/stocks) | Yes |
| **Twitter** | Real-time financial tweets | Yes |
| **CoinGecko** | Crypto prices for live validation | Optional |
| **yfinance** | Historical BTC-USD prices for backtesting | No |

The `NewsAggregator` class deduplicates across sources (semantic + hash), rate-limits (NewsAPI: 95/day, GDELT: 500/hour), and retries with exponential backoff.

---

## Why These Technologies (And Not Others)

| Technology | Why This One | Why Not The Alternative |
|------------|-------------|----------------------|
| **spaCy** | Production-grade NLP: gives sentence structure, SVO triples, verb tense, named entities, dependency parsing — all needed for Linguistic Shock Vectors | NLTK is slower, less accurate. Stanza is heavier. spaCy gives exactly what's needed for structural text analysis without overhead |
| **BART-MNLI** (facebook/bart-large-mnli) | Zero-shot classification — classifies news into 12 categories WITHOUT any training data or fine-tuning | Fine-tuned models need labeled datasets (expensive). BART-MNLI uses natural language inference — give it any categories and it works immediately |
| **MiniLM** (all-MiniLM-L6-v2) | Sentence embeddings for semantic similarity & deduplication — only 22M params, runs on CPU | BERT is 340M params. GPT embeddings need API calls. MiniLM is 15× smaller, 5× faster, 95% as accurate |
| **DeBERTa-NLI** | Cross-encoder for high-accuracy claim verification | Bi-encoders are fast but less accurate. Cross-encoders compare sentences directly for precise entailment checking |
| **NetworkX** | Knowledge graph of entity relationships (Fed→rates→markets influence chains) | Neo4j needs a server. ArangoDB is complex. NetworkX is pure Python, zero config, perfect for research-scale graphs |
| **SQLite** | Signal cache, news history, execution log — zero config, file-based | PostgreSQL needs a server + maintenance. For a single-process research system, SQLite is faster and simpler |
| **Streamlit** | Dashboard in 1 Python file — perfect for research prototyping | React/Vue need frontend build tools. Dash is verbose. Streamlit: `streamlit run app.py` → done |
| **NumPy/SciPy** | Matrix math for collision computation (variance, cross-correlation) | Standard. No alternative needed for numerical computing |
| **feedparser** | Standard RSS parsing library | Only real option for Python RSS |
| **schedule** | Lightweight cron-like periodic task runner | APScheduler is heavier than needed. `schedule` is 1 file, simple API |

---

## The Creator's Thinking: Why This System Exists

### The Core Insight

> "Every sentiment analysis system in the world asks: Is this news GOOD or BAD?  
> That's the wrong question.  
> The right question is: WHO interprets this differently, and WHERE do they COLLIDE?"

### The Problem With Traditional NLP Trading

```
Traditional System:
  News → FinBERT → "0.73 positive" → Buy Signal

Problems:
  1. A bank and a retail trader read the same news COMPLETELY DIFFERENTLY
  2. "Positive" for who? Positive for bonds? Positive for stocks? Positive for vol?
  3. The signal ignores WHO is acting, WHEN they act, and HOW MUCH liquidity exists
  4. Everyone using the same FinBERT signal = crowded trade = alpha = 0
```

### What The Creator Realized

The creator observed that **market microstructure** (who acts, when, how fast, how much) matters more than sentiment direction. Specifically:

1. **HFT doesn't believe news** — it trades other people's reactions to news
2. **Market Makers widen spreads on ambiguity** — reducing liquidity exactly when retail needs it
3. **Retail panics on novelty** — creating predictable liquidity events
4. **Banks move last** — their slow rebalancing creates persistent flow
5. **Hedge Funds confirm or deny thesis** — their conviction creates momentum

By modeling **all five simultaneously** and finding where they DISAGREE, you identify **structural opportunities** that no single-participant model can see.

### The Intellectual Chain

```
Step 1: "Sentiment is useless because it's one number for many different actors"
Step 2: "What if I model each actor's COGNITIVE PROCESS separately?"
Step 3: "The alpha isn't in the prediction — it's in the COLLISION of predictions"
Step 4: "If retail panics AND market makers withdraw AND hedge funds are buying...
         that's a structural buy signal"
Step 5: "Signals should be STRUCTURAL (liquidity, volatility, regime) not DIRECTIONAL"
Step 6: "What about information that's HIDDEN? What's NOT being said?"
```

### Why "Cognitive" and Not Just "Multi-Agent"

The system doesn't just assign different weights to different participants. It models their actual **cognitive transformation function**:

```python
# Retail: novelty and uncertainty → panic
panic_factor = shock.novelty_score * shock.ambiguity_level * (1 - shock.certainty_level)

# HFT: doesn't process news content at all
belief_shift = 0.0  # literal zero — HFT trades market structure, not news

# Hedge Fund: authority and certainty → thesis validation
thesis_impact = shock.authority_strength * shock.certainty_level * news_relevance

# Market Maker: ambiguity → liquidity withdrawal
spread_response = shock.ambiguity_level * 0.8 + shock.surprise_level * 0.6

# Bank: regulatory keywords → compliance-driven action
regulatory_trigger = contains_regulatory_keywords(news) * shock.authority_strength
```

---

## Hidden Truth Detection (The "Silence Is Louder" Module)

The system has 4 sub-modules that detect **information manipulation**:

| Module | What It Detects | Logic |
|--------|----------------|-------|
| **CrossSourceAnalyzer** | Coordinated narratives, single-source stories, conflicting claims | If Reuters says X but Bloomberg says Y → investigate. If only 1 source reports → suspicious |
| **OmissionDetector** | What's NOT being said | Has predefined "TOPIC_EXPECTATIONS": a Fed rate decision MUST mention forward guidance, dot plot, vote count. If missing → deliberate omission |
| **TimingAnalyzer** | Strategic release timing | Friday 5PM news dumps, pre-FOMC positioning stories, holiday releases → manufactured narrative |
| **NarrativeTracker** | Story evolution and consensus formation | Tracks how narrative shifts over time. Sudden consensus = potential manipulation |

> **"The most powerful lies are told through silence."** — System design philosophy

---

## Alpha Signal Generators (22+ Signals)

### 12 Standard Market Signals

| Signal | Data Source | What It Finds |
|--------|------------|---------------|
| Positioning | CFTC COT reports | When speculators are extremely positioned (contrarian) |
| Order Flow | Level 2 order book | Imbalance, sweeps, iceberg orders |
| Volatility Surface | Options chain | Skew, term structure inversion, IV rank |
| Cross-Asset Lead-Lag | Multi-asset prices | Which markets lead others |
| Sentiment Extremes | Fear&Greed, AAII, VIX | Contrarian signals at extremes |
| Fund Flows | ETF/mutual fund data | Where money is moving |
| Calendar Effects | Date/time | Month-end rebalance, FOMC drift, OpEx |
| Earnings Revisions | Analyst estimates | Revision momentum (up/down breadth) |
| Insider Trading | SEC Form 4 | Cluster buying by executives |
| Credit Markets | CDS, HY spreads | Credit stress before equity reacts |
| Macro Surprises | Economic releases | Surprise vs consensus (like Citi ESI) |
| Central Bank Balance Sheet | Fed/ECB/BoJ/PBoC | Global liquidity impulse, QE/QT |

### 5 NLP-Specific Alpha Signals

| Signal | Logic |
|--------|-------|
| News Velocity | Rate of news flow acceleration → >2σ = go with trend; >3σ = crowded; drop = revert |
| Narrative Shift | When media tone changes direction from consensus |
| Hidden Truth | Trade OPPOSITE of detected manipulation |
| Event Surprise | Compare pre-event positioning with actual outcome |
| Cross-Source Divergence | When sources disagree, trade the most credible one |

### 5 Structural Alpha Gaps

| Signal | Logic |
|--------|-------|
| Contrarian | Fade when 80%+ agree + extreme positioning |
| Mean Reversion | Post-shock reversion after retail panic (hold 2-8 hours) |
| Momentum | Trend-following during confirmed regimes |
| Cross-Event Memory | Pattern match against similar historical events |
| Microstructure | Order book structure exploitation |

---

## Backtesting System

### Historical Events Used (Real Events, 2024-2025)

| Event | Actual Price Impact |
|-------|-------------------|
| SEC Bitcoin ETF Approval (Jan 2024) | Measured 1h/4h/24h after |
| BTC $72K All-Time High (Mar 2024) | Measured 1h/4h/24h after |
| Bitcoin Halving (Apr 2024) | Measured 1h/4h/24h after |
| Japan Carry Trade Crash (Aug 2024) | Measured 1h/4h/24h after |
| Trump Election Win (Nov 2024) | Measured 1h/4h/24h after |
| BTC Breaks $100K (Dec 2024) | Measured 1h/4h/24h after |
| Various Fed Decisions | Measured 1h/4h/24h after |

Uses **yfinance** for real BTC-USD historical prices.

### Backtest Configuration

```
Initial Capital:      $100,000
Max Position Size:    8% of account
Default Stop Loss:    2.5%
Default Profit Target: 5%
Max Holding Time:     48 hours
Snapshot Interval:    4 hours
```

### What It Measures

| Metric | What It Shows |
|--------|--------------|
| Total Return | Overall P&L |
| Annualized Return | Yearly equivalent |
| Sharpe Ratio | Risk-adjusted return (target: >1.0) |
| Sortino Ratio | Downside-risk-adjusted return |
| Max Drawdown | Worst peak-to-trough |
| Win Rate | % of profitable trades (target: >55%) |
| Profit Factor | Gross profit / Gross loss |
| Directional Accuracy | Did the direction prediction match reality? (target: 60-70%) |
| Confidence Calibration | When system says 80% confident, is it right 80% of the time? |

---

## Dashboard (What the UI Shows)

7-page Streamlit dashboard:

| Page | Shows |
|------|-------|
| System Overview | Pipeline health, modules loaded, events processed |
| Signal Monitor | Active signals with direction, strength, entry/exit times |
| Model Credibility | Per-participant accuracy (EMA-tracked, self-adjusting) |
| Correlation Matrix | Cross-asset correlation heatmap |
| Scenario Analysis | Branching probability trees (base/bull/bear/tail) |
| Hidden Truth Alerts | Detected manipulation, omissions, timing anomalies |
| News Feed | Live articles with NLP annotations and shock vectors |

---

## System Configuration

### Key Parameters (`config/system_config.py`)

| Setting | Value | Meaning |
|---------|-------|---------|
| News update frequency | 60 seconds | How often to check for new articles |
| Max concurrent events | 100 | Process 100 news events simultaneously |
| Directional accuracy threshold | 65% | Below this, model credibility degrades |
| Signal expiration | 4 hours | Signals auto-expire if not acted on |
| Max position | $1,000,000 | Hard limit per position |
| Max exposure | 80% | Never more than 80% of capital deployed |
| Daily loss limit | -$50,000 | Stop trading for the day |
| Intraday drawdown limit | -$30,000 | Reduce position sizes |
| Vol spike threshold | 2.5× | If vol > 2.5× normal, special handling |
| Feedback loop | Enabled | System learns from past predictions |

### Risk Management Gates

Before ANY signal can execute:
- Max 15% position size
- Max 10% portfolio drawdown
- Max 80% correlation between positions
- Max 10 trades per day
- Minimum 55% confidence required

---

## How The Creator Built This (Development Logic)

### Phase 1: Foundation
Built the `NewsEvent` data model first — proved that text can be decomposed into structural linguistic properties WITHOUT assigning sentiment.

### Phase 2: Cognitive Models  
Created 5 separate participant models, each with different:
- Information processing speed (0.001s to 3600s)
- What dimensions they react to (ambiguity, certainty, authority, novelty)
- Whether they even believe the news (HFT: literally no)

### Phase 3: Collision Math
Invented the "Expectation Collision" concept — computing disagreement across participants as the source of alpha. Built the math for variance, timing disagreement, liquidity stress.

### Phase 4: Signal Safety
Added execution-safe signal generation with gates, stops, time limits. Signals are structural (liquidity, volatility, regime) not just "buy/sell."

### Phase 5: Hidden Truth
Added manipulation detection (omissions, timing, cross-source conflicts). Trade AGAINST detected manipulation.

### Phase 6: 22+ Alpha Sources
Added classical market signals (positioning, flows, credit, calendar) alongside NLP signals. Unified through `AlphaSignalAggregator`.

### Phase 7: Backtesting & Validation
Built historical replay with real events and prices. Self-adjusting credibility system that downgrades poorly-performing participant models.

---

## What Makes This Different From Everything Else

| Traditional Approach | This System |
|---------------------|------------|
| News → Sentiment → Trade | News → 5 different interpretations → Disagreement → Structural trade |
| One model for all text | 5 cognitive models, each thinking differently |
| Positive = Buy | "Positive for WHO?" is the actual question |
| Predict price direction | Predict market STRUCTURE (liquidity, volatility, regime) |
| Ignore who's in the market | Model each participant's speed, size, belief system |
| Trust all news equally | Detect manipulation, omissions, coordinated narratives |
| Same signal for everyone | Signal depends on who's already acting and how fast |
| Static model | Self-adjusting credibility with feedback loop |

---

## Technical Requirements

```
Python >= 3.8
Key Libraries:
  spacy (+ en_core_web_sm model)
  transformers (HuggingFace)
  torch
  numpy, scipy
  networkx
  streamlit
  feedparser
  schedule
  python-dotenv
  yfinance (for backtesting)
  praw (Reddit, optional)
  tweepy (Twitter, optional)
```

### Models Auto-Downloaded on First Run
- `facebook/bart-large-mnli` (~1.6GB) — zero-shot classification
- `sentence-transformers/all-MiniLM-L6-v2` (~90MB) — embeddings
- `cross-encoder/nli-deberta-v3-small` (~140MB) — claim verification

---

## File Structure

```
Cognitive_Market_Engine/
├── main.py                          # Entry point (demo/live/dashboard/test)
├── run_live.py                      # Standalone live monitor
├── run_cognitive_backtest.py        # Full historical backtest
├── pipeline_bridge.py               # Unifies Pipeline A + B
├── config/                          # All system parameters
├── engine/                          # Pipeline A: Cognitive Engine (4 phases)
│   ├── core_cognitive_structures.py # All data structures (enums, dataclasses)
│   ├── participant_models.py        # 5 cognitive models
│   ├── expectation_collision_engine.py # Collision math (alpha source)
│   ├── cognitive_market_system.py   # Main orchestrator
│   └── tradable_signal_translator.py # Signal generation
├── nlp_engine/                      # Deep NLP: spaCy + transformers
├── news_model/                      # News event data model + parser
├── news_ingestion/                  # Multi-source fetching (NewsAPI, GDELT, RSS)
├── hidden_truth/                    # Manipulation detection (4 sub-modules)
├── scenario_engine/                 # Probability-weighted scenario trees
├── decision_system/                 # Final decision with risk gates
├── alpha_models/                    # 22+ signal generators
├── execution/                       # Order execution with safety limits
├── storage/                         # SQLite + NetworkX knowledge graph
├── streaming/                       # Real-time event bus
├── multi_asset/                     # Cross-asset correlation + contagion
├── learning/                        # Feedback loop (credibility EMA)
├── backtesting/                     # Historical replay + performance analytics
├── dashboard/                       # Streamlit 7-page UI
├── participant_cognition/           # Phase 2 legacy
├── market_response/                 # Phase 3 legacy (behavior translation)
├── market_impact/                   # Phase 4 legacy (impact aggregation)
├── reality_validation/              # Phase 5 legacy (prediction validation)
├── signal_auth/                     # Phase 6 legacy (trust scoring)
├── reports/                         # Generated analysis reports
└── tests/                           # Test suite
```

---

## Summary

This system represents a fundamentally different approach to NLP-driven trading. Instead of the simplistic `text → sentiment → buy/sell` pipeline that every other system uses, it models the **cognitive diversity of market participants** and finds alpha in their **structural disagreements**.

The creator's thesis: **Alpha doesn't come from better prediction. It comes from understanding that the same information means different things to different people, and trading the moments when their beliefs collide.**
