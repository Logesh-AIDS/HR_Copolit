import redis
import json
from typing import Optional, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisRepository:
    """Online Feature Store - Provides ultra-low latency feature retrieval."""
    
    def __init__(self):
        self.client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        
    def _generate_key(self, entity_type: str, entity_id: str) -> str:
        return f"feature:{entity_type}:{entity_id}"
        
    def set_feature(self, entity_type: str, entity_id: str, feature_name: str, value: Any, ttl_seconds: int = 86400):
        key = self._generate_key(entity_type, entity_id)
        # Store as Hash map where field=feature_name and value=json
        try:
            val_str = json.dumps(value)
            self.client.hset(key, feature_name, val_str)
            self.client.expire(key, ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis write error: {e}")
            return False
            
    def get_feature(self, entity_type: str, entity_id: str, feature_name: str) -> Optional[Any]:
        key = self._generate_key(entity_type, entity_id)
        try:
            val = self.client.hget(key, feature_name)
            return json.loads(val) if val else None
        except Exception as e:
            logger.error(f"Redis read error: {e}")
            return None
            
    def get_all_features_for_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        key = self._generate_key(entity_type, entity_id)
        try:
            all_fields = self.client.hgetall(key)
            return {k: json.loads(v) for k, v in all_fields.items()}
        except Exception as e:
            logger.error(f"Redis read all error: {e}")
            return {}
