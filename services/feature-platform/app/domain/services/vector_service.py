from typing import List, Dict, Any
from app.adapter.vector.qdrant_repo import QdrantRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
import logging

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, qdrant_repo: QdrantRepository, kafka: KafkaPublisher):
        self.qdrant_repo = qdrant_repo
        self.kafka = kafka

    def save_embedding(self, collection: str, entity_id: str, vector: List[float], metadata: Dict[str, Any]):
        success = self.qdrant_repo.upsert_embedding(collection, entity_id, vector, metadata)
        if success:
            self.kafka.publish_event(
                topic="embedding.generated",
                key=entity_id,
                payload={"collection": collection, "entity_id": entity_id}
            )
        return success

    def search_similar(self, collection: str, query_vector: List[float], limit: int = 5):
        return self.qdrant_repo.search(collection, query_vector, limit)
