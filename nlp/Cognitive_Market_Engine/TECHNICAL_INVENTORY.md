# Cognitive Market Engine — Comprehensive Technical Inventory

> **Generated**: Full deep-reading of every Python file in the project  
> **Total Python Files**: ~78 files across 30+ packages  
> **Total Estimated Lines**: ~42,000+ lines of Python  
> **Language**: Python 3.8+ / 3.11 (Docker)

---

## (A) Directory Tree with File Counts

```
Cognitive_Market_Engine/
│
├── main.py                          # Unified CLI entry point
├── run_live.py                      # Live monitoring loop
├── legacy_main.py                   # 7-phase orchestrator (PipelineOrchestrator)
├── pipeline_bridge.py               # Dual-pipeline bridge (engine + phases)
├── fix_test.py                      # Quick test fix
├── simple_test.py                   # Smoke test
├── test_cognitive_system.py         # System-level test
├── requirements.txt                 # 23 dependencies
├── Dockerfile                       # Multi-stage Python 3.11-slim
├── .env.example                     # Environment variables template
├── .gitignore
├── README.md
├── INDEX.md
├── SYSTEM_STATUS.md
├── COMPREHENSIVE_ANALYSIS_REPORT.md
├── SYSTEM_ANALYSIS_DOCUMENT.md
├── MISSING_CONCEPTS_DOCUMENT.md
│
├── engine/                          [7 files]  Core cognitive engine
│   ├── __init__.py
│   ├── cognitive_market_system.py   (431 lines)
│   ├── core_cognitive_structures.py (~450 lines)
│   ├── expectation_collision_engine.py (~520 lines)
│   ├── participant_models.py        (699 lines)
│   ├── tradable_signal_translator.py (~540 lines)
│   └── real_data_adapter.py         (~130 lines)
│
├── config/                          [3 files]  System configuration
│   ├── __init__.py
│   ├── system_config.py             (394 lines)
│   └── logging_config.py            (~80 lines)
│
├── shared/                          [1 file]   Canonical enums
│   └── __init__.py                  (64 lines)
│
├── streaming/                       [3 files]  Event streaming pipeline
│   ├── __init__.py
│   ├── event_bus.py                 (~280 lines)
│   └── pipeline.py                  (647 lines)
│
├── storage/                         [3 files]  Persistence layer
│   ├── __init__.py
│   ├── database.py                  (605 lines)
│   └── knowledge_graph.py           (641 lines)
│
├── nlp_engine/                      [7 files]  NLP processing core
│   ├── __init__.py
│   ├── deep_nlp_parser.py           (1303 lines)
│   ├── advanced_nlp.py              (801 lines)
│   ├── entity_extraction.py         (~320 lines)
│   ├── contradiction_detector.py    (381 lines)
│   ├── intent_detector.py           (464 lines)
│   └── nlp_extensions.py            (675 lines)
│
├── news_model/                      [3 files]  News event data model
│   ├── __init__.py
│   ├── news_event.py                (~240 lines)
│   └── parser.py                    (~280 lines)
│
├── news_ingestion/                  [5 files]  Multi-source news fetching
│   ├── __init__.py
│   ├── news_api_client.py           (~270 lines)
│   ├── gdelt_client.py              (307 lines)
│   ├── rss_reader.py                (~280 lines)
│   └── news_aggregator.py           (668 lines)
│
├── participant_cognition/           [2 files]  Phase 2: Cognitive models
│   ├── __init__.py
│   └── participant_models.py        (618 lines)
│
├── market_response/                 [2 files]  Phase 3: Behavior translation
│   ├── __init__.py
│   └── behavior_models.py           (606 lines)
│
├── market_impact/                   [3 files]  Phase 4: Impact modeling
│   ├── __init__.py
│   ├── market_impact_models.py      (1151 lines)
│   └── (enums exported via __init__)
│
├── reality_validation/              [2 files]  Phase 5: Reality validation
│   ├── __init__.py
│   └── market_reality.py            (1049 lines)
│
├── signal_auth/                     [2 files]  Phase 6: Signal authorization
│   ├── __init__.py
│   └── signal_authorization.py      (778 lines)
│
├── execution/                       [2 files]  Phase 7: Execution
│   ├── __init__.py
│   └── execution_nexus.py           (634 lines)
│
├── decision_system/                 [3 files]  Trade decision engine
│   ├── __init__.py
│   ├── decision_engine.py           (622 lines)
│   └── human_review_queue.py        (~350 lines)
│
├── hidden_truth/                    [6 files]  Manipulation detection
│   ├── __init__.py
│   ├── timing_analyzer.py           (~350 lines)
│   ├── advanced_detection.py        (926 lines)
│   ├── cross_source_analyzer.py     (725 lines)
│   └── narrative_tracker.py         (473 lines)
│
├── scenario_engine/                 [5 files]  Scenario generation
│   ├── __init__.py
│   ├── scenario_generator.py        (~547 lines)
│   ├── causal_chain.py              (624 lines)
│   ├── monte_carlo.py               (361 lines)
│   └── scenario_extensions.py       (687 lines)
│
├── alpha_models/                    [4 files]  Alpha signal generation
│   ├── __init__.py
│   ├── alpha_signals.py             (1667 lines)
│   ├── nlp_alpha_signals.py         (754 lines)
│   └── structural_alpha.py          (948 lines)
│
├── multi_asset/                     [3 files]  Cross-asset analysis
│   ├── __init__.py
│   ├── correlation_engine.py        (~420 lines)
│   └── contagion_model.py           (~370 lines)
│
├── market_intelligence/             [2 files]  Advanced market models
│   ├── __init__.py
│   └── intelligence_models.py       (1373 lines)
│
├── infrastructure/                  [2 files]  Production infrastructure
│   ├── __init__.py
│   └── infra_layer.py               (1254 lines)
│
├── economics/                       [2 files]  Economic models
│   ├── __init__.py
│   └── economic_models.py           (689 lines)
│
├── backtesting/                     [2 files]  Backtesting framework
│   ├── __init__.py
│   └── backtest_engine.py           (778 lines)
│
├── learning/                        [2 files]  Feedback/learning loop
│   ├── __init__.py
│   └── feedback_loop.py             (456 lines)
│
├── data/                            [2 files]  Market data simulation
│   ├── __init__.py
│   └── market_data_feed.py          (~290 lines)
│
├── dashboard/                       [2 files]  Streamlit dashboard
│   ├── __init__.py
│   └── app.py                       (~350 lines)
│
├── advanced/                        [5 files]  Advanced analysis modules
│   ├── __init__.py
│   ├── geopolitical_risk.py         (~300 lines)
│   ├── llm_analyzer.py              (~250 lines)
│   ├── social_media.py              (~340 lines)
│   └── report_generator.py          (~280 lines)
│
├── alerts/                          [2 files]  Alert delivery
│   ├── __init__.py
│   └── alert_delivery.py            (466 lines)
│
├── scripts/                         [1 file]   Health check
│   └── health_check.py              (305 lines)
│
├── tests/                           [8 files]  Test suites (Phases 1-6 + integration)
│   ├── __init__.py
│   ├── test_phase_1.py              (404 lines, 12 tests)
│   ├── test_phase_2.py              (531 lines, 14 tests)
│   ├── test_phase_3.py              (586 lines, 14 tests)
│   ├── test_phase_4.py              (900 lines, 14 tests)
│   ├── test_phase_5.py              (537 lines, 14 tests)
│   ├── test_phase_6.py              (632 lines, 14 tests)
│   └── test_integration.py          (306 lines, 8 tests)
│
└── logs/                            [empty]    Runtime log directory
```

**Total: 30 packages • ~78 Python files • ~42,000+ lines**

---

## (B) File Registry — Classes, Methods, Imports

### B.1 Root Files

#### `main.py` (~290 lines)
- **Functions**: `bootstrap(asset, verbose)`, `interactive_demo()`, `process_single_news(components, text, source, price)`, `run_tests()`, `launch_dashboard()`, `main()`
- **CLI Modes**: `--live`, `--dashboard`, `--test`, `--news "text"`, `--asset SYMBOL`
- **Imports**: `argparse`, `engine.CognitiveMarketSystem`, `pipeline_bridge.PipelineBridge`, `streaming.StreamingPipeline`, `decision_system.DecisionEngine`, `execution.ExecutionNexus`, `data.MarketDataFeed`, `scenario_engine.ScenarioGenerator`, `hidden_truth`, `learning.FeedbackLoop`, `config.get_config`, `storage.DatabaseManager`, `storage.KnowledgeGraph`, `dashboard.app`

#### `run_live.py` (~150 lines)
- **Functions**: `run_live_monitor(components, interval, asset)`
- **Pattern**: Infinite loop with content-hash deduplication, `news_ingestion.NewsAggregator`

#### `legacy_main.py` (640 lines)
- **Classes**: `PipelineEvent(dataclass)`, `PipelineOrchestrator`
- **Methods on PipelineOrchestrator**: `__init__()`, `run_phase_1(raw_text, source)`, `run_phase_2(news_event)`, `run_phase_3(expectations)`, `run_phase_4(behaviors)`, `run_phase_5(impact_profile, news_event)`, `run_phase_6(validation_record, impact_profile, news_event)`, `run_phase_7(signal_record, market_price)`, `run_full_pipeline(raw_text, source, market_price)`, `get_pipeline_status()`
- **Imports**: All 7 phase packages

