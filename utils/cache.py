"""
Redis Cache Manager
High-performance caching for price data, signals, and API responses
"""
import json
import pickle
from typing import Any, Optional, Callable
from functools import wraps
import redis
from loguru import logger
from utils.config import settings


class CacheManager:
    """
    Redis-based cache manager with automatic serialization

    Features:
    - Automatic JSON/Pickle serialization
    - TTL support
    - Cache invalidation
    - Decorators for easy caching
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connect()

    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=False,  # We'll handle encoding
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.redis_client = None

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if not self.redis_client:
            return default

        try:
            value = self.redis_client.get(key)
            if value is None:
                return default

            # Try JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
        """
        if not self.redis_client:
            return

        try:
            # Try JSON first (faster), fall back to pickle
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)

            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")

    def delete(self, key: str):
        """Delete key from cache"""
        if not self.redis_client:
            return

        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")

    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Deleted {len(keys)} keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error deleting pattern {pattern}: {e}")

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get TTL of key"""
        if not self.redis_client:
            return -1

        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL of key {key}: {e}")
            return -1

    def flush_all(self):
        """Clear all cache (use with caution!)"""
        if not self.redis_client:
            return

        try:
            self.redis_client.flushdb()
            logger.warning("Flushed all cache!")
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")


# Decorator for caching function results
def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results

    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Prefix for cache key

    Usage:
        @cached(ttl=60, key_prefix="price")
        def get_price(symbol):
            return expensive_api_call(symbol)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # Cache miss - call function
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


# Global instance
cache_manager = CacheManager()


# Price data cache keys
class CacheKeys:
    """Standard cache key patterns"""

    PRICE = "price:{symbol}"
    SIGNAL = "signal:{symbol}"
    PORTFOLIO = "portfolio"
    HEATMAP = "heatmap"
    WATCHLIST = "watchlist"
    ORDER_HISTORY = "orders:{symbol}:{days}"
    INDICATORS = "indicators:{symbol}:{indicator}"
    SCAN_RESULTS = "scan:results:{minutes}"

    @staticmethod
    def price(symbol: str) -> str:
        return f"price:{symbol}"

    @staticmethod
    def signal(symbol: str) -> str:
        return f"signal:{symbol}"

    @staticmethod
    def indicators(symbol: str, indicator: str) -> str:
        return f"indicators:{symbol}:{indicator}"
