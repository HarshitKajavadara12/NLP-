"""
MARKET DATA FEED — Live & simulated market data connector

Provides real-time price data for:
- RealityValidator (Phase 5) — validates predictions against actual prices
- ExecutionNexus (Phase 7) — current prices for order execution
- DecisionEngine — market regime detection

Data Sources (priority order):
1. CoinGecko free API (no key required, rate-limited)
2. Simulated fallback (Brownian motion around seed price)

Usage:
    feed = MarketDataFeed()
    price = feed.get_price("BTC")
    data = feed.get_market_snapshot("BTC")
"""

import time
import random
import math
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class MarketSnapshot:
    """Point-in-time market data snapshot."""
    asset: str
    price: float
    bid: float
    ask: float
    spread_bps: float
    volume_24h: float
    change_24h_pct: float
    volatility_estimate: float      # Annualized vol estimate
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "simulated"

    def to_dict(self) -> Dict:
        return {
            "asset": self.asset,
            "price": round(self.price, 2),
            "bid": round(self.bid, 2),
            "ask": round(self.ask, 2),
            "spread_bps": round(self.spread_bps, 1),
            "volume_24h": round(self.volume_24h, 0),
            "change_24h_pct": round(self.change_24h_pct, 3),
            "volatility_estimate": round(self.volatility_estimate, 4),
            "timestamp": self.timestamp,
            "source": self.source,
        }


class MarketDataFeed:
    """
    Market data feed with live API and simulated fallback.
    
    Automatically falls back to simulation if API is unavailable.
    Caches prices to respect rate limits.
    """
    
    # Seed prices for simulation (updated periodically)
    SEED_PRICES = {
        "BTC": 67000.0,
        "ETH": 3500.0,
        "SOL": 180.0,
        "SPY": 530.0,
        "GOLD": 2350.0,
        "DXY": 104.5,
    }
    
    ANNUAL_VOLS = {
        "BTC": 0.65,
        "ETH": 0.75,
        "SOL": 0.90,
        "SPY": 0.15,
        "GOLD": 0.12,
        "DXY": 0.06,
    }
    
    def __init__(self, use_live: bool = True, cache_ttl_seconds: int = 30):
        """
        Initialize market data feed.
        
        Args:
            use_live: Try live API first (falls back to simulation)
            cache_ttl_seconds: Cache duration for live data
        """
        self.use_live = use_live
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Dict] = {}
        self._sim_prices: Dict[str, float] = dict(self.SEED_PRICES)
        self._sim_last_update: Dict[str, float] = {}
        self._live_available = False
        
        # Test live API availability
        if use_live:
            self._live_available = self._test_live_api()
        
        print(f"[MARKET_DATA] Initialized (live={'available' if self._live_available else 'simulated'})")
    
    def _test_live_api(self) -> bool:
        """Test if CoinGecko API is reachable."""
        try:
            import requests
            resp = requests.get(
                "https://api.coingecko.com/api/v3/ping",
                timeout=5,
            )
            return resp.status_code == 200
        except Exception:
            return False
    
    def get_price(self, asset: str = "BTC") -> float:
        """
        Get current price for an asset.
        
        Args:
            asset: Asset symbol (BTC, ETH, SOL, SPY, etc.)
        
        Returns:
            Current price as float
        """
        snapshot = self.get_market_snapshot(asset)
        return snapshot.price
    
    def get_market_snapshot(self, asset: str = "BTC") -> MarketSnapshot:
        """
        Get full market snapshot for an asset.
        
        Tries live API first, falls back to simulation.
        """
        asset = asset.upper()
        
        # Check cache
        cached = self._cache.get(asset)
        if cached and time.time() - cached["time"] < self.cache_ttl:
            return cached["snapshot"]
        
        # Try live data
        if self._live_available and asset in ("BTC", "ETH", "SOL"):
            snapshot = self._fetch_live(asset)
            if snapshot:
                self._cache[asset] = {"snapshot": snapshot, "time": time.time()}
                return snapshot
        
        # Fall back to simulation
        snapshot = self._simulate(asset)
        self._cache[asset] = {"snapshot": snapshot, "time": time.time()}
        return snapshot
    
    def _fetch_live(self, asset: str) -> Optional[MarketSnapshot]:
        """Fetch live data from CoinGecko."""
        try:
            import requests
            
            coin_map = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
            }
            coin_id = coin_map.get(asset)
            if not coin_id:
                return None
            
            resp = requests.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                },
                timeout=10,
            )
            
            if resp.status_code != 200:
                return None
            
            data = resp.json().get(coin_id, {})
            price = data.get("usd", 0)
            if not price:
                return None
            
            vol = self.ANNUAL_VOLS.get(asset, 0.5)
            spread_bps = max(1, vol * 5)  # Tighter spread for lower vol
            
            return MarketSnapshot(
                asset=asset,
                price=price,
                bid=price * (1 - spread_bps / 10000),
                ask=price * (1 + spread_bps / 10000),
                spread_bps=spread_bps * 2,
                volume_24h=data.get("usd_24h_vol", 0),
                change_24h_pct=data.get("usd_24h_change", 0),
                volatility_estimate=vol,
                source="coingecko",
            )
        except Exception:
            return None
    
    def _simulate(self, asset: str) -> MarketSnapshot:
        """Generate simulated market data with Brownian motion."""
        now = time.time()
        base_price = self._sim_prices.get(asset, self.SEED_PRICES.get(asset, 100.0))
        vol = self.ANNUAL_VOLS.get(asset, 0.50)
        
        # Time since last update
        last = self._sim_last_update.get(asset, now - 1)
        dt = min(60, now - last)  # Cap at 60 seconds
        
        # GBM step: dS/S = mu*dt + sigma*sqrt(dt)*Z
        mu = 0.0  # No drift in simulation
        sigma = vol / math.sqrt(365 * 24 * 3600)  # Per-second vol
        z = random.gauss(0, 1)
        
        new_price = base_price * math.exp((mu - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * z)
        new_price = max(new_price, base_price * 0.95)  # Cap at 5% move
        new_price = min(new_price, base_price * 1.05)
        
        self._sim_prices[asset] = new_price
        self._sim_last_update[asset] = now
        
        spread_bps = max(2, vol * 8)
        change_24h = (new_price / self.SEED_PRICES.get(asset, new_price) - 1) * 100
        
        return MarketSnapshot(
            asset=asset,
            price=new_price,
            bid=new_price * (1 - spread_bps / 10000),
            ask=new_price * (1 + spread_bps / 10000),
            spread_bps=spread_bps * 2,
            volume_24h=random.uniform(1e9, 5e10),
            change_24h_pct=change_24h,
            volatility_estimate=vol,
            source="simulated",
        )
    
    def get_multi_asset_snapshot(self, assets: List[str] = None) -> Dict[str, MarketSnapshot]:
        """Get snapshots for multiple assets."""
        assets = assets or list(self.SEED_PRICES.keys())
        return {a: self.get_market_snapshot(a) for a in assets}
    
    def get_price_for_execution(self, asset: str = "BTC") -> Dict:
        """
        Get market data formatted for ExecutionNexus.execute_signal().
        
        Returns dict with 'price' and 'timestamp' keys.
        """
        snap = self.get_market_snapshot(asset)
        return {
            "price": snap.price,
            "timestamp": datetime.now(),
            "volatility": snap.volatility_estimate,
            "spread_bps": snap.spread_bps,
        }
