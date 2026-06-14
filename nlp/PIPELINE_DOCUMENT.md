# COGNITIVE MARKET ENGINE — PIPELINE DOCUMENT

## Purpose

This document describes every pipeline in the **Cognitive Market Engine (CME)** — an NLP-driven quantitative trading system that converts raw financial news text into structured cognitive models, market impact predictions, validated signals, and paper-trade executions. The system implements a **Dual-Pipeline Architecture** (5-Layer Cognitive Engine + 7-Phase Operational Pipeline) unified by a **Pipeline Bridge**.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Pipeline A — 5-Layer Cognitive Engine](#2-pipeline-a--5-layer-cognitive-engine)
3. [Pipeline B — 7-Phase Operational Pipeline](#3-pipeline-b--7-phase-operational-pipeline)
4. [Pipeline C — Unified Bridge](#4-pipeline-c--unified-bridge)
5. [Streaming Pipeline](#5-streaming-pipeline)
6. [NLP Processing Pipeline](#6-nlp-processing-pipeline)
7. [News Ingestion Pipeline](#7-news-ingestion-pipeline)
8. [Cognitive Modeling Pipeline](#8-cognitive-modeling-pipeline)
9. [Behavior Translation Pipeline](#9-behavior-translation-pipeline)
10. [Market Impact Pipeline](#10-market-impact-pipeline)
11. [Reality Validation Pipeline](#11-reality-validation-pipeline)
12. [Signal Authorization Pipeline](#12-signal-authorization-pipeline)
13. [Execution Pipeline](#13-execution-pipeline)
14. [Alpha Signal Pipeline](#14-alpha-signal-pipeline)
15. [Scenario Engine Pipeline](#15-scenario-engine-pipeline)
16. [Hidden Truth / Manipulation Detection Pipeline](#16-hidden-truth--manipulation-detection-pipeline)
17. [Market Intelligence Pipeline](#17-market-intelligence-pipeline)
18. [Multi-Asset Pipeline](#18-multi-asset-pipeline)
19. [Economics Pipeline](#19-economics-pipeline)
20. [Decision System Pipeline](#20-decision-system-pipeline)
21. [Feedback & Learning Pipeline](#21-feedback--learning-pipeline)
22. [Backtesting Pipeline](#22-backtesting-pipeline)
23. [Infrastructure Pipeline](#23-infrastructure-pipeline)
24. [Data Pipeline](#24-data-pipeline)
25. [Visualization & Dashboard Pipeline](#25-visualization--dashboard-pipeline)
26. [Alert Delivery Pipeline](#26-alert-delivery-pipeline)
27. [Storage Pipeline](#27-storage-pipeline)
28. [Advanced Analysis Pipeline](#28-advanced-analysis-pipeline)
29. [Configuration Pipeline](#29-configuration-pipeline)
30. [Complete Module & Class Registry](#30-complete-module--class-registry)

---

## 1. Architecture Overview

### Dual-Pipeline + Bridge Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          ENTRY POINTS                                │
│   main.py │ run_live.py │ legacy_main.py │ pipeline_bridge.py        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Pipeline A (Cognitive Engine)      Pipeline B (7-Phase Ops)        │
│   ┌─────────────────────────┐       ┌──────────────────────────┐    │
│   │ 1. News → LSV           │       │ Phase 1: News Parsing     │    │
│   │ 2. Cognitive Modeling   │       │ Phase 2: Participant Models│    │
│   │ 3. Expectation Collision│       │ Phase 3: Behavior Trans.  │    │
│   │ 4. Signal Translation   │       │ Phase 4: Market Impact    │    │
│   │ 5. Knowledge Graph      │       │ Phase 5: Reality Valid.   │    │
│   └─────────┬───────────────┘       │ Phase 6: Signal Auth      │    │
│             │                       │ Phase 7: Execution         │    │
│             │                       └──────────┬─────────────────┘    │
│             │                                  │                      │
│             └──────────┬───────────────────────┘                      │
│                        ▼                                              │
│              PipelineBridge (hybrid mode)                              │
│                        │                                              │
│             ┌──────────▼──────────┐                                   │
│             │   Unified Result    │                                   │
│             │ (merged signals)    │                                   │
│             └─────────────────────┘                                   │
├──────────────────────────────────────────────────────────────────────┤
│  SUPPORT LAYER: NLP Engine │ Alpha Models │ Hidden Truth │ Scenarios │
│                Intelligence │ Multi-Asset │ Economics │ Backtesting  │
│                Decision System │ Feedback Loop │ Alerts │ Storage    │
├──────────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE: EventBus │ MessageQueue │ TimeSeriesDB │ APILayer  │
│                  ModelRegistry │ FeatureStore │ CICD │ Monitoring   │
└──────────────────────────────────────────────────────────────────────┘
```

### Core Design Rules (Enforced by 90 Tests)

| Rule | Enforcement |
|------|-------------|
| Phase 1 outputs NO sentiment/trading signals | `test_phase_1.py` |
| Phase 2 outputs NO prices | `test_phase_2.py` |
| Phase 3 outputs NO trades/orders | `test_phase_3.py` |
| Phase 4 outputs NO price direction | `test_phase_4.py` |
| Phase 5 is research-only (NO trading) | `test_phase_5.py` |
| Action likelihoods sum to 1.0 | `test_phase_2.py` |
| Same input → same output (deterministic) | `test_phase_2.py` |
| Inaction is meaningful | `test_phase_3.py` |

---

## 2. Pipeline A — 5-Layer Cognitive Engine

**Package**: `engine/`
**Orchestrator**: `CognitiveMarketSystem`
**File**: `engine/cognitive_market_system.py` (431 lines)

### Layer Flow

```
Raw Text
    │
    ▼
Layer 1: DeepNLPParser.parse() → LinguisticShockVector
    │     (magnitude, direction, uncertainty, temporal_focus, narrative_shift)
    ▼
Layer 2: ParticipantModels.interpret() × 5 → ParticipantResponse[]
    │     (RetailTrader, HFT, HedgeFund, Bank, MarketMaker)
    ▼
Layer 3: ExpectationCollisionEngine.compute_collision()
    │     → ExpectationCollisionMetrics
    │     (9-step: extract → disagreement → magnitude → temporal →
    │      volatility → consensus → stress → regime → summary)
    ▼
Layer 4: TradableSignalTranslator.translate()
    │     → TradableSignal (multi-gate: confidence → direction → sizing → risk)
    ▼
Layer 5: KnowledgeGraph.update_from_news_event()
          → persistent entity-relationship graph
```

### Key Classes

| File | Class | Role |
|------|-------|------|
| `cognitive_market_system.py` | `CognitiveMarketSystem` | Main orchestrator with `process_news_event()` |
| `core_cognitive_structures.py` | 4 Enums + 6 Dataclasses | Core types: `LinguisticShockVector`, `CognitiveState`, `ExpectationVector`, `NewsEvent` |
| `expectation_collision_engine.py` | `ExpectationCollisionEngine` | 9-step collision computation |
| `participant_models.py` | `RetailTraderModel`, `HFTModel`, `HedgeFundModel`, `BankModel`, `MarketMakerModel` | Per-type `interpret()` → `ParticipantResponse` |
| `tradable_signal_translator.py` | `TradableSignalTranslator` | Multi-gate signal generation |
| `real_data_adapter.py` | `RealDataProvider` | CoinGecko + RSS data provider |

---

## 3. Pipeline B — 7-Phase Operational Pipeline

**File**: `legacy_main.py` (640 lines)
**Orchestrator**: `PipelineOrchestrator`

### Phase Flow

```
Phase 1: NewsEventParser.parse()
    │     → NewsEvent (raw_text, actors, temporal_markers, uncertainty,
    │                   contradictions, semantic_claims, narrative_types)
    ▼
Phase 2: Participant.interpret() × 5
    │     → Dict[ParticipantType, ParticipantExpectation]
    │       (belief_shift, urgency, uncertainty_level, action_likelihoods)
    ▼
Phase 3: BehaviorTranslator.translate() × 5
    │     → Dict[ParticipantType, BehaviorProfile]
    │       (risk_posture, liquidity_posture, exposure_intent, urgency)
    ▼
Phase 4a: BehaviorAggregator.aggregate()
    │      → AggregatedBehavior (disagreement, concentration, divergence)
Phase 4b: ImpactTranslator.translate()
    │      → MarketImpactProfile (6 categories: liquidity, volatility,
    │        spread, order_flow, price, regime—with timing + non-linearity)
    ▼
Phase 5: RealityValidator.create_validation_record()
    │     → ValidationRecord (5 dimensions: directional, volatility,
    │       timing, participation, regime—weighted composite)
    ▼
Phase 6: SignalAuthorizer.authorize_signal()
    │     → SignalRecord (5-step: trust → filter → weight → direction → vol)
    │       Trust threshold = 0.6, Expiration = 4 hours
    ▼
Phase 7: ExecutionNexus.execute_signal()
          → ExecutedOrder (Kelly-inspired sizing, paper trading,
            $100K capital, 15% max position, 2% stop, 3-4% target)
```

### Phase Packages

| Phase | Package | Main Class | File |
|-------|---------|------------|------|
| 1 | `news_model/` | `NewsEventParser` | `parser.py` |
| 1 | `news_model/` | `NewsEvent` | `news_event.py` |
| 2 | `participant_cognition/` | `Participant` | `participant_models.py` |
| 3 | `market_response/` | `BehaviorTranslator` | `behavior_models.py` |
| 4 | `market_impact/` | `BehaviorAggregator`, `ImpactTranslator`, `MarketImpactCalculator` | `market_impact_models.py` |
| 5 | `reality_validation/` | `RealityValidator`, `MarketDataProvider` | `market_reality.py` |
| 6 | `signal_auth/` | `SignalAuthorizer` | `signal_authorization.py` |
| 7 | `execution/` | `ExecutionNexus` | `execution_nexus.py` |

---

## 4. Pipeline C — Unified Bridge

**File**: `pipeline_bridge.py` (545 lines)
**Class**: `PipelineBridge`

### Three Operating Modes

| Mode | Pipeline Used | Purpose |
|------|---------------|---------|
| `engine_only` | Pipeline A only | Cognitive-only analysis |
| `phase_only` | Pipeline B only | 7-phase operational only |
| `hybrid` | Both A + B merged | Full dual-pipeline |

### Bridge Data Flow

```
PipelineBridge(mode="hybrid")
    │
    ├── _run_engine(text, source, market_price)
    │     → engine_result (signals, collision metrics)
    │
    ├── _run_phases(text, source, market_price)
    │     → phase_result (all 7 phase outputs)
    │
    └── merge → UnifiedResult
```

### Supporting Classes

| Class | Role |
|-------|------|
| `APIKeyManager` | Singleton pattern — centralized API key management |
| `UnifiedResult` | Dataclass merging engine + phase results |

---

## 5. Streaming Pipeline

**Package**: `streaming/`
**Files**: `event_bus.py` (~280 lines), `pipeline.py` (647 lines)

### Event Bus

| Class | Pattern | Key Methods |
|-------|---------|-------------|
| `EventBus` | Pub/Sub with priority | `subscribe()`, `publish()`, `publish_async()`, `replay()`, `get_dead_letters()` |
| `Event` | Dataclass | `event_type`, `data`, `timestamp`, `priority`, `source` |
| `EventTypes` | Constants | All event type strings |

### Streaming Pipeline (7 Stages)

**Class**: `StreamingPipeline`

```
Stage 1: _stage_1_ingest()    → news_ingestion
Stage 2: _stage_2_nlp()       → nlp_processing
Stage 3: _stage_3_cognitive()  → cognitive_modeling
Stage 4: _stage_4_behavior()   → behavior_translation
Stage 5: _stage_5_impact()     → impact_modeling
Stage 6: _stage_6_validate()   → validation
Stage 7: _stage_7_signal()     → signal_generation
```

Method: `process(raw_text, source, market_price)` → runs all 7 stages sequentially with `get_pipeline_metrics()` for observability.

---

## 6. NLP Processing Pipeline

**Package**: `nlp_engine/`
**Files**: 6 processing modules (~4,000+ lines total)

### Core NLP Flow

```
Raw Text
    │
    ├──→ DeepNLPParser.parse() (1303 lines)
    │      ├── spaCy tokenization + NER (en_core_web_sm)
    │      ├── Per-sentence certainty scoring (hedge/boost words)
    │      ├── Conditional/negation/question detection
    │      ├── Narrative classification (12 types via zero-shot or keywords)
    │      ├── Intent detection (8 types via keyword scoring)
    │      ├── Document metrics (certainty, subjectivity, complexity)
    │      ├── Key phrase extraction
    │      ├── Coreference resolution (pronoun→entity)
    │      ├── Temporal timeline extraction (9 pattern types)
    │      └── MiniLM embeddings (document + per-sentence)
    │
    ├──→ EntityExtractor.extract_from_text()
    │      → FinancialEntity[], GeopoliticalEntity[], EntityRelation[]
    │
    ├──→ ContradictionDetector.detect()
    │      → ContradictionResult (negation/antonym/numeric/stance)
    │      Threshold: numeric >20% difference
    │
    ├──→ IntentDetector.analyze()
    │      → IntentAnalysis (communication, strategic, timing,
    │        manipulation, beneficiaries, hidden_agenda)
    │      SOURCE_CREDIBILITY: reuters 0.9 → twitter 0.25
    │
    ├──→ AdvancedNLPEngine.full_analysis() (orchestrator)
    │      ├── MultiLingualFinancialNLP (8 languages)
    │      ├── FinancialEmbeddings (128-dim hash-based)
    │      └── FinancialEventExtractor (WHO-WHAT-WHOM-WHEN-RESULT)
    │
    └──→ EarningsCallAnalyzer.analyze_transcript()
           → section-wise sentiment, tone shift, hedging, guidance, risk signals
```

### NLP Classes

| File | Class | Lines |
|------|-------|-------|
| `deep_nlp_parser.py` | `DeepNLPParser` | 1303 |
| `advanced_nlp.py` | `MultiLingualFinancialNLP`, `FinancialEmbeddings`, `FinancialEventExtractor`, `AdvancedNLPEngine` | 801 |
| `entity_extraction.py` | `EntityExtractor` | ~320 |
| `contradiction_detector.py` | `ContradictionDetector` | 381 |
| `intent_detector.py` | `IntentDetector` | 464 |
| `nlp_extensions.py` | `EarningsCallAnalyzer` | 675 |

### ML Model Dependencies

| Model | Source | Purpose |
|-------|--------|---------|
| `en_core_web_sm` | spaCy | Tokenization + NER |
| `ProsusAI/finbert` | HuggingFace | Financial sentiment |
| `facebook/bart-large-mnli` | HuggingFace | Zero-shot narrative classification |
| `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace | Sentence embeddings |
| `distilbert-base-uncased-finetuned-sst-2-english` | HuggingFace | Fallback sentiment |
| `Helsinki-NLP/opus-mt-*` | HuggingFace | Machine translation (8 langs) |

---

## 7. News Ingestion Pipeline

**Package**: `news_ingestion/`
**Files**: 4 source modules + aggregator

### Source → Aggregator Flow

```
NewsAPI.org ──→ NewsAPIClient.search_financial_news()
                    │
GDELT       ──→ GDELTClient.search_financial_news()
                    │         ├──→ NewsAggregator.fetch_latest()
RSS (14 feeds) ──→ RSSReader.read_all_financial()       │
                    │         │    ├── _deduplicate() 
                    └─────────┘    │   (content_hash + 70% title overlap)
                                   │
                                   ▼
                            UnifiedArticle[]
```

### Source Classes

| File | Class | Sources |
|------|-------|---------|
| `news_api_client.py` | `NewsAPIClient` | NewsAPI.org (80K+ sources, 100 req/day) |
| `gdelt_client.py` | `GDELTClient` | GDELT (events + articles) |
| `rss_reader.py` | `RSSReader` | 14 feeds: Reuters, Bloomberg, CNBC, FT, WSJ, MarketWatch, Yahoo Finance, Seeking Alpha, ZeroHedge, Economist, BBC, NYT, Guardian, AP |
| `news_aggregator.py` | `NewsAggregator` | Unified with dedup + `async_fetch_latest()` (ThreadPoolExecutor) |

---

## 8. Cognitive Modeling Pipeline

**Package**: `participant_cognition/`
**File**: `participant_models.py` (618 lines)

### 5 Participant Types

| Type | Factory Function | Bias | Urgency Style |
|------|-----------------|------|---------------|
| Bank | `create_bank_participant()` | `RISK_AVERSE` | Low — hedging focus |
| Hedge Fund | `create_hedge_fund_participant()` | `OPPORTUNITY_SEEKING` | High — asymmetric returns |
| HFT | `create_hft_participant()` | `TREND_CONFIRMATION` | Immediate — spreads |
| Market Maker | `create_market_maker_participant()` | `LIQUIDITY_PRESERVATION` | Moderate — inventory |
| Retail | `create_retail_participant()` | `OVERREACTION` | Emotional — narrative |

### Interpretation Flow

```
NewsEvent
    │
    ▼
Participant.interpret(news_event)
    ├── _interpret_through_bias(event, bias)
    ├── _calculate_belief_shift(event, bias_result)
    ├── _assess_uncertainty(event)
    ├── _determine_urgency(event)
    └── _calculate_actions(event, belief_shift, uncertainty, urgency)
         │
         ▼
    ParticipantExpectation
      ├── belief_shift (float)
      ├── urgency (float)
      ├── uncertainty_level (float)
      └── action_likelihoods: ActionLikelihoods
            (8 probabilities summing to 1.0:
             increase_exposure, decrease_exposure, increase_hedging,
             hold_position, wait_for_clarity, panic_action,
             widen_spreads, pull_liquidity)
```

---

## 9. Behavior Translation Pipeline

**Package**: `market_response/`
**File**: `behavior_models.py` (606 lines)

### Translation Flow

```
ParticipantExpectation + ParticipantConstraints
    │
    ▼
BehaviorTranslator.translate()
    ├── _determine_risk_posture()      → REDUCE / MAINTAIN / INCREASE
    ├── _determine_liquidity_posture() → PROVIDE / MAINTAIN / REDUCE
    ├── _determine_exposure_intent()   → INCREASE / MAINTAIN / DECREASE
    ├── _determine_urgency()           → IMMEDIATE / SAME_DAY / MULTI_DAY / PASSIVE
    ├── _determine_optionality()
    ├── _identify_contradictions()
    ├── _generate_reasoning()
    ├── _calculate_overall_confidence()
    └── _determine_fallbacks()
         │
         ▼
    BehaviorProfile
      (risk_posture, liquidity_posture, exposure_intent,
       urgency, optionality, contradictions, fallbacks, confidence)
```

---

## 10. Market Impact Pipeline

**Package**: `market_impact/`
**File**: `market_impact_models.py` (1151 lines)

### Two-Stage Flow

```
BehaviorProfile[] (from 5 participants)
    │
    ▼
Stage 1: BehaviorAggregator.aggregate()
    │      → AggregatedBehavior
    │        (avg_risk_signal, avg_liquidity_signal,
    │         disagreement (std dev), concentration (one-sidedness),
    │         participant_divergence)
    ▼
Stage 2: ImpactTranslator.translate()
    │      → MarketImpactProfile
    │        ├── 6 Impact Categories:
    │        │   1. Liquidity impacts
    │        │   2. Volatility impacts
    │        │   3. Spread impacts
    │        │   4. Order flow impacts
    │        │   5. Price dynamics impacts
    │        │   6. Regime impacts
    │        ├── Each with: onset_delay, peak_window, decay_time, persistence
    │        ├── Non-linearity: threshold / saturation / feedback detection
    │        ├── Overall stress score
    │        └── Kyle's Lambda approximation
    ▼
MarketImpactCalculator.calculate()  ←  Unified pipeline
```

### Impact Enums (22 sub-types)

| Category | Types |
|----------|-------|
| Liquidity | 4 types (`LiquidityImpactType`) |
| Volatility | 4 types (`VolatilityImpactType`) |
| Spread | 3 types (`SpreadImpactType`) |
| Order Flow | 4 types (`OrderFlowImpactType`) |
| Price Dynamics | 4 types (`PriceDynamicsType`) |
| Regime | 3 types (`RegimeImpactType`) |

---

## 11. Reality Validation Pipeline

**Package**: `reality_validation/`
**File**: `market_reality.py` (1049 lines)

### Validation Flow

```
PredictedMarketState + MarketReality
    │
    ▼
RealityValidator.create_validation_record()
    ├── validate_directional_accuracy()   → weight 0.30
    ├── validate_volatility_accuracy()    → weight 0.20
    ├── validate_timing_accuracy()        → weight 0.20
    │     (shock 30s, peak 5min, recovery 15min tolerances)
    ├── validate_participation_match()    → weight 0.15
    └── validate_regime_shift()           → weight 0.15
          (temporary ≤1d, semi-persistent ≤7d, structural >7d)
         │
         ▼
    ValidationRecord
      (composite accuracy = weighted sum of 5 dimensions)
      │
      ▼
    test_statistical_significance()
      (one-sided binomial + z-score + p-value + t-test)
```

### Market Data Providers

| Method | Source | Fallback |
|--------|--------|----------|
| `_fetch_coingecko()` | CoinGecko API | Cache |
| `_fetch_yfinance()` | Yahoo Finance | CoinGecko |
| `_fetch_from_cache()` | Local cache | Simulated |

---

## 12. Signal Authorization Pipeline

**Package**: `signal_auth/`
**File**: `signal_authorization.py` (778 lines)

### 5-Step Authorization

```
NewsMetadata + ValidationMetrics + PredictionFromPhase4
    │
    ▼
Step 1: assign_trust_score()
    │     → base from historical accuracy per event type
    │       + participant model accuracies
    ▼
Step 2: filter_signal(threshold=0.6)
    │     → APPROVED or FILTERED
    ▼
Step 3: weight_signal_strength()
    │     → event-type base × trust × participant-weighted confidence
    ▼
Step 4: determine_signal_direction()
    │     → BUY / SELL / NEUTRAL / UNCERTAIN (HFT/HF consensus)
    ▼
Step 5: determine_volatility_impact()
    │     → LOW / MEDIUM / HIGH / EXTREME
    ▼
SignalRecord (with 4-hour expiration)
    │
    ▼
normalize_signals() → weighted vote, conflict detection
```

---

## 13. Execution Pipeline

**Package**: `execution/`
**File**: `execution_nexus.py` (634 lines)

### Execution Flow

```
ApprovedSignal + current_price
    │
    ▼
ExecutionNexus.execute_signal()
    ├── check_position_limits()
    │     ├── Max 3 open positions
    │     ├── Daily loss < 2%
    │     └── Circuit breaker at 5% drawdown
    ├── size_order()
    │     └── Kelly-inspired: strength × confidence × max_position (capped 15%)
    ├── route_order()
    │     ├── AGGRESSIVE → market order, fill <1s
    │     └── PASSIVE → limit order, fill <5min
    └── → ExecutedOrder
           │
           ▼
    check_exit_conditions(position, current_price)
      ├── Stop loss: 2%
      └── Take profit: 3-4%
```

### Configuration

| Parameter | Value |
|-----------|-------|
| Initial capital | $100,000 |
| Max position size | 15% of capital |
| Max open positions | 3 |
| Stop loss | 2% |
| Take profit | 3-4% |
| Circuit breaker | 5% drawdown |
| Max daily loss | 2% |

---

## 14. Alpha Signal Pipeline

**Package**: `alpha_models/`
**Files**: `alpha_signals.py` (1667 lines), `nlp_alpha_signals.py` (754 lines), `structural_alpha.py` (948 lines)

### 22 Alpha Signal Generators

#### 12 Quantitative Alphas (`AlphaSignalAggregator`)

| # | Class | Signal | Weight |
|---|-------|--------|--------|
| 1 | `PositioningAnalyzer` | CFTC COT + options OI contrarian z-score | 0.12 |
| 2 | `OrderFlowAnalyzer` | L2 book + cumulative delta + iceberg detection | 0.12 |
| 3 | `CreditMarketSignals` | CDS + HY bonds + repo composite stress | 0.10 |
| 4 | `VolatilitySurfaceAnalyzer` | 25d risk reversal, butterfly, term structure | 0.10 |
| 5 | `MacroSurpriseIndex` | Citigroup-style economic surprise (11 weights) | 0.10 |
| 6 | `CentralBankBalanceSheet` | Fed/ECB/BoJ/PBoC QE/QT + liquidity pulse | 0.08 |
| 7 | `CrossAssetLeadLag` | Rolling lag cross-correlation | 0.08 |
| 8 | `SentimentExtremesAnalyzer` | CNN Fear/Greed + AAII + P/C + VIX composite | 0.08 |
| 9 | `FlowOfFundsAnalyzer` | ETF + mutual fund flows (5 sectors) | 0.07 |
| 10 | `InsiderTradingAnalyzer` | SEC Form 4, title-weighted (CEO 3x) | 0.06 |
| 11 | `CalendarEffectsAnalyzer` | 7 calendar anomalies | 0.05 |
| 12 | `EarningsRevisionTracker` | Analyst EPS revision momentum | 0.04 |

#### 5 NLP Alphas (`NLPAlphaHub`)

| # | Class | Signal |
|---|-------|--------|
| 1 | `NarrativeMomentumAlpha` | Narrative intensity acceleration |
| 2 | `ContradictionAlpha` | Cross-source contradiction detection |
| 3 | `InstitutionalLanguageAlpha` | Institutional vs retail language patterns |
| 4 | `TemporalClusteringAlpha` | News timing cluster analysis |
| 5 | `SentimentDivergenceAlpha` | Headline vs body sentiment divergence |

#### 5 Structural Alphas (`StructuralAlphaEngine`)

| # | Class | Signal |
|---|-------|--------|
| 1 | `MicrostructureAlpha` | Bid-ask bounce, Kyle's lambda, order flow toxicity |
| 2 | `RealizedVolAlpha` | Realized vs implied vol, vol-of-vol, term structure |
| 3 | `FundingRateAlpha` | Perpetual futures funding rate mean-reversion |
| 4 | `OnChainAlpha` | Exchange flows, whale movements (blockchain) |
| 5 | `LiquidityPremiumAlpha` | Amihud ratio, turnover, bid-ask spread premium |

---

## 15. Scenario Engine Pipeline

**Package**: `scenario_engine/`
**Files**: 4 processing modules

### Scenario Flow

```
EventData
    │
    ├──→ ScenarioGenerator.generate(max_depth=3)
    │      → ScenarioTree (root → children → leaves)
    │        compute_tree_metrics: probability-weighted move,
    │        max upside/downside, tail risk, expected direction
    │
    ├──→ CausalChainBuilder.build_chain(max_depth=3)
    │      → CausalChain
    │        ├── 1st order (7 event templates)
    │        ├── 2nd order (5 rule sets)
    │        ├── 3rd order (3 rule sets: systemic, feedback, policy)
    │        ├── KnowledgeGraph enhancement
    │        └── Metrics: dominant direction, systemic risk, feedback loops
    │
    ├──→ MonteCarloSimulator.simulate(n=10000)
    │      → SimulationResult (mean, VaR 95/99, CVaR 95, max drawdown,
    │        skewness, kurtosis, histogram)
    │
    └──→ CounterfactualAnalyzer + ScenarioPortfolioOptimizer
           ├── CounterFactual analysis (what-if scenarios)
           └── Portfolio optimization (4 methods):
               ├── minimax (maximize minimum return)
               ├── expected_utility (E[R] - λ/2 × Var[R])
               ├── risk_parity (inverse-volatility weights)
               └── cvar (minimize 5th percentile CVaR)
```

---

## 16. Hidden Truth / Manipulation Detection Pipeline

**Package**: `hidden_truth/`
**Files**: 5 detection modules

### Detection Flow

```
News Articles[]
    │
    ├──→ TimingAnalyzer.analyze_timing()
    │      → suspicious timing vs 11 RECURRING_EVENTS
    │        (FOMC, NFP, CPI, GDP, ECB, BoJ, etc.)
    │        + 6 market sessions
    │
    ├──→ FilingAnalyzer.compare_risk_sections()
    │      → tone divergence (PR vs SEC filing)
    │        + Gunning Fog readability index
    │
    ├──→ InsiderCorrelationAnalyzer.analyze()
    │      → insider trades correlated with news events
    │        (C-suite 1.5x weight, $1M+ 1.3x, 5-day cluster window)
    │
    ├──→ SourceNetworkAnalyzer.build_network()
    │      → echo chambers (co-coverage ≥5, sentiment corr >0.8,
    │        timing corr >0.6)
    │      → independence scoring, credibility ranking
    │
    ├──→ CrossSourceAnalyzer.analyze()
    │      → coordinated releases (<30s from 3+ sources)
    │      → conflicts (sentiment divergence >0.3)
    │      → trust score (5-component weighted)
    │      → SQLite pattern persistence
    │
    └──→ NarrativeTracker.track()
           → narrative evolution (growing/fading/stable/new)
           → manufactured consensus detection
           → credibility scoring (multi-source × consistency × stability)
```

---

## 17. Market Intelligence Pipeline

**Package**: `market_intelligence/`
**File**: `intelligence_models.py` (1373 lines)

### 9 Intelligence Models (`MarketIntelligenceHub`)

| # | Class | Capability |
|---|-------|-----------|
| 1 | `AlternativeDataFusion` | 8 alt data categories → z-score composite |
| 2 | `RegimeDetector` | HMM-inspired 5 regimes + CUSUM changepoint |
| 3 | `CrowdingRiskDetector` | Short squeeze + factor crowding + ETF concentration |
| 4 | `LiquidityForecaster` | Volume/spread/depth + flash crash conditions |
| 5 | `CrossMarketArbitrage` | Basis trade + ETF NAV deviation + put-call parity |
| 6 | `SentimentDecayModel` | Exponential decay with regime-dependent half-lives |
| 7 | `InformationCascadeDetector` | Sequential alignment >80%, declining independence |
| 8 | `ReflexivityModel` | Soros-style narrative-price coupling + reversal prediction |
| 9 | `DarkPoolAnalyzer` | Dark pool volume %, block clustering, VWAP divergence |

**Orchestrator**: `MarketIntelligenceHub.full_scan()` → `risk_summary()` (critical/elevated/moderate/normal)

---

## 18. Multi-Asset Pipeline

**Package**: `multi_asset/`
**Files**: `correlation_engine.py`, `contagion_model.py`

### Cross-Asset Analysis

| Class | Scope | Key Methods |
|-------|-------|-------------|
| `CorrelationEngine` | 21 baseline correlations (BTC-ETH 0.85, BTC-SPX 0.45, etc.) | `update()`, `detect_anomalies()` (>2σ deviation), `get_contagion_risk()` |
| `ContagionModel` | 19 transmission channels + 20 susceptibility ratings | `simulate_contagion()`, `get_transmission_path()`, `get_systemic_risk_score()` |

---

## 19. Economics Pipeline

**Package**: `economics/`
**File**: `economic_models.py` (689 lines)

### 5 Economic Models (`EconomicAnalyzer`)

| Class | Model | Key Methods |
|-------|-------|-------------|
| `PhillipsCurve` | Unemployment ↔ Inflation tradeoff | `estimate_inflation()`, `get_nairu()` |
| `YieldCurve` | Term structure analysis | `get_yield()`, `is_inverted()`, `recession_probability()` |
| `TaylorRule` | Optimal interest rate | `recommended_rate()`, `deviation_from_actual()` |
| `GDPImpact` | Fiscal + monetary → GDP | `estimate_gdp_impact()`, ISM/PMI analysis |
| `ExchangeRate` | Rate differentials + trade | `estimate_impact()`, PPP deviation |

---

## 20. Decision System Pipeline

**Package**: `decision_system/`
**Files**: `decision_engine.py` (622 lines), `human_review_queue.py` (~350 lines)

### Decision Flow

```
CognitiveSignal[]
    │
    ▼
DecisionEngine.decide()
    ├── _aggregate_signals()
    ├── _check_risk_gates()
    ├── _check_hidden_truth()      → manipulation flags
    ├── _determine_action()        → BUY/SELL/HOLD/REDUCE/HEDGE/EMERGENCY_EXIT/WATCH
    ├── _compute_sizing()          → Kelly-inspired, regime-adjusted, half-Kelly
    ├── _compute_risk_levels()     → volatility-adjusted stops/targets
    └── _finalize()
         │
         ▼
    DecisionPacket
      (action, reasoning_chain, risk_gates_triggered,
       hidden_truth_flags, position_pct, stop_loss, take_profit,
       risk_reward_ratio, overall_confidence)
         │
         ▼ (if escalation triggered)
    HumanReviewQueue.submit_for_review()
      6 escalation rules:
        ├── high_value > $50K
        ├── low_confidence < 0.4
        ├── hidden_truth_flagged
        ├── regime_crisis
        ├── contradictory_signals
        └── novel_event_type
```

---

## 21. Feedback & Learning Pipeline

**Package**: `learning/`
**File**: `feedback_loop.py` (456 lines)

### Feedback Flow

```
PredictionRecord (event_type, participant_type, prediction, actual_outcome)
    │
    ▼
FeedbackLoop.record_prediction()
    │
    ▼
update_credibility(participant_type, accuracy)
    │
    ▼
get_model_weights()        → current per-type credibility
get_accuracy_by_event_type() → per-type accuracy history
get_improvement_recommendations() → actionable suggestions
    │
    ▼
_save_to_storage() → persist to DatabaseManager
```

---

## 22. Backtesting Pipeline

**Package**: `backtesting/`
**File**: `backtest_engine.py` (778 lines)

### Backtesting Flow

```
Historical News Events + Price Data
    │
    ▼
BacktestRunner.run(events, price_data)
    ├── EventReplayEngine.load_events() → chronological replay
    ├── Per event:
    │     ├── Process through pipeline → signal
    │     ├── PositionTracker.open_position()
    │     └── mark_to_market() → check exit conditions
    │
    └── PerformanceAnalytics.compute(trades)
          → Sharpe ratio, Sortino ratio, max drawdown,
            win rate, profit factor, avg win/loss, expectancy
```

### Backtesting Config

| Parameter | Value |
|-----------|-------|
| Capital | $100,000 |
| Max position | 10% |
| Stop loss | 2% |
| Take profit | 4% |

---

## 23. Infrastructure Pipeline

**Package**: `infrastructure/`
**File**: `infra_layer.py` (1254 lines)

### 7 Production Components (`InfrastructureManager`)

| # | Class | Purpose |
|---|-------|---------|
| 1 | `MessageQueue` | Redis/Kafka/in-memory pub/sub + dead letter queue |
| 2 | `TimeSeriesDB` | InfluxDB/TimescaleDB/SQLite + retention policies |
| 3 | `ModelRegistry` | MLflow-style versioning, A/B testing, stage transitions |
| 4 | `FeatureStore` | Online/offline stores, point-in-time joins, freshness SLAs |
| 5 | `CICDPipeline` | 6-stage (lint→test→model_validation→build→deploy_staging→deploy_production) |
| 6 | `MonitoringSystem` | Prometheus counters/gauges/histograms, 12 metrics, 5 alerts, Grafana JSON |
| 7 | `APILayer` | FastAPI REST+WebSocket, 13 routes, API key auth, rate limiting |

### API Routes (Port 8000)

| Route | Method | Purpose |
|-------|--------|---------|
| `/health` | GET | Health check |
| `/signals/latest` | GET | Latest signals |
| `/signals/history` | GET | Signal history |
| `/intelligence/{asset}` | GET | Market intelligence |
| `/regime/current` | GET | Current regime |
| `/nlp/analyze` | POST | NLP analysis |
| `/events/extract` | POST | Event extraction |
| `/alpha/scan` | GET | Alpha scan |
| `/risk/summary` | GET | Risk summary |
| `/models/list` | GET | Model registry |
| `/features/{entity}` | GET | Feature store |
| `/metrics` | GET | Prometheus metrics |
| `ws:/signals` | WebSocket | Real-time signals |

---

## 24. Data Pipeline

**Package**: `data/`
**File**: `market_data_feed.py` (~290 lines)

### Data Feed

| Class | Method | Source | Fallback |
|-------|--------|--------|----------|
| `MarketDataFeed` | `get_market_snapshot(asset)` | CoinGecko API (live) | GBM simulation |

**Seed Prices**: BTC=$65,000, ETH=$3,500, SPX=$5,200, GOLD=$2,300

**Output**: `(price, bid, ask, volume, timestamp)` tuple

---

## 25. Visualization & Dashboard Pipeline

**Package**: `dashboard/`
**File**: `app.py` (~350 lines)

### 7 Streamlit Pages (Port 8501)

| Page | Content |
|------|---------|
| Overview | System status, key metrics |
| Live Feed | Real-time news + signals |
| Signal History | Historical signal performance |
| Market Intelligence | Cross-asset analytics |
| Hidden Truth | Manipulation detection results |
| Backtesting | Backtest results + performance |
| System Health | Infrastructure health metrics |

---

## 26. Alert Delivery Pipeline

**Package**: `alerts/`
**File**: `alert_delivery.py` (466 lines)

### 5 Delivery Channels

| Channel | Implementation |
|---------|---------------|
| Console | Formatted terminal output |
| File | Rotating log file |
| Webhook | HTTP POST (configurable URL) |
| Email | SMTP (configurable server) |
| SMS | Twilio API |

**Priority Levels**: LOW → MEDIUM → HIGH → CRITICAL

---

## 27. Storage Pipeline

**Package**: `storage/`
**Files**: `database.py` (605 lines), `knowledge_graph.py` (641 lines)

### SQLite (DatabaseManager) — 9 Tables

| Table | Content |
|-------|---------|
| `news_events` | Raw news events |
| `signals` | Generated signals |
| `positions` | Open/closed positions |
| `trades` | Executed trades |
| `performance` | Performance metrics |
| `model_credibility` | Per-model accuracy |
| `validation_records` | Phase 5 validation results |
| `alert_history` | Alert delivery log |
| `system_metrics` | Infrastructure metrics |

### Knowledge Graph (NetworkX DiGraph + JSON)

- **40+ seed entities**: Federal_Reserve, ECB, BoJ, etc.
- **Methods**: `add_entity()`, `add_relationship()`, `get_influence_chain()`, `find_shortest_path()`, `update_from_news_event()`, `save()`/`load()`

---

## 28. Advanced Analysis Pipeline

**Package**: `advanced/`
**Files**: 4 specialized modules

| File | Class | Capability |
|------|-------|-----------|
| `geopolitical_risk.py` | `GeopoliticalRiskScorer` | 8 event types × 6 regions × 7 sectors |
| `llm_analyzer.py` | `LLMAnalyzer` | GPT-4o-mini with keyword fallback |
| `social_media.py` | `SocialMediaSentiment` | Reddit (7 subs) + Twitter (20 tickers) |
| `report_generator.py` | `ReportGenerator` | 5 report types (event, daily, risk, health, custom) |

---

## 29. Configuration Pipeline

**Package**: `config/`
**Files**: `system_config.py` (394 lines), `logging_config.py` (~80 lines)

### 8 Configuration Dataclasses

| Config | Key Parameters |
|--------|---------------|
| `NewsIngestionConfig` | sources, polling interval |
| `NLPConfig` | model names, thresholds |
| `CognitiveEngineConfig` | participant types, collision params |
| `StorageConfig` | db_path, graph_path |
| `TradingConfig` | capital=$100K, max_position=15%, stop=2%, target=4% |
| `AlertConfig` | channels, thresholds |
| `DashboardConfig` | port=8501, refresh interval |
| `SystemConfig` | Master config combining all above |

### Environment Variables (`.env.example`)

```
NEWS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
TWITTER_BEARER_TOKEN=...
TWILIO_SID=...
TWILIO_TOKEN=...
```

---

## 30. Complete Module & Class Registry

### Directory Registry (30 Packages)

| # | Package | Files | Lines (approx) |
|---|---------|-------|-----------------|
| 1 | `engine/` | 7 | ~2,770 |
| 2 | `config/` | 3 | ~475 |
| 3 | `shared/` | 1 | 64 |
| 4 | `streaming/` | 3 | ~930 |
| 5 | `storage/` | 3 | ~1,250 |
| 6 | `nlp_engine/` | 7 | ~3,950 |
| 7 | `news_model/` | 3 | ~520 |
| 8 | `news_ingestion/` | 5 | ~1,525 |
| 9 | `participant_cognition/` | 2 | ~620 |
| 10 | `market_response/` | 2 | ~610 |
| 11 | `market_impact/` | 3 | ~1,155 |
| 12 | `reality_validation/` | 2 | ~1,050 |
| 13 | `signal_auth/` | 2 | ~780 |
| 14 | `execution/` | 2 | ~635 |
| 15 | `decision_system/` | 3 | ~975 |
| 16 | `hidden_truth/` | 6 | ~2,475 |
| 17 | `scenario_engine/` | 5 | ~2,220 |
| 18 | `alpha_models/` | 4 | ~3,370 |
| 19 | `multi_asset/` | 3 | ~790 |
| 20 | `market_intelligence/` | 2 | ~1,375 |
| 21 | `infrastructure/` | 2 | ~1,255 |
| 22 | `economics/` | 2 | ~690 |
| 23 | `backtesting/` | 2 | ~780 |
| 24 | `learning/` | 2 | ~460 |
| 25 | `data/` | 2 | ~290 |
| 26 | `dashboard/` | 2 | ~350 |
| 27 | `advanced/` | 5 | ~1,170 |
| 28 | `alerts/` | 2 | ~470 |
| 29 | `scripts/` | 1 | 305 |
| 30 | `tests/` | 8 | ~3,900 |
| — | Root files | 7 | ~2,000 |
| **TOTAL** | **30 packages** | **~78 files** | **~42,000+** |

### Class Registry (120+ Classes)

| Package | Classes |
|---------|---------|
| `engine/` | `CognitiveMarketSystem`, `ExpectationCollisionEngine`, `TradableSignalTranslator`, `RetailTraderModel`, `HFTModel`, `HedgeFundModel`, `BankModel`, `MarketMakerModel`, `RealDataProvider` |
| `streaming/` | `EventBus`, `StreamingPipeline` |
| `storage/` | `DatabaseManager`, `KnowledgeGraph` |
| `nlp_engine/` | `DeepNLPParser`, `MultiLingualFinancialNLP`, `FinancialEmbeddings`, `FinancialEventExtractor`, `AdvancedNLPEngine`, `EntityExtractor`, `ContradictionDetector`, `IntentDetector`, `EarningsCallAnalyzer` |
| `news_model/` | `NewsEvent`, `NewsEventParser` |
| `news_ingestion/` | `NewsAPIClient`, `GDELTClient`, `RSSReader`, `NewsAggregator` |
| `participant_cognition/` | `Participant` |
| `market_response/` | `BehaviorTranslator` |
| `market_impact/` | `BehaviorAggregator`, `ImpactTranslator`, `MarketImpactCalculator` |
| `reality_validation/` | `MarketDataProvider`, `RealityValidator` |
| `signal_auth/` | `SignalAuthorizer` |
| `execution/` | `ExecutionNexus` |
| `decision_system/` | `DecisionEngine`, `HumanReviewQueue` |
| `hidden_truth/` | `TimingAnalyzer`, `FilingAnalyzer`, `InsiderCorrelationAnalyzer`, `SourceNetworkAnalyzer`, `CrossSourceAnalyzer`, `NarrativeTracker` |
| `scenario_engine/` | `ScenarioGenerator`, `CausalChainBuilder`, `MonteCarloSimulator`, `CounterfactualAnalyzer`, `ScenarioPortfolioOptimizer` |
| `alpha_models/` | `PositioningAnalyzer`, `OrderFlowAnalyzer`, `VolatilitySurfaceAnalyzer`, `CrossAssetLeadLag`, `SentimentExtremesAnalyzer`, `FlowOfFundsAnalyzer`, `CalendarEffectsAnalyzer`, `EarningsRevisionTracker`, `InsiderTradingAnalyzer`, `CreditMarketSignals`, `MacroSurpriseIndex`, `CentralBankBalanceSheet`, `AlphaSignalAggregator`, `NarrativeMomentumAlpha`, `ContradictionAlpha`, `InstitutionalLanguageAlpha`, `TemporalClusteringAlpha`, `SentimentDivergenceAlpha`, `NLPAlphaHub`, `MicrostructureAlpha`, `RealizedVolAlpha`, `FundingRateAlpha`, `OnChainAlpha`, `LiquidityPremiumAlpha`, `StructuralAlphaEngine` |
| `multi_asset/` | `CorrelationEngine`, `ContagionModel` |
| `market_intelligence/` | `AlternativeDataFusion`, `RegimeDetector`, `CrowdingRiskDetector`, `LiquidityForecaster`, `CrossMarketArbitrage`, `SentimentDecayModel`, `InformationCascadeDetector`, `ReflexivityModel`, `DarkPoolAnalyzer`, `MarketIntelligenceHub` |
| `infrastructure/` | `MessageQueue`, `TimeSeriesDB`, `ModelRegistry`, `FeatureStore`, `CICDPipeline`, `MonitoringSystem`, `APILayer`, `InfrastructureManager` |
| `economics/` | `PhillipsCurve`, `YieldCurve`, `TaylorRule`, `GDPImpact`, `ExchangeRate`, `EconomicAnalyzer` |
| `backtesting/` | `PositionTracker`, `PerformanceAnalytics`, `EventReplayEngine`, `BacktestRunner` |
| `learning/` | `FeedbackLoop` |
| `data/` | `MarketDataFeed` |
| `dashboard/` | (Streamlit app — function-based) |
| `advanced/` | `GeopoliticalRiskScorer`, `LLMAnalyzer`, `SocialMediaSentiment`, `ReportGenerator` |
| `alerts/` | `AlertDeliverySystem` |
| `pipeline_bridge.py` | `APIKeyManager`, `PipelineBridge` |
| `legacy_main.py` | `PipelineOrchestrator` |

---

*Document generated from full source code analysis of 78 Python files across 30 packages.*
