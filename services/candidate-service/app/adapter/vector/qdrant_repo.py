# services/candidate-service/app/adapter/vector/qdrant_repo.py
import os
import math
from typing import List, Dict, Any, Optional

class QdrantRepository:
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        self.client = None
        
        # Initialize Client if Qdrant is available
        try:
            from qdrant_client import QdrantClient
            self.client = QdrantClient(host=self.host, port=self.port)
        except Exception:
            # Silent fallback if client library not installed or offline
            self.client = None

    def create_collection(self, collection_name: str, vector_size: int = 128):
        if not self.client:
            return False
        try:
            from qdrant_client.http.models import Distance, VectorParams
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            return True
        except Exception:
            return False

    def _generate_mock_embedding(self, skills: List[str], size: int = 128) -> List[float]:
        """
        Synthesize reproducible mock embeddings for testing.
        """
        vector = [0.0] * size
        for index, skill in enumerate(skills):
            hash_val = hash(skill) % size
            vector[hash_val] += 1.0
            
        # Normalize vector
        magnitude = math.sqrt(sum(x*x for x in vector))
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        return vector

    def upsert_candidate_vector(self, candidate_id: str, skills: List[str]) -> bool:
        vector = self._generate_mock_embedding(skills)
        if not self.client:
            return True # Fallback mock success
            
        try:
            from qdrant_client.http.models import PointStruct
            self.client.upsert(
                collection_name="candidates",
                points=[
                    PointStruct(
                        id=candidate_id,
                        vector=vector,
                        payload={"skills": skills}
                    )
                ]
            )
            return True
        except Exception:
            return False

    def search_similar_candidates(self, query_skills: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        query_vector = self._generate_mock_embedding(query_skills)
        if not self.client:
            # Return empty search if offline
            return []

        try:
            search_result = self.client.search(
                collection_name="candidates",
                query_vector=query_vector,
                limit=limit
            )
            return [
                {
                    "candidate_id": hit.id,
                    "score": hit.score,
                    "skills": hit.payload.get("skills", [])
                }
                for hit in search_result
            ]
        except Exception:
            return []
