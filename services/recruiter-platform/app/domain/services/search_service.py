import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from app.config import settings
from app.domain.models import SearchQuery
from app.adapter.messaging.kafka_publisher import KafkaPublisher

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, kafka: KafkaPublisher):
        self.kafka = kafka
        # In a real deployment, we'd embed the query via an LLM. Here we mock the vector search.
        try:
            self.qdrant = QdrantClient(host=settings.QDRANT_URL, port=settings.QDRANT_PORT)
        except Exception as e:
            logger.warning(f"Could not connect to Qdrant: {e}")
            self.qdrant = None

    def semantic_search(self, query: SearchQuery) -> List[Dict[str, Any]]:
        self.kafka.publish_event(
            topic="recruiter.search_performed",
            key="search",
            payload={"query": query.query}
        )
        
        # Mock response returning matched candidates based on semantic search
        return [
            {"candidate_id": "c_101", "name": "Alice Backend", "relevance_score": 0.94, "matched_skills": ["Python", "FastAPI"]},
            {"candidate_id": "c_102", "name": "Bob Data", "relevance_score": 0.88, "matched_skills": ["Kafka", "PostgreSQL"]}
        ]
