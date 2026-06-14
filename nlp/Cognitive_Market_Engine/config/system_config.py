"""
System Configuration

Central configuration file for the entire 7-phase NLP-driven trading pipeline.
All settings, thresholds, and parameters in one place.
"""

import os
import logging
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger("cme.config")


def _clamp(value: float, low: float, high: float, name: str) -> float:
    """Clamp a value to [low, high] and warn if adjusted."""
    if value < low:
        logger.warning(f"Config '{name}' = {value} below minimum {low}, clamping")
        return low
    if value > high:
        logger.warning(f"Config '{name}' = {value} above maximum {high}, clamping")
        return high
    return value

# ============================================================================
# SYSTEM PATHS (cross-platform)
# ============================================================================

SYSTEM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SYSTEM_ROOT, "data")
CONFIG_DIR = os.path.join(SYSTEM_ROOT, "config")
LOG_DIR = os.path.join(SYSTEM_ROOT, "logs")

# Ensure directories exist
for _dir in [DATA_DIR, LOG_DIR]:
    os.makedirs(_dir, exist_ok=True)

# Database paths
NEWS_CACHE_DB = os.path.join(DATA_DIR, "news_cache.db")
RESEARCH_DB = os.path.join(DATA_DIR, "research.db")
SIGNAL_CACHE_DB = os.path.join(DATA_DIR, "signal_cache.db")
EXECUTION_DB = os.path.join(DATA_DIR, "execution.db")

# ============================================================================
# PHASE CONFIGURATION
# ============================================================================

@dataclass
class NewsIngestionConfig:
    """Phase 1: News Acquisition & Preprocessing"""
    # Sources
    sources: List[str] = None  # Reuters, Bloomberg, Twitter, etc.
    update_frequency_seconds: int = 60
    max_articles_per_batch: int = 100
    
    # Text preprocessing
    min_article_length: int = 50  # words
    max_article_length: int = 5000
    remove_duplicates: bool = True
    
    # Cache
    cache_db_path: str = NEWS_CACHE_DB
    cache_retention_days: int = 30
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = [
                "reuters",
                "bloomberg",
                "cnbc",
                "marketwatch",
                "seeking_alpha",
            ]
        self.update_frequency_seconds = max(10, self.update_frequency_seconds)
        self.max_articles_per_batch = max(1, min(1000, self.max_articles_per_batch))
        self.min_article_length = max(0, self.min_article_length)
        self.max_article_length = max(self.min_article_length + 1, self.max_article_length)
        self.cache_retention_days = max(1, self.cache_retention_days)


@dataclass
class CognitiveModelConfig:
    """Phase 2: Participant Cognitive Models"""
    # Participant types
    participants: List[str] = None
    
    # Model parameters
    sentiment_weight: float = 0.4
    intensity_weight: float = 0.3
    ambiguity_penalty: float = 0.15
    
    # Cache
    model_update_frequency_hours: int = 24
    profiles_yaml_path: str = ""
    
    def __post_init__(self):
        if self.participants is None:
            self.participants = [
                "bank",
                "hft",
                "hedge_fund",
                "market_maker",
                "retail",
            ]
        self.sentiment_weight = _clamp(self.sentiment_weight, 0.0, 1.0, "sentiment_weight")
        self.intensity_weight = _clamp(self.intensity_weight, 0.0, 1.0, "intensity_weight")
        self.ambiguity_penalty = _clamp(self.ambiguity_penalty, 0.0, 1.0, "ambiguity_penalty")
        self.model_update_frequency_hours = max(1, self.model_update_frequency_hours)


