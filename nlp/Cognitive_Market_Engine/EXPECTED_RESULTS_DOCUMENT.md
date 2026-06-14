# EXPECTED RESULTS DOCUMENT

## Cognitive Market Engine (CME) — Complete Expected Outcomes

**System:** Cognitive Market Engine  
**Version:** Production  
**Core Thesis:** "News does not move markets. Interpretation moves markets."  
**Codebase:** ~38,000 lines across 75+ Python files, 120+ classes, 30+ directories  
**Python:** 3.8+  

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Installation & Dependencies](#2-installation--dependencies)
3. [Entry Point 1: `python main.py` (Interactive Demo)](#3-entry-point-1-python-mainpy-interactive-demo)
4. [Entry Point 2: `python main.py --live` (Live Monitoring)](#4-entry-point-2-python-mainpy---live-live-monitoring)
5. [Entry Point 3: `python main.py --dashboard` (Streamlit Dashboard)](#5-entry-point-3-python-mainpy---dashboard-streamlit-dashboard)
6. [Entry Point 4: `python main.py --test` (Validation Suite)](#6-entry-point-4-python-mainpy---test-validation-suite)
7. [Entry Point 5: `python main.py --news "..."` (Single News)](#7-entry-point-5-python-mainpy---news--single-news)
8. [Entry Point 6: `python legacy_main.py` (7-Phase Pipeline)](#8-entry-point-6-python-legacy_mainpy-7-phase-pipeline)
9. [Entry Point 7: `python pipeline_bridge.py` (Unified Bridge)](#9-entry-point-7-python-pipeline_bridgepy-unified-bridge)
10. [Engine Pipeline (Pipeline A) — 4-Phase Cognitive](#10-engine-pipeline-pipeline-a--4-phase-cognitive)
11. [7-Phase Pipeline (Pipeline B) — Legacy Operational](#11-7-phase-pipeline-pipeline-b--legacy-operational)
12. [NLP Engine Expected Outputs](#12-nlp-engine-expected-outputs)
13. [Participant Cognitive Models — 5 Archetypes](#13-participant-cognitive-models--5-archetypes)
14. [Expectation Collision Engine](#14-expectation-collision-engine)
15. [Signal Translation Expected Outputs](#15-signal-translation-expected-outputs)
16. [Market Impact Layer](#16-market-impact-layer)
17. [Reality Validation (Phase 5)](#17-reality-validation-phase-5)
18. [Signal Authorization (Phase 6)](#18-signal-authorization-phase-6)
19. [Execution Engine (Phase 7)](#19-execution-engine-phase-7)
20. [Decision Engine](#20-decision-engine)
21. [Hidden Truth Detection](#21-hidden-truth-detection)
22. [Scenario Engine](#22-scenario-engine)
23. [Alpha Models — 31 Signal Generators](#23-alpha-models--31-signal-generators)
24. [Market Intelligence Hub — 9 Models](#24-market-intelligence-hub--9-models)
25. [Multi-Asset / Contagion](#25-multi-asset--contagion)
26. [Economics Models](#26-economics-models)
27. [Storage Layer](#27-storage-layer)
28. [Streaming Pipeline & EventBus](#28-streaming-pipeline--eventbus)
29. [Dashboard (Streamlit)](#29-dashboard-streamlit)
30. [News Ingestion Pipeline](#30-news-ingestion-pipeline)
31. [Infrastructure Layer](#31-infrastructure-layer)
32. [Backtesting Engine](#32-backtesting-engine)
33. [Learning / Feedback Loop](#33-learning--feedback-loop)
34. [Alert Delivery System](#34-alert-delivery-system)
35. [Test Suite Expected Results](#35-test-suite-expected-results)
36. [Validation Script Results](#36-validation-script-results)
37. [Health Check Script](#37-health-check-script)
38. [Docker Deployment](#38-docker-deployment)
39. [Configuration Reference](#39-configuration-reference)
40. [Performance Benchmarks](#40-performance-benchmarks)
41. [Error Handling & Graceful Degradation](#41-error-handling--graceful-degradation)
42. [File Artifacts Map](#42-file-artifacts-map)

---

## 1. System Overview

The Cognitive Market Engine is a **cognitive finance system** that models how different market participants interpret the same news differently and how those divergent interpretations create market dynamics.

### Architecture — Three Pipelines

| Pipeline | Description | Orchestrator | Phases |
|----------|-------------|--------------|--------|
| **Pipeline A** (Engine) | 4-layer cognitive model: NLP → Interpret → Collide → Signal | `CognitiveMarketSystem` | Ingest → Interpret → Collision → Signal |
| **Pipeline B** (7-Phase) | Operational flow: News → Cognition → Behavior → Impact → Validate → Authorize → Execute | `PipelineOrchestrator` | 7 sequential phases |
| **Pipeline C** (Bridge) | Unified: Engine for analysis, Phase 3-7 for execution | `PipelineBridge` | 3 modes: engine_only, phase_only, hybrid |

### Codebase Statistics

| Category | Count |
|----------|-------|
| Python files | 75+ |
| Total lines of code | ~38,000 |
| Classes | 120+ |
| Dataclasses | 80+ |
| Enums | 30+ |
| Directories | 30 |
| Test files | 8 (84+ tests) |

---

## 2. Installation & Dependencies

### Expected `pip install` Output

```
pip install -r requirements.txt
```

**Required packages (18):**

| Package | Purpose | Priority |
|---------|---------|----------|
| `spacy>=3.5` | Core NLP parsing | P1 |
| `transformers>=4.30` | Zero-shot classification, NLI, embeddings | P1 |
| `torch>=2.0` | Transformer backend | P1 |
| `sentencepiece>=0.1.99` | Tokenization | P1 |
| `requests>=2.28` | HTTP API clients | P1 |
| `feedparser>=6.0` | RSS parsing | P1 |
| `aiohttp>=3.8` | Async HTTP | P1 |
| `networkx>=3.0` | Knowledge graph | P1 |
| `numpy>=1.24` | Numerical computation | P2 |
| `scipy>=1.10` | Statistical models | P2 |
| `streamlit>=1.25` | Dashboard | P3 |
| `pandas>=2.0` | Data processing | P3 |
| `schedule>=1.2` | Task scheduling | P3 |
| `openai>=1.0` | LLM integration | P4 |
| `praw>=7.7` | Reddit API | P4 |
| `tweepy>=4.14` | Twitter API | P4 |
| `beautifulsoup4>=4.12` | Web scraping | P4 |
| `python-dotenv>=1.0` | Environment variables | Util |

### spaCy Model Download

```bash
python -m spacy download en_core_web_sm
# Optional transformer model:
python -m spacy download en_core_web_trf
```

### Environment Variables (.env)

```
NEWSAPI_KEY=           # NewsAPI.org key (optional — enables NewsAPI source)
LOG_LEVEL=INFO         # DEBUG|INFO|WARNING|ERROR
LOG_FILE=              # Path for file logging (optional)
DEFAULT_ASSET=BTC      # Default asset
DATABASE_PATH=         # SQLite path (auto-created if empty)
DASHBOARD_PORT=8501    # Streamlit port
```

---

## 3. Entry Point 1: `python main.py` (Interactive Demo)

### Expected Console Output

```
======================================================================
  COGNITIVE MARKET ENGINE — Bootstrap
======================================================================
  [OK] NLP Engine loaded (DeepNLPParser)
  [OK] Storage connected (SQLite)
  [OK] Feedback loop active
  [OK] Cognitive Engine initialized (asset=BTC)
  [OK] Scenario Engine ready
  [OK] Hidden Truth modules: ['crosssource', 'omission', 'timing', 'narrative']
  [OK] Multi-Asset modules: ['correlation', 'contagion']
  [OK] NewsAggregator ready
  [OK] Execution Engine ready
  [OK] Market Data Feed connected
  [OK] DecisionEngine initialized
  [OK] Streaming Pipeline & EventBus wired (Decision + Execution connected)

  Bootstrap complete: 11/12 modules loaded
======================================================================

======================================================================
  INTERACTIVE DEMO
======================================================================

--- Event 1: Reuters ---
    Federal Reserve signals unexpected dovish pivot in interest rate ...
  -> Signal: passive_accumulation | Direction: BUY | Strength: 0.72 | Confidence: HIGH

  -> Scenarios: bullish, tail_risk=0.08

--- Event 2: Bloomberg ---
    Major financial institution announces sudden failure with $50 ...
  -> Signal: aggressive_mean_reversion | Direction: BUY | Strength: 0.85 | Confidence: MEDIUM

  -> Scenarios: bearish, tail_risk=0.35

--- Event 3: CNBC ---
    SEC announces new regulatory framework for digital assets...
  -> Signal: no_trade | Direction: NEUTRAL | Strength: 0.15 | Confidence: VERY_LOW

  -> Scenarios: neutral, tail_risk=0.12

[SUMMARY] Processed 3 events, generated 2 tradable signals

[STATUS]
  asset: BTC
  events_processed: 3
  signals_generated: 3
  active_signals: 2
  last_signal_type: no_trade
```

### Bootstrap Module Loading (11 modules)

| # | Module | Class | Expected Status |
|---|--------|-------|-----------------|
| 1 | NLP Engine | `DeepNLPParser` | `[OK]` or `[--]` if spaCy unavailable |
| 2 | Storage | `DatabaseManager` | `[OK]` SQLite auto-created |
| 3 | Feedback | `FeedbackLoop` | `[OK]` |
| 4 | Cognitive Engine | `CognitiveMarketSystem` | `[OK]` (always succeeds) |
| 5 | Scenario Engine | `ScenarioGenerator` | `[OK]` |
| 6 | Hidden Truth | 4 analyzers | `[OK]` list of loaded modules |
| 7 | Multi-Asset | Correlation + Contagion | `[OK]` |
| 8 | NewsAggregator | `NewsAggregator` | `[OK]` |
| 9 | Execution | `ExecutionNexus` | `[OK]` |
| 10 | Market Data | `MarketDataFeed` | `[OK]` |
| 11 | Pipeline + EventBus + Decision | `StreamingPipeline` | `[OK]` |

### 3 Sample News Events Processed

| Event | Source | Signal Type | Direction | Strength Range | Confidence |
|-------|--------|-------------|-----------|----------------|------------|
| Fed dovish pivot | Reuters | `PASSIVE_ACCUMULATION` | BUY | 0.60–0.85 | HIGH |
| Bank failure crisis | Bloomberg | `AGGRESSIVE_MEAN_REVERSION` or `PASSIVE_DISTRIBUTION` | BUY or SELL | 0.50–0.90 | MEDIUM |
| SEC regulation (ambiguous) | CNBC | `NO_TRADE` | NEUTRAL | 0.00–0.30 | VERY_LOW |

### System Status Dict (Final)

```python
{
    "asset": "BTC",
    "events_processed": 3,
    "signals_generated": 3,
    "active_signals": 2,
    "last_signal_type": "no_trade",
    "engine_state": "active"
}
```

---

## 4. Entry Point 2: `python main.py --live` (Live Monitoring)

Delegates to `run_live.py` — continuous market monitoring loop.

### Expected Console Output

```
================================================================================
COGNITIVE MARKET ENGINE - LIVE INITIALIZATION
================================================================================
[STORAGE] Database connected
[FEEDBACK] Learning loop active
[SYSTEM] Connecting via NewsAggregator (multi-source)...
[DATA] NewsAggregator ready
[SYSTEM] Initializing Cognitive Models...

[LOOP] Starting Continuous Market Scanner (Ctrl+C to stop)...
[14:32:15] Monitoring... (No new events)
[14:33:15] Monitoring... (No new events)

================================================================================
>>> NEW EVENT: Federal Reserve Holds Rates Steady Amid Inflation Concerns
================================================================================

   SIGNAL: PASSIVE_ACCUMULATION
   REASON: Structural opportunity detected via expectation collision...

   >>> TRADE SIGNAL: BUY, strength=0.68
```

### Behavior

| Aspect | Expected |
|--------|----------|
| Poll interval | 60 seconds |
| News sources | NewsAggregator (NewsAPI + GDELT + RSS) or legacy RealDataProvider |
| Deduplication | Content hash — each article processed exactly once |
| Asset scope | `["BTC", "ETH", "CRYPTO"]` |
| Macro scope | `["finance", "rates"]` |
| Exit | `Ctrl+C` → `[STOP] Monitoring stopped by user.` |
| No data fallback | `[FATAL] No data source available.` |

### Signal Output Per Event

```
SIGNAL: <signal_type>           # One of 8 SignalType values
REASON: <human-readable>        # Why this signal was generated
>>> TRADE SIGNAL: <direction>, strength=<0.00-1.00>    # Only if not NO_TRADE
```

---

## 5. Entry Point 3: `python main.py --dashboard` (Streamlit Dashboard)

### Launch Command

```bash
python main.py --dashboard
# or directly:
streamlit run dashboard/app.py --server.port 8501
```

### Expected Output

```
  COGNITIVE MARKET ENGINE — Bootstrap
  ...
  Bootstrap complete: 11/12 modules loaded

You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

### Dashboard Pages (7 pages)

| # | Page | Key Components |
|---|------|---------------|
| 1 | **System Overview** | 4 metric cards (Events Processed, Avg Latency, Errors, Status), Model Performance table, Storage Stats |
| 2 | **Signal Monitor** | Recent signals with direction, strength, trust score, timestamp |
| 3 | **Model Credibility** | Per-model accuracy rankings, confidence calibration, ensemble weights |
| 4 | **Correlation Matrix** | Cross-asset correlation heatmap, anomaly alerts (z-score > 2) |
| 5 | **Scenario Analysis** | Expandable scenario trees with probability-weighted outcomes |
| 6 | **Hidden Truth Alerts** | Severity-coded alerts (red=high, yellow=medium, blue=info) |
| 7 | **News Feed** | Manual text input → process → result display; recent events table |

### Dashboard Metrics Displayed

```
┌──────────────────┬──────────────┬──────────────┬──────────────┐
│ Events Processed │ Avg Latency  │ Errors       │ Status       │
│ 147              │ 45.2 ms      │ 3            │ running      │
└──────────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 6. Entry Point 4: `python main.py --test` (Validation Suite)

Runs `simple_test.py` and `test_cognitive_system.py`.

### Expected Output

```
[TEST] Running validation suite ...

=== Test 1: Complete Pipeline ===
Phase 1: News Ingested
  Event ID: <uuid>
  Source: Reuters
  Participants: 5

Phase 2: Cognitive Interpretation
  Retail: belief_shift=0.65, urgency=0.80
  HFT: belief_shift=0.00, urgency=1.00
  Hedge Fund: belief_shift=0.45, urgency=0.55
  Bank: belief_shift=0.30, urgency=0.20
  Market Maker: belief_shift=0.00, urgency=0.90

Phase 3: Expectation Collision
  Variance: 0.42
  Disagreement: 0.55
  Liquidity Stress: -0.30
  Market Stress Index: 0.48

Phase 4: Signal Translation
  Signal: PASSIVE_ACCUMULATION
  Direction: BUY
  Strength: 0.72
  Confidence: HIGH

=== Test 2: Signal Execution ===
Signal generated: <signal_id>
Executed at $67,250.00
Closed at $68,100.00
P&L: +$850.00
Status: CLOSED

=== Test 3: Multiple Events ===
Processed 4 events from different sources
All signals valid
Signal types observed: ['passive_accumulation', 'no_trade', 'volatility_capture', ...]

=== COGNITIVE SYSTEM TESTS ===
Scenario 1 (Bullish): PASS — signal_type != NO_TRADE
Scenario 2 (Crash):   PASS — direction = SELL or NEUTRAL
Scenario 3 (Earnings): PASS — valid signal generated
Scenario 4 (Ambiguous): PASS — NO_TRADE or low confidence
Full Workflow: PASS — execution + P&L close works
Signal Properties: PASS — all 17 properties present

RESULTS: 9 passed, 0 failed
```

### 17 Required Signal Properties

Every `TradableSignal` must contain:

| Property | Type | Range |
|----------|------|-------|
| `signal_id` | str | UUID format |
| `signal_type` | SignalType | 8 possible values |
| `direction` | str | BUY / SELL / NEUTRAL |
| `strength` | float | [0.0, 1.0] |
| `confidence` | ConfidenceLevel | VERY_LOW to VERY_HIGH |
| `execution_mode` | ExecutionMode | PASSIVE / ALGORITHMIC / AGGRESSIVE |
| `urgency` | float | [0.0, 1.0] |
| `suggested_position_pct` | float | [0.01, 0.15] |
| `max_position_pct` | float | ≥ suggested |
| `stop_loss_distance` | float | [0.02, 0.10] |
| `profit_target_distance` | float | > 0 |
| `entry_window_open_sec` | float | ≥ 0 |
| `entry_window_close_sec` | float | ≥ open |
| `hold_duration_sec` | float | > 0 |
| `exit_time_sec` | float | > 0 |
| `reason` | str | Human-readable |
| `participant_drivers` | dict | Per-participant data |

---

## 7. Entry Point 5: `python main.py --news "..."` (Single News)

### Command

```bash
python main.py --news "Fed raises interest rates by 50 basis points"
```

### Expected Output

```
Signal: passive_distribution
Direction: SELL
Strength: 0.650
Confidence: MEDIUM
Reason: Regime fragility detected (0.72) with moderate expectation collision...
```

### Signal Type Decision Matrix

| News Content | Expected Signal | Direction | Strength Range |
|-------------|-----------------|-----------|----------------|
| Fed rate hike | `PASSIVE_DISTRIBUTION` or `REGIME_FADE` | SELL | 0.50–0.80 |
| Fed rate cut | `PASSIVE_ACCUMULATION` | BUY | 0.60–0.85 |
| Bank failure | `AGGRESSIVE_MEAN_REVERSION` | BUY | 0.70–0.90 |
| Ambiguous regulation | `NO_TRADE` | NEUTRAL | 0.00–0.30 |
| Earnings beat | `PASSIVE_ACCUMULATION` | BUY | 0.40–0.70 |
| Geopolitical crisis | `VOLATILITY_CAPTURE` | NEUTRAL | 0.50–0.80 |

---

## 8. Entry Point 6: `python legacy_main.py` (7-Phase Pipeline)

### Expected Output

```
Pipeline Status: {
    'phase_1': 'READY',
    'phase_2': 'READY',
    'phase_3': 'READY',
    'phase_4': 'READY',
    'phase_5': 'READY',
    'phase_6': 'READY',
    'phase_7': 'NOT_READY'   # Only READY if live_execution=True
}


            7-PHASE PIPELINE EXECUTION SUMMARY


Event ID:           EVT_1709312400.0
Timestamp:          2026-03-01 14:00:00
Source:             reuters
Final Status:       PHASE_4_COMPLETE

Phase 1 (News):      ✓
Phase 2 (Cognitive):  ✓
Phase 3 (Behavior):   ✓
Phase 4 (Impact):     ✓
Phase 5 (Validate):   ✗  (no actual market data provided)
Phase 6 (Authorize):  ✗
Phase 7 (Execute):    ✗

No errors
```

### Pipeline Status Values

| Status | Meaning |
|--------|---------|
| `PENDING` | Not yet processed |
| `PROCESSING` | Currently in pipeline |
| `PHASE_N_COMPLETE` | Phase N finished successfully |
| `PHASE_N_SKIPPED` | Phase N skipped (dependency missing) |
| `APPROVED_FOR_EXECUTION` | Phase 6 approved the signal |
| `FILTERED` | Phase 6 rejected the signal (trust < 0.6) |
| `EXECUTED` | Phase 7 executed successfully |
| `REJECTED` | Error in any phase |

---

## 9. Entry Point 7: `python pipeline_bridge.py` (Unified Bridge)

### Three Modes

| Mode | Behavior |
|------|----------|
| `engine_only` | Runs only Pipeline A (cognitive). Fast, analysis-only. |
| `phase_only` | Runs only Pipeline B (7-phase). Full operational flow. |
| `hybrid` (default) | Engine for cognitive analysis → feeds into Phase 3-7 for execution. |

### Expected `UnifiedResult` Output

```python
{
    "timestamp": "2026-03-01T14:00:00",
    "source": "reuters",
    "engine_ran": True,
    "phase_ran": True,
    "final_direction": "bullish",
    "final_confidence": 0.7200,
    "final_action": "BUY",
    "reasoning": [
        "Engine: passive_accumulation signal (strength=0.72, confidence=HIGH)",
        "Phase Pipeline: 3 of 7 phases completed"
    ]
}
```

### API Key Manager Status

```python
APIKeyManager().status_report()
# Returns:
{
    "newsapi": "configured",     # or "MISSING"
    "openai": "MISSING",
    "reddit": "MISSING",
    "reddit_secret": "MISSING",
    "twitter": "MISSING",
    "coingecko": "MISSING",
    "gdelt": "MISSING"
}
```

---

## 10. Engine Pipeline (Pipeline A) — 4-Phase Cognitive

### Phase 1: News Ingestion → `NewsEvent`

**Input:** Raw text string  
**Output:** `NewsEvent` dataclass

```python
NewsEvent(
    event_id="EVT_abc123",
    timestamp=datetime(2026, 3, 1, 14, 0),
    source_id="Reuters",
    raw_text="Federal Reserve signals...",
    asset_scope=["BTC", "ETH", "SPY"],
    macro_scope=["rates", "monetary-policy"],
    linguistic_shock=LinguisticShockVector(
        surprise_level=0.60,        # [0,1]
        ambiguity_level=0.25,       # [0,1]
        certainty_level=0.75,       # [0,1]
        authority_strength=0.80,    # [0,1]
        novelty_score=0.45,         # [0,1]
        temporal_focus=TemporalFocus.FUTURE,
        narrative_shift=NarrativeShift.STRONG,
        is_macro=True,
        is_asset_specific=False,
    ),
    participant_responses=[]        # Filled in Phase 2
)
```

### Linguistic Shock Vector Computation

**Path A (NLP available):**
- `surprise_level = 1.0 - overall_certainty`
- `ambiguity_level = overall_subjectivity`
- `authority_strength = min(1.0, 0.4 + len(authority_entities) × 0.1)`
- `novelty_score = complexity_score`

**Path B (Keyword fallback):**
- `surprise_level = min(1.0, surprise_word_count × 0.2)`
- `ambiguity_level = min(1.0, ambiguity_word_count × 0.15)`
- `certainty_level = min(1.0, 0.3 + certainty_word_count × 0.15)`
- `authority_strength = min(1.0, 0.4 + authority_source_count × 0.2)`

### Phase 2: Cognitive Interpretation

All 5 participant models process the same `LinguisticShockVector` and produce different `ParticipantResponse` objects. See Section 13 for detailed expected outputs.

### Phase 3: Expectation Collision

The `ExpectationCollisionEngine` compares all 5 participant responses and produces collision metrics. See Section 14.

### Phase 4: Signal Translation

The `TradableSignalTranslator` converts `MarketStressVector` into one of 8 `TradableSignal` types. See Section 15.

---

## 11. 7-Phase Pipeline (Pipeline B) — Legacy Operational

### Phase-by-Phase Expected Outputs

| Phase | Input | Output | Key Module |
|-------|-------|--------|------------|
| 1. News Parsing | Raw text | `NewsEvent` (structured) | `news_model/parser.py` |
| 2. Cognitive Interpretation | `NewsEvent` | 5 `ParticipantExpectation` objects | `participant_cognition/participant_models.py` |
| 3. Behavior Translation | `ParticipantExpectation` | 5 `BehaviorProfile` objects | `market_response/behavior_models.py` |
| 4. Market Impact | `BehaviorProfile` list | `MarketImpactProfile` | `market_impact/market_impact_models.py` |
| 5. Reality Validation | Predicted vs Actual | `ValidationRecord` | `reality_validation/market_reality.py` |
| 6. Signal Authorization | `ValidationRecord` | `SignalRecord` (APPROVED/FILTERED) | `signal_auth/signal_authorization.py` |
| 7. Execution | `SignalRecord` | `ExecutedOrder` | `execution/execution_nexus.py` |

### Phase 1: NewsEvent (news_model)

```python
NewsEvent(
    event_id="EVT_<uuid>",
    timestamp_utc=datetime(...),
    source="Reuters",
    raw_text="<preserved exactly>",
    sentences=[Sentence(text="...", index=0), ...],
    clauses=[Clause(text="...", is_conditional=True, ...)],
    modality_markers=[ModalityMarker(text="may", marker_type="uncertainty", strength=0.6)],
    temporal_markers=[TemporalMarker(temporal_type=TemporalType.FUTURE, ...)],
    actors=[Actor(name="Federal Reserve", category="central_bank", certainty=0.9)],
    semantic_claims=[SemanticClaim(actor="Fed", action="signal patience", object_="rates", confidence=0.75)],
    narrative_types=[NarrativeType.MACRO_POLICY],
    ambiguity_score=0.50,           # [0,1]
    confidence_level=ConfidenceLevel.MEDIUM,
    contradicts_prior_news=False,
    participant_interpretations={}   # Filled in Phase 2
)
```

**Ambiguity Scoring Rules:**
- `authority_count > uncertainty_count` → ambiguity=0.2, confidence=HIGH
- `uncertainty_count > authority_count` → ambiguity=0.7, confidence=LOW
- Equal → ambiguity=0.5, confidence=MEDIUM
- Conditional temporal markers: +0.2 to ambiguity
- Contradiction markers: +0.1 to ambiguity

### 9 Narrative Types

| NarrativeType | Triggers |
|---------------|----------|
| `MACRO_POLICY` | rate, fed, monetary, policy, fiscal |
| `LIQUIDITY` | liquidity, volume, flow |
| `GROWTH` | GDP, growth, expansion, earnings |
| `CREDIT_RISK` | default, credit, downgrade, debt |
| `GEOPOLITICAL` | war, sanction, conflict, trade war |
| `TECHNOLOGICAL` | tech, innovation, AI |
| `CRISIS_SHOCK` | crash, panic, crisis, collapse |
| `NARRATIVE_REINFORCEMENT` | (aligned with prior narrative) |
| `NARRATIVE_CONTRADICTION` | (contradicts prior narrative) |

---

## 12. NLP Engine Expected Outputs

### DeepNLPParser (~1,300 lines)

**Input:** Raw text  
**Output:** `DeepParseResult`

```python
DeepParseResult(
    raw_text="The Federal Reserve signaled patience...",
    text_hash="a1b2c3d4...",
    timestamp=datetime(...),
    sentences=[
        SentenceAnalysis(
            text="The Federal Reserve signaled patience...",
            index=0,
            tokens=["The", "Federal", "Reserve", ...],
            pos_tags=["DT", "NNP", "NNP", ...],
            dependencies=[...],
            triples=[
                SemanticTriple(
                    subject="Federal Reserve",
                    predicate="signaled",
                    object_="patience",
                    confidence=0.85,
                    negated=False,
                    conditional=False,
                )
            ],
            entities=[
                EntityMention(text="Federal Reserve", label="ORG", confidence=0.95)
            ],
            is_conditional=False,
            is_negated=False,
            tense="past",
            voice="active",
            certainty_score=0.65,        # [0,1]
            hedging_words=["signaled"],
            boosting_words=[],
        ),
    ],
    all_entities=[...],
    all_triples=[...],
    narrative_types=[NarrativeIntent.SIGNAL_POLICY],
    detected_intent=NarrativeIntent.SIGNAL_POLICY,
    overall_certainty=0.65,
    overall_subjectivity=0.30,
    complexity_score=0.45,
    key_phrases=["Federal Reserve", "patience", "rate cuts"],
    document_embedding=[0.023, -0.156, ...],  # 384-dim vector
    language="en",
    word_count=42,
    parse_method="spacy+transformers",
)
```

### Certainty Score Formula

$$\text{certainty} = \max\left(0, \min\left(1, 0.5 - \text{hedge\_count} \times 0.15 + \text{boost\_count} \times 0.15\right)\right)$$

### 26 Hedge Words

`may, might, could, possibly, reportedly, allegedly, seemingly, appears, suggests, likely, unlikely, probably, potentially, roughly, approximately, about, perhaps, some, somewhat, believed, understood, expected, anticipated, uncertain, unclear, debatable`

### 21 Boost Words

`confirmed, announced, declared, will, shall, must, certainly, definitely, absolutely, clearly, officially, immediately, directly, explicitly, unequivocally, categorically, decisively, firmly, undoubtedly, indisputably, unanimously`

### Entity Extraction Output

```python
EntityExtractor().extract_all(text)
# Returns:
{
    "financial": [
        FinancialEntity(text="Federal Reserve", entity_type="central_bank", sector="banking"),
        FinancialEntity(text="S&P 500", entity_type="INDEX"),
    ],
    "geopolitical": [
        GeopoliticalEntity(text="United States", entity_type="COUNTRY", iso_code="US"),
    ],
    "people": ["Chair Powell"],
    "monetary": [{"amount": 50, "unit": "basis points", "normalized": 0.005}],
    "temporal": [{"type": "relative", "text": "next quarter"}],
    "indicators": ["CPI", "unemployment"],
    "relations": [
        EntityRelation(source="Fed", target="rates", relation_type="regulates")
    ],
}
```

### Contradiction Detection Output

```python
ContradictionDetector().check_contradiction(
    claim_a="Inflation is rising sharply",
    claim_b="Prices are declining steadily",
    source_a="reuters",
    source_b="bloomberg",
)
# Returns:
ContradictionResult(
    claim_a="Inflation is rising sharply",
    claim_b="Prices are declining steadily",
    contradiction_type=ContradictionType.ANTONYM,
    confidence=0.82,
    reasoning="Antonym detected: 'rising' vs 'declining'",
    severity="high",
    resolution_hint="Check primary data sources for actual CPI figures",
)
```

### Intent Detection Output

```python
IntentDetector().analyze(text, source="reuters", publish_time=datetime.now())
# Returns:
IntentAnalysis(
    communication_intent=CommunicationIntent.INFORM,
    communication_confidence=0.85,
    strategic_intent=StrategicIntent.ROUTINE,
    strategic_confidence=0.70,
    target_audience=TargetAudience.INSTITUTIONAL_INVESTORS,
    timing_intent=TimingIntent.MARKET_HOURS,
    manipulation_score=0.05,        # [0,1]
    manipulation_signals=[],
    source_credibility=0.95,         # Reuters = 0.95
    claim_verifiability=0.75,
    hidden_agenda_score=0.08,
    beneficiaries=["bond traders"],
    harmed_parties=["leveraged borrowers"],
    reasoning="Routine policy communication from high-credibility source...",
)
```

### Source Credibility Rankings

| Source | Score |
|--------|-------|
| Reuters | 0.95 |
| Bloomberg | 0.95 |
| AP | 0.90 |
| WSJ | 0.88 |
| FT | 0.88 |
| CNBC | 0.75 |
| MarketWatch | 0.70 |
| Seeking Alpha | 0.55 |
| ZeroHedge | 0.40 |
| Twitter/X | 0.35 |
| Reddit | 0.30 |
| Telegram | 0.25 |

---

## 13. Participant Cognitive Models — 5 Archetypes

### Same News → Different Interpretations

Given `LinguisticShockVector(surprise=0.7, ambiguity=0.3, certainty=0.7, authority=0.8)`:

| Participant | Belief Shift | Risk Perception | Urgency | Action Bias | Direction Bias |
|-------------|-------------|-----------------|---------|-------------|----------------|
| **Retail** | 0.65 | 0.72 | 0.80 | 0.75 | +0.35 (BUY) |
| **HFT** | 0.00 | 0.51 | 1.00 | 1.00 | 0.00 (NEUTRAL) |
| **Hedge Fund** | 0.52 | 0.40 | 0.55 | 0.60 | +0.18 (BUY) |
| **Bank** | 0.55 | 0.35 | 0.20 | 0.40 | 0.00 (NEUTRAL) |
| **Market Maker** | 0.00 | 0.51 | 0.90 | 0.85 | 0.00 (NEUTRAL) |

### Participant Profiles

| Property | Retail | HFT | Hedge Fund | Bank | Market Maker |
|----------|--------|-----|------------|------|--------------|
| Latency | FAST | INSTANT | MEDIUM | VERY_SLOW | INSTANT |
| Capital | RETAIL (<$1M) | MEGA (>$1B) | MEGA | MEGA | INSTITUTIONAL |
| Reliability | 0.45 | 0.92 | 0.75 | 0.70 | 0.88 |
| Overreaction | 0.85 | 0.05 | 0.35 | 0.15 | 0.10 |
| Reversal | 0.30 | 0.60 | 0.55 | 0.20 | 0.95 |
| Provides liquidity | No | Yes | No | Yes | Yes |
| Uses stops | Yes | No | Yes | No | No |
| Time horizon | Weeks | Milliseconds | Days | Months | Minutes |
| Risk tolerance | HIGH | ULTRA_LOW | ADAPTIVE | LOW | MEDIUM |
| Bias | OVERREACTION | LIQ_PRESERVATION | OPPORTUNITY_SEEKING | RISK_AVERSE | LIQ_PRESERVATION |

### Key Cognitive Formulas

**Retail belief_shift:**
$$\text{shift} = \text{surprise} \times 0.4 + \text{novelty} \times 0.3 + (1 - \text{certainty}) \times 0.3$$

**HFT** always: belief_shift = 0.0, urgency = 1.0, direction_bias = 0.0

**Hedge Fund belief_shift:**
$$\text{shift} = \text{certainty} \times 0.4 + \text{authority} \times 0.3 + \text{surprise} \times 0.3$$

**Bank belief_shift:**
$$\text{shift} = \text{authority} \times 0.5 + \text{certainty} \times 0.3 + 0.3 \times (\text{is\_regulatory})$$

**Market Maker** always: belief_shift = 0.0, spread_expectation = ambiguity × 0.9 + surprise × 0.5

### Action Likelihoods (Phase 2B)

8 probabilities that **always sum to 1.0**:

| Action | Description |
|--------|-------------|
| `increase_exposure` | Add to position |
| `decrease_exposure` | Reduce position |
| `widen_spreads` | Increase bid-ask (MM/HFT) |
| `pull_liquidity` | Withdraw from market |
| `hold_position` | No change |
| `increase_hedging` | Add hedges |
| `wait_for_clarity` | Wait for more information |
| `panic_action` | Fear-driven immediate action |

---

## 14. Expectation Collision Engine

### Expected Output

```python
(metrics, stress_vector) = collision_engine.compute_collision(news_event)

# ExpectationCollisionMetrics:
metrics = ExpectationCollisionMetrics(
    expectation_variance=0.42,          # [0,1] — how much participants disagree
    direction_disagreement=0.55,        # [0,1]
    timing_disagreement=0.38,           # [0,1]
    magnitude_disagreement=0.30,        # [0,1]
    total_expected_consumption=0.65,     # [0,1]
    total_expected_provision=0.45,       # [0,1]
    liquidity_stress_index=-0.20,       # [-1,1] — negative = consumption > provision
    buyers=2,
    sellers=1,
    neutral_expected=2,
    fastest_reactor="HFT",
    fastest_reaction_time_sec=0.001,
    collision_start_sec=0.001,
    collision_peak_sec=60.0,
    collision_end_sec=7200.0,
    market_stress_index=0.48,           # [0,1]
)

# MarketStressVector:
stress_vector = MarketStressVector(
    liquidity_stress=0.50,              # [0,1]
    volatility_stress=0.65,             # [0,1]
    disagreement_index=0.55,            # [0,1]
    reaction_asymmetry=0.40,            # [0,1]
    regime_fragility=0.45,              # [0,1]
    immediate_impact_expected=True,
    hft_volatility_spike=True,
    structural_opportunity=0.52,        # [0,1]
    confidence_in_assessment=0.72,      # [0,1]
    retail_panic_window=(3.0, 7.0),     # minutes
    institutional_rebalance_window=(30.0, 120.0),  # minutes
)
```

### Key Collision Formulas

$$\text{expectation\_variance} = \text{mean}\left(\frac{\text{var}(\text{vol})}{\bar{\text{vol}}}, \frac{\text{var}(\text{liq})}{\bar{\text{liq}}}, \frac{\text{var}(\text{spread})}{\bar{\text{spread}}}\right)$$

$$\text{market\_stress\_index} = 0.25 \times \text{exp\_var} + 0.25 \times |\text{liq\_stress}| + 0.25 \times \bar{\text{vol}} + 0.25 \times \mathbb{1}[\text{MM withdrawing}]$$

$$\text{regime\_fragility} = 0.4 \times \text{exp\_var} + 0.3 \times \text{timing\_disagr} + 0.3 \times |\text{liq\_stress}|$$

---

## 15. Signal Translation Expected Outputs

### 8 Signal Types

| Signal Type | Trigger Conditions | Direction | Urgency |
|-------------|-------------------|-----------|---------|
| `PASSIVE_ACCUMULATION` | disagreement > 0.5, retail panic, no immediate impact | BUY | Low |
| `PASSIVE_DISTRIBUTION` | regime_fragility > 0.7, liquidity stress > 0.5 | SELL | Low |
| `AGGRESSIVE_MEAN_REVERSION` | liquidity stress > 0.6, vol > 0.7, immediate impact | BUY | High |
| `LIQUIDITY_ARBITRAGE` | liquidity stress, disagreement, no HFT spike | NEUTRAL | Medium |
| `VOLATILITY_CAPTURE` | HFT spike, volatility > 0.7 | NEUTRAL | High |
| `LIQUIDITY_PROVISION` | liquidity stress, low fragility, no immediate impact | NEUTRAL | Low |
| `REGIME_FADE` | regime_fragility > 0.6, reaction asymmetry > 0.5 | Context-dependent | Medium |
| `NO_TRADE` | confidence < 0.5 OR opportunity < 0.4 | NEUTRAL | None |

### Gate Checks (Must Pass)

| Gate | Threshold | Outcome if Failed |
|------|-----------|-------------------|
| Gate 1: Confidence | `confidence_in_assessment < 0.5` | → `NO_TRADE` |
| Gate 2: Opportunity | `structural_opportunity < 0.4` | → `NO_TRADE` |

### Position Sizing Formula

$$\text{base\_position} = \text{strength} \times 0.10$$
$$\text{suggested} = \begin{cases} \max(0.01, \text{base} \times 0.5) & \text{if urgency} > 0.8 \\ \text{base} & \text{otherwise} \end{cases}$$
$$\text{max\_position} = \min(0.15, \text{suggested} \times 1.5)$$

### Stop Loss Formula

$$\text{vol\_adjusted\_stop} = \text{volatility\_stress} \times 0.08 + 0.02$$

Multipliers per signal type: 0.5× (arbitrage) to 2.0× (passive accumulation)

---

## 16. Market Impact Layer

### BehaviorAggregator Output

```python
aggregated = AggregatedBehavior(
    avg_risk_posture_signal=-0.30,       # [-1,1]
    avg_liquidity_posture_signal=-0.20,   # [-1,1]
    avg_exposure_intent_signal=0.15,      # [-1,1]
    avg_urgency_signal=0.65,              # [0,1]
    avg_optionality_signal=0.25,          # [0,1]
    hft_urgency_weighted=0.85,            # [0,1]
    bank_risk_weighted=0.30,              # [0,1]
    mm_withdrawal_weighted=0.45,          # [0,1]
    behavior_disagreement=0.42,           # [0,1]
    participant_divergence=["HFT vs Bank: urgency divergence"],
    behavior_concentration=0.55,          # [0,1]
)
```

### Default Participant Weights

| Participant | Weight |
|-------------|--------|
| HFT | 0.25 |
| Market Maker | 0.25 |
| Bank | 0.20 |
| Hedge Fund | 0.20 |
| Retail | 0.10 |

### MarketImpactProfile Output

```python
impact = MarketImpactProfile(
    news_event_id="EVT_abc123",
    liquidity_impacts=[
        ImpactMeasurement(
            impact_type=LiquidityImpactType.DEPTH_REDUCTION,
            magnitude=0.55,
            confidence=0.70,
            timing=ImpactTiming(onset_delay=timedelta(seconds=1), peak_window=timedelta(minutes=5)),
        )
    ],
    volatility_impacts=[
        ImpactMeasurement(impact_type=VolatilityImpactType.INSTANT_SPIKE, magnitude=0.72, ...)
    ],
    spread_impacts=[...],
    order_flow_impacts=[...],
    price_dynamics_impacts=[...],
    regime_impacts=[...],
    overall_market_stress=0.62,          # [0,1] — 0=calm, 1=crisis
    confidence_in_impact=0.68,           # [0,1]
    threshold_breached=False,
    saturation_detected=False,
    feedback_loop_risk=True,
)
```

### 6 Impact Dimensions

| Dimension | Types | Trigger Example |
|-----------|-------|-----------------|
| Liquidity | DEPTH_REDUCTION, DEPTH_CONCENTRATION, LIQUIDITY_ASYMMETRY, TEMPORARY_VACUUM | MM withdrawal > 0.3 |
| Volatility | INSTANT_SPIKE, SUSTAINED, CLUSTERING, SUPPRESSION | HFT urgency > 0.6 |
| Spread | SPREAD_WIDENING, INSTABILITY, ASYMMETRIC | MM withdrawal > 0.3 |
| Order Flow | AGGRESSIVE_IMBALANCE, PASSIVE, ONE_SIDED, FRAGMENTATION | concentration > 0.6 |
| Price | JUMP_RISK, DRIFT, MEAN_REVERSION_PRESSURE, RANGE_EXPANSION | urgency > 0.7 |
| Regime | REGIME_TRANSITION, INSTABILITY, TEMPORARY_DISLOCATION | disagreement > 0.5 |

---

## 17. Reality Validation (Phase 5)

### ValidationRecord Output

```python
record = ValidationRecord(
    directional_accuracy=DirectionalValidity(
        predicted_direction=DirectionType.UP,
        actual_direction=DirectionType.UP,
        matches=True,
        confidence=0.85,
    ),
    volatility_accuracy=VolatilityValidity(
        predicted_vol_expansion=0.65,
        actual_vol_expansion=0.58,
        difference=0.07,
        accuracy=0.93,
    ),
    timing_accuracy=TimingValidity(
        expected_shock_onset=5.0,
        actual_shock_onset=3.2,
        shock_error=1.8,
        expected_peak=300.0,
        actual_peak=280.0,
        peak_error=20.0,
        overall_timing_accuracy=0.88,
    ),
    participation_accuracy=[
        ParticipationValidity(participant="HFT", timing_match=True, direction_match=True, overall_accuracy=0.95),
        ParticipationValidity(participant="Retail", timing_match=True, direction_match=False, overall_accuracy=0.50),
    ],
    regime_validity=RegimeValidity(predicted_shift=True, actual_regime_changed=True, event_classification=ValidityScore.ACCURATE),
    overall_accuracy=0.82,
    model_credibility=0.78,
    most_accurate_participant="HFT",
    least_accurate_participant="Retail",
)
```

### Overall Accuracy Formula

$$\text{overall} = 0.30 \times \text{directional} + 0.20 \times \text{volatility} + 0.20 \times \text{timing} + 0.15 \times \text{participation} + 0.15 \times \text{regime}$$

### Timing Tolerances

| Window | Tolerance |
|--------|-----------|
| Shock onset | 30 seconds |
| Peak | 300 seconds (5 min) |
| Recovery | 900 seconds (15 min) |

### Statistical Significance Testing

- **Binomial test** for direction accuracy (null p=0.5)
- **Z-test** with continuity correction for large samples
- **One-sample t-test** for overall accuracy vs baseline
- Implemented via `math.erfc` for Gaussian CDF

---

## 18. Signal Authorization (Phase 6)

### SignalRecord Output

```python
record = SignalRecord(
    signal_id="SIG_<uuid>",
    direction=SignalDirection.BUY,
    strength=0.72,
    volatility_impact=VolatilityImpact.MEDIUM,
    trust_score=0.78,
    participant_weights=ParticipantWeights(hft=0.95, hf=0.80, retail=0.40, bank=0.70, mm=0.85),
    source_news_ids=["EVT_abc123"],
    horizon=ReactionHorizon.SHORT_TERM,
    status=SignalStatus.APPROVED,
    approval_timestamp=datetime(...),
    expiration_timestamp=datetime(...) + timedelta(hours=4),
)
```

### Trust Score Formula

$$\text{trust} = \begin{cases}
0.3 \times 0.5 + 0.7 \times \text{current\_accuracy} & \text{first event} \\
0.6 \times \text{historical} + 0.4 \times \text{current} & \text{subsequent}
\end{cases}$$

Adjusted by:
- Intensity > 0.8: × 0.98
- Ambiguity: × (1 - 0.15 × ambiguity)

### Signal Filtering Gate

| Trust Score | Status |
|-------------|--------|
| ≥ 0.60 | `APPROVED` |
| 0.50–0.59 | `PENDING_VALIDATION` |
| < 0.50 | `FILTERED` |
| Regime = NOISY | `FILTERED` regardless |

### Signal Expiration

All approved signals expire after **4 hours**. After expiration:
- `is_expired() → True`
- `get_effective_strength() → 0.0`

---

## 19. Execution Engine (Phase 7)

### ExecutedOrder Output

```python
order = ExecutedOrder(
    order_id="ORD_<uuid>",
    signal_id="SIG_abc123",
    timestamp=datetime(...),
    direction="BUY",
    order_size=250000.0,
    entry_price=67250.00,
    status=ExecutionStatus.FILLED,
    profit_loss=0.0,
    exit_timestamp=None,
    exit_price=None,
)
```

### Position Sizing Formula (Convex)

$$\text{size} = \text{strength}^2 \times \text{max\_position\_size}$$

| Strength | Position % | Dollar Size (of $1M max) |
|----------|-----------|--------------------------|
| 0.50 | 25% | $250,000 |
| 0.70 | 49% | $490,000 |
| 0.90 | 81% | $810,000 |

**Adjustments:**
- EXTREME volatility: × 0.5
- Trust < 0.7: × 0.8

### Stop Loss / Take Profit

| Direction | Stop Loss | Take Profit |
|-----------|-----------|-------------|
| BUY | entry × 0.98 (−2%) | entry × 1.03 (+3%) |
| SELL | entry × 1.02 (+2%) | entry × 0.97 (−3%) |

### Circuit Breaker Thresholds

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Daily loss limit | −$50,000 | Stop all trading |
| Intraday drawdown | −$30,000 | Stop all trading |
| Volatility spike | 2.5× normal | Stop all trading |
| Execution failure | Consecutive failures | Stop all trading |

### Risk Level Colors

| Level | PnL Range | Action |
|-------|-----------|--------|
| 🟢 GREEN | > −$10,000 | Normal trading |
| 🟡 YELLOW | −$10K to −$30K | Reduced sizing |
| 🔴 RED | < −$30,000 | Stop trading |

### Execution Routing

| Horizon | Strategy | Timeout |
|---------|----------|---------|
| IMMEDIATE | Aggressive market order | 5 seconds |
| SHORT_TERM | VWAP | 60 seconds |
| MEDIUM/LONG | Passive limit | 300 seconds |

---

## 20. Decision Engine

### DecisionPacket Output

```python
decision = DecisionPacket(
    action=DecisionAction.BUY,
    asset="BTC",
    direction="bullish",
    suggested_position_pct=0.045,
    max_position_pct=0.08,
    overall_confidence=0.72,
    signal_agreement=0.80,
    stop_loss_pct=0.035,
    take_profit_pct=0.070,
    max_risk_pct=0.02,
    risk_reward_ratio=2.0,
    market_regime=MarketRegime.TRENDING,
    risk_gates_triggered=[],
    factor_scores={
        "NLP_ANALYSIS": 0.55,
        "COGNITIVE_MODELS": 0.72,
        "BEHAVIOR_TRANSLATION": 0.65,
        "MARKET_IMPACT": 0.60,
        "SCENARIO_ENGINE": 0.58,
        "HIDDEN_TRUTH": 0.10,
        "REALITY_VALIDATION": 0.45,
        "CROSS_ASSET": 0.30,
    },
    reasoning_chain=["Strong cognitive signal", "Trending regime favors momentum", ...],
    dissenting_signals=[],
    hidden_truth_flags=[],
)
```

### 8 Signal Source Weights

| Source | Default Weight | Crisis Weight |
|--------|---------------|---------------|
| NLP_ANALYSIS | 0.10 | 0.05 |
| COGNITIVE_MODELS | 0.20 | 0.15 |
| BEHAVIOR_TRANSLATION | 0.15 | 0.10 |
| MARKET_IMPACT | 0.15 | 0.25 |
| SCENARIO_ENGINE | 0.15 | 0.20 |
| HIDDEN_TRUTH | 0.10 | 0.10 |
| REALITY_VALIDATION | 0.10 | 0.10 |
| CROSS_ASSET | 0.05 | 0.05 |

### Decision Actions

| Action | Condition |
|--------|-----------|
| `BUY` | Bullish > Bearish × 1.2 AND strength > 0.4 |
| `SELL` | Bearish > Bullish × 1.2 AND strength > 0.4 |
| `HOLD` | Neither side has 20% edge |
| `REDUCE` | Moderate bearish signal |
| `HEDGE` | High uncertainty, existing position |
| `WATCH` | Interesting but not actionable |
| `EMERGENCY_EXIT` | Crisis regime + risk gates triggered |

### 5 Risk Gates

| Gate | Threshold | Effect |
|------|-----------|--------|
| Portfolio drawdown | > 10% | Block trade |
| Daily trade limit | > 10 trades | Block trade |
| Confidence floor | < 0.55 | Block trade |
| Position size limit | > 15% portfolio | Reduce size |
| Gross exposure | > 100% | Block new positions |

### Position Sizing Formula (Decision Engine)

$$\text{base} = \text{strength} \times \text{agreement} \times 0.10$$

Regime multipliers: CALM=1.0, TRENDING=1.2, VOLATILE=0.6, CRISIS=0.3

Half-Kelly constraint:
$$\text{max} = \frac{\text{edge}}{\text{strength}} \times 0.5 \times 0.15 \quad \text{where } \text{edge} = \text{strength} - 0.5$$

### Hidden Truth Adjustments

| Flag | Strength Modifier |
|------|-------------------|
| `manufactured_consensus` | × 0.5 |
| `omission` | × 0.7 |
| `strategic_timing` | × 0.8 |

---

## 21. Hidden Truth Detection

### 4 Core Analyzers

#### CrossSourceAnalyzer Output

```python
result = VerificationResult(
    story_hash="abc123",
    source_count=5,
    source_diversity=0.75,
    claim_consistency=0.82,
    narrative_alignment=0.78,
    cross_source_trust=0.80,
    single_source_only=False,
    conflicting_claims=["Reuters says 'rising', Bloomberg says 'stable'"],
    coordinated_narrative=False,
    suspicious_timing=False,
)
```

**Trust Formula:**
$$\text{trust} = 0.25 \times \text{diversity} + 0.30 \times \text{consistency} + 0.20 \times \text{alignment} + 0.15 \times (1 - \text{conflicts}) + 0.10 \times (1 - \text{coordination}) + 0.20 \times \text{credibility}$$

#### OmissionDetector Output

```python
report = OmissionReport(
    total_omissions=3,
    critical_omissions=1,
    overall_omission_score=0.45,
    omissions=[
        Omission(category="risk_factor", expected="default rates", significance="high", manipulation_risk=0.6),
    ],
    hedging_score=0.35,
    specificity_score=0.60,
)
```

**7 Event Types with Required Fields:**
- Rate decisions, earnings, M&A, regulatory, geopolitical, labor, macro data

#### TimingAnalyzer Output

```python
analysis = TimingAnalysis(
    release_time=datetime(2026, 3, 1, 17, 30),
    market_session="after_hours",
    strategic_timing_score=0.65,
    news_dump_probability=0.70,
    pre_positioning_risk=0.30,
    proximity_events=["FOMC meeting in 2 days"],
    timing_flags=["after_hours", "pre_event"],
)
```

**Strategic Score:**
$$\text{score} = 0.30 \times \text{dump} + 0.25 \times \text{preposition} + 0.10 \times \text{proximity} + 0.08 \times \text{flags} + \text{session\_bonus}$$

#### NarrativeTracker Output

```python
narrative = NarrativeEvolution(
    narrative_id="NAR_fed_rates_001",
    topic="Federal Reserve Rate Policy",
    first_seen=datetime(2026, 2, 15),
    last_updated=datetime(2026, 3, 1),
    snapshots=[NarrativeSnapshot(...)],
    direction_changes=2,
    amplification_trend="accelerating",
    current_sentiment=0.35,
    current_intensity=0.72,
    source_coverage=8,
    consensus_score=0.65,
    credibility=0.78,
)
```

### Advanced Detection (4 more analyzers)

| Analyzer | Output | Key Formula |
|----------|--------|-------------|
| `ManipulationPatternDetector` | `ManipulationSignal` with confidence | Sigmoid: $\frac{1}{1+e^{-10(s-0.5)}}$ |
| `SECFilingAnalyzer` | `FilingAnalysis` with PR/filing divergence | Gunning Fog: $0.4 \times (\bar{L}_{sent} + 100 \times r_{complex})$ |
| `InsiderCorrelationAnalyzer` | `InsiderSentimentCorrelation` | C-suite weight ×1.5, large transaction ×1.3 |
| `SourceNetworkAnalyzer` | Echo chamber detection | Credibility = $0.4 \times \text{cred} + 0.3 \times \text{accuracy} + 0.3 \times \text{independence}$ |

---

## 22. Scenario Engine

### ScenarioTree Output

```python
tree = ScenarioTree(
    event_id="EVT_abc123",
    event_text="Fed signals dovish pivot...",
    root=ScenarioNode(
        label="Base Case",
        probability=0.45,
        direction="bullish",
        magnitude=0.03,
        volatility_change=0.02,
        timeline_hours=24,
        children=[
            ScenarioNode(label="Follow-through rally", probability=0.30, ...),
            ScenarioNode(label="Profit-taking reversal", probability=0.15, ...),
        ]
    ),
    expected_direction="bullish",
    probability_weighted_move=0.018,
    max_upside=0.05,
    max_downside=-0.03,
    tail_risk_probability=0.08,
)
```

### 7 Event Templates

Each template generates 4-6 scenario nodes:

| Event Type | Scenarios |
|------------|-----------|
| Rate decision | Hawkish surprise, dovish surprise, as expected, mixed signals |
| Earnings | Beat + guidance up, beat + guidance down, miss, in-line |
| Geopolitical | Escalation, de-escalation, status quo, surprise resolution |
| Credit event | Contained, contagion, systemic, recovery |
| Regulatory | Positive framework, restrictive, unclear, delayed |
| Macro data | Strong beat, mild beat, mild miss, strong miss |
| Tech disrupt | Adoption, resistance, competitive response, regulatory pushback |

### Monte Carlo Simulation Output

```python
result = SimulationResult(
    n_simulations=10000,
    mean_return=0.012,
    median_return=0.008,
    std_dev=0.045,
    skewness=-0.35,
    kurtosis=4.2,
    var_95=-0.065,             # 95% Value at Risk
    var_99=-0.098,             # 99% Value at Risk
    cvar_95=-0.082,            # Conditional VaR (avg of worst 5%)
    max_drawdown=-0.12,
    prob_positive=0.62,
    prob_negative=0.38,
    prob_extreme_up=0.05,
    prob_extreme_down=0.08,
)
```

**Fat-tailed noise model:** Student-t distribution with jump diffusion
$$t = \frac{N(0,1)}{\sqrt{\chi^2(df)/df}}, \quad \text{jumps} \sim \text{Poisson}(0.05) \times \text{Exp}(1) \times \sigma \times 3$$

### Causal Chain Output

```python
chain = CausalChain(
    event_id="EVT_abc123",
    first_order=[CausalEffect(cause="Fed cuts", effect="USD weakens", delay_hours=0.5, ...)],
    second_order=[CausalEffect(cause="USD weakens", effect="Gold rallies", delay_hours=4, ...)],
    third_order=[CausalEffect(cause="Gold rallies", effect="Mining stocks surge", delay_hours=24, ...)],
    total_effects=12,
    dominant_direction="bullish",
    systemic_risk_score=0.25,
    feedback_loop_detected=False,
)
```

### Scenario Portfolio Optimization

4 methods available:
- **Minimax:** Maximize worst-case return
- **Expected Utility:** $\max E[R] - \frac{\gamma}{2} \text{Var}[R]$ (default γ=2.0)
- **Risk Parity:** Inverse-volatility weighting
- **CVaR Optimization:** Minimize 5th percentile tail risk

---

## 23. Alpha Models — 31 Signal Generators

### 12 Quantitative Alpha Signals

| # | Analyzer | Key Output |
|---|----------|------------|
| 1 | `PositioningAnalyzer` | COT z-score, put/call ratio |
| 2 | `OrderFlowAnalyzer` | Dark pool sweeps, iceberg orders |
| 3 | `VolatilitySurfaceAnalyzer` | 25-delta risk reversal, IV percentile |
| 4 | `CrossAssetLeadLag` | Pearson correlation at lag |
| 5 | `SentimentExtremesAnalyzer` | Composite fear/greed index (6 components) |
| 6 | `FlowOfFundsAnalyzer` | ETF flow z-scores, margin debt trend |
| 7 | `CalendarEffectsAnalyzer` | FOMC drift, turn-of-month, OpEx |
| 8 | `EarningsRevisionTracker` | Revision breadth and momentum |
| 9 | `InsiderTradingAnalyzer` | Cluster detection (≥3 buys or ≥5 sells) |
| 10 | `CreditMarketSignals` | HY spread, CDS, TED spread, repo rate |
| 11 | `MacroSurpriseIndex` | Weighted surprise index with half-life decay |
| 12 | `CentralBankBalanceSheet` | QE/QT classification, global liquidity pulse |

### 6 NLP Alpha Signals

| # | Analyzer | Logic |
|---|----------|-------|
| 1 | `NewsVelocityAlpha` | Z-score of article rate vs 7-day baseline |
| 2 | `NarrativeShiftAlpha` | Short (48h) vs long (336h) sentiment divergence |
| 3 | `HiddenTruthAlpha` | Contrarian signals from manipulation flags |
| 4 | `EventSurpriseAlpha` | Surprise z-score + vol mispricing + positioning squeeze |
| 5 | `CrossSourceDivergenceAlpha` | Credibility-weighted sentiment divergence |
| 6 | `NLPAlphaHub` | Composite of all 5 NLP alphas |

### 6 Structural Alpha Signals

| # | Analyzer | Key Formula |
|---|----------|-------------|
| 1 | `ContrarianSignalGenerator` | Triggers at ≥80% consensus extremity |
| 2 | `MeanReversionFramework` | Half-life: $-\ln(2)/\beta$ (OLS lag-1 regression) |
| 3 | `MomentumFramework` | ADX, golden/death cross, Donchian breakout |
| 4 | `CrossEventMemory` | Event accumulation acceleration |
| 5 | `MicrostructureAlpha` | PIN (Easley-O'Hara), Kyle's λ: $\lambda = \text{Cov}(\Delta P, SV) / \text{Var}(SV)$ |
| 6 | `StructuralAlphaEngine` | Orchestrator with conflict detection |

### Alpha Signal Aggregation

```python
aggregator = AlphaSignalAggregator()
result = aggregator.aggregate(signals)
# Returns:
{
    "net_direction": "BULLISH",
    "net_score": 0.35,
    "total_signals": 8,
    "bullish_signals": 5,
    "bearish_signals": 2,
    "neutral_signals": 1,
    "agreement_ratio": 0.625,
    "by_horizon": {"short": {...}, "medium": {...}, "long": {...}},
}
```

---

## 24. Market Intelligence Hub — 9 Models

### Full Scan Output

```python
hub = MarketIntelligenceHub()
signals = hub.full_scan("BTC")
# Returns dict of IntelSignal objects:
{
    "alt_data":    IntelSignal(source="AlternativeDataFusion",   severity=0.30, ...),
    "regime":      IntelSignal(source="RegimeDetector",          severity=0.45, ...),
    "crowding":    IntelSignal(source="CrowdingRiskDetector",    severity=0.20, ...),
    "liquidity":   IntelSignal(source="LiquidityForecaster",     severity=0.55, ...),
    "arbitrage":   IntelSignal(source="CrossMarketArbitrage",    severity=0.10, ...),
    "decay":       IntelSignal(source="SentimentDecayModel",     severity=0.35, ...),
    "cascade":     IntelSignal(source="InformationCascadeDetector", severity=0.15, ...),
    "reflexivity": IntelSignal(source="ReflexivityModel",        severity=0.40, ...),
    "dark_pool":   IntelSignal(source="DarkPoolAnalyzer",        severity=0.25, ...),
}
```

### Risk Summary

```python
hub.risk_summary("BTC")
# Returns:
{
    "asset": "BTC",
    "overall_risk": 0.31,
    "risk_level": "moderate",     # critical (>0.7), elevated (>0.4), moderate (>0.2), normal
    "signals": {...},
}
```

### Key Model Details

| Model | Key Formula |
|-------|-------------|
| RegimeDetector | 5×5 HMM transition matrix; CUSUM change-point: z-score cumulative sum with 0.5 drift |
| SentimentDecayModel | $\text{impact}(t) = \text{initial} \times e^{-0.693 \times t_h / \text{halflife}}$ |
| ReflexivityModel | Soros reflexivity — Pearson coupling between narrative and price |
| LiquidityForecaster | Score = $0.4 \times \text{vol\_ratio} + 0.3 / \text{spread\_ratio} + 0.3 \times \text{depth\_ratio}$ |
| CrossMarketArbitrage | Put-call parity: $C - P = Se^{-qT} - Ke^{-rT}$ |

### 5 Market Regimes

| Regime | Conditions |
|--------|------------|
| `BULL_QUIET` | 20d return > 0, vol < median |
| `BULL_VOLATILE` | 20d return > 0, vol ≥ median |
| `BEAR_QUIET` | 20d return ≤ 0, vol < median |
| `BEAR_VOLATILE` | 20d return ≤ 0, vol ≥ median |
| `RANGING` | |20d return| < 1% |

---

## 25. Multi-Asset / Contagion

### Correlation Engine Output

```python
matrix = CorrelationMatrix(
    timestamp=datetime(...),
    regime="risk_off",
    pairs=[
        CorrelationPair(asset_a="SPX", asset_b="NASDAQ", correlation=0.92, rolling_30d=0.90, current_z_score=0.5, is_breaking_down=False),
        CorrelationPair(asset_a="SPX", asset_b="VIX", correlation=-0.82, ...),
        CorrelationPair(asset_a="BTC", asset_b="GOLD", correlation=0.15, is_breaking_down=True, breakdown_severity=0.6),
    ],
    avg_correlation=0.45,
    correlation_dispersion=0.35,
    n_breakdowns=2,
    systemic_risk_indicator=0.40,
)
```

### 21 Baseline Correlation Pairs

Key pairs include: SPX-NASDAQ (0.90), SPX-VIX (−0.82), BTC-ETH (0.85), GOLD-DXY (−0.60), OIL-ENERGY (0.75)

### Contagion Simulation Output

```python
result = ContagionSimulation(
    initial_shock="SPX",
    shock_magnitude=0.50,
    infected_nodes=["NASDAQ", "VIX", "BTC", "GOLD"],
    propagation_steps=3,
    total_spread=0.65,
    max_reach=12,
    systemic_risk=0.55,
    containment_probability=0.40,
    critical_nodes=["SPX", "VIX", "DXY"],
)
```

**Transmission Formula:**
$$\text{transmitted} = \text{stress}_{src} \times \text{strength} \times \text{susceptibility} \times (1 - \text{stress}_{current})$$

**Systemic Risk:**
$$\text{risk} = 0.4 \times \text{infection\_rate} + 0.35 \times \bar{\text{stress}} + 0.25 \times \text{speed}$$

---

## 26. Economics Models

### EconomicImpact Output

```python
impact = EconomicImpact(
    event_description="Fed raises rates by 50bps",
    gdp_impact_pct=-0.15,
    gdp_impact_direction="contractionary",
    inflation_impact_pct=-0.25,
    inflation_direction="disinflationary",
    implied_policy_rate=5.75,
    rate_change_probability=0.85,
    yield_curve_slope=-0.15,
    recession_signal=True,
    usd_impact="strengthening",
    severity="significant",
    confidence=0.75,
)
```

### 5 Economic Models

| Model | Key Formula |
|-------|-------------|
| **Phillips Curve** | $\pi = \pi_e - \beta(U - U^*) + \epsilon_{oil}$ (NAIRU=4.5%, β=0.5) |
| **Taylor Rule** | $i^* = r^* + \pi + 0.5(\pi - \pi^*) + 0.5(y - y^*)$ (r*=1.0, π*=2.0) |
| **Yield Curve** | Spread < −0.5% = deeply inverted → 60% recession probability |
| **GDP Impact** | Rate→GDP: −0.3% per 100bps; Oil→GDP: −0.02 per %Δ; Fiscal multiplier: 1.2 |
| **Exchange Rate** | 25bps differential ≈ 0.7% USD move |

---

## 27. Storage Layer

### SQLite Database — 9 Tables

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `news_events` | event_id, timestamp, source, raw_text, ambiguity_score | News archive |
| `participant_interpretations` | event_id, participant_type, belief_shift, urgency | Interpretation history |
| `impact_predictions` | event_id, overall_stress, confidence | Impact forecasts |
| `validation_records` | event_id, directional_accuracy, timing_accuracy | Model validation |
| `trading_signals` | signal_id, direction, strength, trust_score, profit_loss | Signal + P&L tracking |
| `model_credibility` | model_name, accuracy_ema, weight | Model weights |
| `scenario_history` | event_id, scenario_tree (JSON) | Scenario archive |
| `knowledge_graph_snapshots` | timestamp, graph_data (JSON) | Graph persistence |
| `system_metrics` | metric_name, value, timestamp | System metrics |

### Knowledge Graph — NetworkX DiGraph

**Seed knowledge:** 38 entities + 31 relationships

| Entity Category | Count | Examples |
|-----------------|-------|---------|
| Central banks | 5 | FED, ECB, BOJ, BOE, PBOC |
| Indices | 7 | SPX, NASDAQ, DJI, FTSE, DAX, NIKKEI, HSI |
| Currencies | 6 | USD, EUR, JPY, GBP, CNY, BTC |
| Commodities | 6 | OIL, GOLD, SILVER, NATGAS, COPPER, WHEAT |
| Bonds | 4 | US_10Y, US_2Y, BUND, JGB |
| Crypto | 2 | BTC, ETH |
| Indicators | 6 | GDP, CPI, UNEMPLOYMENT, NFP, PMI, CONSUMER_CONFIDENCE |

**12 Relationship Types:**
influences (0.7), correlates_with (0.5), opposes (−0.5), depends_on (0.8), reacts_to (0.6), competes_with (−0.3), regulates (0.9), trades_in (0.4), hedges_against (−0.6), leads (0.65), lags (0.45), causes (0.85)

**Edge update formula (weighted moving average):**
$$w_{new} = 0.3 \times w_{input} + 0.7 \times w_{existing}$$

---

## 28. Streaming Pipeline & EventBus

### 21 Event Types

| Category | Events |
|----------|--------|
| Data | `NEWS_RAW`, `NEWS_PARSED`, `NEWS_ENRICHED` |
| NLP | `NLP_ENTITIES`, `NLP_INTENT`, `NLP_CONTRADICTION` |
| Cognitive | `INTERPRETATION_READY`, `BEHAVIOR_COMPUTED`, `IMPACT_COMPUTED` |
| Validation | `VALIDATION_COMPLETE`, `CREDIBILITY_UPDATE` |
| Signals | `SIGNAL_GENERATED`, `SIGNAL_APPROVED`, `SIGNAL_REJECTED`, `SIGNAL_EXECUTED` |
| Hidden Truth | `OMISSION_DETECTED`, `CONTRADICTION_FOUND`, `NARRATIVE_SHIFT` |
| Scenario | `SCENARIO_GENERATED`, `SCENARIO_INVALIDATED` |
| System | `SYSTEM_ALERT`, `SYSTEM_METRIC`, `SYSTEM_ERROR` |

### 7-Stage Processing

| Stage | Trigger Event | Output Event | Module Used |
|-------|---------------|--------------|-------------|
| 1. Parse | `NEWS_RAW` | `NEWS_PARSED` | NLP Engine |
| 2. Cognitive | `NEWS_PARSED` | `INTERPRETATION_READY` | CognitiveMarketSystem |
| 3. Scenario | `INTERPRETATION_READY` | `SCENARIO_GENERATED` | ScenarioGenerator |
| 4. Signal | `SCENARIO_GENERATED` | `SIGNAL_GENERATED` | DecisionEngine |
| 5. Validate | `SIGNAL_GENERATED` | `VALIDATION_COMPLETE` | ExecutionNexus |
| 6. Hidden Truth | `NEWS_PARSED` | Various alerts | Hidden Truth analyzers |
| 7. Multi-Asset | `INTERPRETATION_READY` | Correlation updates | CorrelationEngine |

### EventBus Stats

```python
event_bus.get_stats()
# Returns:
{
    "total_published": 1247,
    "total_delivered": 4891,
    "total_errors": 3,
    "queue_size": 0,
    "subscriber_count": 15,
    "dead_letters": 3,
}
```

---

## 29. Dashboard (Streamlit)

### Port Configuration

| Service | Port | Access |
|---------|------|--------|
| Streamlit dashboard | 8501 | `http://localhost:8501` |
| FastAPI (infrastructure) | 8000 | `http://localhost:8000` |

### 7 Dashboard Pages

#### Page 1: System Overview

```
┌────────────────────────────────────────────────────────────┐
│  COGNITIVE MARKET ENGINE — System Overview                  │
├──────────┬──────────┬──────────┬──────────────────────────┤
│ Events   │ Latency  │ Errors   │ Pipeline Status           │
│ 147      │ 45.2ms   │ 3        │ running                   │
├──────────┴──────────┴──────────┴──────────────────────────┤
│                                                            │
│  Model Performance                                         │
│  ┌─────────────────────┬──────────┬────────┐              │
│  │ Model               │ Accuracy │ Weight │              │
│  ├─────────────────────┼──────────┼────────┤              │
│  │ HFT                 │ 0.92     │ 1.20   │              │
│  │ Market Maker        │ 0.88     │ 1.10   │              │
│  │ Hedge Fund          │ 0.75     │ 0.90   │              │
│  │ Bank                │ 0.70     │ 0.85   │              │
│  │ Retail              │ 0.45     │ 0.50   │              │
│  └─────────────────────┴──────────┴────────┘              │
│                                                            │
│  Storage: 2.3 MB, 147 events, 735 interpretations          │
└────────────────────────────────────────────────────────────┘
```

#### Page 7: News Feed (Manual Input)

Text area → Submit → Process through `pipeline.process_news()` → Display signal result + recent events table.

---

## 30. News Ingestion Pipeline

### 3 Data Sources

| Source | Class | Rate Limit | Data Format |
|--------|-------|------------|-------------|
| NewsAPI | `NewsAPIClient` | 95/day | JSON REST |
| GDELT | `GDELTClient` | 500/hour | JSON REST |
| RSS | `RSSReader` | 1000/hour | XML/Atom feeds |

### 14 Pre-configured RSS Feeds

| Feed | URL Category | Source |
|------|-------------|--------|
| `fed_press` | Central bank | Federal Reserve |
| `ecb_press` | Central bank | ECB |
| `reuters_business` | Major outlet | Reuters |
| `reuters_markets` | Major outlet | Reuters |
| `bloomberg_markets` | Major outlet | Bloomberg |
| `cnbc_top` | Major outlet | CNBC |
| `ft_markets` | Major outlet | Financial Times |
| `wsj_markets` | Major outlet | WSJ |
| `bbc_business` | Major outlet | BBC |
| `bls_releases` | Data | Bureau of Labor Statistics |
| `coindesk` | Crypto | CoinDesk |
| `cointelegraph` | Crypto | CoinTelegraph |
| `ap_top` | General | AP |

### News Aggregator Output (`UnifiedArticle`)

```python
article = UnifiedArticle(
    article_id="ART_<hash>",
    title="Fed Holds Rates Steady",
    content="The Federal Reserve...",
    summary="...",
    source="reuters",
    source_type="rss",
    url="https://...",
    published_at=datetime(...),
    fetched_at=datetime(...),
    language="en",
    author="John Doe",
    categories=["economy", "central_bank"],
    tone=0.0,
    entities=[],
    content_hash="a1b2c3d4...",
    duplicate_of=None,
)
```

### Deduplication

- Hash-based: SHA-256 of title + content (first 16 chars)
- Title similarity: 70% word overlap threshold
- Content hash collision → `duplicate_of = <original_id>`

### Rate Limiter (Token Bucket)

```python
rate_limiter.remaining("newsapi")   # → 93
rate_limiter.can_request("gdelt")   # → True
```

### Retry with Exponential Backoff

$$\text{delay} = \min(\text{max\_delay}, \text{base\_delay} \times 2^{\text{attempt}})$$

Default: base=1.0s, max=30.0s, 3 retries, 30% jitter

---

## 31. Infrastructure Layer

### 7 Production Components

| Component | Backend | Purpose |
|-----------|---------|---------|
| `MessageQueue` | Redis / Kafka / in-memory | Pub/sub messaging |
| `TimeSeriesDB` | InfluxDB / TimescaleDB / SQLite | Time-series storage |
| `ModelRegistry` | File-based (MLflow-inspired) | Model versioning |
| `FeatureStore` | In-memory online + offline | Feature management |
| `CICDPipeline` | GitHub Actions / GitLab CI | Deployment automation |
| `MonitoringSystem` | Prometheus-compatible | Metrics & alerting |
| `APILayer` | FastAPI | REST + WebSocket API |

### 13 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/signals/latest` | Latest signals |
| GET | `/api/v1/signals/history` | Signal history |
| GET | `/api/v1/intelligence/{asset}` | Market intelligence |
| GET | `/api/v1/regime/current` | Current market regime |
| POST | `/api/v1/nlp/analyze` | Analyze text via NLP |
| POST | `/api/v1/events/extract` | Extract events from text |
| GET | `/api/v1/alpha/scan` | Alpha signal scan |
| GET | `/api/v1/risk/summary` | Risk summary |
| GET | `/api/v1/models/list` | Registered models |
| GET | `/api/v1/features/{entity}` | Feature store lookup |
| GET | `/api/v1/metrics` | Prometheus metrics |
| WS | `/ws/signals` | Real-time signal stream |

### 12 Default Prometheus Metrics

```
cme_signals_processed_total
cme_signal_latency_seconds
cme_active_models
cme_prediction_accuracy
cme_nlp_processing_seconds
cme_market_data_lag_seconds
cme_risk_score
cme_errors_total
cme_api_requests_total
cme_api_latency_seconds
cme_feature_freshness_seconds
cme_queue_depth
```

### 5 Default Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighErrorRate | errors > 50 | critical |
| HighLatency | latency > 5s | warning |
| LowAccuracy | accuracy < 0.5 | critical |
| StaleData | freshness > 600s | warning |
| QueueBacklog | depth > 1000 | warning |

---

## 32. Backtesting Engine

### BacktestResult Output

```python
result = BacktestResult(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2026, 1, 1),
    initial_capital=100000.0,
    final_capital=112500.0,
    total_trades=156,
    winning_trades=89,
    losing_trades=67,
    total_return=0.125,
    annualized_return=0.125,
    sharpe_ratio=1.45,
    sortino_ratio=2.10,
    max_drawdown=-0.065,
    max_drawdown_duration=timedelta(days=12),
    win_rate=0.5705,
    profit_factor=1.42,
    avg_win=0.028,
    avg_loss=-0.019,
    avg_holding_period=timedelta(hours=8.5),
    directional_accuracy=0.615,
    avg_signal_confidence=0.68,
    confidence_calibration=0.12,
)
```

### Performance Analytics Formulas

**Sharpe Ratio:**
$$\text{Sharpe} = \frac{\bar{r} - r_f/252}{\sigma} \times \sqrt{252}$$

**Sortino Ratio:** Same but using only downside deviation

**Profit Factor:** $\text{gross\_profit} / \text{gross\_loss}$

**Confidence Calibration:** high_confidence_WR − low_confidence_WR

### Default Parameters

| Parameter | Default | Range |
|-----------|---------|-------|
| Initial capital | $100,000 | — |
| Max position size | 10% | — |
| Stop loss | 2% | — |
| Take profit | 4% | — |
| Max holding period | 24 hours | — |
| Snapshot interval | 1 hour | — |

---

## 33. Learning / Feedback Loop

### FeedbackLoop Output

```python
report = feedback_loop.get_credibility_report()
# Returns dict of ModelCredibility objects:
{
    "institutional_strategist": ModelCredibility(
        name="institutional_strategist",
        total_predictions=45,
        correct_predictions=32,
        accuracy_ema=0.72,
        direction_accuracy=0.75,
        magnitude_accuracy=0.65,
        weight=1.15,
        best_event_type="rate_decision",
        worst_event_type="geopolitical",
    ),
    "retail_herd": ModelCredibility(
        accuracy_ema=0.42,
        weight=0.55,
        ...
    ),
    ...
}
```

### EMA Update Formula

$$\text{accuracy}_{new} = (1 - \alpha) \times \text{accuracy}_{old} + \alpha \times \text{score}$$

Default α = 0.15

### Weight Update Formula

$$w_{target} = 0.5 + \text{accuracy}_{ema} \times 2.0$$
$$w_{new} = 0.9 \times w_{old} + 0.1 \times w_{target}$$

Clamped to [0.1, 3.0]

### Decay Formula (Inactive Models)

$$w_{decayed} = w \times e^{-0.01 \times \text{days\_inactive}}$$

### Confidence Calibration

$$\text{calibration} = 1 - |\text{predicted\_confidence} - \text{actual\_accuracy}|$$

---

## 34. Alert Delivery System

### Supported Channels

| Channel | Method | Config Required |
|---------|--------|-----------------|
| `LOG` | Python logging | None |
| `TELEGRAM` | urllib.request to bot API | `bot_token`, `chat_id` |
| `EMAIL` | smtplib SMTP+TLS | `smtp_server`, `port`, `username`, `password`, `to_address` |
| `SLACK` | Webhook POST | `webhook_url` |
| `WEBHOOK` | Generic HTTP POST | `url` |
| `SMS` | Twilio REST API | `account_sid`, `auth_token`, `from_number`, `to_number` |

### Priority Routing

| Priority | Channels |
|----------|----------|
| CRITICAL (4) | ALL channels |
| HIGH (3) | Telegram + Email + Slack |
| MEDIUM (2) | Telegram + Slack |
| LOW (1) | Log only |

### Deduplication

MD5 fingerprint of `title + message + asset + category`, 300-second window.

### Rate Limiting

Per-minute sliding window per channel.

---

## 35. Test Suite Expected Results

### Phase Test Results

```
python -m pytest tests/ -v
```

| Test File | Tests | Expected | Duration |
|-----------|-------|----------|----------|
| `test_phase_1.py` | 12 | 12 PASSED | ~1s |
| `test_phase_2.py` | 14 | 14 PASSED | ~2s |
| `test_phase_3.py` | 14 | 14 PASSED | ~2s |
| `test_phase_4.py` | 14 | 14 PASSED | ~3s |
| `test_phase_5.py` | 14 | 14 PASSED | ~2s |
| `test_phase_6.py` | 14 | 14 PASSED | ~2s |
| `test_integration.py` | 8 | 8 PASSED | ~5s |
| **Total** | **90** | **90 PASSED** | **~17s** |

### Critical Design Rules Enforced by Tests

| Phase | Rule | Test |
|-------|------|------|
| Phase 1 | NO sentiment scores, NO trading signals, NO market direction | `test_09_no_trading_signals` |
| Phase 2 | NO prices, NO P&L, NO signal fields | `test_09_no_prices_no_signals` |
| Phase 3 | NO trade objects, NO order fields | `test_07_no_prices_no_trades` |
| Phase 5 | Research-only: NO execution fields | `test_12_no_trading_signals` |

### Phase 1 Specific Tests

| Test | Validates |
|------|-----------|
| Raw text preserved exactly | Whitespace, punctuation, case |
| Ambiguity score computed | Uncertain text → ambiguity > 0.4 |
| Temporal markers extracted | FUTURE, CONDITIONAL types detected |
| Actors extracted | "Federal Reserve" → central_bank category |
| Narrative classification | MACRO_POLICY, CREDIT_RISK |
| Deterministic parsing | Same input → same output |

### Integration Tests

| Test | Validates |
|------|-----------|
| Bootstrap | ≥8 modules loaded |
| Cognitive engine | process_news_event → valid signal |
| Streaming pipeline | process_news → metrics |
| Scenario engine | generate → tree with direction + tail risk |
| Execution engine | execute_signal + close_position methods exist |
| Type unification | `shared.ParticipantType is engine.ParticipantType` |

---

## 36. Validation Script Results

### Running the Validator

```bash
python validate_pipeline_workflow.py
```

### Expected Output

```
============================================================
  COGNITIVE MARKET ENGINE — PIPELINE & WORKFLOW VALIDATION
============================================================
CME Root: /path/to/Cognitive_Market_Engine
Root exists: True

============================================================
  1. Directory Structure
============================================================
  [PASS] Directory exists: engine/
  [PASS] Directory exists: config/
  ...

============================================================
  VALIDATION SUMMARY
============================================================
  Total Checks: 350+
  PASSED:       350+
  FAILED:       0
  WARNINGS:     0
  Pass Rate:    350/350 = 100.0%

  ✅ VERDICT: YES — Pipeline and Workflow validated successfully
============================================================
```

### 30 Validation Sections

| # | Section | Checks |
|---|---------|--------|
| 1 | Directory Structure | 30 directories |
| 2 | Entry Point Files | 11 root files + 15 function checks |
| 3 | Engine (Pipeline A) | 30+ class/method checks |
| 4 | NLP Engine | 25+ checks |
| 5 | News Model & Ingestion | 15+ checks |
| 6 | Streaming Pipeline | 10 checks |
| 7 | Storage | 15 checks |
| 8 | 7-Phase Pipeline | 40+ checks |
| 9 | Decision System | 12 checks |
| 10 | Hidden Truth | 12 checks |
| 11 | Scenario Engine | 15 checks |
| 12 | Alpha Models | 25+ checks |
| 13 | Multi-Asset | 8 checks |
| 14 | Market Intelligence | 12 checks |
| 15 | Infrastructure | 10 checks |
| 16 | Economics | 8 checks |
| 17 | Backtesting | 6 checks |
| 18 | Learning/Feedback | 7 checks |
| 19 | Data Feed | 5 checks |
| 20 | Dashboard | 2 checks |
| 21 | Advanced Analysis | 8 checks |
| 22 | Alerts | 5 checks |
| 23 | Config | 12 checks |
| 24 | Tests | 8 checks |
| 25 | Pipeline Wiring | 15+ checks |
| 26 | Workflow Integrity | 12 checks |
| 27 | Architecture | 8 checks |
| 28 | Thresholds & Constants | 7 checks |
| 29 | Line Counts | 21 checks (big files only) |
| 30 | Scripts & Docker | 5 checks |

---

## 37. Health Check Script

### Running

```bash
cd Cognitive_Market_Engine
python scripts/health_check.py
```

### Expected Output

```
✅ Module Import: engine.cognitive_market_system
✅ Module Import: nlp_engine.deep_nlp_parser
✅ Module Import: news_model.news_event
✅ Module Import: participant_cognition.participant_models
... (38 module imports)

✅ Component: DecisionEngine()
✅ Component: ExecutionNexus()
✅ Component: MarketDataFeed()
✅ Component: PipelineBridge()

✅ Pipeline: DecisionEngine.decide()
✅ Pipeline: ExecutionNexus.execute_signal()
✅ Pipeline: MarketDataFeed.get_market_snapshot()
✅ Pipeline: PipelineBridge.process()

✅ Bootstrap: main.bootstrap() → ≥8 modules

RESULTS: 45 passed, 0 failed, 0 warned
```

### 38 Module Imports Tested

engine, nlp_engine (6), news_model (2), participant_cognition, market_response, market_impact, reality_validation, signal_auth, decision_system (2), execution, scenario_engine (3), hidden_truth (4), multi_asset (2), streaming (2), storage (2), learning, news_ingestion (4), config (2), pipeline_bridge, data, dashboard

---

## 38. Docker Deployment

### Build

```bash
docker build -t cognitive-market-engine .
```

### Expected Build Output

```
[+] Building 45.2s
Step 1/15: FROM python:3.11-slim AS base
Step 2/15: FROM base AS deps
...
Step 10/15: RUN python -m spacy download en_core_web_sm
Step 11/15: RUN python -m spacy download en_core_web_trf
...
Step 14/15: EXPOSE 8501 8000
Step 15/15: CMD ["python", "main.py"]
Successfully built abc123def456
```

### Running

```bash
docker run -p 8501:8501 -p 8000:8000 \
  -e NEWSAPI_KEY=your_key \
  cognitive-market-engine
```

### Ports

| Port | Service |
|------|---------|
| 8501 | Streamlit dashboard |
| 8000 | FastAPI REST API |

### Health Check

```
HEALTHCHECK --interval=30s --timeout=30s --retries=3
CMD python -c "import engine.cognitive_market_system"
```

---

## 39. Configuration Reference

### SystemConfig Defaults

| Config | Key Parameters | Default Values |
|--------|---------------|----------------|
| **NewsIngestion** | update_frequency, max_batch, min_len, max_len, cache_days | 60s, 100, 50, 5000, 30d |
| **CognitiveModel** | sentiment_weight, intensity_weight, ambiguity_penalty | 0.4, 0.3, 0.15 |
| **BehaviorTranslation** | regulatory, risk_limit, capital, inventory | 0.2, 0.3, 0.2, 0.25 |
| **MarketImpact** | impact_scaling_power, hft_dominance, shock/digest/institutional/structural | 1.5, 0.8, 60s/900s/7200s/86400s |
| **RealityValidation** | directional/vol accuracy, timing tolerances, credibility thresholds | 0.65, 0.60, 30s/300s/900s, 0.65/0.50 |
| **SignalAuthorization** | trust_approved/warning/unreliable, historical_weight, expiration | 0.60/0.50/0.40, 0.60, 4h |
| **Execution** | max_position, max_exposure, daily_loss, drawdown, vol_spike | $1M, 80%, -$50K, -$30K, 2.5× |

### Logging Configuration

```
Format: [2026-03-01 14:00:00] INFO    cme.engine — Processing news event...
Rotation: 5 MB per file, 3 backup files
Silenced: urllib3, requests, chardet, feedparser
```

---

## 40. Performance Benchmarks

### Expected Processing Times

| Operation | Expected Latency |
|-----------|------------------|
| NLP parse (spaCy) | 50–200 ms |
| NLP parse (fallback) | 5–20 ms |
| Cognitive interpretation (5 participants) | 10–30 ms |
| Expectation collision | 5–15 ms |
| Signal translation | 2–5 ms |
| Full Pipeline A (end-to-end) | 70–270 ms |
| Full Pipeline B (7-phase) | 100–400 ms |
| NewsAPI fetch | 500–2000 ms |
| GDELT fetch | 200–1000 ms |
| RSS fetch (all 14 feeds) | 2–10 seconds |
| Bootstrap (all modules) | 3–8 seconds |

### Memory Usage

| Component | Expected Memory |
|-----------|----------------|
| Base Python process | ~50 MB |
| spaCy (en_core_web_sm) | ~150 MB |
| Transformer models (MiniLM + BART-MNLI) | ~500 MB |
| FinBERT (if loaded) | ~400 MB |
| Full system (all modules) | ~800 MB – 1.5 GB |

---

## 41. Error Handling & Graceful Degradation

### Module Unavailability

Every module is **optional**. The system degrades gracefully:

| Missing Module | Fallback | Impact |
|---------------|----------|--------|
| spaCy | Keyword-based NLP | Reduced accuracy, faster processing |
| transformers | No zero-shot, no embeddings | No narrative classification, no similarity |
| torch | No transformer models | Falls back to rule-based |
| NewsAPI key | GDELT + RSS only | Reduced news coverage |
| Redis | In-memory message queue | No distributed messaging |
| InfluxDB | SQLite time-series | Local-only metrics |
| OpenAI key | Rule-based analysis | No LLM deep analysis |
| Reddit/Twitter keys | Demo data | No social media scanning |

### Error Message Patterns

```
[--] NLP Engine init failed: <reason>          # Module unavailable
[WARN] Aggregator fetch error: <reason>        # Network issue
[FATAL] No data source available               # No news source at all
[ERROR] <exception message>                    # Generic error
```

### Circuit Breaker Activation

```
[CIRCUIT BREAKER] Activated: DAILY_LOSS_LIMIT
[CIRCUIT BREAKER] All trading halted
[CIRCUIT BREAKER] Reason: Daily P&L ($-52,300) exceeded limit ($-50,000)
```

---

## 42. File Artifacts Map

### Files Created at Runtime

| File/Directory | Purpose | Created By |
|---------------|---------|------------|
| `data/` | Data directory | `system_config.py` (auto-created) |
| `logs/` | Log directory | `system_config.py` (auto-created) |
| `data/news_cache.db` | News event SQLite database | `DatabaseManager` |
| `data/research.db` | Research database | `DatabaseManager` |
| `data/signal_cache.db` | Signal cache | `DatabaseManager` |
| `data/execution.db` | Execution records | `DatabaseManager` |
| `data/logs/engine.log` | Engine log file (if logging enabled) | `setup_logging()` |
| `data/knowledge_graph.json` | Persisted knowledge graph | `KnowledgeGraph.save()` |
| `data/market_cache/` | Market data cache | `MarketDataFeed` |
| `reports/` | Generated reports | `ReportGenerator` |
| `models/{name}/v{n}_meta.json` | Model registry metadata | `ModelRegistry` |

### Console Output Summary

| Entry Point | Expected Lines | Key Sections |
|-------------|---------------|--------------|
| `python main.py` | ~50–80 | Bootstrap (15), Demo (45), Status (5) |
| `python main.py --live` | Continuous | Init (10), then per-event (5–8 each) |
| `python main.py --test` | ~60–100 | 3 tests + 6 scenarios |
| `python main.py --news "..."` | 5 | Signal + Direction + Strength + Confidence + Reason |
| `python legacy_main.py` | ~30 | Status dict + Summary table |
| `python validate_pipeline_workflow.py` | ~400+ | 30 sections + summary |
| `python scripts/health_check.py` | ~50 | 38 imports + 4 components + 4 pipeline + bootstrap |

---

## Appendix A: Complete Enum Reference

### Signal & Direction Enums

| Enum | Module | Values |
|------|--------|--------|
| `SignalType` | engine/ | PASSIVE_ACCUMULATION, PASSIVE_DISTRIBUTION, AGGRESSIVE_MEAN_REVERSION, LIQUIDITY_ARBITRAGE, VOLATILITY_CAPTURE, LIQUIDITY_PROVISION, REGIME_FADE, NO_TRADE |
| `ConfidenceLevel` | engine/ | VERY_LOW(0.2), LOW(0.4), MEDIUM(0.6), HIGH(0.8), VERY_HIGH(0.95) |
| `ExecutionMode` | engine/ | PASSIVE, ALGORITHMIC, AGGRESSIVE |
| `ParticipantType` | shared/ | RETAIL, HFT, HEDGE_FUND, BANK, MARKET_MAKER |
| `TimeHorizon` | shared/ | MICROSECONDS through YEARS (9 values) |
| `RiskTolerance` | shared/ | ULTRA_LOW, LOW, MEDIUM, ADAPTIVE, HIGH |
| `DirectionType` | shared/ | BUY, SELL, NEUTRAL, UNCERTAIN, LONG, SHORT, FLAT |

### NLP Enums

| Enum | Module | Values |
|------|--------|--------|
| `SemanticRole` | nlp_engine/ | AGENT, ACTION, PATIENT, INSTRUMENT, LOCATION, TEMPORAL, CAUSE, CONDITION |
| `NarrativeIntent` | nlp_engine/ | INFORM, WARN, REASSURE, DEFLECT, SIGNAL_POLICY, MARKET_MOVE, CRISIS_MANAGE, PROPAGANDA, LEAK, TRIAL_BALLOON |
| `NarrativeType` | news_model/ | MACRO_POLICY, LIQUIDITY, GROWTH, CREDIT_RISK, GEOPOLITICAL, TECHNOLOGICAL, CRISIS_SHOCK, NARRATIVE_REINFORCEMENT, NARRATIVE_CONTRADICTION |
| `TemporalType` | news_model/ | NOW, FUTURE, CONDITIONAL, PAST, UNCERTAIN |

### Pipeline Status Enums

| Enum | Module | Values |
|------|--------|--------|
| `SignalStatus` | signal_auth/ | APPROVED, FILTERED, PENDING_VALIDATION, CONFLICTED |
| `ExecutionStatus` | execution/ | PENDING, PARTIAL, FILLED, CANCELLED, REJECTED |
| `RiskLevel` | execution/ | GREEN, YELLOW, RED |
| `DecisionAction` | decision/ | BUY, SELL, HOLD, REDUCE, HEDGE, WATCH, EMERGENCY_EXIT |
| `MarketRegime` | decision/ | CALM, TRENDING, VOLATILE, CRISIS, TRANSITIONING |
| `ReviewStatus` | decision/ | PENDING, APPROVED, REJECTED, MODIFIED, EXPIRED, AUTO_APPROVED |

---

## Appendix B: Mathematical Formulas Reference

### Core Engine

$$\text{action\_magnitude} = 0.4 \times \text{aggressiveness} + 0.3 \times \text{urgency} + 0.3 \times \text{belief\_shift}$$

$$\text{will\_act} = (\text{urgency} > 0.5) \wedge (\text{action\_bias} > 0.3)$$

### Collision

$$\text{market\_stress} = 0.25 \times \sigma^2_{exp} + 0.25 \times |L_{stress}| + 0.25 \times \bar{V} + 0.25 \times \mathbb{1}_{MM}$$

### Signal Translation

$$\text{stop\_loss} = (\sigma_{vol} \times 0.08 + 0.02) \times m_{type}$$

### Market Impact

$$\text{price\_impact}_{bps} = \text{stress} \times \text{liquidity\_signal} \times 100$$

### Reality Validation

$$\text{overall} = 0.30D + 0.20V + 0.20T + 0.15P + 0.15R$$

### Trust Scoring

$$\text{trust} = 0.6 \times \text{historical} + 0.4 \times \text{current} \times (1 - 0.15 \times \text{ambiguity})$$

### Execution Sizing

$$\text{size} = \text{strength}^2 \times \$1{,}000{,}000$$

### Taylor Rule

$$i^* = r^* + \pi + 0.5(\pi - \pi^*) + 0.5(y - y^*)$$

### Phillips Curve

$$\pi = \pi_e - \beta(U - U^*) + \epsilon_{oil}$$

### Sentiment Decay

$$\text{impact}(t) = I_0 \times e^{-0.693 \times t / t_{1/2}}$$

### Sharpe Ratio

$$S = \frac{\bar{r} - r_f / 252}{\sigma} \times \sqrt{252}$$

### GBM Simulation

$$S_{new} = S_{base} \times e^{(\mu - 0.5\sigma^2)\Delta t + \sigma\sqrt{\Delta t} \cdot Z}$$

---

## Appendix C: Quick Reference Card

### 5-Second Status Check

```bash
python main.py --test                    # Run all tests
python scripts/health_check.py           # Module health
python validate_pipeline_workflow.py     # Full validation (350+ checks)
```

### Process Single News

```bash
python main.py --news "Fed raises rates by 25bps"
```

### Start Live Monitoring

```bash
python main.py --live
```

### Launch Dashboard

```bash
python main.py --dashboard
# Access: http://localhost:8501
```

### Key Thresholds

| Threshold | Value | Purpose |
|-----------|-------|---------|
| Trust approved | 0.60 | Signal authorization gate |
| NO_TRADE confidence | < 0.50 | Engine confidence gate |
| NO_TRADE opportunity | < 0.40 | Structural opportunity gate |
| Max position | $1M / 15% | Position size limit |
| Daily loss limit | −$50K | Circuit breaker |
| Drawdown limit | −$30K | Circuit breaker |
| Vol spike threshold | 2.5× | Circuit breaker |
| Signal expiration | 4 hours | Auto-expire |
| Stop loss (default) | 2% | Per-trade risk |
| Take profit (default) | 3% | Per-trade target |

---

*Document generated from exhaustive analysis of 75+ source files totaling ~38,000 lines of code across 30 directories.*