#### `pipeline_bridge.py` (545 lines)
- **Classes**: `APIKeyManager` (Singleton pattern), `UnifiedResult(dataclass)`, `PipelineBridge`
- **PipelineBridge modes**: `engine_only`, `phase_only`, `hybrid`
- **Methods**: `__init__(mode)`, `process(text, source, market_price)`, `_run_engine(text, source, market_price)`, `_run_phases(text, source, market_price)`, `_run_hybrid(text, source, market_price)`, `get_status()`

---

### B.2 `engine/` — Core Cognitive Engine

#### `cognitive_market_system.py` (431 lines)
- **Class**: `CognitiveMarketSystem`
- **Methods**: `__init__(config)`, `ingest_news(raw_text, source, timestamp)`, `interpret_cognitively(news_event)`, `compute_collision(participant_states)`, `translate_to_signal(collision_result)`, `process_news_event(raw_text, source, timestamp, market_price)`, `execute_signal(signal, market_price)`, `close_signal(signal_id, exit_price)`, `get_system_status()`
- **Imports**: `engine.core_cognitive_structures`, `engine.expectation_collision_engine`, `engine.tradable_signal_translator`, `engine.participant_models`, `nlp_engine.DeepNLPParser`, `storage.KnowledgeGraph`

#### `core_cognitive_structures.py` (~450 lines)
- **Enums**: `TemporalFocus` (IMMEDIATE/SHORT_TERM/MEDIUM_TERM/LONG_TERM), `NarrativeShift` (CONTINUATION/ESCALATION/REVERSAL/NEW_THEME), `LatencyClass` (MICROSECONDS/MILLISECONDS/SECONDS/MINUTES/HOURS/DAYS), `CapitalScale` (RETAIL/INSTITUTIONAL/SOVEREIGN)
- **Dataclasses**: `LinguisticShockVector` (magnitude, direction, uncertainty, temporal_focus, narrative_shift), `CognitiveState` (attention_level, uncertainty, narrative_frame, dominant_emotion, cognitive_load), `ExpectationVector` (direction, magnitude, confidence, time_horizon, volatility_expectation), `BehaviorIntention` (action_type, urgency, size_fraction, condition), `ParticipantProfile` (name, type, latency_class, capital_scale, risk_tolerance, cognitive_biases), `ParticipantResponse` (profile, expectation, behavior_intention, reasoning), `NewsEvent` (event_id, raw_text, source, timestamp, linguistic_shock_vector, parsed_entities, narrative_type, temporal_markers, uncertainty_markers, contradiction_pairs, semantic_claims, narrative_types, actors, ambiguity_score, participant_interpretations)

#### `expectation_collision_engine.py` (~520 lines)
- **Dataclasses**: `ExpectationCollisionMetrics`, `MarketStressVector`
- **Class**: `ExpectationCollisionEngine`
- **9-step `compute_collision()` pipeline**: 1. Extract expectations → 2. Compute directional disagreement → 3. Compute magnitude divergence → 4. Detect temporal misalignment → 5. Compute volatility expectation spread → 6. Check for unanimous consensus → 7. Calculate market stress → 8. Detect regime change signals → 9. Produce collision summary

#### `participant_models.py` (699 lines) — _Engine-layer version_
- **Classes**: `RetailTraderModel`, `HFTModel`, `HedgeFundModel`, `BankModel`, `MarketMakerModel`
- **Each has**: `interpret(news_event)` → `ParticipantResponse`
- **Registry**: `PARTICIPANT_REGISTRY` dict mapping types to model classes
- **Factory**: `create_participant_response(participant_type, news_event)`

#### `tradable_signal_translator.py` (~540 lines)
- **Enums**: `SignalType` (LONG/SHORT/HEDGE/FLATTEN/WAIT), `ConfidenceLevel` (HIGH/MEDIUM/LOW/INSUFFICIENT), `ExecutionMode` (AGGRESSIVE/NORMAL/PASSIVE)
- **Dataclass**: `TradableSignal` (signal_type, confidence, entry_conditions, exit_conditions, position_size_fraction, stop_loss_pct, take_profit_pct, max_holding_period, reasoning)
- **Class**: `TradableSignalTranslator`
- **Multi-gate `translate(collision_result)` pipeline**: Confidence gate → Direction gate → Sizing gate → Risk gate → Signal assembly

#### `real_data_adapter.py` (~130 lines)
- **Class**: `RealDataProvider`
- **Methods**: `get_price(asset)` (CoinGecko free API), `get_news()` (RSS feeds)

---

### B.3 `config/`

#### `system_config.py` (394 lines)
- **8 Dataclasses**: `NewsIngestionConfig`, `NLPConfig`, `CognitiveEngineConfig`, `StorageConfig`, `TradingConfig`, `AlertConfig`, `DashboardConfig`, `SystemConfig`
- **Globals**: `SYSTEM_CONFIG`, `get_config()`, `reload_config()`
- **Notable defaults**: `initial_capital=100000`, `max_position_pct=0.15`, `stop_loss_pct=0.02`, `take_profit_pct=0.04`, `max_open_positions=5`

#### `logging_config.py` (~80 lines)
- **Functions**: `setup_logging(log_level, log_dir)`, `get_logger(name)`
- Rotating file handler + console handler

---

### B.4 `shared/`

#### `__init__.py` (64 lines)
- **Canonical Enums**: `ParticipantType` (BANK/HEDGE_FUND/HFT/MARKET_MAKER/RETAIL), `TimeHorizon` (MICROSECONDS/MILLISECONDS/SECONDS/MINUTES/HOURS/DAYS/WEEKS/MONTHS/YEARS), `RiskTolerance` (ULTRA_LOW/LOW/MEDIUM/HIGH/ADAPTIVE), `DirectionType` (UP/DOWN/SIDEWAYS/VOLATILE)

---

### B.5 `streaming/`

#### `event_bus.py` (~280 lines)
- **Dataclass**: `Event` (event_type, data, timestamp, priority, source)
- **Class**: `EventTypes` — string constants for all event types
- **Class**: `EventBus` — pub/sub system
- **Methods**: `subscribe(event_type, handler, priority)`, `publish(event)`, `publish_async(event)`, `get_dead_letters()`, `replay(event_type, since)`

#### `pipeline.py` (647 lines)
- **Class**: `StreamingPipeline`
- **7 stages**: news_ingestion → nlp_processing → cognitive_modeling → behavior_translation → impact_modeling → validation → signal_generation
- **Methods**: `__init__()`, `process(raw_text, source, market_price)`, `_stage_1_ingest()`, `_stage_2_nlp()`, `_stage_3_cognitive()`, `_stage_4_behavior()`, `_stage_5_impact()`, `_stage_6_validate()`, `_stage_7_signal()`, `get_pipeline_metrics()`

---

### B.6 `storage/`

#### `database.py` (605 lines)
- **Class**: `DatabaseManager`
- **9 SQLite tables**: `news_events`, `signals`, `positions`, `trades`, `performance`, `model_credibility`, `validation_records`, `alert_history`, `system_metrics`
- **Methods**: `__init__(db_path)`, `store_news_event(event)`, `store_signal(signal)`, `store_position(position)`, `store_trade(trade)`, `get_signal_history(limit)`, `get_performance_summary()`, `get_active_positions()`, `store_model_credibility(cred)`, `get_model_credibilities()`, `store_validation_record(record)`, `vacuum()`, `get_table_sizes()`

#### `knowledge_graph.py` (641 lines)
- **Class**: `KnowledgeGraph` — NetworkX DiGraph with JSON persistence
- **40+ seed entities**: Federal_Reserve, ECB, BoJ, etc.
- **Methods**: `__init__(persist_path)`, `add_entity(name, type, attrs)`, `add_relationship(from, to, type, weight)`, `get_entity(name)`, `get_relationships(entity)`, `get_influence_chain(entity, depth)`, `find_related_entities(entity, relation_type)`, `update_from_news_event(event)`, `get_graph_stats()`, `save()`, `load()`, `get_entity_importance(name)`, `find_shortest_path(from, to)`

---

### B.7 `nlp_engine/` — NLP Processing Core

#### `deep_nlp_parser.py` (1303 lines)
- **Dataclasses**: `EntityMention`, `SemanticTriple`, `SentenceAnalysis`, `DeepParseResult`
- **Enum**: `NarrativeIntent` (INFORM/WARN/REASSURE/SIGNAL_POLICY/CRISIS_MANAGE/DEFLECT/TRIAL_BALLOON/LEAK/PROPAGANDA)
- **Class**: `DeepNLPParser`
- **Models loaded**: spaCy `en_core_web_sm`, FinBERT (`ProsusAI/finbert` or `distilbert-base-uncased-finetuned-sst-2-english`), Zero-shot (`facebook/bart-large-mnli`), Embeddings (`sentence-transformers/all-MiniLM-L6-v2`)
- **Core Methods**: `parse(text)` → `DeepParseResult`, `_analyze_sentences(text)`, `_classify_narrative(text)` (12 narrative types), `_detect_intent(text)` (8 intents), `_compute_document_metrics(sentences)`, `_extract_key_phrases(sentences, entities, triples)`, `_compute_embeddings(text, sentences)`
- **Advanced Methods**: `resolve_coreferences(texts)` (pronoun resolution: recency + gender/number + syntactic roles), `extract_temporal_timeline(texts)` (9 temporal pattern types: absolute_date, relative_time, relative_offset, temporal_anchor, frequency, sequence_marker, duration, deadline; chronological sorting, acceleration detection, temporal clustering, event velocity), `compute_similarity(text1, text2)` (embedding cosine or Jaccard fallback)
- **Certainty Analysis**: `HEDGE_WORDS` (may, might, possibly, potentially, etc.), `BOOST_WORDS` (will, shall, definitely, certainly, etc.), conditional/negation/question detection per sentence

