"""
LEARNING — Self-learning feedback loop system.

Tracks prediction accuracy and adjusts model weights
using Phase 5 validation results.
"""

from .feedback_loop import FeedbackLoop, ModelCredibility, PredictionRecord

__all__ = ["FeedbackLoop", "ModelCredibility", "PredictionRecord"]