@dataclass
class BehaviorTranslationConfig:
    """Phase 3: Expectation → Behavior Translation"""
    # Constraint types
    regulatory_constraint_weight: float = 0.2
    risk_limit_constraint_weight: float = 0.3
    capital_constraint_weight: float = 0.2
    inventory_constraint_weight: float = 0.25
    
    # Behavior dimensions
    max_risk_aversion: float = 0.95
    min_liquidity_focus: float = 0.1
    max_urgency: float = 0.99
    
    def __post_init__(self):
        self.regulatory_constraint_weight = _clamp(self.regulatory_constraint_weight, 0.0, 1.0, "regulatory_constraint_weight")
        self.risk_limit_constraint_weight = _clamp(self.risk_limit_constraint_weight, 0.0, 1.0, "risk_limit_constraint_weight")
        self.capital_constraint_weight = _clamp(self.capital_constraint_weight, 0.0, 1.0, "capital_constraint_weight")
        self.inventory_constraint_weight = _clamp(self.inventory_constraint_weight, 0.0, 1.0, "inventory_constraint_weight")
        self.max_risk_aversion = _clamp(self.max_risk_aversion, 0.0, 1.0, "max_risk_aversion")
        self.min_liquidity_focus = _clamp(self.min_liquidity_focus, 0.0, 1.0, "min_liquidity_focus")
        self.max_urgency = _clamp(self.max_urgency, 0.0, 1.0, "max_urgency")


@dataclass
class MarketImpactConfig:
    """Phase 4: Behavior → Market Impact Modeling"""
    # Non-linearity
    impact_scaling_power: float = 1.5  # Non-linear aggregation
    hft_dominance_threshold: float = 0.8
    
    # Time windows
    shock_window_seconds: int = 60
    digestion_window_seconds: int = 900
    institutional_window_seconds: int = 7200
    structural_window_seconds: int = 86400
    
    # Impact bounds
    max_directional_impact: float = 1.0
    max_vol_impact: float = 2.5
    max_liquidity_impact: float = 3.0
    
    def __post_init__(self):
        self.impact_scaling_power = _clamp(self.impact_scaling_power, 0.5, 5.0, "impact_scaling_power")
        self.hft_dominance_threshold = _clamp(self.hft_dominance_threshold, 0.0, 1.0, "hft_dominance_threshold")
        self.shock_window_seconds = max(1, self.shock_window_seconds)
        self.digestion_window_seconds = max(self.shock_window_seconds, self.digestion_window_seconds)
        self.institutional_window_seconds = max(self.digestion_window_seconds, self.institutional_window_seconds)
        self.structural_window_seconds = max(self.institutional_window_seconds, self.structural_window_seconds)
        self.max_directional_impact = _clamp(self.max_directional_impact, 0.01, 10.0, "max_directional_impact")
        self.max_vol_impact = _clamp(self.max_vol_impact, 0.01, 20.0, "max_vol_impact")
        self.max_liquidity_impact = _clamp(self.max_liquidity_impact, 0.01, 20.0, "max_liquidity_impact")


@dataclass
class RealityValidationConfig:
    """Phase 5: Market Reality Validation"""
    # Validation thresholds
    directional_accuracy_threshold: float = 0.65  # >65% = reliable
    volatility_accuracy_threshold: float = 0.60
    timing_accuracy_tolerance_seconds: Dict[str, int] = None
    
    # Credibility scoring
    credibility_threshold_reliable: float = 0.65
    credibility_threshold_degraded: float = 0.50
    
    # Database
    validation_db_path: str = RESEARCH_DB
    record_retention_days: int = 365
    
    def __post_init__(self):
        if self.timing_accuracy_tolerance_seconds is None:
            self.timing_accuracy_tolerance_seconds = {
                "shock": 30,
                "peak": 300,
                "recovery": 900,
            }
        self.directional_accuracy_threshold = _clamp(self.directional_accuracy_threshold, 0.0, 1.0, "directional_accuracy_threshold")
        self.volatility_accuracy_threshold = _clamp(self.volatility_accuracy_threshold, 0.0, 1.0, "volatility_accuracy_threshold")
        self.credibility_threshold_reliable = _clamp(self.credibility_threshold_reliable, 0.0, 1.0, "credibility_threshold_reliable")
        self.credibility_threshold_degraded = _clamp(self.credibility_threshold_degraded, 0.0, 1.0, "credibility_threshold_degraded")
        if self.credibility_threshold_degraded >= self.credibility_threshold_reliable:
            logger.warning("credibility_threshold_degraded >= credibility_threshold_reliable; adjusting")
            self.credibility_threshold_degraded = self.credibility_threshold_reliable - 0.1
        self.record_retention_days = max(1, self.record_retention_days)
        # Validate timing tolerance values
        for key in ["shock", "peak", "recovery"]:
            if key in self.timing_accuracy_tolerance_seconds:
                self.timing_accuracy_tolerance_seconds[key] = max(1, self.timing_accuracy_tolerance_seconds[key])