#### `advanced_nlp.py` (801 lines)
- **Class**: `MultiLingualFinancialNLP` — 8 language patterns (en, zh, ja, ko, de, fr, es, ar)
  - **Methods**: `detect_language(text)`, `translate_to_english(text, source_lang)` (MarianMT or keyword fallback), `process_text(text)`
- **Class**: `FinancialEmbeddings` — FINANCIAL_VOCAB (30+ terms with domain/intensity/direction)
  - **Methods**: `embed_text(text)` (hash-based 128-dim), `get_financial_sentiment(text)` (FinBERT or keyword), `semantic_similarity(text1, text2)`, `classify_domain(text)`
- **Class**: `FinancialEventExtractor` — 8 EVENT_PATTERNS (rate_decision, earnings, merger_acquisition, regulatory, geopolitical, labor, product_launch, macro_data)
  - **Methods**: `extract_events(text)` (structured WHO-WHAT-WHOM-WHEN-RESULT), `extract_event_chain(texts)` (chronological linking)
- **Class**: `AdvancedNLPEngine` — Orchestrator
  - **Methods**: `full_analysis(text)` → combined multilingual + embeddings + event extraction

#### `entity_extraction.py` (~320 lines)
- **Dataclasses**: `FinancialEntity`, `GeopoliticalEntity`, `EntityRelation`
- **Class**: `EntityExtractor`
- **Methods**: `extract_from_text(text)`, `_extract_financial_entities()`, `_extract_geopolitical()`, `_extract_relations()`, `_classify_entity_type()`

#### `contradiction_detector.py` (381 lines)
- **Class**: `ContradictionDetector`
- **Dataclass**: `ContradictionResult` (claim_a, claim_b, source_a, source_b, contradiction_type, confidence, reasoning, severity)
- **Enum**: `ContradictionType` (NEGATION/ANTONYM/NUMERIC/STANCE)
- **Methods**: `detect(claim_a, claim_b, source_a, source_b)`, `_check_negation_contradiction()`, `_check_antonym_contradiction()`, `_check_numeric_contradiction()` (>20% difference threshold)
- **Data**: `NEGATION_PATTERNS`, antonym pairs (rise/fall, increase/decrease, strong/weak, hawkish/dovish, etc.)

#### `intent_detector.py` (464 lines)
- **Enums**: `CommunicationIntent` (6 types), `StrategicIntent` (9 types: ROUTINE/GUIDANCE/WARNING/REASSURANCE/TRIAL_BALLOON/LEAK_STRATEGIC/DISTRACTION/PUMP/SHORT_ATTACK), `TargetAudience` (5 types), `TimingIntent` (7 types: MARKET_HOURS/AFTER_HOURS/FRIDAY_DUMP/WEEKEND/BREAKING/DISTRACTION/EMBARGO_LIFT)
- **Dataclass**: `IntentAnalysis`
- **Class**: `IntentDetector`
- **Methods**: `analyze(text, source, publish_time, market_hours)`, `_detect_communication_intent()`, `_detect_strategic_intent()`, `_detect_target_audience()`, `_detect_timing_intent()`, `_detect_manipulation()`, `_assess_credibility()`, `_detect_beneficiaries()`, `_detect_hidden_agenda()`, `_generate_reasoning()`
- **Data**: `SOURCE_CREDIBILITY` dict (reuters 0.9, bloomberg 0.88, wsj 0.85, down to cnbc 0.55, twitter 0.25), `MANIPULATION_PATTERNS` (5 categories), `BENEFICIARY_PATTERNS`

#### `nlp_extensions.py` (675 lines)
- **Dataclasses**: `EarningsCallSection`, `ToneShift`, `EarningsCallAnalysis`
- **Class**: `EarningsCallAnalyzer`
- **Methods**: `analyze_transcript(transcript, company)`, `_split_prepared_qa(transcript)`, `_determine_guidance_direction(guidance_texts)`, `_extract_speakers(text)` (per-speaker sentiment)
- **Constants**: `HEDGING_PHRASES`, `FORWARD_GUIDANCE_PATTERNS`, `POSITIVE_WORDS`, `NEGATIVE_WORDS`
- **Risk signal patterns** (10): material weakness, restatement, going concern, SEC investigation, litigation, covenant breach, impairment, executive departure, supply chain risk, cybersecurity

---

### B.8 `news_model/`

#### `news_event.py` (~240 lines)
- **Enums**: `NarrativeType` (9: MACRO_POLICY/EARNINGS/GEOPOLITICAL/CREDIT_RISK/LIQUIDITY/REGULATORY/TECHNOLOGY/SENTIMENT_SHIFT/UNKNOWN), `TemporalType` (5), `ConfidenceLevel` (3)
- **Class**: `NewsEvent` — structured event container with immutable raw_text

#### `parser.py` (~280 lines)
- **Class**: `NewsEventParser`
- **Methods**: `parse(timestamp_utc, source, raw_text)` → `NewsEvent`, `_extract_actors(text)`, `_extract_temporal_markers(text)`, `_extract_semantic_claims(text)`, `_classify_narratives(text)`, `_calculate_ambiguity(text)`, `_detect_uncertainty(text)`, `_detect_contradictions(text)`

---

### B.9 `news_ingestion/`

#### `news_api_client.py` (~270 lines)
- **Class**: `NewsAPIClient` — NewsAPI.org wrapper (80K+ sources)
- **Methods**: `search_everything(query, from_date, page_size)`, `search_financial_news(hours_back)`, `get_top_headlines(page_size)`, `get_status()`
- **Features**: Response caching, rate limiting (100 req/day free tier)

#### `gdelt_client.py` (307 lines)
- **Dataclasses**: `GDELTEvent`, `GDELTArticle`
- **Class**: `GDELTClient`
- **Methods**: `search_articles(query, timespan, max_records)`, `search_financial_news(hours_back, max_records)`, `get_events(query, max_records)`, `get_status()`

#### `rss_reader.py` (~280 lines)
- **Class**: `RSSReader` — 14 pre-configured financial feeds (Reuters, Bloomberg, CNBC, FT, WSJ, MarketWatch, Yahoo Finance, Seeking Alpha, ZeroHedge, Economist, BBC Business, NYT Business, Guardian Business, AP Business)
- **Dataclass**: `RSSArticle`
- **Methods**: `read_feed(url)`, `read_all_financial()`, `add_feed(name, url)`, `get_status()`

#### `news_aggregator.py` (668 lines)
- **Dataclass**: `UnifiedArticle` (with content_hash for dedup)
- **Class**: `NewsAggregator`
- **Methods**: `__init__(sources)`, `fetch_latest(query, hours_back, max_per_source, financial_only)`, `_convert_newsapi()`, `_convert_gdelt()`, `_convert_rss()`, `_deduplicate(articles)` (content hash + 70% title word overlap), `async_fetch_latest()` (ThreadPoolExecutor for async), `_fetch_newsapi()`, `_fetch_gdelt()`, `_fetch_rss()`, `get_status()`

---

### B.10 `participant_cognition/` — Phase 2

#### `participant_models.py` (618 lines)
- **Enums**: `ParticipantType`, `TimeHorizon`, `RiskTolerance`, `ObjectiveType` (6: BALANCE_SHEET_PROTECTION/ASYMMETRIC_RETURN/SPREAD_CAPTURE/INVENTORY_STABILITY/DIRECTIONAL_GAIN/NARRATIVE_ALIGNMENT), `InformationPriority` (5), `InterpretationBias` (6: RISK_AVERSE/OPPORTUNITY_SEEKING/LIQUIDITY_PRESERVATION/OVERREACTION/TREND_CONFIRMATION/MEAN_REVERSION)
- **Dataclasses**: `CognitiveProfile` (6 dimensions), `ActionLikelihoods` (8 action probabilities: increase_exposure, decrease_exposure, increase_hedging, hold_position, wait_for_clarity, panic_action, widen_spreads, pull_liquidity), `ParticipantExpectation`
- **Class**: `Participant`
  - **Methods**: `interpret(news_event)` → `ParticipantExpectation`, `_interpret_through_bias(event, bias)`, `_calculate_belief_shift(event, bias_result)`, `_assess_uncertainty(event)`, `_determine_urgency(event)`, `_calculate_actions(event, belief_shift, uncertainty, urgency)`
  - **Per-type action matrices**: Bank→hedging, HF→asymmetric, HFT→spreads, MM→inventory, Retail→emotional
- **Factory functions**: `create_bank_participant()`, `create_hedge_fund_participant()`, `create_hft_participant()`, `create_market_maker_participant()`, `create_retail_participant()`

---

### B.11 `market_response/` — Phase 3

