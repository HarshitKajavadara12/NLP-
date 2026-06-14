"""
DATABASE MANAGER — SQLite persistent storage

Stores:
- News events (raw text, parsed data, metadata)
- Participant interpretations and expectations
- Validation records and model credibility
- Trading signals and execution results
- System configuration and state

Schema designed for time-series queries and historical analysis.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import asdict


class DatabaseManager:
    """
    SQLite database for Cognitive Market Engine.
    
    Thread-safe, auto-creates schema, supports full history tracking.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize database.
        
        Args:
            db_path: Path to SQLite file. Defaults to data/cognitive_engine.db
        """
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "cognitive_engine.db")
        
        self.db_path = db_path
        self._create_schema()
        print(f"[DB] Initialized: {db_path}")
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def _create_schema(self):
        """Create all database tables."""
        conn = self._get_conn()
        try:
            conn.executescript("""
                -- ============================================================
                -- NEWS EVENTS
                -- ============================================================
                CREATE TABLE IF NOT EXISTS news_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp_utc TEXT NOT NULL,
                    source TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    content_hash TEXT UNIQUE,
                    
                    -- Parsed data (JSON)
                    sentences_json TEXT,
                    entities_json TEXT,
                    triples_json TEXT,
                    narrative_types_json TEXT,
                    
                    -- Metrics
                    ambiguity_score REAL DEFAULT 0.5,
                    certainty_score REAL DEFAULT 0.5,
                    complexity_score REAL DEFAULT 0.5,
                    detected_intent TEXT,
                    intent_confidence REAL DEFAULT 0.0,
                    
                    -- Metadata
                    language TEXT DEFAULT 'en',
                    word_count INTEGER DEFAULT 0,
                    parse_method TEXT,
                    
                    -- Timestamps
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news_events(timestamp_utc);
                CREATE INDEX IF NOT EXISTS idx_news_source ON news_events(source);
                CREATE INDEX IF NOT EXISTS idx_news_hash ON news_events(content_hash);
                
                -- ============================================================
                -- PARTICIPANT INTERPRETATIONS
                -- ============================================================
                CREATE TABLE IF NOT EXISTS participant_interpretations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    participant_type TEXT NOT NULL,
                    
                    -- Expectation data
                    belief_shift REAL,
                    confidence TEXT,
                    uncertainty_level REAL,
                    urgency REAL,
                    short_term_expectation REAL,
                    long_term_expectation REAL,
                    narrative_alignment REAL,
                    
                    -- Action likelihoods (JSON)
                    action_likelihoods_json TEXT,
                    reasoning TEXT,
                    
                    -- Timestamps
                    created_at TEXT DEFAULT (datetime('now')),
                    
                    FOREIGN KEY (event_id) REFERENCES news_events(event_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_interp_event ON participant_interpretations(event_id);
                CREATE INDEX IF NOT EXISTS idx_interp_participant ON participant_interpretations(participant_type);
                
                -- ============================================================
                -- MARKET IMPACT PREDICTIONS
                -- ============================================================
                CREATE TABLE IF NOT EXISTS impact_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    
                    -- Impact metrics
                    overall_market_stress REAL,
                    confidence_in_impact REAL,
                    threshold_breached INTEGER DEFAULT 0,
                    saturation_detected INTEGER DEFAULT 0,
                    feedback_loop_risk INTEGER DEFAULT 0,
                    
                    -- Detail (JSON)
                    liquidity_impacts_json TEXT,
                    volatility_impacts_json TEXT,
                    spread_impacts_json TEXT,
                    order_flow_impacts_json TEXT,
                    price_dynamics_json TEXT,
                    regime_impacts_json TEXT,
                    
                    reasoning TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    
                    FOREIGN KEY (event_id) REFERENCES news_events(event_id)
                );
                
                -- ============================================================
                -- VALIDATION RECORDS
                -- ============================================================
                CREATE TABLE IF NOT EXISTS validation_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    news_type TEXT,
                    
                    -- Validation scores
                    directional_accuracy REAL,
                    volatility_accuracy REAL,
                    timing_accuracy REAL,
                    overall_accuracy REAL,
                    model_credibility REAL,
                    
                    -- Participation accuracy (JSON)
                    participation_json TEXT,
                    
                    -- Regime
                    regime_predicted TEXT,
                    regime_actual TEXT,
                    regime_correct INTEGER,
                    
                    -- Analysis
                    most_accurate_participant TEXT,
                    least_accurate_participant TEXT,
                    biggest_failure TEXT,
                    research_notes TEXT,
                    
                    created_at TEXT DEFAULT (datetime('now')),
                    
                    FOREIGN KEY (event_id) REFERENCES news_events(event_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_valid_event ON validation_records(event_id);
                
                -- ============================================================
                -- TRADING SIGNALS
                -- ============================================================
                CREATE TABLE IF NOT EXISTS trading_signals (
                    signal_id TEXT PRIMARY KEY,
                    event_id TEXT,
                    
                    -- Signal data
                    direction TEXT,
                    strength REAL,
                    signal_type TEXT,
                    trust_score REAL,
                    status TEXT,
                    
                    -- Execution
                    execution_mode TEXT,
                    position_size REAL,
                    entry_price REAL,
                    exit_price REAL,
                    profit_loss REAL,
                    
                    -- Timing
                    created_at TEXT DEFAULT (datetime('now')),
                    approved_at TEXT,
                    executed_at TEXT,
                    expired_at TEXT,
                    
                    -- Detail (JSON)
                    detail_json TEXT,
                    
                    FOREIGN KEY (event_id) REFERENCES news_events(event_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_signal_status ON trading_signals(status);
                CREATE INDEX IF NOT EXISTS idx_signal_created ON trading_signals(created_at);
                
                -- ============================================================
                -- MODEL CREDIBILITY TRACKING
                -- ============================================================
                CREATE TABLE IF NOT EXISTS model_credibility (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    participant_type TEXT NOT NULL,
                    event_type TEXT,
                    
                    -- Scores
                    accuracy REAL,
                    event_count INTEGER DEFAULT 0,
                    mean_accuracy REAL,
                    
                    updated_at TEXT DEFAULT (datetime('now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_cred_participant ON model_credibility(participant_type);
                
                -- ============================================================
                -- SCENARIO HISTORY
                -- ============================================================
                CREATE TABLE IF NOT EXISTS scenario_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    scenario_tree_json TEXT,
                    generated_at TEXT DEFAULT (datetime('now')),
                    materialized_path TEXT,
                    accuracy REAL,
                    
                    FOREIGN KEY (event_id) REFERENCES news_events(event_id)
                );
                
                -- ============================================================
                -- KNOWLEDGE GRAPH SNAPSHOTS
                -- ============================================================
                CREATE TABLE IF NOT EXISTS knowledge_graph_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_json TEXT,
                    node_count INTEGER,
                    edge_count INTEGER,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                
                -- ============================================================
                -- SYSTEM METRICS
                -- ============================================================
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_json TEXT,
                    recorded_at TEXT DEFAULT (datetime('now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_name ON system_metrics(metric_name);
            """)
            conn.commit()
        finally:
            conn.close()
    
    # ========================================================================
    # NEWS EVENTS CRUD
    # ========================================================================
    
    def store_news_event(self, event_data: Dict) -> str:
        """Store a news event. Returns event_id."""
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO news_events 
                (event_id, timestamp_utc, source, raw_text, content_hash,
                 sentences_json, entities_json, triples_json, narrative_types_json,
                 ambiguity_score, certainty_score, complexity_score,
                 detected_intent, intent_confidence,
                 language, word_count, parse_method, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                event_data.get("event_id", ""),
                event_data.get("timestamp_utc", datetime.now().isoformat()),
                event_data.get("source", ""),
                event_data.get("raw_text", ""),
                event_data.get("content_hash", ""),
                json.dumps(event_data.get("sentences", [])),
                json.dumps(event_data.get("entities", [])),
                json.dumps(event_data.get("triples", [])),
                json.dumps(event_data.get("narrative_types", [])),
                event_data.get("ambiguity_score", 0.5),
                event_data.get("certainty_score", 0.5),
                event_data.get("complexity_score", 0.5),
                event_data.get("detected_intent", ""),
                event_data.get("intent_confidence", 0.0),
                event_data.get("language", "en"),
                event_data.get("word_count", 0),
                event_data.get("parse_method", ""),
            ))
            conn.commit()
            return event_data.get("event_id", "")
        finally:
            conn.close()
    
    def get_news_event(self, event_id: str) -> Optional[Dict]:
        """Retrieve a news event by ID."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM news_events WHERE event_id = ?", (event_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_recent_news(self, limit: int = 50, source: str = None) -> List[Dict]:
        """Get recent news events."""
        conn = self._get_conn()
        try:
            if source:
                rows = conn.execute(
                    "SELECT * FROM news_events WHERE source = ? ORDER BY timestamp_utc DESC LIMIT ?",
                    (source, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM news_events ORDER BY timestamp_utc DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    
    def search_news(self, query: str, limit: int = 20) -> List[Dict]:
        """Full-text search on news events."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM news_events WHERE raw_text LIKE ? ORDER BY timestamp_utc DESC LIMIT ?",
                (f"%{query}%", limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    
    # ========================================================================
    # INTERPRETATIONS
    # ========================================================================
    
    def store_interpretation(self, data: Dict):
        """Store participant interpretation."""
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO participant_interpretations
                (event_id, participant_type, belief_shift, confidence,
                 uncertainty_level, urgency, short_term_expectation,
                 long_term_expectation, narrative_alignment,
                 action_likelihoods_json, reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("event_id"), data.get("participant_type"),
                data.get("belief_shift"), data.get("confidence"),
                data.get("uncertainty_level"), data.get("urgency"),
                data.get("short_term_expectation"),
                data.get("long_term_expectation"),
                data.get("narrative_alignment"),
                json.dumps(data.get("action_likelihoods", {})),
                data.get("reasoning", ""),
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_interpretations(self, event_id: str) -> List[Dict]:
        """Get all interpretations for an event."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM participant_interpretations WHERE event_id = ?",
                (event_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    
    # ========================================================================
    # VALIDATION RECORDS
    # ========================================================================
    
    def store_validation(self, data: Dict):
        """Store validation record."""
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO validation_records
                (event_id, news_type, directional_accuracy, volatility_accuracy,
                 timing_accuracy, overall_accuracy, model_credibility,
                 participation_json, regime_predicted, regime_actual,
                 regime_correct, most_accurate_participant,
                 least_accurate_participant, biggest_failure, research_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("event_id"), data.get("news_type"),
                data.get("directional_accuracy"),
                data.get("volatility_accuracy"),
                data.get("timing_accuracy"),
                data.get("overall_accuracy"),
                data.get("model_credibility"),
                json.dumps(data.get("participation", {})),
                data.get("regime_predicted"),
                data.get("regime_actual"),
                data.get("regime_correct"),
                data.get("most_accurate_participant"),
                data.get("least_accurate_participant"),
                data.get("biggest_failure"),
                data.get("research_notes"),
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_validation_history(self, limit: int = 100) -> List[Dict]:
        """Get validation history."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM validation_records ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    
    def get_model_accuracy(self, participant_type: str = None) -> Dict:
        """Get aggregate model accuracy stats."""
        conn = self._get_conn()
        try:
            if participant_type:
                rows = conn.execute("""
                    SELECT AVG(overall_accuracy) as avg_accuracy,
                           COUNT(*) as event_count,
                           MIN(overall_accuracy) as min_accuracy,
                           MAX(overall_accuracy) as max_accuracy
                    FROM validation_records 
                    WHERE most_accurate_participant = ?
                """, (participant_type,)).fetchone()
            else:
                rows = conn.execute("""
                    SELECT AVG(overall_accuracy) as avg_accuracy,
                           COUNT(*) as event_count,
                           MIN(overall_accuracy) as min_accuracy,
                           MAX(overall_accuracy) as max_accuracy
                    FROM validation_records
                """).fetchone()
            return dict(rows) if rows else {}
        finally:
            conn.close()
    
    # ========================================================================
    # TRADING SIGNALS
    # ========================================================================
    
    def store_signal(self, data: Dict):
        """Store a trading signal."""
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO trading_signals
                (signal_id, event_id, direction, strength, signal_type,
                 trust_score, status, execution_mode, position_size,
                 entry_price, exit_price, profit_loss, detail_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("signal_id"), data.get("event_id"),
                data.get("direction"), data.get("strength"),
                data.get("signal_type"), data.get("trust_score"),
                data.get("status"), data.get("execution_mode"),
                data.get("position_size"), data.get("entry_price"),
                data.get("exit_price"), data.get("profit_loss"),
                json.dumps(data.get("detail", {})),
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_signal_performance(self) -> Dict:
        """Get aggregate signal performance."""
        conn = self._get_conn()
        try:
            row = conn.execute("""
                SELECT COUNT(*) as total_signals,
                       SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning,
                       SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing,
                       SUM(profit_loss) as total_pnl,
                       AVG(profit_loss) as avg_pnl
                FROM trading_signals WHERE profit_loss IS NOT NULL
            """).fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()
    
    # ========================================================================
    # SCENARIO HISTORY
    # ========================================================================
    
    def store_scenario(self, event_id: str, scenario_tree: Dict):
        """Store a scenario tree."""
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO scenario_history (event_id, scenario_tree_json) VALUES (?, ?)",
                (event_id, json.dumps(scenario_tree))
            )
            conn.commit()
        finally:
            conn.close()
    
    def update_scenario_outcome(self, scenario_id: int, 
                                materialized_path: str, accuracy: float):
        """Update scenario with actual outcome."""
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE scenario_history SET materialized_path = ?, accuracy = ? WHERE id = ?",
                (materialized_path, accuracy, scenario_id)
            )
            conn.commit()
        finally:
            conn.close()
    
    # ========================================================================
    # SYSTEM METRICS
    # ========================================================================
    
    def record_metric(self, name: str, value: float = None, data: Dict = None):
        """Record a system metric."""
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO system_metrics (metric_name, metric_value, metric_json) VALUES (?, ?, ?)",
                (name, value, json.dumps(data) if data else None)
            )
            conn.commit()
        finally:
            conn.close()
    
    def get_metrics(self, name: str, limit: int = 100) -> List[Dict]:
        """Get metric history."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM system_metrics WHERE metric_name = ? ORDER BY recorded_at DESC LIMIT ?",
                (name, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    
    # ========================================================================
    # STATS
    # ========================================================================
    
    def get_database_stats(self) -> Dict:
        """Get overall database statistics."""
        conn = self._get_conn()
        try:
            stats = {}
            tables = ["news_events", "participant_interpretations", 
                      "validation_records", "trading_signals",
                      "scenario_history", "system_metrics"]
            
            for table in tables:
                row = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                stats[table] = row["count"]
            
            # DB file size
            if os.path.exists(self.db_path):
                stats["db_size_mb"] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            
            return stats
        finally:
            conn.close()