@dataclass
class SignalAuthorizationConfig:
    """Phase 6: Signal Authorization & Trust Weighting"""
    # Trust thresholds
    trust_threshold_approved: float = 0.60
    trust_threshold_warning: float = 0.50
    trust_threshold_unreliable: float = 0.40
    
    # Weighting
    historical_weight: float = 0.60
    current_validation_weight: float = 0.40
    
    # Signal parameters
    signal_expiration_hours: int = 4
    signal_strength_floor: float = 0.0
    signal_strength_ceiling: float = 1.0
    
    # Database
    signal_cache_db_path: str = SIGNAL_CACHE_DB
    max_concurrent_signals: int = 50
    
    def __post_init__(self):
        self.trust_threshold_approved = _clamp(self.trust_threshold_approved, 0.0, 1.0, "trust_threshold_approved")
        self.trust_threshold_warning = _clamp(self.trust_threshold_warning, 0.0, 1.0, "trust_threshold_warning")
        self.trust_threshold_unreliable = _clamp(self.trust_threshold_unreliable, 0.0, 1.0, "trust_threshold_unreliable")
        self.historical_weight = _clamp(self.historical_weight, 0.0, 1.0, "historical_weight")
        self.current_validation_weight = _clamp(self.current_validation_weight, 0.0, 1.0, "current_validation_weight")
        # Weights should sum to ~1.0
        total_w = self.historical_weight + self.current_validation_weight
        if abs(total_w - 1.0) > 0.01:
            logger.warning(f"Signal auth weights sum to {total_w:.2f}, renormalizing to 1.0")
            self.historical_weight /= total_w
            self.current_validation_weight /= total_w
        self.signal_expiration_hours = max(1, self.signal_expiration_hours)
        self.signal_strength_floor = _clamp(self.signal_strength_floor, 0.0, 1.0, "signal_strength_floor")
        self.signal_strength_ceiling = _clamp(self.signal_strength_ceiling, 0.0, 1.0, "signal_strength_ceiling")
        if self.signal_strength_floor >= self.signal_strength_ceiling:
            logger.warning("signal_strength_floor >= signal_strength_ceiling; resetting")
            self.signal_strength_floor = 0.0
            self.signal_strength_ceiling = 1.0
        self.max_concurrent_signals = max(1, self.max_concurrent_signals)


@dataclass
class ExecutionConfig:
    """Phase 7: Execution & Live Trading"""
    # Position sizing
    max_position_size_dollars: float = 1_000_000.0
    max_portfolio_exposure_pct: float = 0.80  # 80% of capital
    position_scaling_exponent: float = 2.0  # Signal_strength^2
    
    # Risk management
    daily_loss_limit_dollars: float = -50_000.0
    intraday_drawdown_limit_dollars: float = -30_000.0
    volatility_spike_threshold: float = 2.5  # 2.5x normal vol
    
    # Execution algorithms
    aggressive_execution_seconds: int = 5
    vwap_execution_seconds: int = 60
    passive_execution_seconds: int = 300
    
    # Broker integration
    use_live_execution: bool = False  # False for simulation/research
    broker_api_key: str = "PLACEHOLDER"
    broker_endpoint: str = "https://api.broker.com"
    
    # Database
    execution_db_path: str = EXECUTION_DB
    order_retention_days: int = 365
    
    def __post_init__(self):
        self.max_position_size_dollars = max(0, self.max_position_size_dollars)
        self.max_portfolio_exposure_pct = _clamp(self.max_portfolio_exposure_pct, 0.01, 1.0, "max_portfolio_exposure_pct")
        self.position_scaling_exponent = _clamp(self.position_scaling_exponent, 0.5, 5.0, "position_scaling_exponent")
        if self.daily_loss_limit_dollars > 0:
            logger.warning("daily_loss_limit_dollars should be negative (it's a loss limit)")
            self.daily_loss_limit_dollars = -abs(self.daily_loss_limit_dollars)
        if self.intraday_drawdown_limit_dollars > 0:
            logger.warning("intraday_drawdown_limit_dollars should be negative")
            self.intraday_drawdown_limit_dollars = -abs(self.intraday_drawdown_limit_dollars)
        self.volatility_spike_threshold = _clamp(self.volatility_spike_threshold, 1.0, 10.0, "volatility_spike_threshold")
        self.aggressive_execution_seconds = max(1, self.aggressive_execution_seconds)
        self.vwap_execution_seconds = max(self.aggressive_execution_seconds, self.vwap_execution_seconds)
        self.passive_execution_seconds = max(self.vwap_execution_seconds, self.passive_execution_seconds)
        self.order_retention_days = max(1, self.order_retention_days)