#### `behavior_models.py` (606 lines)
- **Enums**: `RiskPosture` (REDUCE_RISK/MAINTAIN_RISK/INCREASE_RISK), `LiquidityPosture` (PROVIDE_LIQUIDITY/MAINTAIN_LIQUIDITY/REDUCE_LIQUIDITY), `ExposureIntent` (INCREASE_EXPOSURE/MAINTAIN_EXPOSURE/DECREASE_EXPOSURE), `TimeUrgency` (IMMEDIATE/SAME_DAY/MULTI_DAY/PASSIVE)
- **Dataclasses**: `ParticipantConstraints` (max_position_size, mandate, capital_available, leverage_limit, no_short_sale), `ProbabilisticOutcome` (label, likelihood), `BehaviorProfile`
- **Class**: `BehaviorTranslator`
  - **Methods**: `translate(expectation, constraints)` → `BehaviorProfile`, `_determine_risk_posture()`, `_determine_liquidity_posture()`, `_determine_exposure_intent()`, `_determine_urgency()`, `_determine_optionality()`, `_identify_contradictions()`, `_generate_reasoning()`, `_calculate_overall_confidence()`, `_determine_fallbacks()`
- **Factory**: `create_behavior_translator()`

---

### B.12 `market_impact/` — Phase 4

#### `market_impact_models.py` (1151 lines)
- **Enums**: `LiquidityImpactType` (4), `VolatilityImpactType` (4), `SpreadImpactType` (3), `OrderFlowImpactType` (4), `PriceDynamicsType` (4), `RegimeImpactType` (3)
- **Dataclasses**: `ImpactTiming` (onset_delay, peak_window, decay_time, persistence), `ImpactItem`, `AggregatedBehavior`, `MarketImpactProfile`
- **Class**: `BehaviorAggregator`
  - **Methods**: `aggregate(behaviors)` → `AggregatedBehavior`, `_calculate_disagreement()` (std dev), `_calculate_concentration()` (one-sidedness), `_identify_divergence()` (distance from average)
- **Class**: `ImpactTranslator`
  - **Methods**: `translate(agg_behavior, event_id)` → `MarketImpactProfile`, `_identify_drivers()` (9 driver rules), `_generate_liquidity_impacts()`, `_generate_volatility_impacts()`, `_generate_spread_impacts()`, `_generate_order_flow_impacts()`, `_generate_price_impacts()`, `_generate_regime_impacts()`, `_apply_non_linearity()` (threshold/saturation/feedback detection), `_calculate_stress()`, `_calculate_confidence()`, `_generate_reasoning()`
- **Class**: `MarketImpactCalculator` — Unified pipeline
  - **Methods**: `calculate(behaviors, event_id)`, includes Kyle's Lambda approximation

---

### B.13 `reality_validation/` — Phase 5

#### `market_reality.py` (1049 lines)
- **Enums**: `NewsEventType`, `RegimeType`, `ValidityScore` (ACCURATE/NOISY/INACCURATE)
- **Dataclasses**: `NewsUnderstanding`, `ParticipantExpectation`, `PredictedMarketState`, `OHLCV`, `MarketSnapshot`, `MarketReality`, `DirectionalValidity`, `VolatilityValidity`, `TimingValidity`, `ParticipationValidity`, `RegimeValidity`, `ValidationRecord`, `ModelCredibility`, `CredibilityDataset`, `FailurePattern`, `FailureAnalysis`
- **Class**: `MarketDataProvider`
  - **Methods**: `get_price_around_event(asset, timestamp)`, `_fetch_coingecko()`, `_fetch_yfinance()`, `_fetch_from_cache()`, `build_market_reality(event_id, timestamp, snapshots)`
- **Class**: `RealityValidator`
  - **5 validation dimensions**: `validate_directional_accuracy()` → `DirectionalValidity`, `validate_volatility_accuracy()` → `VolatilityValidity`, `validate_timing_accuracy()` → `TimingValidity` (tolerances: shock 30s, peak 5min, recovery 15min), `validate_participation_match()` → `ParticipationValidity`, `validate_regime_shift()` → `RegimeValidity` (temporary ≤1d, semi-persistent ≤7d, structural >7d)
  - **Composite**: `create_validation_record()` — weighted (direction 0.3, vol 0.2, timing 0.2, participation 0.15, regime 0.15)
  - **Statistical testing**: `test_statistical_significance()` — one-sided binomial test + z-score + p-value + one-sample t-test
  - **Research methods**: `get_credibility_report()`, `credibility_dataset`, `failure_analysis`

---

### B.14 `signal_auth/` — Phase 6

#### `signal_authorization.py` (778 lines)
- **Enums**: `SignalDirection` (BUY/SELL/NEUTRAL/UNCERTAIN), `SignalStatus` (APPROVED/FILTERED/PENDING_VALIDATION), `VolatilityImpact` (LOW/MEDIUM/HIGH/EXTREME), `ReactionHorizon` (IMMEDIATE/SHORT_TERM/MEDIUM_TERM/LONG_TERM)
- **Dataclasses**: `NewsMetadata`, `ValidationMetrics`, `PredictionFromPhase4`, `ParticipantWeights`, `NormalizedSignal`, `SignalRecord`, `TrustWeightHistory`
- **Class**: `SignalAuthorizer`
  - **5-step pipeline**:
    1. `assign_trust_score(news, validation)` — base from historical accuracy per event type + participant model accuracies
    2. `filter_signal(trust, validation, threshold=0.6)` — threshold gate
    3. `weight_signal_strength(trust, validation, prediction, news)` — event-type base × trust × participant-weighted confidence
    4. `determine_signal_direction(validation, news, prediction)` — HFT/HF consensus
    5. `determine_volatility_impact(validation, prediction, news)` — intensity × vol prediction × accuracy
  - **Additional**: `determine_reaction_horizon()`, `normalize_signals(signals, now)` (weighted vote, conflict detection), `authorize_signal(news, validation, prediction)` (full pipeline, 4h expiry), `get_approved_signals()`, `update_participant_weights()`, `get_signal_statistics()`

---

### B.15 `execution/` — Phase 7

#### `execution_nexus.py` (634 lines)
- **Enums**: `ExecutionStatus` (PENDING/FILLED/PARTIAL/REJECTED/CANCELLED), `RiskLevel` (GREEN/YELLOW/RED/BLACK)
- **Dataclasses**: `ApprovedSignal`, `ExecutedOrder`, `PositionSnapshot`
- **Class**: `ExecutionNexus`
  - **Config**: $100K paper capital, 15% max position, 2% max daily loss, 5% drawdown circuit breaker
  - **Methods**: `size_order(signal, price)` (Kelly-inspired: strength × confidence × max_position, capped 15%), `check_position_limits()` (3 max open, daily loss, circuit breaker), `route_order(signal)` (AGGRESSIVE market/<1s vs PASSIVE limit/<5min), `execute_signal(signal, current_price, current_time)`, `get_position_snapshot()`, `check_exit_conditions(position, current_price)` (2% stop, 3% target), `get_execution_report()`
- **Function**: `execute_from_phase_6_signal(signal_record, price, time)` — Phase 6→7 interface

---

### B.16 `decision_system/`

#### `decision_engine.py` (622 lines)
- **Enums**: `DecisionAction` (BUY/SELL/HOLD/REDUCE/HEDGE/EMERGENCY_EXIT/WATCH), `MarketRegime` (CALM/TRENDING/VOLATILE/CRISIS/TRANSITIONING)
- **Dataclass**: `CognitiveSignal`, `DecisionPacket` (decision_id, action, reasoning_chain, risk_gates_triggered, hidden_truth_flags, suggested_position_pct, max_position_pct, stop_loss_pct, take_profit_pct, risk_reward_ratio, max_risk_pct, overall_confidence)
- **Class**: `DecisionEngine`
  - **Methods**: `decide(signals)` → `DecisionPacket`, `_aggregate_signals()`, `_check_risk_gates()`, `_check_hidden_truth()`, `_determine_action(packet, strength, agreement)`, `_compute_sizing(packet, strength, agreement)` (Kelly-inspired, regime-adjusted, half-Kelly), `_compute_risk_levels(packet, strength)` (volatility-adjusted stops/targets), `_finalize(packet)`, `get_recent_decisions(n)`, `get_performance_summary()`

#### `human_review_queue.py` (~350 lines)
- **Class**: `HumanReviewQueue`
- **6 escalation rules**: high_value (>$50K), low_confidence (<0.4), hidden_truth_flagged, regime_crisis, contradictory_signals, novel_event_type
- **Methods**: `submit_for_review(decision_packet)`, `approve(review_id)`, `reject(review_id)`, `get_pending_reviews()`, `get_review_stats()`

---

### B.17 `hidden_truth/` — Manipulation Detection

#### `timing_analyzer.py` (~350 lines)
- **Class**: `TimingAnalyzer`
- **Data**: 11 `RECURRING_EVENTS` (FOMC, NFP, CPI, GDP, ECB, BoJ, Retail Sales, ISM, Fed Minutes, Options Expiry, Quad Witching), 6 market sessions (US pre-market, US market, US after-hours, Asia, Europe, overlap)
- **Methods**: `analyze_timing(timestamp, event_type)`, `detect_suspicious_timing(articles)`, `get_upcoming_events()`, `is_market_hours(timestamp)`

