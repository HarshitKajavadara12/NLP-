"""
SHARED TYPES — Canonical type definitions used across all modules.

This module provides the single source of truth for enumerated types
that appear in both the engine pipeline and the phase-based pipeline,
eliminating duplicate/incompatible definitions.
"""

from enum import Enum


class ParticipantType(str, Enum):
    """
    Canonical market participant classification.
    
    Used by: engine/, participant_cognition/, learning/, streaming/
    """
    RETAIL = "retail"
    HFT = "hft"
    HEDGE_FUND = "hedge_fund"
    BANK = "bank"
    MARKET_MAKER = "market_maker"


class TimeHorizon(str, Enum):
    """Time horizon classification."""
    MICROSECONDS = "microseconds"
    MILLISECONDS = "milliseconds"
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


class RiskTolerance(str, Enum):
    """Risk tolerance classification."""
    ULTRA_LOW = "ultra_low"
    LOW = "low"
    MEDIUM = "medium"
    ADAPTIVE = "adaptive"
    HIGH = "high"


class DirectionType(str, Enum):
    """Trading or prediction direction."""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


__all__ = [
    "ParticipantType",
    "TimeHorizon",
    "RiskTolerance",
    "DirectionType",
]