@dataclass
class SystemConfig:
    """Master system configuration"""
    # Environment
    environment: str = "research"  # research, staging, production
    debug_mode: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: str = ""
    
    # Components
    news_ingestion: NewsIngestionConfig = None
    cognitive_model: CognitiveModelConfig = None
    behavior_translation: BehaviorTranslationConfig = None
    market_impact: MarketImpactConfig = None
    reality_validation: RealityValidationConfig = None
    signal_authorization: SignalAuthorizationConfig = None
    execution: ExecutionConfig = None
    
    # System parameters
    pipeline_update_interval_seconds: int = 60
    max_concurrent_events: int = 100
    enable_feedback_loop: bool = True
    
    def __post_init__(self):
        """Initialize all sub-configs if not provided, with validation."""
        # Validate environment
        valid_envs = {"research", "staging", "production"}
        if self.environment not in valid_envs:
            logger.warning(f"Unknown environment '{self.environment}', defaulting to 'research'")
            self.environment = "research"
        
        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            logger.warning(f"Unknown log_level '{self.log_level}', defaulting to 'INFO'")
            self.log_level = "INFO"
        else:
            self.log_level = self.log_level.upper()
        
        if not self.log_file:
            self.log_file = os.path.join(LOG_DIR, "system.log")
        
        self.pipeline_update_interval_seconds = max(5, self.pipeline_update_interval_seconds)
        self.max_concurrent_events = max(1, min(10000, self.max_concurrent_events))
        
        if self.news_ingestion is None:
            self.news_ingestion = NewsIngestionConfig()
        if self.cognitive_model is None:
            self.cognitive_model = CognitiveModelConfig()
        if self.behavior_translation is None:
            self.behavior_translation = BehaviorTranslationConfig()
        if self.market_impact is None:
            self.market_impact = MarketImpactConfig()
        if self.reality_validation is None:
            self.reality_validation = RealityValidationConfig()
        if self.signal_authorization is None:
            self.signal_authorization = SignalAuthorizationConfig()
        if self.execution is None:
            self.execution = ExecutionConfig()
        
        # Safety: production mode should not have debug enabled
        if self.environment == "production" and self.debug_mode:
            logger.warning("Debug mode enabled in production — disabling for safety")
            self.debug_mode = False


# ============================================================================
# GLOBAL CONFIG INSTANCE
# ============================================================================

# This is loaded once at system startup
SYSTEM_CONFIG = SystemConfig()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config() -> SystemConfig:
    """Get the global system configuration"""
    return SYSTEM_CONFIG


def reload_config(environment: str = "research") -> SystemConfig:
    """Reload configuration from environment"""
    global SYSTEM_CONFIG
    SYSTEM_CONFIG = SystemConfig(environment=environment)
    return SYSTEM_CONFIG


def get_phase_config(phase: int):
    """Get configuration for specific phase"""
    configs = {
        1: SYSTEM_CONFIG.news_ingestion,
        2: SYSTEM_CONFIG.cognitive_model,
        3: SYSTEM_CONFIG.behavior_translation,
        4: SYSTEM_CONFIG.market_impact,
        5: SYSTEM_CONFIG.reality_validation,
        6: SYSTEM_CONFIG.signal_authorization,
        7: SYSTEM_CONFIG.execution,
    }
    return configs.get(phase)