#### `advanced_detection.py` (926 lines)
- **Class**: `FilingAnalyzer` — SEC 10-K/10-Q analysis
  - **Methods**: `compare_risk_sections(current, previous)` (diff new/removed/modified risks), `_compare_pr_vs_filing(pr_text, filing_text)` (tone divergence, risk keyword comparison, qualifier density), `_calculate_tone(text)`, `_gunning_fog(text)` (readability index)
- **Class**: `InsiderCorrelationAnalyzer` — Form 4 insider transactions
  - **Dataclasses**: `InsiderTransaction`, `InsiderSentimentCorrelation`
  - **Methods**: `analyze(transactions, news_events, price_data)` (detects: sale_before_bad_news, purchase_before_good_news, transaction_before_earnings, insider_cluster within 5 days)
  - C-suite 1.5x weight, large transactions ($1M+) 1.3x, suspicion scoring 0-1
- **Class**: `SourceNetworkAnalyzer` — Source relationship graph
  - **Dataclasses**: `SourceNode`, `SourceEdge`
  - **Methods**: `build_network(articles)`, `get_echo_chambers()` (co-coverage ≥5 + sentiment corr >0.8 + timing corr >0.6), `_calculate_independence()` (1 - echo_ratio), `get_credibility_ranking()` (0.4×credibility + 0.3×accuracy + 0.3×independence)

#### `cross_source_analyzer.py` (725 lines)
- **Class**: `CrossSourceAnalyzer`
  - **Methods**: `analyze(articles_on_topic)`, `_check_timing(articles)` (coordinated releases: <30s from 3+ unique sources), `_find_conflicts(articles)` (sentiment >0.3 divergence, number conflicts), `_compute_trust_score()` (5-component: diversity 0.25, consistency 0.30, alignment 0.20, conflicts 0.15, coordination 0.10)
  - **SQLite historical database**: `manipulation_patterns` + `source_reliability_history` tables
  - **Methods**: `record_pattern(pattern)`, `record_source_accuracy(source, accurate)`, `get_source_reliability(source)`, `find_similar_patterns(pattern_type, narrative)`, `confirm_pattern(pattern_id, market_impact)`

#### `narrative_tracker.py` (473 lines)
- **Dataclasses**: `NarrativeSnapshot`, `NarrativeEvolution`
- **Class**: `NarrativeTracker`
  - **Methods**: `track(event)`, `get_active_narratives(hours)`, `get_trending(top_n)`, `detect_manufactured_consensus()`, `_compute_intensity()` (recency×0.4 + source×0.3 + sentiment×0.3), `_compute_trend()` (growing/fading/stable/new), `_compute_consensus()` (variance-based), `_compute_credibility()` (multi-source×0.4 + consistency×0.3 + stability×0.3), `get_summary()`

---

### B.18 `scenario_engine/`

#### `scenario_generator.py` (~547 lines)
- **Dataclasses**: `ScenarioNode`, `ScenarioTree`
- **Class**: `ScenarioGenerator`
  - **Methods**: `generate(event_data, max_depth=3)` → `ScenarioTree`, `_create_root(event_data)`, `_expand_node(node)`, `_generate_children(node)`, `_compute_tree_metrics(tree)` (probability-weighted move, max upside/downside, tail risk probability, expected direction), `get_flat_scenarios(tree)` (flatten + sort by probability)

#### `causal_chain.py` (624 lines)
- **Dataclasses**: `CausalEffect` (order, cause, effect, mechanism, direction, magnitude, confidence, delay_hours, affected_assets, affected_participants), `CausalChain` (first_order, second_order, third_order, total_effects, dominant_direction, systemic_risk_score, feedback_loop_detected)
- **Class**: `CausalChainBuilder`
  - **Template dictionaries**: `FIRST_ORDER_TEMPLATES` (rate_hike, rate_cut, inflation_high, geopolitical_crisis, economic_weakness, strong_earnings, generic), `SECOND_ORDER_RULES` (equity_bearish, equity_bullish, usd_strong, usd_weak, oil_spike), `THIRD_ORDER_RULES` (systemic_stress, feedback_loop, policy_response)
  - **Methods**: `build_chain(event_data, max_depth=3)` → `CausalChain`, `_classify_event(event_data)`, `_get_first_order(event_type, event_data)`, `_get_second_order(first_order)`, `_get_third_order(first_order, second_order)`, `_enhance_with_graph(chain, event_data)` (KnowledgeGraph integration), `_compute_chain_metrics(chain)` (dominant direction, systemic risk, feedback loop detection)

#### `monte_carlo.py` (361 lines)
- **Dataclass**: `SimulationResult` (n_simulations, mean_return, median_return, std_dev, skewness, kurtosis, var_95, var_99, cvar_95, max_drawdown, prob_positive, prob_negative, prob_extreme_up, prob_extreme_down, histogram, returns)
- **Class**: `MonteCarloSimulator`
  - **Methods**: `simulate(base_scenario, n_simulations=10000)`, `_compute_stats(returns)`, `_build_histogram(sorted_returns, n_bins=10)`

#### `scenario_extensions.py` (687 lines)
- **Class**: `CounterfactualAnalyzer`
  - **Dataclass**: `CounterFactual`
  - **Methods**: `register_event_impact(event_id, asset_impacts)`, `analyze_counterfactual(event_id, realized_returns)`, `compare_counterfactuals(event_ids, realized_returns)`, `sensitivity_analysis(event_id, realized_returns, scale_range)` — vary impact magnitude
- **Dataclasses**: `ScenarioWeight`, `OptimizedPortfolio`
- **Class**: `ScenarioPortfolioOptimizer` — 4 optimization methods:
  - `optimize(scenarios, assets, method, constraints)` → `OptimizedPortfolio`
  - `_minimax_optimize()` — maximize minimum return (grid search on simplex)
  - `_expected_utility_optimize()` — maximize E[R] - (λ/2)×Var[R]
  - `_risk_parity_optimize()` — inverse-volatility weights
  - `_cvar_optimize()` — minimize 5th percentile CVaR
  - `_generate_weight_candidates()` (full grid for n≤4, random perturbation for n>4)
  - `_calculate_risk_budget()` — marginal risk contribution per asset

---

### B.19 `alpha_models/`

#### `alpha_signals.py` (1667 lines)
**12 alpha signal generators + unified aggregator:**

| # | Class | Signal Source | Key Method |
|---|-------|--------------|------------|
| 1 | `PositioningAnalyzer` | CFTC COT + options OI | `analyze()` → contrarian z-score |
| 2 | `OrderFlowAnalyzer` | L2 order book + trade tape | `analyze()` → cumulative delta, iceberg detection |
| 3 | `VolatilitySurfaceAnalyzer` | Options IV surface | `analyze()` → 25d risk reversal, butterfly, term structure |
| 4 | `CrossAssetLeadLag` | Cross-correlation | `analyze()` → rolling lag correlation |
| 5 | `SentimentExtremesAnalyzer` | CNN Fear/Greed, AAII, P/C, VIX | `analyze()` → composite 0-100 |
| 6 | `FlowOfFundsAnalyzer` | ETF+mutual fund flows | `analyze()` → 5-sector flow tracking |
| 7 | `CalendarEffectsAnalyzer` | Calendar anomalies | `detect_active_effects()` → 7 effects |
| 8 | `EarningsRevisionTracker` | Analyst EPS revisions | `analyze()` → revision momentum |
| 9 | `InsiderTradingAnalyzer` | SEC Form 4 | `analyze()` → title-weighted signals (CEO 3x) |
| 10 | `CreditMarketSignals` | CDS, HY bonds, repo | `analyze()` → composite credit stress |
| 11 | `MacroSurpriseIndex` | Economic indicator surprises | `analyze()` → Citigroup-style index, 11 weights |
| 12 | `CentralBankBalanceSheet` | Fed/ECB/BoJ/PBoC | `analyze()` → QE/QT regime, global liquidity pulse |

- **Class**: `AlphaSignalAggregator`
  - **12 source weights**: positioning 0.12, order_flow 0.12, credit 0.10, vol_surface 0.10, macro_surprise 0.10, central_bank 0.08, lead_lag 0.08, sentiment 0.08, flow_of_funds 0.07, insider 0.06, calendar 0.05, earnings_revision 0.04
  - **Methods**: `aggregate()` → weighted conviction, agreement ratio, horizon breakdown

#### `nlp_alpha_signals.py` (754 lines)
**5 NLP-derived alpha generators:**

| # | Class | Signal Source |
|---|-------|-------------|
| 1 | `NarrativeMomentumAlpha` | Narrative intensity acceleration |
| 2 | `ContradictionAlpha` | Cross-source contradiction detection |
| 3 | `InstitutionalLanguageAlpha` | Institutional vs retail language patterns |
| 4 | `TemporalClusteringAlpha` | News timing cluster analysis |
| 5 | `SentimentDivergenceAlpha` | Headline vs body sentiment divergence |

- **Class**: `NLPAlphaHub` — Orchestrator with `generate_signals(articles)`, aggregated composite with weights

#### `structural_alpha.py` (948 lines)
**5 structural alpha models:**

| # | Class | Signal Source |
|---|-------|-------------|
| 1 | `MicrostructureAlpha` | Bid-ask bounce, Kyle's lambda, order flow toxicity |
| 2 | `RealizedVolAlpha` | Realized vs implied vol, vol-of-vol, term structure |
| 3 | `FundingRateAlpha` | Perpetual futures funding rate mean-reversion |
| 4 | `OnChainAlpha` | Blockchain metrics (exchange flows, whale movements) |
| 5 | `LiquidityPremiumAlpha` | Amihud ratio, turnover, bid-ask spread premium |

