# COGNITIVE MARKET ENGINE — WORKFLOW DOCUMENT

## Purpose

This document describes every operational workflow in the **Cognitive Market Engine (CME)**. Each workflow maps to real code paths, real classes, and real methods. These workflows cover the full operational lifecycle from system initialization through live trading, backtesting, monitoring, and emergency shutdown.

---

## Table of Contents

1. [WF1: System Initialization](#wf1-system-initialization)
2. [WF2: News Ingestion Workflow](#wf2-news-ingestion-workflow)
3. [WF3: NLP Processing Workflow](#wf3-nlp-processing-workflow)
4. [WF4: Cognitive Engine Workflow](#wf4-cognitive-engine-workflow)
5. [WF5: 7-Phase Pipeline Workflow](#wf5-7-phase-pipeline-workflow)
6. [WF6: Pipeline Bridge Workflow](#wf6-pipeline-bridge-workflow)
7. [WF7: Streaming Pipeline Workflow](#wf7-streaming-pipeline-workflow)
8. [WF8: Alpha Signal Generation Workflow](#wf8-alpha-signal-generation-workflow)
9. [WF9: Hidden Truth Detection Workflow](#wf9-hidden-truth-detection-workflow)
10. [WF10: Scenario Analysis Workflow](#wf10-scenario-analysis-workflow)
11. [WF11: Market Intelligence Workflow](#wf11-market-intelligence-workflow)
12. [WF12: Decision Making Workflow](#wf12-decision-making-workflow)
13. [WF13: Execution Workflow](#wf13-execution-workflow)
14. [WF14: Reality Validation Workflow](#wf14-reality-validation-workflow)
15. [WF15: Signal Authorization Workflow](#wf15-signal-authorization-workflow)
16. [WF16: Feedback & Learning Workflow](#wf16-feedback--learning-workflow)
17. [WF17: Backtesting Workflow](#wf17-backtesting-workflow)
18. [WF18: Live Monitoring Workflow](#wf18-live-monitoring-workflow)
19. [WF19: Dashboard Workflow](#wf19-dashboard-workflow)
20. [WF20: Alert Delivery Workflow](#wf20-alert-delivery-workflow)
21. [WF21: Human Review Workflow](#wf21-human-review-workflow)
22. [WF22: Infrastructure Health Workflow](#wf22-infrastructure-health-workflow)
23. [WF23: Full End-to-End Workflow](#wf23-full-end-to-end-workflow)

---

## WF1: System Initialization

**Entry**: `main.py` → `bootstrap(asset, verbose)`
**Purpose**: Load all system components and verify readiness

### Steps

```
1. Load configuration
   → config.get_config() → SystemConfig
   → 8 config dataclasses loaded from defaults / .env

2. Initialize storage
   → DatabaseManager(db_path) → create 9 SQLite tables
   → KnowledgeGraph(persist_path) → load or create 40+ seed entities

3. Initialize NLP engine
   → DeepNLPParser() → load spaCy, FinBERT, MiniLM, zero-shot models

4. Initialize cognitive engine
   → CognitiveMarketSystem(config)
     → creates 5 participant models (PARTICIPANT_REGISTRY)
     → creates ExpectationCollisionEngine
     → creates TradableSignalTranslator
     → connects KnowledgeGraph

5. Initialize pipeline bridge
   → PipelineBridge(mode="hybrid")
     → instantiates CognitiveMarketSystem (Pipeline A)
     → instantiates PipelineOrchestrator (Pipeline B)

6. Initialize streaming pipeline
   → StreamingPipeline() → 7-stage processor

7. Initialize support systems
   → DecisionEngine()
   → ExecutionNexus() → $100K paper capital
   → MarketDataFeed(use_live=True/False)
   → ScenarioGenerator()
   → FeedbackLoop()
   → NewsAggregator(sources)

8. Setup logging
   → setup_logging(log_level, log_dir)
   → rotating file handler + console handler

9. Return components dict
```

### Key Files

| Component | File | Class |
|-----------|------|-------|
| Config | `config/system_config.py` | `get_config()` → `SystemConfig` |
| Database | `storage/database.py` | `DatabaseManager` |
| Knowledge Graph | `storage/knowledge_graph.py` | `KnowledgeGraph` |
| NLP | `nlp_engine/deep_nlp_parser.py` | `DeepNLPParser` |
| Cognitive Engine | `engine/cognitive_market_system.py` | `CognitiveMarketSystem` |
| Bridge | `pipeline_bridge.py` | `PipelineBridge` |

---

## WF2: News Ingestion Workflow

**Entry**: `news_ingestion/news_aggregator.py` → `NewsAggregator.fetch_latest()`
**Purpose**: Gather news from multiple sources, deduplicate, return unified articles

### Steps

```
1. Initialize sources
   → NewsAPIClient(api_key)    — NewsAPI.org (80K+ sources, 100 req/day)
   → GDELTClient()             — GDELT events + articles
   → RSSReader()               — 14 pre-configured financial feeds

2. Fetch from all sources (parallel via ThreadPoolExecutor)
   → _fetch_newsapi(query, hours_back, max_per_source)
   → _fetch_gdelt(query, hours_back, max_per_source)
   → _fetch_rss(financial_only=True)

3. Convert to unified format
   → _convert_newsapi(articles) → UnifiedArticle[]
   → _convert_gdelt(articles)   → UnifiedArticle[]
   → _convert_rss(articles)     → UnifiedArticle[]

4. Deduplicate
   → _deduplicate(all_articles)
     ├── content_hash matching (SHA256)
     └── title word overlap > 70% → mark as duplicate

5. Return UnifiedArticle[]
   → each has: title, content, source, url, timestamp, content_hash
```

### RSS Feeds (14 Sources)

Reuters, Bloomberg, CNBC, Financial Times, Wall Street Journal, MarketWatch, Yahoo Finance, Seeking Alpha, ZeroHedge, The Economist, BBC Business, NYT Business, Guardian Business, AP Business

---

## WF3: NLP Processing Workflow

**Entry**: `nlp_engine/deep_nlp_parser.py` → `DeepNLPParser.parse(text)`
**Purpose**: Convert raw text into structured linguistic analysis

### Steps

```
1. Tokenize and parse with spaCy
   → en_core_web_sm → tokens, entities, POS tags, dependency tree

2. Per-sentence analysis
   → For each sentence:
     ├── Compute certainty score (hedge words - boost words)
     ├── Detect conditionals (if, whether, depending)
     ├── Detect negations (not, no, never, fail)
     ├── Detect questions (?)
     └── Classify sentence type

3. Entity extraction
   → FinancialEntity[], GeopoliticalEntity[], EntityRelation[]

4. Narrative classification (12 types)
   → zero-shot (facebook/bart-large-mnli) or keyword fallback
   → Types: MACRO_POLICY, EARNINGS, GEOPOLITICAL, CREDIT_RISK,
            LIQUIDITY, REGULATORY, TECHNOLOGY, SENTIMENT_SHIFT, UNKNOWN, ...

5. Intent detection (8 types)
   → keyword scoring against StrategicIntent patterns
   → ROUTINE/GUIDANCE/WARNING/REASSURANCE/TRIAL_BALLOON/
     LEAK_STRATEGIC/DISTRACTION/PUMP/SHORT_ATTACK

6. Document metrics
   → overall certainty, subjectivity, complexity

7. Key phrase extraction
   → from entities + semantic triples + sentence analysis

8. Embedding computation
   → sentence-transformers/all-MiniLM-L6-v2
   → document-level + per-sentence embeddings

9. Return DeepParseResult
   → sentences[], entities[], triples[], narrative_type,
     intent, document_metrics, key_phrases, embeddings
```

### Models Used

| Step | Model | Fallback |
|------|-------|----------|
| Tokenize | spaCy `en_core_web_sm` | Regex |
| Sentiment | `ProsusAI/finbert` | `distilbert-sst-2` |
| Classification | `facebook/bart-large-mnli` | Keywords |
| Embeddings | `all-MiniLM-L6-v2` | Hash-based |

---

## WF4: Cognitive Engine Workflow

**Entry**: `engine/cognitive_market_system.py` → `CognitiveMarketSystem.process_news_event()`
**Purpose**: Run the 5-layer cognitive engine on a news event

### Steps

```
1. Ingest news
   → ingest_news(raw_text, source, timestamp)
   → DeepNLPParser.parse() → creates LinguisticShockVector
     (magnitude, direction, uncertainty, temporal_focus, narrative_shift)

2. Interpret cognitively
   → interpret_cognitively(news_event) 
   → 5 participant models each call interpret():
     ├── RetailTraderModel → emotional response
     ├── HFTModel          → spread/latency focus
     ├── HedgeFundModel    → asymmetric return
     ├── BankModel          → hedging/risk-averse
     └── MarketMakerModel   → inventory stability

3. Compute collision
   → ExpectationCollisionEngine.compute_collision()
   → 9 steps:
     1. Extract expectations
     2. Compute directional disagreement
     3. Compute magnitude divergence
     4. Detect temporal misalignment
     5. Compute volatility expectation spread
     6. Check for unanimous consensus
     7. Calculate market stress
     8. Detect regime change signals
     9. Produce collision summary

4. Translate to signal
   → TradableSignalTranslator.translate(collision_result)
   → Multi-gate pipeline:
     ├── Confidence gate (minimum threshold)
     ├── Direction gate (consensus direction)
     ├── Sizing gate (risk-adjusted position size)
     └── Risk gate (stop loss, take profit, max holding)
   → TradableSignal (LONG/SHORT/HEDGE/FLATTEN/WAIT)

5. Update knowledge graph
   → KnowledgeGraph.update_from_news_event()
   → persist entity relationships

6. Return full result
```

---

## WF5: 7-Phase Pipeline Workflow

**Entry**: `legacy_main.py` → `PipelineOrchestrator.run_full_pipeline()`
**Purpose**: Run the 7-phase operational pipeline end-to-end

### Steps

```
Phase 1: run_phase_1(raw_text, source)
    → NewsEventParser.parse() → NewsEvent
    RULE: NO sentiment/trading signals — only linguistic structure

Phase 2: run_phase_2(news_event)
    → 5× Participant.interpret() → ParticipantExpectation[]
    RULE: NO prices — only cognitive expectations
    RULE: Action likelihoods sum to 1.0

Phase 3: run_phase_3(expectations)
    → 5× BehaviorTranslator.translate() → BehaviorProfile[]
    RULE: NO trades/orders — only behavioral profiles
    RULE: Inaction is meaningful

Phase 4: run_phase_4(behaviors)
    → BehaviorAggregator.aggregate() → AggregatedBehavior
    → ImpactTranslator.translate() → MarketImpactProfile
    RULE: NO price direction — only market structure impacts

Phase 5: run_phase_5(impact_profile, news_event)
    → RealityValidator.create_validation_record() → ValidationRecord
    RULE: Research-only — NO trading signals

Phase 6: run_phase_6(validation, impact, news_event)
    → SignalAuthorizer.authorize_signal() → SignalRecord
    → Trust threshold = 0.6, Expiration = 4 hours

Phase 7: run_phase_7(signal_record, market_price)
    → ExecutionNexus.execute_signal() → ExecutedOrder
    → Kelly sizing, paper trading, circuit breaker checks

Return: get_pipeline_status() → all phase results
```

---

## WF6: Pipeline Bridge Workflow

**Entry**: `pipeline_bridge.py` → `PipelineBridge.process()`
**Purpose**: Merge cognitive engine + 7-phase pipeline results

### Steps

```
1. Determine mode (engine_only / phase_only / hybrid)

2. If hybrid:
   a. Run Pipeline A (cognitive engine)
      → _run_engine(text, source, market_price)
      → engine_result (signals, collision metrics)
   
   b. Run Pipeline B (7-phase pipeline)
      → _run_phases(text, source, market_price)
      → phase_result (all 7 phase outputs)
   
   c. Merge into UnifiedResult
      → combines signals, validations, execution data

3. Return UnifiedResult with get_status()
```

---

## WF7: Streaming Pipeline Workflow

**Entry**: `streaming/pipeline.py` → `StreamingPipeline.process()`
**Purpose**: Process news through 7 streaming stages with event bus integration

### Steps

```
1. _stage_1_ingest(raw_text, source)
   → News ingestion
   → Publish: EventTypes.NEWS_INGESTED

2. _stage_2_nlp(news_data)
   → NLP processing
   → Publish: EventTypes.NLP_PROCESSED

3. _stage_3_cognitive(nlp_result)
   → Cognitive modeling
   → Publish: EventTypes.COGNITIVE_MODELED

4. _stage_4_behavior(cognitive_result)
   → Behavior translation
   → Publish: EventTypes.BEHAVIOR_TRANSLATED

5. _stage_5_impact(behavior_result)
   → Impact modeling
   → Publish: EventTypes.IMPACT_MODELED

6. _stage_6_validate(impact_result)
   → Reality validation
   → Publish: EventTypes.VALIDATED

7. _stage_7_signal(validation_result)
   → Signal generation
   → Publish: EventTypes.SIGNAL_GENERATED

get_pipeline_metrics() → per-stage timing + throughput
```

---

## WF8: Alpha Signal Generation Workflow

**Entry**: `alpha_models/alpha_signals.py` → `AlphaSignalAggregator.aggregate()`
**Purpose**: Generate 22 alpha signals from quantitative, NLP, and structural sources

### Steps

```
1. Run 12 quantitative alpha generators
   → PositioningAnalyzer.analyze()        (weight 0.12)
   → OrderFlowAnalyzer.analyze()          (weight 0.12)
   → CreditMarketSignals.analyze()        (weight 0.10)
   → VolatilitySurfaceAnalyzer.analyze()  (weight 0.10)
   → MacroSurpriseIndex.analyze()         (weight 0.10)
   → CentralBankBalanceSheet.analyze()    (weight 0.08)
   → CrossAssetLeadLag.analyze()          (weight 0.08)
   → SentimentExtremesAnalyzer.analyze()  (weight 0.08)
   → FlowOfFundsAnalyzer.analyze()        (weight 0.07)
   → InsiderTradingAnalyzer.analyze()     (weight 0.06)
   → CalendarEffectsAnalyzer.detect_active_effects() (weight 0.05)
   → EarningsRevisionTracker.analyze()    (weight 0.04)
   → AlphaSignalAggregator.aggregate()
     → weighted conviction, agreement ratio, horizon breakdown

2. Run 5 NLP alpha generators
   → NarrativeMomentumAlpha.generate()
   → ContradictionAlpha.generate()
   → InstitutionalLanguageAlpha.generate()
   → TemporalClusteringAlpha.generate()
   → SentimentDivergenceAlpha.generate()
   → NLPAlphaHub.generate_signals()
     → narrative composite with weights

3. Run 5 structural alpha generators
   → MicrostructureAlpha.analyze()
   → RealizedVolAlpha.analyze()
   → FundingRateAlpha.analyze()
   → OnChainAlpha.analyze()
   → LiquidityPremiumAlpha.analyze()
   → StructuralAlphaEngine.analyze()
     → structural composite with weights

4. Merge all 22 signals
   → combined conviction score
```

---

## WF9: Hidden Truth Detection Workflow

**Entry**: `hidden_truth/` — multiple entry points
**Purpose**: Detect market manipulation, coordinated narratives, and hidden agendas

### Steps

```
1. Timing analysis
   → TimingAnalyzer.analyze_timing(timestamp, event_type)
   → Check against 11 recurring events (FOMC, NFP, CPI, GDP, ...)
   → Suspicious: releases at non-standard times before events

2. Filing analysis (SEC)
   → FilingAnalyzer.compare_risk_sections(current, previous)
   → Tone divergence between PR releases and SEC filings
   → Gunning Fog readability index (obfuscation detection)

3. Insider correlation
   → InsiderCorrelationAnalyzer.analyze(transactions, news, prices)
   → Detect: sale_before_bad_news, purchase_before_good_news
   → C-suite weight 1.5x, large ($1M+) 1.3x, 5-day cluster window

4. Source network analysis
   → SourceNetworkAnalyzer.build_network(articles)
   → Echo chambers: co-coverage ≥5, sentiment corr >0.8, timing >0.6
   → Independence scoring, credibility ranking (0.4+0.3+0.3 weighted)

5. Cross-source analysis
   → CrossSourceAnalyzer.analyze(articles_on_topic)
   → Coordinated releases: <30s from 3+ unique sources
   → Conflicts: sentiment divergence >0.3
   → Trust score: 5-component (diversity+consistency+alignment+
     conflicts+coordination)
   → SQLite persistence for pattern matching

6. Narrative tracking
   → NarrativeTracker.track(event)
   → Evolution: growing/fading/stable/new
   → Manufactured consensus detection
   → Intensity = recency×0.4 + source×0.3 + sentiment×0.3
```

---

## WF10: Scenario Analysis Workflow

**Entry**: `scenario_engine/scenario_generator.py` → `ScenarioGenerator.generate()`
**Purpose**: Generate probabilistic scenarios for market events

### Steps

```
1. Generate scenario tree
   → ScenarioGenerator.generate(event_data, max_depth=3)
   → Root → children → leaves (probability tree)
   → compute_tree_metrics: prob-weighted move, tail risk

2. Build causal chain
   → CausalChainBuilder.build_chain(event_data, max_depth=3)
   → 1st order (7 templates: rate_hike, rate_cut, inflation_high, ...)
   → 2nd order (5 rules: equity_bearish, usd_strong, oil_spike, ...)
   → 3rd order (3 rules: systemic_stress, feedback_loop, policy_response)
   → KnowledgeGraph enhancement
   → Metrics: dominant direction, systemic risk, feedback loops

3. Monte Carlo simulation
   → MonteCarloSimulator.simulate(base_scenario, n=10000)
   → mean, VaR 95/99, CVaR 95, max drawdown, skew, kurtosis

4. Counterfactual analysis
   → CounterfactualAnalyzer.analyze_counterfactual(event_id, realized)
   → sensitivity_analysis: vary impact magnitude ±scale_range

5. Portfolio optimization (4 methods)
   → ScenarioPortfolioOptimizer.optimize(scenarios, assets, method)
   → minimax | expected_utility | risk_parity | cvar
```

---

## WF11: Market Intelligence Workflow

**Entry**: `market_intelligence/intelligence_models.py` → `MarketIntelligenceHub.full_scan()`
**Purpose**: Run 9 advanced market intelligence models

### Steps

```
1. AlternativeDataFusion    → 8 alt data → z-score composite
2. RegimeDetector           → HMM 5-regime + CUSUM changepoint
3. CrowdingRiskDetector     → short squeeze + factor crowding
4. LiquidityForecaster      → volume/spread + flash crash conditions
5. CrossMarketArbitrage     → basis trade + ETF NAV + put-call parity
6. SentimentDecayModel      → exponential decay, regime half-lives
7. InformationCascadeDetector → alignment >80%, declining independence
8. ReflexivityModel         → narrative-price coupling, reversal
9. DarkPoolAnalyzer         → dark volume %, block clustering, VWAP

→ MarketIntelligenceHub.risk_summary()
  → critical / elevated / moderate / normal
```

---

## WF12: Decision Making Workflow

**Entry**: `decision_system/decision_engine.py` → `DecisionEngine.decide()`
**Purpose**: Aggregate signals + risk gates → final trading decision

### Steps

```
1. Aggregate incoming signals
   → _aggregate_signals(CognitiveSignal[])
   → compute: overall strength, agreement ratio

2. Check risk gates
   → _check_risk_gates()
   → portfolio exposure limits, drawdown checks, regime checks

3. Check hidden truth flags
   → _check_hidden_truth()
   → manipulation flags from hidden_truth detection

4. Determine action
   → _determine_action(packet, strength, agreement)
   → BUY / SELL / HOLD / REDUCE / HEDGE / EMERGENCY_EXIT / WATCH

5. Compute position sizing
   → _compute_sizing(packet, strength, agreement)
   → Kelly-inspired, regime-adjusted, half-Kelly
   → max_position_pct capped

6. Compute risk levels
   → _compute_risk_levels(packet, strength)
   → volatility-adjusted stop_loss_pct, take_profit_pct
   → risk_reward_ratio computed

7. Finalize decision
   → _finalize(packet) → DecisionPacket
   → includes reasoning_chain, confidence, all risk parameters

8. Check escalation triggers
   → If triggered → HumanReviewQueue.submit_for_review()
```

---

## WF13: Execution Workflow

**Entry**: `execution/execution_nexus.py` → `ExecutionNexus.execute_signal()`
**Purpose**: Execute approved signals with risk controls

### Steps

```
1. Receive approved signal
   → ApprovedSignal with direction, strength, confidence

2. Check position limits
   → check_position_limits()
   ├── Max 3 open positions
   ├── Daily loss < 2% of capital
   └── Circuit breaker at 5% drawdown → REJECT if triggered

3. Size the order
   → size_order(signal, price)
   → Kelly-inspired: strength × confidence × max_position
   → Capped at 15% of $100K = $15,000

4. Route the order
   → route_order(signal)
   ├── AGGRESSIVE → market order, expected fill <1s
   └── PASSIVE → limit order, expected fill <5min

5. Execute
   → ExecutedOrder (order_id, direction, size, entry_price,
     stop_loss, take_profit, status)

6. Monitor exits
   → check_exit_conditions(position, current_price)
   ├── Stop loss hit (2% adverse move) → close
   ├── Take profit hit (3-4% favorable move) → close
   └── Max holding period exceeded → close

7. Record trade
   → DatabaseManager.store_trade(trade)
```

---

## WF14: Reality Validation Workflow

**Entry**: `reality_validation/market_reality.py` → `RealityValidator.create_validation_record()`
**Purpose**: Validate predictions against market reality (research-only, no trading)

### Steps

```
1. Collect market data
   → MarketDataProvider.get_price_around_event(asset, timestamp)
   → Sources: CoinGecko → Yahoo Finance → cache → simulated
   → Build: MarketReality (snapshots around event)

2. Validate 5 dimensions (weighted)
   a. validate_directional_accuracy()    (weight 0.30)
      → predicted vs actual price direction
   
   b. validate_volatility_accuracy()     (weight 0.20)
      → predicted vs actual volatility magnitude
   
   c. validate_timing_accuracy()         (weight 0.20)
      → shock onset (30s tolerance)
      → peak impact (5min tolerance)
      → recovery (15min tolerance)
   
   d. validate_participation_match()     (weight 0.15)
      → predicted vs actual participant behavior
   
   e. validate_regime_shift()            (weight 0.15)
      → temporary (≤1d) / semi-persistent (≤7d) / structural (>7d)

3. Compute composite accuracy
   → weighted sum of 5 dimensions

4. Statistical significance testing
   → one-sided binomial test
   → z-score + p-value
   → one-sample t-test

5. Update model credibility
   → per participant type accuracy tracking
   → failure pattern analysis
```

---

## WF15: Signal Authorization Workflow

**Entry**: `signal_auth/signal_authorization.py` → `SignalAuthorizer.authorize_signal()`
**Purpose**: 5-step authorization pipeline for trading signals

### Steps

```
1. Assign trust score
   → assign_trust_score(news, validation)
   → base from historical accuracy per event type
   → + participant model accuracies

2. Filter signal
   → filter_signal(trust, validation, threshold=0.6)
   → APPROVED if trust ≥ 0.6, FILTERED otherwise

3. Weight signal strength
   → weight_signal_strength(trust, validation, prediction, news)
   → event-type base × trust × participant-weighted confidence

4. Determine direction
   → determine_signal_direction(validation, news, prediction)
   → BUY / SELL / NEUTRAL / UNCERTAIN
   → Based on HFT/HF consensus

5. Determine volatility impact
   → determine_volatility_impact(validation, prediction, news)
   → LOW / MEDIUM / HIGH / EXTREME

6. Assemble SignalRecord
   → direction, strength, trust_score, volatility_impact,
     reaction_horizon, participant_weights, status, expiration (4h)

7. Normalize across multiple signals
   → normalize_signals(signals, now)
   → weighted vote, conflict detection
```

---

## WF16: Feedback & Learning Workflow

**Entry**: `learning/feedback_loop.py` → `FeedbackLoop.record_prediction()`
**Purpose**: Track prediction accuracy and update model credibility

### Steps

```
1. Record prediction
   → record_prediction(event_type, participant_type, prediction, actual)

2. Compute accuracy
   → compare prediction vs actual outcome

3. Update credibility
   → update_credibility(participant_type, accuracy)
   → per-type running accuracy

4. Generate insights
   → get_model_weights()          → current credibility per type
   → get_accuracy_by_event_type() → which types each model handles best
   → get_improvement_recommendations() → actionable suggestions

5. Persist to storage
   → _save_to_storage() → DatabaseManager
```

---

## WF17: Backtesting Workflow

**Entry**: `backtesting/backtest_engine.py` → `BacktestRunner.run()`
**Purpose**: Replay historical events through the pipeline and measure performance

### Steps

```
1. Load historical events
   → EventReplayEngine.load_events(events)
   → chronological sorting

2. Replay loop
   → For each event in timeline:
     a. EventReplayEngine.replay(start, end, speed)
     b. Process through pipeline → generate signal
     c. PositionTracker.open_position(signal)
     d. mark_to_market(prices) → check exit conditions
     e. Close positions at stop/target/expiry

3. Compute performance
   → PerformanceAnalytics.compute(trades)
   → Sharpe ratio
   → Sortino ratio
   → Max drawdown
   → Win rate
   → Profit factor
   → Avg win / avg loss
   → Expectancy

4. Return backtest results with full metrics
```

### Configuration

| Parameter | Value |
|-----------|-------|
| Capital | $100,000 |
| Max position | 10% |
| Stop loss | 2% |
| Take profit | 4% |

---

## WF18: Live Monitoring Workflow

**Entry**: `run_live.py` → `run_live_monitor()`
**Purpose**: Continuous live monitoring with automatic news processing

### Steps

```
1. Initialize components
   → bootstrap(asset) → all system components

2. Enter infinite loop
   → while True:
     a. NewsAggregator.fetch_latest(query=asset)
        → UnifiedArticle[] (deduplicated)
     
     b. For each new article (content-hash dedup):
        → process_single_news(components, text, source, price)
        → PipelineBridge.process() or direct engine call
     
     c. MarketDataFeed.get_market_snapshot(asset)
        → current price, bid, ask, volume
     
     d. Check exit conditions on open positions
        → ExecutionNexus.check_exit_conditions()
     
     e. Sleep(interval)
        → configurable polling interval

3. Deduplication
   → content_hash set prevents reprocessing
```

---

## WF19: Dashboard Workflow

**Entry**: `dashboard/app.py` → Streamlit app
**Purpose**: Real-time visual monitoring via web interface

### Steps

```
1. Launch Streamlit on port 8501
   → streamlit run dashboard/app.py

2. Render 7 pages:
   a. Overview     → system status, key metrics
   b. Live Feed    → real-time news + signals
   c. Signal History → historical signal performance
   d. Market Intelligence → cross-asset analytics
   e. Hidden Truth → manipulation detection results
   f. Backtesting  → backtest results + performance
   g. System Health → infrastructure health metrics

3. Auto-refresh
   → configurable interval from DashboardConfig
```

---

## WF20: Alert Delivery Workflow

**Entry**: `alerts/alert_delivery.py` → `AlertDeliverySystem.send_alert()`
**Purpose**: Multi-channel alert delivery for trading signals and system events

### Steps

```
1. Create alert
   → Alert(priority, message, data)
   → Priority: LOW / MEDIUM / HIGH / CRITICAL

2. Route to channels
   → For each configured channel:
     ├── _deliver_console(alert)   → formatted terminal output
     ├── _deliver_file(alert)      → rotating log file
     ├── _deliver_webhook(alert)   → HTTP POST to URL
     ├── _deliver_email(alert)     → SMTP (configurable server)
     └── _deliver_sms(alert)       → Twilio API

3. Record delivery
   → DatabaseManager.store_alert() → alert_history table
   → get_stats() → delivery success/failure counts
```

---

## WF21: Human Review Workflow

**Entry**: `decision_system/human_review_queue.py` → `HumanReviewQueue`
**Purpose**: Escalate high-risk decisions for human approval

### Steps

```
1. Check escalation rules (6 triggers)
   → high_value: position > $50K
   → low_confidence: confidence < 0.4
   → hidden_truth_flagged: manipulation detected
   → regime_crisis: crisis regime active
   → contradictory_signals: conflicting signal directions
   → novel_event_type: unseen event category

2. Submit for review
   → submit_for_review(decision_packet)
   → queued with review_id

3. Human acts
   → approve(review_id) → proceed to execution
   → reject(review_id)  → discard decision

4. Track statistics
   → get_pending_reviews() → current queue
   → get_review_stats() → approval/rejection rates
```

---

## WF22: Infrastructure Health Workflow

**Entry**: `scripts/health_check.py` + `infrastructure/infra_layer.py`
**Purpose**: Verify all system components are operational

### Steps

```
1. Health check script
   → scripts/health_check.py (305 lines)
   → checks: database connectivity, NLP model loading,
     API endpoints, storage paths, configuration validity

2. Infrastructure manager
   → InfrastructureManager.health_report()
   → Check each component:
     ├── MessageQueue → message throughput, dead letters
     ├── TimeSeriesDB → write/read latency, retention
     ├── ModelRegistry → model versions, active stage
     ├── FeatureStore → feature freshness, SLA compliance
     ├── CICDPipeline → stage statuses
     ├── MonitoringSystem → metric values, alert states
     └── APILayer → endpoint availability, rate limit status

3. Monitoring metrics
   → MonitoringSystem exports Prometheus format
   → 12 default metrics, 5 alert rules
   → Grafana dashboard JSON for visualization

4. API health endpoint
   → GET /health → component status report
```

---

## WF23: Full End-to-End Workflow

**Entry**: `main.py --live` or `main.py --news "text"`
**Purpose**: Complete news-to-trade pipeline

### Steps

```
1. INITIALIZE (WF1)
   → bootstrap(asset) → all components loaded

2. INGEST (WF2)
   → NewsAggregator.fetch_latest() or manual --news input
   → Deduplicated UnifiedArticle[]

3. PROCESS NLP (WF3)
   → DeepNLPParser.parse() → DeepParseResult
   → EntityExtractor, ContradictionDetector, IntentDetector

4. COGNITIVE ENGINE (WF4)
   → CognitiveMarketSystem.process_news_event()
   → 5 participant models → collision → signal

5. 7-PHASE PIPELINE (WF5)
   → PipelineOrchestrator.run_full_pipeline()
   → Phase 1-7 sequential processing

6. BRIDGE (WF6)
   → PipelineBridge.process(mode="hybrid")
   → Merge cognitive + operational results

7. ALPHA SIGNALS (WF8)
   → 22 alpha generators → composite conviction

8. HIDDEN TRUTH (WF9)
   → 6 manipulation detectors → flags

9. SCENARIOS (WF10)
   → ScenarioGenerator + CausalChain + MonteCarlo

10. INTELLIGENCE (WF11)
    → 9 models → risk assessment

11. DECIDE (WF12)
    → DecisionEngine.decide() → DecisionPacket
    → Human review if escalation triggered (WF21)

12. AUTHORIZE (WF15)
    → SignalAuthorizer → trust ≥ 0.6 gate → SignalRecord

13. EXECUTE (WF13)
    → ExecutionNexus.execute_signal() → paper trade
    → Position monitoring, stop/target exits

14. VALIDATE (WF14)
    → RealityValidator → 5-dimension validation
    → Statistical significance testing

15. LEARN (WF16)
    → FeedbackLoop.record_prediction()
    → Update model credibility, generate recommendations

16. ALERT (WF20)
    → AlertDeliverySystem → multi-channel notification

17. STORE
    → DatabaseManager → all events, signals, trades, metrics
    → KnowledgeGraph → entity relationships updated

18. VISUALIZE (WF19)
    → Dashboard auto-refreshes with new data

19. LOOP BACK TO STEP 2 (in live mode)
    → sleep(interval) → fetch next batch
```

### End-to-End Data Flow Diagram

```
Raw News Text
    │
    ▼
┌─────────────────┐     ┌──────────────────┐
│ News Ingestion   │────▶│ NLP Engine        │
│ (14 RSS + API)  │     │ (spaCy+FinBERT+  │
└─────────────────┘     │  MiniLM+BART)    │
                        └────────┬─────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │ Cognitive │ │ 7-Phase  │ │ Streaming│
             │ Engine    │ │ Pipeline │ │ Pipeline │
             │ (5-layer) │ │(Phases1-7│ │(7-stage) │
             └─────┬─────┘ └─────┬────┘ └─────┬───┘
                   │             │             │
                   └──────┬──────┘             │
                          ▼                    │
                   PipelineBridge              │
                   (hybrid merge)──────────────┘
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
  ┌──────────┐    ┌──────────────┐   ┌──────────────┐
  │ Alpha    │    │ Hidden Truth │   │ Scenarios    │
  │ (22 sigs)│    │ (6 detectors)│   │ (MC+Causal)  │
  └────┬─────┘    └──────┬───────┘   └──────┬───────┘
       │                 │                   │
       └────────┬────────┘                   │
                ▼                            │
         ┌──────────────┐                    │
         │ Decision     │◀───────────────────┘
         │ Engine       │
         │ (risk gates) │
         └──────┬───────┘
                │
         ┌──────▼───────┐
         │ Signal Auth  │
         │ (trust ≥ 0.6)│
         └──────┬───────┘
                │
         ┌──────▼───────┐
         │ Execution    │
         │ ($100K paper)│
         └──────┬───────┘
                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼
┌──────────┐ ┌────────┐ ┌──────────┐
│ Reality  │ │Feedback│ │ Storage  │
│Validation│ │ Loop   │ │(SQLite+  │
│(5-dim)   │ │(credit)│ │ Graph)   │
└──────────┘ └────────┘ └──────────┘
```

---

*Document generated from full source code analysis of 78 Python files across 30 packages.*
