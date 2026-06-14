"""
EVENT BUS — Publish-subscribe event system for the cognitive engine

All modules communicate through events:
- NewsEvent: New article/statement arrives
- ParseComplete: NLP parsing finished
- InterpretationReady: Participant models done
- SignalGenerated: Trading signal produced
- ValidationUpdate: Reality check completed

This enables loose coupling and real-time streaming.
"""

import threading
import queue
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import uuid


@dataclass
class Event:
    """Base event in the system."""
    event_type: str = ""
    event_id: str = ""
    timestamp: str = ""
    payload: Dict = field(default_factory=dict)
    source: str = ""
    priority: int = 5  # 1=highest, 10=lowest
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())[:12]
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# Pre-defined event types
class EventTypes:
    # Data ingestion
    NEWS_RAW = "news.raw"
    NEWS_PARSED = "news.parsed"
    NEWS_ENRICHED = "news.enriched"
    
    # NLP
    NLP_ENTITIES = "nlp.entities"
    NLP_INTENT = "nlp.intent"
    NLP_CONTRADICTION = "nlp.contradiction"
    
    # Cognitive processing
    INTERPRETATION_READY = "cognitive.interpretation"
    BEHAVIOR_COMPUTED = "cognitive.behavior"
    IMPACT_COMPUTED = "cognitive.impact"
    
    # Validation
    VALIDATION_COMPLETE = "validation.complete"
    CREDIBILITY_UPDATE = "validation.credibility"
    
    # Signals
    SIGNAL_GENERATED = "signal.generated"
    SIGNAL_APPROVED = "signal.approved"
    SIGNAL_REJECTED = "signal.rejected"
    SIGNAL_EXECUTED = "signal.executed"
    
    # Hidden truth
    OMISSION_DETECTED = "truth.omission"
    CONTRADICTION_FOUND = "truth.contradiction"
    NARRATIVE_SHIFT = "truth.narrative_shift"
    
    # Scenario
    SCENARIO_GENERATED = "scenario.generated"
    SCENARIO_INVALIDATED = "scenario.invalidated"
    
    # System
    SYSTEM_ALERT = "system.alert"
    SYSTEM_METRIC = "system.metric"
    SYSTEM_ERROR = "system.error"


class EventBus:
    """
    Central publish-subscribe event bus for the Cognitive Market Engine.
    
    Features:
    - Topic-based pub/sub
    - Priority queue processing
    - Synchronous and async handlers
    - Event history for replay
    - Dead letter queue for failed events
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize EventBus.
        
        Args:
            max_history: Max events to retain in history
        """
        self._subscribers = defaultdict(list)  # event_type -> [(handler, filter)]
        self._wildcard_subscribers = []         # handlers for all events
        self._event_queue = queue.PriorityQueue()
        self._history = []
        self._max_history = max_history
        self._dead_letters = []
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread = None
        self._stats = defaultdict(int)
        
        print("[EVENT_BUS] Initialized")
    
    def subscribe(self, event_type: str, handler: Callable,
                  filter_fn: Callable = None):
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Event type to listen for (or "*" for all)
            handler: Callback function(event: Event) -> None
            filter_fn: Optional filter function(event: Event) -> bool
        """
        if event_type == "*":
            self._wildcard_subscribers.append((handler, filter_fn))
        else:
            self._subscribers[event_type].append((handler, filter_fn))
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Remove a subscription."""
        if event_type == "*":
            self._wildcard_subscribers = [
                (h, f) for h, f in self._wildcard_subscribers if h != handler
            ]
        else:
            self._subscribers[event_type] = [
                (h, f) for h, f in self._subscribers[event_type] if h != handler
            ]
    
    def publish(self, event: Event):
        """
        Publish an event for immediate synchronous delivery.
        
        Args:
            event: Event to publish
        """
        self._stats[event.event_type] += 1
        self._stats["total_published"] += 1
        
        # Store in history
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
        
        # Deliver to subscribers
        handlers = (
            self._subscribers.get(event.event_type, []) + 
            self._wildcard_subscribers
        )
        
        for handler, filter_fn in handlers:
            try:
                if filter_fn and not filter_fn(event):
                    continue
                handler(event)
                self._stats["total_delivered"] += 1
            except Exception as e:
                self._stats["total_errors"] += 1
                self._dead_letters.append({
                    "event": event,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                })
    
    def publish_async(self, event: Event):
        """
        Queue an event for asynchronous delivery.
        
        Args:
            event: Event to queue
        """
        self._event_queue.put((event.priority, event.timestamp, event))
    
    def emit(self, event_type: str, payload: Dict = None, 
             source: str = "", priority: int = 5) -> Event:
        """
        Convenience method: create and publish an event.
        
        Args:
            event_type: Type of event
            payload: Event data
            source: Source module
            priority: Priority (1=highest)
            
        Returns:
            The created Event
        """
        event = Event(
            event_type=event_type,
            payload=payload or {},
            source=source,
            priority=priority,
        )
        self.publish(event)
        return event
    
    def start(self):
        """Start async event processing."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._process_loop, daemon=True
        )
        self._worker_thread.start()
        print("[EVENT_BUS] Async processing started")
    
    def stop(self):
        """Stop async event processing."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        print("[EVENT_BUS] Stopped")
    
    def _process_loop(self):
        """Worker thread for async event processing."""
        while self._running:
            try:
                _, _, event = self._event_queue.get(timeout=1)
                self.publish(event)
            except queue.Empty:
                continue
            except Exception as e:
                self._stats["total_errors"] += 1
    
    # ================================================================
    # QUERY METHODS
    # ================================================================
    
    def get_history(self, event_type: str = None, 
                    limit: int = 50) -> List[Event]:
        """Get event history, optionally filtered by type."""
        with self._lock:
            if event_type:
                filtered = [e for e in self._history if e.event_type == event_type]
            else:
                filtered = list(self._history)
        
        return filtered[-limit:]
    
    def get_stats(self) -> Dict:
        """Get event bus statistics."""
        return {
            "total_published": self._stats["total_published"],
            "total_delivered": self._stats["total_delivered"],
            "total_errors": self._stats["total_errors"],
            "queue_size": self._event_queue.qsize(),
            "subscriber_count": sum(len(v) for v in self._subscribers.values()) + len(self._wildcard_subscribers),
            "history_size": len(self._history),
            "dead_letters": len(self._dead_letters),
            "event_type_counts": {
                k: v for k, v in self._stats.items()
                if k not in ("total_published", "total_delivered", "total_errors")
            },
        }
    
    def get_dead_letters(self, limit: int = 20) -> List[Dict]:
        """Get failed events."""
        return self._dead_letters[-limit:]
    
    def replay(self, event_type: str = None, since: str = None):
        """
        Replay historical events.
        
        Args:
            event_type: Filter by type
            since: Replay only events after this timestamp
        """
        events = self.get_history(event_type, limit=self._max_history)
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        for event in events:
            self.publish(event)