- **Class**: `StructuralAlphaEngine` — Orchestrator with `analyze()`, weighted composite

---

### B.20 `multi_asset/`

#### `correlation_engine.py` (~420 lines)
- **Class**: `CorrelationEngine`
- **21 BASELINE_CORRELATIONS**: BTC-ETH 0.85, BTC-SPX 0.45, BTC-GOLD 0.20, etc.
- **Methods**: `update(asset_pair, returns)`, `get_correlation(asset1, asset2)`, `detect_anomalies()` (>2σ deviation from baseline), `get_regime_correlations()`, `get_contagion_risk()`

#### `contagion_model.py` (~370 lines)
- **Class**: `ContagionModel`
- **19 TRANSMISSION_CHANNELS**: equity→credit, credit→funding, USD→EM, oil→inflation, etc.
- **20 SUSCEPTIBILITY ratings**: BTC 0.7, ETH 0.75, SPX 0.5, etc.
- **Methods**: `simulate_contagion(shock_asset, shock_magnitude)`, `get_transmission_path(from_asset, to_asset)`, `get_systemic_risk_score()`

---

### B.21 `market_intelligence/`

#### `intelligence_models.py` (1373 lines)
**9 advanced market intelligence models:**

| # | Class | Capability |
|---|-------|-----------|
| 1 | `AlternativeDataFusion` | 8 alt data categories → z-score composite |
| 2 | `RegimeDetector` | HMM-inspired 5 regimes, CUSUM changepoint |
| 3 | `CrowdingRiskDetector` | Short squeeze, factor crowding, ETF concentration |
| 4 | `LiquidityForecaster` | Volume/spread/depth + event proximity, flash crash conditions |
| 5 | `CrossMarketArbitrage` | Basis trade, ETF NAV deviation, put-call parity |
| 6 | `SentimentDecayModel` | Exponential decay, regime-dependent half-lives |
| 7 | `InformationCascadeDetector` | Sequential alignment >80%, declining independence |
| 8 | `ReflexivityModel` | Soros-style narrative-price coupling, reversal prediction |
| 9 | `DarkPoolAnalyzer` | Dark pool volume %, block clustering, VWAP divergence |

- **Class**: `MarketIntelligenceHub` — Orchestrator
  - **Methods**: `full_scan(market_data)`, `risk_summary()` (critical/elevated/moderate/normal)

---

### B.22 `infrastructure/`

#### `infra_layer.py` (1254 lines)
**7 production infrastructure components:**

| # | Class | Purpose |
|---|-------|---------|
| 1 | `MessageQueue` | Redis/Kafka/in-memory pub/sub + dead letter queue |
| 2 | `TimeSeriesDB` | InfluxDB/TimescaleDB/SQLite + retention policy |
| 3 | `ModelRegistry` | MLflow-style versioning, stage transitions, A/B testing |
| 4 | `FeatureStore` | Online/offline stores, point-in-time joins, freshness SLAs |
| 5 | `CICDPipeline` | 6-stage (lint→test→model_validation→build→deploy_staging→deploy_production), GitHub Actions + GitLab CI generation |
| 6 | `MonitoringSystem` | Prometheus-compatible (Counter/Gauge/Histogram/Summary), 12 default metrics, 5 alert rules, Prometheus exposition format, Grafana dashboard JSON export |
| 7 | `APILayer` | FastAPI REST+WebSocket, 13 routes, API key auth, rate limiting, OpenAPI 3.0 spec |

- **Class**: `InfrastructureManager` — Orchestrator
  - **Methods**: `initialize_all()`, `health_report()`

**API Routes (port 8000)**:
`/health`, `/signals/latest`, `/signals/history`, `/intelligence/{asset}`, `/regime/current`, `/nlp/analyze`, `/events/extract`, `/alpha/scan`, `/risk/summary`, `/models/list`, `/features/{entity}`, `/metrics`, `ws:/signals` (WebSocket)

---

### B.23 `economics/`

#### `economic_models.py` (689 lines)
- **Classes**: `PhillipsCurve`, `YieldCurve`, `TaylorRule`, `GDPImpact`, `ExchangeRate`
- **PhillipsCurve**: `estimate_inflation(unemployment, expected_inflation)`, `get_nairu()`, `natural_rate_shift()`
- **YieldCurve**: `get_yield(maturity)`, `is_inverted()`, `get_term_premium()`, `recession_probability()`
- **TaylorRule**: `recommended_rate(inflation, output_gap)`, `deviation_from_actual(current_rate)`
- **GDPImpact**: `estimate_gdp_impact(rate_change, fiscal_change)`, ISM/PMI analysis
- **ExchangeRate**: `estimate_impact(rate_differential, trade_balance)`, PPP deviation
- **Class**: `EconomicAnalyzer` — Orchestrator combining all 5 models
  - **Methods**: `full_analysis(macro_data)`, `get_recession_indicators()`

---

### B.24 `backtesting/`

#### `backtest_engine.py` (778 lines)
- **Class**: `PositionTracker` — Position lifecycle management
  - **Methods**: `open_position(signal)`, `close_position(position_id, price)`, `get_open_positions()`, `mark_to_market(prices)`
- **Class**: `PerformanceAnalytics`
  - **Methods**: `compute(trades)` → Sharpe ratio, Sortino ratio, max drawdown, win rate, profit factor, avg win/loss, expectancy
- **Class**: `EventReplayEngine` — Replay historical news events
  - **Methods**: `load_events(events)`, `replay(start, end, speed)`, `get_event_at(timestamp)`
- **Class**: `BacktestRunner` — Unified backtest orchestrator
  - **Config**: $100K capital, 10% max position, 2% stop loss, 4% take profit
  - **Methods**: `run(events, price_data)` → backtest results with performance metrics

---

### B.25 `learning/`

#### `feedback_loop.py` (456 lines)
- **Dataclasses**: `PredictionRecord`, `ModelCredibility`
- **Class**: `FeedbackLoop`
  - **Methods**: `record_prediction(event_type, participant_type, prediction, actual_outcome)`, `update_credibility(participant_type, accuracy)`, `get_model_weights()`, `get_accuracy_by_event_type()`, `get_improvement_recommendations()`, `_save_to_storage()`, `_load_from_storage()`

---

### B.26 `data/`

#### `market_data_feed.py` (~290 lines)
- **SEED_PRICES**: BTC=65000, ETH=3500, SPX=5200, GOLD=2300, etc.
- **Class**: `MarketDataFeed`
  - **Methods**: `__init__(use_live)`, `get_market_snapshot(asset)` → (price, bid, ask, volume, timestamp), `_fetch_live_price(asset)` (CoinGecko), `_simulate_price(asset)` (Geometric Brownian Motion)

---

### B.27 `dashboard/`

#### `app.py` (~350 lines)
- **7 Streamlit pages**: Overview, Live Feed, Signal History, Market Intelligence, Hidden Truth, Backtesting, System Health
- **Port**: 8501
- **Imports**: `streamlit`, `engine`, `storage`, `alpha_models`, `hidden_truth`

---

### B.28 `advanced/`

#### `geopolitical_risk.py` (~300 lines)
- **Class**: `GeopoliticalRiskScorer`
- **8 event types**: war, sanctions, trade_war, regime_change, terrorism, cyber_attack, territorial_dispute, nuclear_threat
- **6 regions** with impact multipliers, **7 sectors** with exposure scores
- **Methods**: `score(event_type, region, affected_sectors)`, `get_escalation_probability()`, `historical_comparison()`

#### `llm_analyzer.py` (~250 lines)
- **Class**: `LLMAnalyzer`
- **Model**: GPT-4o-mini (configurable)
- **Methods**: `analyze_sentiment(text)`, `extract_implications(text)`, `generate_scenario(context)`, `compare_narratives(texts)`
- **Fallback**: Keyword-based analysis when API unavailable

#### `social_media.py` (~340 lines)
- **Class**: `SocialMediaSentiment`
- **Reddit**: 7 subreddits (wallstreetbets, stocks, investing, cryptocurrency, options, stockmarket, forex), via PRAW
- **Twitter**: 20 tracked tickers, via Tweepy
- **Methods**: `get_reddit_sentiment(subreddit, keyword)`, `get_twitter_sentiment(ticker)`, `get_social_momentum(asset)`, `detect_viral_narratives()`

#### `report_generator.py` (~280 lines)
- **Class**: `ReportGenerator`
- **5 report types**: event_analysis, daily_summary, risk_report, system_health, custom
- **Methods**: `generate(report_type, data)` → formatted markdown, `_event_report()`, `_daily_report()`, `_risk_report()`, `_health_report()`

---

### B.29 `alerts/`

#### `alert_delivery.py` (466 lines)
- **Enum**: `AlertPriority` (LOW/MEDIUM/HIGH/CRITICAL)
- **Dataclass**: `Alert`
- **Class**: `AlertDeliverySystem`
- **Channels**: console, file, webhook, email (SMTP), SMS (Twilio)
- **Methods**: `send_alert(alert)`, `add_channel(name, config)`, `_deliver_console()`, `_deliver_file()`, `_deliver_webhook()`, `_deliver_email()`, `_deliver_sms()`, `get_stats()`, `get_delivery_log()`

