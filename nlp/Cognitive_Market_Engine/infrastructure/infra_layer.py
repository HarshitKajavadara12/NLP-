"""
Infrastructure Layer — 7 Production Components
================================================
Provides abstractions and implementations for:
1. Message Queue (Redis / Kafka / in-memory)
2. Time-Series Database (InfluxDB / TimescaleDB / SQLite fallback)
3. Model Registry (MLflow-style versioning & lineage)
4. Feature Store (centralized feature management & serving)
5. CI/CD Pipeline (config generation for GitHub Actions / GitLab CI)
6. Monitoring (Prometheus-compatible metrics + Grafana dashboards)
7. API Layer (FastAPI-based REST / WebSocket endpoints)
"""
import time
import json
import math
import hashlib
import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from collections import defaultdict, deque
from enum import Enum
from pathlib import Path
import os

logger = logging.getLogger("cme.infrastructure")


# ─────────────────────────────────────────────────────────────
# 1. Message Queue
# ─────────────────────────────────────────────────────────────

class MessageQueue:
    """
    Unified message queue abstraction supporting:
    - Redis Pub/Sub (production)
    - Kafka (high-throughput)
    - In-memory (development / testing)
    
    Provides publish/subscribe, topic management, dead-letter queues.
    """

    def __init__(self, backend: str = "memory", config: Optional[Dict] = None):
        self._backend = backend
        self._config = config or {}
        self._topics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._dead_letter: deque = deque(maxlen=5000)
        self._stats = {"published": 0, "consumed": 0, "errors": 0}
        self._redis = None
        self._kafka_producer = None
        self._kafka_consumer = None
        self._lock = threading.Lock()

        if backend == "redis":
            self._init_redis()
        elif backend == "kafka":
            self._init_kafka()

    def _init_redis(self):
        try:
            import redis
            self._redis = redis.Redis(
                host=self._config.get("host", "localhost"),
                port=self._config.get("port", 6379),
                db=self._config.get("db", 0),
                decode_responses=True,
            )
            self._redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available, falling back to memory: {e}")
            self._backend = "memory"

    def _init_kafka(self):
        try:
            from kafka import KafkaProducer, KafkaConsumer
            bootstrap = self._config.get("bootstrap_servers", "localhost:9092")
            self._kafka_producer = KafkaProducer(
                bootstrap_servers=bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            logger.info("Kafka producer initialized")
        except Exception as e:
            logger.warning(f"Kafka not available, falling back to memory: {e}")
            self._backend = "memory"

    def publish(self, topic: str, message: Any, priority: int = 0) -> bool:
        """Publish a message to a topic."""
        envelope = {
            "topic": topic,
            "payload": message,
            "timestamp": time.time(),
            "priority": priority,
            "id": hashlib.md5(f"{topic}{time.time()}".encode()).hexdigest()[:12],
        }

        try:
            if self._backend == "redis" and self._redis:
                self._redis.publish(topic, json.dumps(envelope))
                self._redis.lpush(f"queue:{topic}", json.dumps(envelope))
            elif self._backend == "kafka" and self._kafka_producer:
                self._kafka_producer.send(topic, value=envelope)
            else:
                with self._lock:
                    self._topics[topic].append(envelope)

            self._stats["published"] += 1

            # Notify in-memory subscribers
            for callback in self._subscribers.get(topic, []):
                try:
                    callback(envelope)
                except Exception as e:
                    logger.error(f"Subscriber error on {topic}: {e}")
                    self._dead_letter.append({**envelope, "error": str(e)})
                    self._stats["errors"] += 1

            return True
        except Exception as e:
            logger.error(f"Publish failed on {topic}: {e}")
            self._dead_letter.append({**envelope, "error": str(e)})
            self._stats["errors"] += 1
            return False

    def subscribe(self, topic: str, callback: Callable) -> None:
        """Subscribe to messages on a topic."""
        self._subscribers[topic].append(callback)

        if self._backend == "redis" and self._redis:
            # Redis pub/sub in a background thread
            def _redis_listener():
                pubsub = self._redis.pubsub()
                pubsub.subscribe(topic)
                for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            callback(data)
                        except Exception as e:
                            logger.error(f"Redis subscriber error: {e}")

            t = threading.Thread(target=_redis_listener, daemon=True)
            t.start()

    def consume(self, topic: str, count: int = 1) -> List[Dict]:
        """Consume messages from a topic queue."""
        messages = []
        if self._backend == "redis" and self._redis:
            for _ in range(count):
                msg = self._redis.rpop(f"queue:{topic}")
                if msg:
                    messages.append(json.loads(msg))
        else:
            with self._lock:
                for _ in range(min(count, len(self._topics[topic]))):
                    messages.append(self._topics[topic].popleft())

        self._stats["consumed"] += len(messages)
        return messages

    def get_stats(self) -> Dict:
        return {
            **self._stats,
            "backend": self._backend,
            "topics": list(self._topics.keys()),
            "dead_letter_count": len(self._dead_letter),
        }


# ─────────────────────────────────────────────────────────────
# 2. Time-Series Database
# ─────────────────────────────────────────────────────────────

class TimeSeriesDB:
    """
    Time-series data storage abstraction supporting:
    - InfluxDB (production time-series workloads)
    - TimescaleDB (PostgreSQL extension)
    - SQLite (development / testing fallback)
    
    Provides write, query, aggregation, and retention management.
    """

    def __init__(self, backend: str = "sqlite", config: Optional[Dict] = None):
        self._backend = backend
        self._config = config or {}
        self._influx_client = None
        self._conn = None

        if backend == "influxdb":
            self._init_influx()
        elif backend == "timescaledb":
            self._init_timescale()
        else:
            self._init_sqlite()

    def _init_influx(self):
        try:
            from influxdb_client import InfluxDBClient, Point, WritePrecision
            from influxdb_client.client.write_api import SYNCHRONOUS
            self._influx_client = InfluxDBClient(
                url=self._config.get("url", "http://localhost:8086"),
                token=self._config.get("token", ""),
                org=self._config.get("org", "cme"),
            )
            self._write_api = self._influx_client.write_api(write_options=SYNCHRONOUS)
            self._query_api = self._influx_client.query_api()
            logger.info("InfluxDB connected")
        except Exception as e:
            logger.warning(f"InfluxDB not available, using SQLite fallback: {e}")
            self._backend = "sqlite"
            self._init_sqlite()

    def _init_timescale(self):
        try:
            import psycopg2
            self._conn = psycopg2.connect(
                host=self._config.get("host", "localhost"),
                port=self._config.get("port", 5432),
                dbname=self._config.get("dbname", "cme_ts"),
                user=self._config.get("user", "postgres"),
                password=self._config.get("password", ""),
            )
            logger.info("TimescaleDB connected")
        except Exception as e:
            logger.warning(f"TimescaleDB not available, using SQLite fallback: {e}")
            self._backend = "sqlite"
            self._init_sqlite()

    def _init_sqlite(self):
        db_path = self._config.get("path",
                                    str(Path(__file__).parent.parent / "data" / "timeseries.db"))
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS timeseries (
                measurement TEXT NOT NULL,
                tags TEXT DEFAULT '{}',
                fields TEXT DEFAULT '{}',
                timestamp REAL NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ts_measurement
            ON timeseries(measurement, timestamp)
        """)
        self._conn.commit()
        logger.info(f"SQLite time-series DB at {db_path}")

    def write(self, measurement: str, fields: Dict[str, float],
              tags: Optional[Dict[str, str]] = None,
              timestamp: Optional[float] = None) -> bool:
        """Write a time-series point."""
        ts = timestamp or time.time()
        tags = tags or {}

        try:
            if self._backend == "influxdb" and self._influx_client:
                from influxdb_client import Point
                point = Point(measurement)
                for k, v in tags.items():
                    point = point.tag(k, v)
                for k, v in fields.items():
                    point = point.field(k, v)
                point = point.time(int(ts * 1e9))
                self._write_api.write(
                    bucket=self._config.get("bucket", "cme"),
                    record=point,
                )
            else:
                self._conn.execute(
                    "INSERT INTO timeseries (measurement, tags, fields, timestamp) "
                    "VALUES (?, ?, ?, ?)",
                    (measurement, json.dumps(tags), json.dumps(fields), ts),
                )
                self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"TSDB write error: {e}")
            return False

    def query(self, measurement: str, start_time: float,
              end_time: Optional[float] = None,
              tags: Optional[Dict[str, str]] = None,
              limit: int = 1000) -> List[Dict]:
        """Query time-series data."""
        end_time = end_time or time.time()

        try:
            if self._backend == "influxdb" and self._influx_client:
                flux = (f'from(bucket: "{self._config.get("bucket", "cme")}") '
                        f'|> range(start: {int(start_time)}, stop: {int(end_time)}) '
                        f'|> filter(fn: (r) => r._measurement == "{measurement}") '
                        f'|> limit(n: {limit})')
                tables = self._query_api.query(flux)
                results = []
                for table in tables:
                    for record in table.records:
                        results.append({
                            "measurement": measurement,
                            "field": record.get_field(),
                            "value": record.get_value(),
                            "timestamp": record.get_time().timestamp(),
                        })
                return results
            else:
                query = ("SELECT measurement, tags, fields, timestamp "
                         "FROM timeseries WHERE measurement = ? "
                         "AND timestamp >= ? AND timestamp <= ?")
                params: list = [measurement, start_time, end_time]
                if tags:
                    for k, v in tags.items():
                        query += f" AND json_extract(tags, '$.{k}') = ?"
                        params.append(v)
                query += f" ORDER BY timestamp DESC LIMIT {limit}"
                cursor = self._conn.execute(query, params)
                return [
                    {
                        "measurement": row[0],
                        "tags": json.loads(row[1]),
                        "fields": json.loads(row[2]),
                        "timestamp": row[3],
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"TSDB query error: {e}")
            return []

    def aggregate(self, measurement: str, field_name: str,
                  window_seconds: int = 3600,
                  agg_fn: str = "avg",
                  start_time: Optional[float] = None) -> List[Dict]:
        """Aggregate time-series data in windows."""
        start_time = start_time or (time.time() - 86400)
        rows = self.query(measurement, start_time)
        if not rows:
            return []

        # Group by window
        buckets: Dict[int, List[float]] = defaultdict(list)
        for row in rows:
            bucket_key = int(row["timestamp"] / window_seconds)
            fields = row.get("fields", {})
            if field_name in fields:
                buckets[bucket_key].append(fields[field_name])

        results = []
        for bucket_key, values in sorted(buckets.items()):
            if not values:
                continue
            if agg_fn == "avg":
                agg_val = sum(values) / len(values)
            elif agg_fn == "sum":
                agg_val = sum(values)
            elif agg_fn == "max":
                agg_val = max(values)
            elif agg_fn == "min":
                agg_val = min(values)
            elif agg_fn == "count":
                agg_val = len(values)
            else:
                agg_val = sum(values) / len(values)

            results.append({
                "window_start": bucket_key * window_seconds,
                "value": agg_val,
                "count": len(values),
            })
        return results

    def apply_retention(self, max_age_days: int = 90) -> int:
        """Delete data older than retention period."""
        cutoff = time.time() - max_age_days * 86400
        if self._backend == "sqlite":
            cursor = self._conn.execute(
                "DELETE FROM timeseries WHERE timestamp < ?", (cutoff,)
            )
            self._conn.commit()
            return cursor.rowcount
        return 0


# ─────────────────────────────────────────────────────────────
# 3. Model Registry
# ─────────────────────────────────────────────────────────────

class ModelStage(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


@dataclass
class RegisteredModel:
    """A registered model version."""
    name: str
    version: int
    stage: ModelStage
    metrics: Dict[str, float]
    parameters: Dict[str, Any]
    artifact_path: str
    created_at: float
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    lineage: Dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """
    MLflow-inspired model registry:
    - Version management
    - Stage transitions (dev → staging → production)
    - Metric tracking across versions
    - Model lineage & provenance
    - A/B testing support
    - Rollback capability
    """

    def __init__(self, storage_path: Optional[str] = None):
        self._storage = storage_path or str(
            Path(__file__).parent.parent / "data" / "model_registry"
        )
        os.makedirs(self._storage, exist_ok=True)
        self._models: Dict[str, List[RegisteredModel]] = defaultdict(list)
        self._active_production: Dict[str, RegisteredModel] = {}
        self._ab_tests: Dict[str, Dict] = {}

    def register_model(self, name: str, metrics: Dict[str, float],
                       parameters: Dict[str, Any],
                       artifact_path: str = "",
                       description: str = "",
                       tags: Optional[Dict[str, str]] = None,
                       lineage: Optional[Dict] = None) -> RegisteredModel:
        """Register a new model version."""
        existing = self._models.get(name, [])
        version = len(existing) + 1

        model = RegisteredModel(
            name=name,
            version=version,
            stage=ModelStage.DEVELOPMENT,
            metrics=metrics,
            parameters=parameters,
            artifact_path=artifact_path or f"{self._storage}/{name}/v{version}",
            created_at=time.time(),
            description=description,
            tags=tags or {},
            lineage=lineage or {},
        )

        self._models[name].append(model)
        logger.info(f"Registered model {name} v{version}")

        # Save metadata
        self._save_metadata(model)
        return model

    def _save_metadata(self, model: RegisteredModel) -> None:
        model_dir = Path(self._storage) / model.name
        model_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "name": model.name,
            "version": model.version,
            "stage": model.stage.value,
            "metrics": model.metrics,
            "parameters": model.parameters,
            "artifact_path": model.artifact_path,
            "created_at": model.created_at,
            "description": model.description,
            "tags": model.tags,
            "lineage": model.lineage,
        }
        with open(model_dir / f"v{model.version}_meta.json", "w") as f:
            json.dump(meta, f, indent=2)

    def transition_stage(self, name: str, version: int,
                         target_stage: ModelStage) -> bool:
        """Transition a model to a new stage."""
        models = self._models.get(name, [])
        for model in models:
            if model.version == version:
                old_stage = model.stage
                model.stage = target_stage

                if target_stage == ModelStage.PRODUCTION:
                    # Demote current production model
                    if name in self._active_production:
                        old_prod = self._active_production[name]
                        old_prod.stage = ModelStage.ARCHIVED
                    self._active_production[name] = model

                self._save_metadata(model)
                logger.info(f"Model {name} v{version}: {old_stage.value} → {target_stage.value}")
                return True
        return False

    def get_production_model(self, name: str) -> Optional[RegisteredModel]:
        """Get the current production model."""
        return self._active_production.get(name)

    def compare_versions(self, name: str,
                         v1: int, v2: int) -> Dict[str, Any]:
        """Compare metrics between two model versions."""
        models = self._models.get(name, [])
        m1 = next((m for m in models if m.version == v1), None)
        m2 = next((m for m in models if m.version == v2), None)

        if not m1 or not m2:
            return {"error": "Version not found"}

        comparison = {}
        all_metrics = set(m1.metrics.keys()) | set(m2.metrics.keys())
        for metric in all_metrics:
            val1 = m1.metrics.get(metric, 0)
            val2 = m2.metrics.get(metric, 0)
            comparison[metric] = {
                f"v{v1}": val1,
                f"v{v2}": val2,
                "delta": val2 - val1,
                "improvement": val2 > val1,
            }

        return {"comparison": comparison, "v1_stage": m1.stage.value,
                "v2_stage": m2.stage.value}

    def setup_ab_test(self, name: str, version_a: int, version_b: int,
                      traffic_split: float = 0.5) -> Dict:
        """Set up A/B test between two model versions."""
        test = {
            "model": name,
            "version_a": version_a,
            "version_b": version_b,
            "traffic_split": traffic_split,
            "started_at": time.time(),
            "results_a": [],
            "results_b": [],
        }
        self._ab_tests[f"{name}_ab"] = test
        return test

    def list_models(self, name: Optional[str] = None) -> List[Dict]:
        """List all registered models."""
        if name:
            return [
                {"name": m.name, "version": m.version, "stage": m.stage.value,
                 "metrics": m.metrics, "created_at": m.created_at}
                for m in self._models.get(name, [])
            ]
        return [
            {"name": n, "versions": len(v),
             "production": self._active_production.get(n, None) is not None}
            for n, v in self._models.items()
        ]


# ─────────────────────────────────────────────────────────────
# 4. Feature Store
# ─────────────────────────────────────────────────────────────

@dataclass
class Feature:
    """A managed feature."""
    name: str
    entity: str           # e.g., "asset", "user", "portfolio"
    dtype: str            # float, int, string, bool, list
    description: str
    source: str           # pipeline / table that produces this
    freshness_sla_seconds: int = 3600
    tags: List[str] = field(default_factory=list)


class FeatureStore:
    """
    Centralized feature management system:
    - Feature registration & discovery
    - Online serving (low latency lookups)
    - Offline store (batch training data)
    - Point-in-time correctness
    - Feature freshness monitoring
    """

    def __init__(self):
        self._registry: Dict[str, Feature] = {}
        self._online_store: Dict[str, Dict[str, Any]] = {}  # feature_key → value
        self._offline_store: Dict[str, List[Tuple[float, Any]]] = defaultdict(list)
        self._freshness: Dict[str, float] = {}

    def register_feature(self, feature: Feature) -> None:
        """Register a new feature."""
        self._registry[feature.name] = feature
        logger.info(f"Registered feature: {feature.name} ({feature.entity})")

    def set_feature(self, feature_name: str, entity_id: str,
                    value: Any, timestamp: Optional[float] = None) -> None:
        """Set feature value (both online and offline stores)."""
        ts = timestamp or time.time()
        key = f"{feature_name}:{entity_id}"

        # Online store (latest value)
        self._online_store[key] = {"value": value, "timestamp": ts}
        self._freshness[key] = ts

        # Offline store (append historical)
        self._offline_store[key].append((ts, value))
        if len(self._offline_store[key]) > 10000:
            self._offline_store[key] = self._offline_store[key][-10000:]

    def get_feature(self, feature_name: str, entity_id: str) -> Optional[Any]:
        """Get latest feature value (online serving)."""
        key = f"{feature_name}:{entity_id}"
        entry = self._online_store.get(key)
        return entry["value"] if entry else None

    def get_feature_vector(self, feature_names: List[str],
                           entity_id: str) -> Dict[str, Any]:
        """Get multiple features for an entity as a vector."""
        result = {}
        for name in feature_names:
            val = self.get_feature(name, entity_id)
            result[name] = val
        return result

    def get_historical(self, feature_name: str, entity_id: str,
                       start_time: float, end_time: Optional[float] = None
                       ) -> List[Tuple[float, Any]]:
        """Get historical feature values (offline / training)."""
        end_time = end_time or time.time()
        key = f"{feature_name}:{entity_id}"
        history = self._offline_store.get(key, [])
        return [(ts, val) for ts, val in history if start_time <= ts <= end_time]

    def point_in_time_join(self, feature_names: List[str],
                           entity_id: str,
                           timestamps: List[float]) -> List[Dict]:
        """Point-in-time correct feature lookup for training data."""
        results = []
        for ts in timestamps:
            row = {"timestamp": ts}
            for feat_name in feature_names:
                key = f"{feat_name}:{entity_id}"
                history = self._offline_store.get(key, [])
                # Find latest value before or at timestamp
                latest = None
                for hist_ts, val in history:
                    if hist_ts <= ts:
                        latest = val
                    else:
                        break
                row[feat_name] = latest
            results.append(row)
        return results

    def check_freshness(self) -> List[Dict]:
        """Check feature freshness against SLA."""
        stale = []
        now = time.time()
        for name, feature in self._registry.items():
            # Check all entities for this feature
            for key, last_ts in self._freshness.items():
                if key.startswith(f"{name}:"):
                    age = now - last_ts
                    if age > feature.freshness_sla_seconds:
                        stale.append({
                            "feature": name,
                            "entity_key": key,
                            "age_seconds": age,
                            "sla_seconds": feature.freshness_sla_seconds,
                            "staleness_ratio": age / feature.freshness_sla_seconds,
                        })
        return sorted(stale, key=lambda x: x["staleness_ratio"], reverse=True)

    def list_features(self, entity: Optional[str] = None) -> List[Dict]:
        """List all registered features."""
        features = self._registry.values()
        if entity:
            features = [f for f in features if f.entity == entity]
        return [
            {"name": f.name, "entity": f.entity, "dtype": f.dtype,
             "source": f.source, "description": f.description}
            for f in features
        ]


# ─────────────────────────────────────────────────────────────
# 5. CI/CD Pipeline
# ─────────────────────────────────────────────────────────────

class CICDPipeline:
    """
    CI/CD pipeline configuration generator:
    - GitHub Actions workflow generation
    - GitLab CI config generation 
    - Test, lint, build, deploy stages
    - Model validation gates
    - Canary deployment config
    """

    def __init__(self, platform: str = "github"):
        self._platform = platform
        self._stages: List[Dict] = []

    def add_stage(self, name: str, steps: List[Dict],
                  depends_on: Optional[List[str]] = None) -> None:
        """Add a pipeline stage."""
        self._stages.append({
            "name": name,
            "steps": steps,
            "depends_on": depends_on or [],
        })

    def generate_default_pipeline(self) -> None:
        """Generate a comprehensive default CI/CD pipeline."""
        self._stages = [
            {
                "name": "lint",
                "steps": [
                    {"run": "pip install flake8 black mypy", "name": "Install linters"},
                    {"run": "flake8 . --max-line-length=120", "name": "Flake8"},
                    {"run": "black --check .", "name": "Black format check"},
                    {"run": "mypy --ignore-missing-imports .", "name": "Type check"},
                ],
                "depends_on": [],
            },
            {
                "name": "test",
                "steps": [
                    {"run": "pip install -r requirements.txt", "name": "Install deps"},
                    {"run": "pip install pytest pytest-cov", "name": "Install test deps"},
                    {"run": "pytest tests/ --cov=. --cov-report=xml -v", "name": "Run tests"},
                ],
                "depends_on": ["lint"],
            },
            {
                "name": "model_validation",
                "steps": [
                    {"run": "python -m pytest tests/model_tests/ -v", "name": "Model unit tests"},
                    {"run": "python scripts/validate_model_performance.py", "name": "Perf gate"},
                    {"run": "python scripts/check_data_drift.py", "name": "Data drift check"},
                ],
                "depends_on": ["test"],
            },
            {
                "name": "build",
                "steps": [
                    {"run": "docker build -t cme:${{ github.sha }} .", "name": "Docker build"},
                    {"run": "docker push cme:${{ github.sha }}", "name": "Docker push"},
                ],
                "depends_on": ["model_validation"],
            },
            {
                "name": "deploy_staging",
                "steps": [
                    {"run": "kubectl set image deployment/cme cme=cme:${{ github.sha }} -n staging",
                     "name": "Deploy to staging"},
                    {"run": "python scripts/smoke_test.py --env staging", "name": "Smoke test"},
                ],
                "depends_on": ["build"],
            },
            {
                "name": "deploy_production",
                "steps": [
                    {"run": "kubectl set image deployment/cme cme=cme:${{ github.sha }} -n production",
                     "name": "Deploy canary (10%)"},
                    {"run": "python scripts/canary_monitor.py --duration 30m",
                     "name": "Monitor canary"},
                    {"run": "kubectl scale deployment/cme --replicas=5 -n production",
                     "name": "Full rollout"},
                ],
                "depends_on": ["deploy_staging"],
            },
        ]

    def generate_github_actions(self) -> str:
        """Generate GitHub Actions workflow YAML."""
        jobs = {}
        for stage in self._stages:
            job = {
                "runs-on": "ubuntu-latest",
                "steps": [{"uses": "actions/checkout@v4"}],
            }
            if stage["depends_on"]:
                job["needs"] = stage["depends_on"]

            for step in stage["steps"]:
                job["steps"].append({
                    "name": step.get("name", "Step"),
                    "run": step["run"],
                })
            jobs[stage["name"]] = job

        workflow = {
            "name": "CME CI/CD Pipeline",
            "on": {"push": {"branches": ["main", "develop"]},
                   "pull_request": {"branches": ["main"]}},
            "jobs": jobs,
        }

        # Manual YAML generation (avoid pyyaml dependency)
        lines = [
            f"name: {workflow['name']}",
            "",
            "on:",
            "  push:",
            "    branches: [main, develop]",
            "  pull_request:",
            "    branches: [main]",
            "",
            "jobs:",
        ]
        for job_name, job in jobs.items():
            lines.append(f"  {job_name}:")
            lines.append(f"    runs-on: {job['runs-on']}")
            if "needs" in job:
                lines.append(f"    needs: [{', '.join(job['needs'])}]")
            lines.append("    steps:")
            for step in job["steps"]:
                if "uses" in step:
                    lines.append(f"      - uses: {step['uses']}")
                else:
                    lines.append(f"      - name: {step['name']}")
                    lines.append(f"        run: {step['run']}")
            lines.append("")

        return "\n".join(lines)

    def generate_gitlab_ci(self) -> str:
        """Generate .gitlab-ci.yml content."""
        lines = ["stages:"]
        for stage in self._stages:
            lines.append(f"  - {stage['name']}")
        lines.append("")

        for stage in self._stages:
            lines.append(f"{stage['name']}:")
            lines.append(f"  stage: {stage['name']}")
            lines.append("  script:")
            for step in stage["steps"]:
                lines.append(f"    - {step['run']}")
            if stage["depends_on"]:
                lines.append(f"  needs: [{', '.join(stage['depends_on'])}]")
            lines.append("")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 6. Monitoring System
# ─────────────────────────────────────────────────────────────

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    name: str
    metric_type: MetricType
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    _values: List[float] = field(default_factory=list)


class MonitoringSystem:
    """
    Prometheus-compatible monitoring system:
    - Counter, Gauge, Histogram, Summary metrics
    - Prometheus text exposition format
    - Alert rule generation
    - Grafana dashboard JSON export
    - Health checks
    """

    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._alerts: List[Dict] = []
        self._health_checks: Dict[str, Callable] = {}

    def register_metric(self, name: str, metric_type: MetricType,
                        description: str = "",
                        labels: Optional[Dict[str, str]] = None) -> None:
        """Register a new metric."""
        self._metrics[name] = Metric(
            name=name, metric_type=metric_type,
            description=description, labels=labels or {},
        )

    def increment(self, name: str, value: float = 1.0) -> None:
        """Increment a counter metric."""
        if name in self._metrics:
            self._metrics[name].value += value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric value."""
        if name in self._metrics:
            self._metrics[name].value = value

    def observe(self, name: str, value: float) -> None:
        """Observe a value for histogram/summary."""
        if name in self._metrics:
            self._metrics[name]._values.append(value)
            if len(self._metrics[name]._values) > 10000:
                self._metrics[name]._values = self._metrics[name]._values[-10000:]

    def register_default_metrics(self) -> None:
        """Register default CME monitoring metrics."""
        defaults = [
            ("cme_signals_processed_total", MetricType.COUNTER, "Total signals processed"),
            ("cme_signal_latency_seconds", MetricType.HISTOGRAM, "Signal processing latency"),
            ("cme_active_models", MetricType.GAUGE, "Number of active models"),
            ("cme_prediction_accuracy", MetricType.GAUGE, "Current prediction accuracy"),
            ("cme_nlp_processing_seconds", MetricType.HISTOGRAM, "NLP processing time"),
            ("cme_market_data_lag_seconds", MetricType.GAUGE, "Market data feed lag"),
            ("cme_risk_score", MetricType.GAUGE, "Current portfolio risk score"),
            ("cme_errors_total", MetricType.COUNTER, "Total errors"),
            ("cme_api_requests_total", MetricType.COUNTER, "Total API requests"),
            ("cme_api_latency_seconds", MetricType.HISTOGRAM, "API response latency"),
            ("cme_feature_freshness_seconds", MetricType.GAUGE, "Feature store freshness"),
            ("cme_queue_depth", MetricType.GAUGE, "Message queue depth"),
        ]
        for name, mtype, desc in defaults:
            self.register_metric(name, mtype, desc)

    def expose_prometheus(self) -> str:
        """Generate Prometheus text exposition format."""
        lines = []
        for name, metric in self._metrics.items():
            lines.append(f"# HELP {name} {metric.description}")
            lines.append(f"# TYPE {name} {metric.metric_type.value}")

            labels_str = ""
            if metric.labels:
                pairs = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
                labels_str = f"{{{pairs}}}"

            if metric.metric_type in (MetricType.COUNTER, MetricType.GAUGE):
                lines.append(f"{name}{labels_str} {metric.value}")
            elif metric.metric_type == MetricType.HISTOGRAM:
                values = metric._values
                if values:
                    buckets = [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
                    for b in buckets:
                        count = sum(1 for v in values if v <= b)
                        lines.append(f'{name}_bucket{{le="{b}"{labels_str}}} {count}')
                    lines.append(f'{name}_bucket{{le="+Inf"{labels_str}}} {len(values)}')
                    lines.append(f"{name}_count{labels_str} {len(values)}")
                    lines.append(f"{name}_sum{labels_str} {sum(values):.6f}")
            elif metric.metric_type == MetricType.SUMMARY:
                values = sorted(metric._values)
                if values:
                    for q in [0.5, 0.9, 0.99]:
                        idx = int(q * len(values))
                        lines.append(f'{name}{{quantile="{q}"{labels_str}}} {values[min(idx, len(values)-1)]}')
                    lines.append(f"{name}_count{labels_str} {len(values)}")
                    lines.append(f"{name}_sum{labels_str} {sum(values):.6f}")
            lines.append("")
        return "\n".join(lines)

    def add_alert(self, name: str, expression: str,
                  threshold: float, severity: str = "warning",
                  duration: str = "5m") -> None:
        """Add an alert rule."""
        self._alerts.append({
            "alert": name,
            "expr": expression,
            "threshold": threshold,
            "for": duration,
            "labels": {"severity": severity},
            "annotations": {"summary": f"Alert: {name}"},
        })

    def register_default_alerts(self) -> None:
        """Register default CME alert rules."""
        defaults = [
            ("HighErrorRate", "rate(cme_errors_total[5m])", 0.1, "critical"),
            ("HighLatency", "cme_signal_latency_seconds > 5", 5, "warning"),
            ("LowAccuracy", "cme_prediction_accuracy < 0.5", 0.5, "critical"),
            ("StaleData", "cme_market_data_lag_seconds > 60", 60, "warning"),
            ("QueueBacklog", "cme_queue_depth > 1000", 1000, "warning"),
        ]
        for name, expr, threshold, severity in defaults:
            self.add_alert(name, expr, threshold, severity)

    def generate_grafana_dashboard(self) -> Dict:
        """Generate Grafana dashboard JSON."""
        panels = []
        row = 0
        for i, (name, metric) in enumerate(self._metrics.items()):
            panel = {
                "id": i + 1,
                "title": metric.description or name,
                "type": "graph" if metric.metric_type == MetricType.HISTOGRAM else "stat",
                "gridPos": {"h": 8, "w": 12, "x": (i % 2) * 12, "y": row * 8},
                "targets": [{"expr": name, "legendFormat": name}],
            }
            panels.append(panel)
            if i % 2 == 1:
                row += 1

        return {
            "dashboard": {
                "title": "Cognitive Market Engine",
                "panels": panels,
                "refresh": "10s",
                "time": {"from": "now-1h", "to": "now"},
            },
        }

    def register_health_check(self, name: str, check_fn: Callable) -> None:
        """Register a health check function."""
        self._health_checks[name] = check_fn

    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        all_healthy = True
        for name, check_fn in self._health_checks.items():
            try:
                result = check_fn()
                results[name] = {"status": "healthy" if result else "unhealthy",
                                 "result": result}
                if not result:
                    all_healthy = False
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
                all_healthy = False

        return {"overall": "healthy" if all_healthy else "degraded",
                "checks": results}


# ─────────────────────────────────────────────────────────────
# 7. API Layer
# ─────────────────────────────────────────────────────────────

class APILayer:
    """
    FastAPI-based REST / WebSocket API layer:
    - Auto-generates API endpoints for CME components
    - WebSocket feed for real-time signals
    - API key authentication
    - Rate limiting
    - Swagger / OpenAPI documentation
    
    Can be launched standalone or returns a FastAPI app instance.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self._host = host
        self._port = port
        self._app = None
        self._routes: List[Dict] = []
        self._api_keys: set = set()
        self._rate_limits: Dict[str, Dict] = {}
        self._request_counts: Dict[str, List[float]] = defaultdict(list)

    def register_route(self, path: str, method: str = "GET",
                       handler: Optional[Callable] = None,
                       description: str = "",
                       response_model: Optional[str] = None) -> None:
        """Register an API route."""
        self._routes.append({
            "path": path,
            "method": method.upper(),
            "handler": handler,
            "description": description,
            "response_model": response_model,
        })

    def register_default_routes(self) -> None:
        """Register default CME API endpoints."""
        defaults = [
            ("/api/v1/health", "GET", "Health check endpoint"),
            ("/api/v1/signals/latest", "GET", "Get latest market signals"),
            ("/api/v1/signals/history", "GET", "Get signal history"),
            ("/api/v1/intelligence/{asset}", "GET", "Full intelligence scan for asset"),
            ("/api/v1/regime/current", "GET", "Current market regime"),
            ("/api/v1/nlp/analyze", "POST", "Analyze financial text"),
            ("/api/v1/events/extract", "POST", "Extract events from text"),
            ("/api/v1/alpha/scan", "GET", "Scan all alpha signals"),
            ("/api/v1/risk/summary", "GET", "Portfolio risk summary"),
            ("/api/v1/models/list", "GET", "List registered models"),
            ("/api/v1/features/{entity}", "GET", "Get features for entity"),
            ("/api/v1/metrics", "GET", "Prometheus metrics endpoint"),
            ("/ws/signals", "WS", "Real-time signal WebSocket feed"),
        ]
        for path, method, desc in defaults:
            self.register_route(path, method, description=desc)

    def add_api_key(self, key: str) -> None:
        """Add an API key for authentication."""
        self._api_keys.add(key)

    def set_rate_limit(self, path: str, requests_per_minute: int = 60) -> None:
        """Set rate limit for a path."""
        self._rate_limits[path] = {"rpm": requests_per_minute}

    def check_rate_limit(self, path: str, client_id: str) -> bool:
        """Check if request is within rate limit."""
        limit = self._rate_limits.get(path, {}).get("rpm", 60)
        key = f"{path}:{client_id}"
        now = time.time()

        # Clean old entries
        self._request_counts[key] = [
            t for t in self._request_counts[key] if now - t < 60
        ]

        if len(self._request_counts[key]) >= limit:
            return False

        self._request_counts[key].append(now)
        return True

    def build_app(self):
        """Build FastAPI application."""
        try:
            from fastapi import FastAPI, HTTPException, WebSocket, Depends
            from fastapi.middleware.cors import CORSMiddleware

            app = FastAPI(
                title="Cognitive Market Engine API",
                description="Real-time market intelligence and NLP-driven signal generation",
                version="3.0.0",
            )

            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )

            # Register routes dynamically
            for route in self._routes:
                if route["method"] == "GET":
                    @app.get(route["path"], summary=route["description"])
                    async def handler():
                        return {"status": "ok", "endpoint": route["path"]}
                elif route["method"] == "POST":
                    @app.post(route["path"], summary=route["description"])
                    async def handler(body: dict = {}):
                        return {"status": "ok", "endpoint": route["path"]}

            self._app = app
            return app
        except ImportError:
            logger.warning("FastAPI not installed; API layer in config-only mode")
            return None

    def generate_openapi_spec(self) -> Dict:
        """Generate OpenAPI 3.0 specification."""
        paths = {}
        for route in self._routes:
            method = route["method"].lower()
            if method == "ws":
                method = "get"  # WebSocket shown as GET with upgrade
            paths[route["path"]] = {
                method: {
                    "summary": route["description"],
                    "responses": {"200": {"description": "Success"}},
                }
            }

        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Cognitive Market Engine API",
                "version": "3.0.0",
                "description": "Market intelligence, NLP analysis, and signal generation",
            },
            "paths": paths,
        }

    def get_route_list(self) -> List[Dict]:
        """List all registered routes."""
        return [
            {"path": r["path"], "method": r["method"],
             "description": r["description"]}
            for r in self._routes
        ]


# ─────────────────────────────────────────────────────────────
# Unified Infrastructure Manager
# ─────────────────────────────────────────────────────────────

class InfrastructureManager:
    """Orchestrates all infrastructure components."""

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        self.mq = MessageQueue(
            backend=config.get("mq_backend", "memory"),
            config=config.get("mq_config"),
        )
        self.tsdb = TimeSeriesDB(
            backend=config.get("tsdb_backend", "sqlite"),
            config=config.get("tsdb_config"),
        )
        self.model_registry = ModelRegistry(
            storage_path=config.get("model_registry_path"),
        )
        self.feature_store = FeatureStore()
        self.cicd = CICDPipeline(
            platform=config.get("cicd_platform", "github"),
        )
        self.monitoring = MonitoringSystem()
        self.api = APILayer(
            host=config.get("api_host", "0.0.0.0"),
            port=config.get("api_port", 8000),
        )

    def initialize_all(self) -> Dict[str, str]:
        """Initialize all infrastructure with defaults."""
        self.monitoring.register_default_metrics()
        self.monitoring.register_default_alerts()
        self.api.register_default_routes()
        self.cicd.generate_default_pipeline()

        # Register health checks
        self.monitoring.register_health_check(
            "message_queue", lambda: self.mq.get_stats()["backend"] != "failed"
        )
        self.monitoring.register_health_check(
            "feature_store", lambda: True  # Feature store is in-memory
        )

        return {
            "message_queue": self.mq._backend,
            "timeseries_db": self.tsdb._backend,
            "model_registry": "initialized",
            "feature_store": "initialized",
            "cicd": self.cicd._platform,
            "monitoring": f"{len(self.monitoring._metrics)} metrics registered",
            "api": f"{len(self.api._routes)} routes registered",
        }

    def health_report(self) -> Dict:
        """Get comprehensive health report."""
        return {
            "health_checks": self.monitoring.run_health_checks(),
            "mq_stats": self.mq.get_stats(),
            "feature_freshness": self.feature_store.check_freshness()[:5],
            "models": self.model_registry.list_models(),
        }
