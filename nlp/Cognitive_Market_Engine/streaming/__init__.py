"""
Streaming Pipeline — Priority 3 Module

Real-time event-driven processing pipeline.
"""

from .pipeline import StreamingPipeline
from .event_bus import EventBus

__all__ = ["StreamingPipeline", "EventBus"]