---

### B.30 `tests/`

| File | Tests | Phase | Key Assertions |
|------|-------|-------|----------------|
| `test_phase_1.py` | 12 | News Data Model | Raw text immutability, no trading signals, parsing, uncertainty, contradiction, temporal markers, actors, narratives |
| `test_phase_2.py` | 14 | Cognitive Models | 5 participants exist, cognitive profiles complete, same news→different expectations, no prices/signals, deterministic, action likelihoods sum to 1.0 |
| `test_phase_3.py` | 14 | Behavior Translation | Translator exists, constraints impact behavior, probabilistic outcomes, contradictions allowed, no prices/trades, fallbacks, inaction meaningful |
| `test_phase_4.py` | 14 | Market Impact | Aggregator exists, 22 impact type enums, no price direction, time structure, non-linearity, 6 impact categories, disagreement/concentration |
| `test_phase_5.py` | 14 | Reality Validation | No trading signals (research-only), directional/volatility/timing/participation/regime validation, credibility tracking, failure patterns |
| `test_phase_6.py` | 14 | Signal Authorization | Trust assignment, filtering gate, strength weighting, direction determination, signal normalization, expiration, participant weight updates |
| `test_integration.py` | 8 | End-to-end | Bootstrap loads all modules, cognitive engine E2E, streaming pipeline, scenario engine, execution engine, legacy orchestrator, type unification, config paths |

**Total: 90 tests across 7 test files**

---

## (C) Architecture Summary

### C.1 Dual-Pipeline Architecture

The system implements two parallel processing pipelines bridged by `PipelineBridge`:

**Pipeline A — 5-Layer Cognitive Engine** (`engine/`):
```
News → LSV → Cognitive Modeling → Expectation Collision → Tradable Signal
```
- Managed by `CognitiveMarketSystem`
- Uses `LinguisticShockVector` as core data abstraction
- `ExpectationCollisionEngine` computes disagreement across 5 participant models

**Pipeline B — 7-Phase Operational Pipeline** (`legacy_main.py`):
```
Phase 1: News → structured NewsEvent (no interpretation)
Phase 2: NewsEvent → 5 ParticipantExpectations (cognitive models)
Phase 3: Expectations → BehaviorProfiles (with constraints)
Phase 4: Behaviors → AggregatedBehavior → MarketImpactProfile (no prices)
Phase 5: Predictions vs Reality → ValidationRecord (research-only)
Phase 6: Validation → Signal Authorization (trust-weighted)
Phase 7: Approved Signal → Execution (paper trading)
```
- Managed by `PipelineOrchestrator`
- Strict phase separation: each phase only adds its concern

**Pipeline C — Unified Bridge** (`pipeline_bridge.py`):
```
PipelineBridge(mode="hybrid") → merges results from A and B
```

### C.2 System Layers

```
┌─────────────────────────────────────────────────────────────┐
│  ENTRY POINTS: main.py, run_live.py, dashboard/app.py      │
├─────────────────────────────────────────────────────────────┤
│  ORCHESTRATION: PipelineBridge, StreamingPipeline,          │
│                 PipelineOrchestrator, DecisionEngine         │
├─────────────────────────────────────────────────────────────┤
│  NLP CORE: DeepNLPParser, AdvancedNLPEngine,                │
│           EntityExtractor, ContradictionDetector,            │
│           IntentDetector, EarningsCallAnalyzer               │
├─────────────────────────────────────────────────────────────┤
│  COGNITIVE MODELS: 5 Participant Types × CognitiveProfile   │
│                    → BehaviorTranslator → BehaviorProfile    │
├─────────────────────────────────────────────────────────────┤
│  MARKET ANALYSIS: BehaviorAggregator → ImpactTranslator,    │
│                   CorrelationEngine, ContagionModel,         │
│                   ScenarioGenerator, CausalChainBuilder,     │
│                   EconomicAnalyzer                           │
├─────────────────────────────────────────────────────────────┤
│  ALPHA GENERATION: 12 quant + 5 NLP + 5 structural =       │
│                    22 alpha signal generators                │
├─────────────────────────────────────────────────────────────┤
│  INTELLIGENCE: 9 market intelligence models,                │
│               6 hidden truth detectors                       │
├─────────────────────────────────────────────────────────────┤
│  VALIDATION: RealityValidator (5 dimensions),               │
│             StatisticalSignificanceTesting, FeedbackLoop     │
├─────────────────────────────────────────────────────────────┤
│  EXECUTION: SignalAuthorizer → ExecutionNexus → paper trades │
├─────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE: MessageQueue, TimeSeriesDB, ModelRegistry, │
│                  FeatureStore, CICDPipeline, Monitoring,     │
│                  APILayer (FastAPI), AlertDelivery           │
├─────────────────────────────────────────────────────────────┤
│  STORAGE: SQLite (DatabaseManager), NetworkX (KnowledgeGraph)│
└─────────────────────────────────────────────────────────────┘
```

---

## (D) Entry Points

| Entry Point | Command | Function |
|-------------|---------|----------|
| `main.py` | `python main.py` | Interactive demo (default) |
| `main.py --live` | `python main.py --live` | Live monitoring with news ingestion |
| `main.py --dashboard` | `python main.py --dashboard` | Streamlit dashboard on port 8501 |
| `main.py --test` | `python main.py --test` | Run all tests |
| `main.py --news "text"` | `python main.py --news "Fed cuts rates"` | Process single news event |
| `main.py --asset BTC` | `python main.py --asset BTC` | Set target asset |
| `run_live.py` | `python run_live.py` | Standalone live monitor |
| `legacy_main.py` | `python legacy_main.py` | 7-phase pipeline demo |
| `pipeline_bridge.py` | `python pipeline_bridge.py` | Bridge mode demo |
| `dashboard/app.py` | `streamlit run dashboard/app.py` | Dashboard only |
| `Dockerfile` | `docker build & run` | Containerized (ports 8501+8000) |
| `tests/test_phase_N.py` | `python tests/test_phase_N.py` | Per-phase test suite |
| `tests/test_integration.py` | `python tests/test_integration.py` | Integration tests |
| `scripts/health_check.py` | `python scripts/health_check.py` | System health verification |

---

## (E) Key Patterns

### E.1 Design Patterns

| Pattern | Where Used | Details |
|---------|-----------|---------|
| **Singleton** | `APIKeyManager` | Single instance for API key management |
| **Factory** | `create_bank_participant()`, etc. | 5 factory functions for participant creation |
| **Strategy** | `ScenarioPortfolioOptimizer` | 4 interchangeable optimization strategies |
| **Observer/Pub-Sub** | `EventBus` | Priority-based event subscription with dead letter queue |
| **Pipeline** | `StreamingPipeline`, `PipelineOrchestrator` | Sequential stage processing |
| **Bridge** | `PipelineBridge` | Merge two pipeline architectures |
| **Template Method** | `ImpactTranslator._generate_*_impacts()` | 6 impact generators following same pattern |
| **Registry** | `PARTICIPANT_REGISTRY`, `ModelRegistry` | Type-to-handler mapping |
| **Adapter** | `RealDataProvider`, `NewsAggregator` | Normalize multiple data sources |
| **Decorator** | Rate limiting in API clients | Request throttling |

### E.2 Critical Design Rules (Enforced in Tests)

1. **Phase 1 outputs NO sentiment/trading signals** — only linguistic structure
2. **Phase 2 outputs NO prices** — only cognitive expectations and action likelihoods
3. **Phase 3 outputs NO trades/orders** — only behavioral profiles with probabilities
4. **Phase 4 outputs NO price direction** — only market structure impacts (liquidity, volatility, spreads)
5. **Phase 5 is research-only** — NO trading signals, only validation records
6. **Action likelihoods sum to 1.0** — normalized across 8 action types per participant
7. **Same input → same output** — deterministic interpretation (no randomness in cognitive models)
8. **Inaction is meaningful** — passive/hold/wait behaviors explicitly captured

### E.3 Key Thresholds and Constants

| Constant | Value | Location |
|----------|-------|----------|
| Initial capital | $100,000 | `config/system_config.py`, `execution/execution_nexus.py` |
| Max position | 15% of capital | `execution/execution_nexus.py` |
| Max open positions | 3-5 | `execution/execution_nexus.py`, `config/system_config.py` |
| Stop loss | 2% | `execution/execution_nexus.py` |
| Take profit | 3-4% | `execution/execution_nexus.py` |
| Circuit breaker | 5% drawdown | `execution/execution_nexus.py` |
| Signal trust threshold | 0.6 | `signal_auth/signal_authorization.py` |
| Signal expiration | 4 hours | `signal_auth/signal_authorization.py` |
| Title word overlap dedup | 70% | `news_ingestion/news_aggregator.py` |
| Echo chamber threshold | co-coverage ≥5, sentiment corr >0.8, timing corr >0.6 | `hidden_truth/advanced_detection.py` |
| Coordinated release | <30s from 3+ sources | `hidden_truth/cross_source_analyzer.py` |
| Numeric contradiction | >20% difference | `nlp_engine/contradiction_detector.py` |
| Kelly sizing | Half-Kelly | `decision_system/decision_engine.py` |

---

## (F) Data Flow

### F.1 End-to-End Signal Generation (7-Phase Pipeline)

