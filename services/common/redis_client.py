# services/common/redis_client.py
import json
import logging
from typing import Any, Optional, Union
import redis
from services.common.config import settings

logger = logging.getLogger(__name__)

class RedisCacheClient:
    """
    Centralized caching connection coordinator wrapping redis-py.
    Provides robust, connection-resilient cache interactions.
    """
    def __init__(self):
        self.pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)
        logger.info("Redis connection pool established.")

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves parsed JSON value from cache. Bypasses on connection errors.
        """
        try:
            val = self.client.get(key)
            if val:
                return json.loads(val)
            return None
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis cache GET error for key '{key}': {e}")
            return None

    def get_raw(self, key: str) -> Optional[str]:
        """
        Retrieves raw string value from cache.
        """
        try:
            return self.client.get(key)
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis cache GET raw error for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """
        Serializes and stores value inside the cache with an optional TTL.
        """
        try:
            serialized = json.dumps(value)
            return self.client.set(key, serialized, ex=expire_seconds)
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis cache SET error for key '{key}': {e}")
            return False

    def set_raw(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """
        Stores raw string inside the cache.
        """
        try:
            return self.client.set(key, value, ex=expire_seconds)
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis cache SET raw error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Removes cache entry by key.
        """
        try:
            deleted = self.client.delete(key)
            return deleted > 0
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis cache DELETE error for key '{key}': {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Checks if key exists inside the cache store.
        """
        try:
            return bool(self.client.exists(key))
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis cache EXISTS check error for key '{key}': {e}")
            return False

    def get_client(self) -> redis.Redis:
        """
        Returns raw redis-py client for direct usage (e.g. state machine limits).
        """
        return self.client


# Singleton instance shared across microservices
redis_cache = RedisCacheClient()
