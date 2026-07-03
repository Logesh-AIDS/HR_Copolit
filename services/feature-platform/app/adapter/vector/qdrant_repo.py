from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
from app.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

class QdrantRepository:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        
    def create_collection_if_not_exists(self, collection_name: str, vector_size: int = 1536):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            
    def upsert_embedding(self, collection_name: str, entity_id: str, vector: List[float], payload: Dict[str, Any]):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entity_id))
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vector: {e}")
            return False
            
    def search(self, collection_name: str, query_vector: List[float], limit: int = 5):
        try:
            hits = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )
            return hits
        except Exception as e:
            logger.error(f"Failed to search vector: {e}")
            return []