```
Raw Text (str)
    │
    ▼
[Phase 1: NewsEventParser]
    │ → NewsEvent (event_id, raw_text, actors, temporal_markers,
    │              uncertainty_markers, contradiction_pairs,
    │              semantic_claims, narrative_types, ambiguity_score)
    ▼
[Phase 2: Participant.interpret() × 5]
    │ → Dict[ParticipantType, ParticipantExpectation]
    │   (belief_shift, urgency, uncertainty_level, action_likelihoods,
    │    short/long_term_expectation, narrative_alignment)
    ▼
[Phase 3: BehaviorTranslator.translate() × 5]
    │ → Dict[ParticipantType, BehaviorProfile]
    │   (risk_posture, liquidity_posture, exposure_intent,
    │    urgency, optionality, contradictions, fallbacks)
    ▼
[Phase 4a: BehaviorAggregator.aggregate()]
    │ → AggregatedBehavior
    │   (avg_risk_signal, avg_liquidity_signal, disagreement,
    │    concentration, participant_divergence)
    │
[Phase 4b: ImpactTranslator.translate()]
    │ → MarketImpactProfile
    │   (6 impact categories × items with timing,
    │    overall_stress, threshold/saturation/feedback flags)
    ▼
[Phase 5: RealityValidator.create_validation_record()]
    │ → ValidationRecord
    │   (directional, volatility, timing, participation,
    │    regime accuracy, overall_accuracy, model_credibility)
    ▼
[Phase 6: SignalAuthorizer.authorize_signal()]
    │ → SignalRecord
    │   (direction, strength, trust_score, volatility_impact,
    │    reaction_horizon, participant_weights, status, expiration)
    ▼
[Phase 7: ExecutionNexus.execute_signal()]
    │ → ExecutedOrder
    │   (order_id, direction, size, entry_price, stop_loss,
    │    take_profit, status)
    ▼
[FeedbackLoop.record_prediction()] → update model credibility
```

### F.2 NLP Processing Pipeline

```
Raw Text
    │
    ├─→ DeepNLPParser.parse()
    │     ├─→ spaCy tokenization + NER
    │     ├─→ Per-sentence: certainty scoring, conditional/negation detection
    │     ├─→ Narrative classification (12 types via zero-shot or keywords)
    │     ├─→ Intent detection (8 types via keyword scoring)
    │     ├─→ Document metrics (certainty, subjectivity, complexity)
    │     ├─→ Key phrase extraction
    │     └─→ MiniLM embeddings (document + per-sentence)
    │
    ├─→ EntityExtractor.extract_from_text()
    │     └─→ FinancialEntity[], GeopoliticalEntity[], EntityRelation[]
    │
    ├─→ ContradictionDetector.detect()
    │     └─→ ContradictionResult (negation/antonym/numeric/stance)
    │
    ├─→ IntentDetector.analyze()
    │     └─→ IntentAnalysis (communication, strategic, timing, manipulation,
    │                         beneficiaries, hidden_agenda)
    │
    ├─→ AdvancedNLPEngine.full_analysis()
    │     ├─→ Language detection + translation (8 languages)
    │     ├─→ Financial embeddings + domain classification
    │     └─→ Structured event extraction (WHO-WHAT-WHOM-WHEN-RESULT)
    │
    └─→ EarningsCallAnalyzer.analyze_transcript()
          └─→ Section-wise sentiment, tone shift, hedging, guidance, risk signals
```

### F.3 Alpha Signal Aggregation

```
Market Data + News
    │
    ├─→ 12 Quantitative Alphas (alpha_signals.py)
    │     └─→ AlphaSignalAggregator.aggregate() → weighted conviction
    │
    ├─→ 5 NLP Alphas (nlp_alpha_signals.py)
    │     └─→ NLPAlphaHub.generate_signals() → narrative momentum, contradiction, etc.
    │
    ├─→ 5 Structural Alphas (structural_alpha.py)
    │     └─→ StructuralAlphaEngine.analyze() → microstructure, vol, funding, on-chain
    │
    └─→ 9 Intelligence Models (intelligence_models.py)
          └─→ MarketIntelligenceHub.full_scan() → regime, crowding, arbitrage, reflexivity
```

---

## (G) Cross-Module Dependencies

### G.1 Import Dependency Graph (Major Flows)

```
main.py
  ├── engine.CognitiveMarketSystem
  │     ├── engine.core_cognitive_structures
  │     ├── engine.expectation_collision_engine
  │     ├── engine.tradable_signal_translator
  │     ├── engine.participant_models
  │     ├── nlp_engine.DeepNLPParser
  │     └── storage.KnowledgeGraph
  │
  ├── pipeline_bridge.PipelineBridge
  │     ├── engine.CognitiveMarketSystem
  │     └── legacy_main.PipelineOrchestrator
  │           ├── news_model.NewsEventParser
  │           ├── participant_cognition.participant_models
  │           ├── market_response.BehaviorTranslator
  │           ├── market_impact.BehaviorAggregator + ImpactTranslator
  │           ├── reality_validation.RealityValidator
  │           ├── signal_auth.SignalAuthorizer
  │           └── execution.ExecutionNexus
  │
  ├── streaming.StreamingPipeline
  │     ├── streaming.EventBus
  │     └── [all 7 phase packages]
  │
  ├── decision_system.DecisionEngine
  │     └── hidden_truth (manipulation checks)
  │
  ├── data.MarketDataFeed
  ├── storage.DatabaseManager
  ├── storage.KnowledgeGraph
  ├── scenario_engine.ScenarioGenerator
  ├── learning.FeedbackLoop
  └── config.get_config
```

### G.2 Shared Type Dependencies

```
shared/__init__.py (canonical enums)
  └── ParticipantType, TimeHorizon, RiskTolerance, DirectionType
       │
       ├── Used by: engine/core_cognitive_structures.py
       ├── Used by: participant_cognition/participant_models.py
       ├── Used by: market_response/behavior_models.py
       ├── Used by: market_impact/market_impact_models.py
       ├── Used by: tests/test_integration.py (type unification test)
       └── Used by: all phase packages
```

### G.3 Storage Dependencies

```
storage/database.py (SQLite)
  └── Used by: learning/feedback_loop.py
  └── Used by: hidden_truth/cross_source_analyzer.py
  └── Used by: config/system_config.py
  └── Used by: main.py (bootstrap)

storage/knowledge_graph.py (NetworkX + JSON)
  └── Used by: engine/cognitive_market_system.py
  └── Used by: scenario_engine/causal_chain.py (_enhance_with_graph)
  └── Used by: main.py (bootstrap)
```

### G.4 External API Dependencies

| Dependency | Package | Used By | Fallback |
|-----------|---------|---------|----------|
| NewsAPI.org | `newsapi` | `news_ingestion/news_api_client.py` | RSS feeds |
| GDELT | HTTP requests | `news_ingestion/gdelt_client.py` | RSS feeds |
| CoinGecko | HTTP requests | `engine/real_data_adapter.py`, `data/market_data_feed.py` | GBM simulation |
| Yahoo Finance | `yfinance` | `reality_validation/market_reality.py` | CoinGecko or cache |
| OpenAI GPT | `openai` | `advanced/llm_analyzer.py` | Keyword fallback |
| Reddit | `praw` | `advanced/social_media.py` | None (optional) |
| Twitter | `tweepy` | `advanced/social_media.py` | None (optional) |
| HuggingFace | `transformers` | `nlp_engine/*.py` | Keyword-based analysis |
| spaCy | `spacy` | `nlp_engine/deep_nlp_parser.py` | Regex-based NER |
| Twilio SMS | HTTP API | `alerts/alert_delivery.py` | Console/file fallback |

### G.5 Model Dependencies

| Model | Source | Used By |
|-------|--------|---------|
| `en_core_web_sm` | spaCy | `DeepNLPParser`, `FinancialEventExtractor` |
| `ProsusAI/finbert` | HuggingFace | `DeepNLPParser` sentiment |
| `facebook/bart-large-mnli` | HuggingFace | `DeepNLPParser` zero-shot classification |
| `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace | `DeepNLPParser` embeddings |
| `distilbert-base-uncased-finetuned-sst-2-english` | HuggingFace | Fallback sentiment |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | HuggingFace | Optional relevance scoring |
| `bert-base-multilingual-cased` | HuggingFace | `MultiLingualFinancialNLP` |
| `Helsinki-NLP/opus-mt-*` | HuggingFace | `MultiLingualFinancialNLP` translation |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Python files | ~78 |
| Total packages/directories | 30+ |
| Total lines of Python | ~42,000+ |
| Unique classes | ~120+ |
| Test files | 7 (90 tests total) |
| Alpha signal generators | 22 (12 quant + 5 NLP + 5 structural) |
| Intelligence models | 9 |
| Infrastructure components | 7 |
| NLP model dependencies | 8 HuggingFace models |
| External API integrations | 7 |
| Pipeline phases | 7 |
| Participant types | 5 |
| Impact categories | 6 (22 impact sub-types) |
| Validation dimensions | 5 |
| Economic models | 5 |
| Scenario optimization methods | 4 |
| Portfolio optimization methods | 4 |
| Alert delivery channels | 5 |
| Streamlit dashboard pages | 7 |
| API routes | 13 |
| SQLite tables | 9 |
| Knowledge graph seed entities | 40+ |
| RSS feeds pre-configured | 14 |
| Supported languages | 8 |
