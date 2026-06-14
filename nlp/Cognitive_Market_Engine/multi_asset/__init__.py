"""
Multi-Asset Analysis — Priority 3 Module

Cross-asset correlation engine, contagion modeling,
and global macro state tracking.
"""

from .correlation_engine import CorrelationEngine
from .contagion_model import ContagionModel

__all__ = ["CorrelationEngine", "ContagionModel"]
