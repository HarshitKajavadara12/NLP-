"""Data package — market data feeds and storage."""

try:
    from .market_data_feed import MarketDataFeed, MarketSnapshot
except ImportError:
    pass
