# services/interview-engine/app/adapter/vector/question_qdrant_repo.py
import os
import math
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class QuestionQdrantRepository:
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        self.client = None
        
        try:
            from qdrant_client import QdrantClient
            self.client = QdrantClient(host=self.host, port=self.port)
        except Exception as e:
            logger.warning(f"Qdrant client offline fallback initialized. Error: {e}")
            self.client = None

    def create_collection(self, collection_name: str, vector_size: int = 128) -> bool:
        if not self.client:
            return False
        try:
            from qdrant_client.http.models import Distance, VectorParams
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection: {e}")
            return False

    def _generate_mock_embedding(self, skills: List[str], text: str = "", size: int = 128) -> List[float]:
        vector = [0.0] * size
        # Factor skills
        for index, skill in enumerate(skills):
            hash_val = (hash(skill) + index) % size
            vector[hash_val] += 1.5
            
        # Factor text keywords
        if text:
            words = text.lower().split()
            for index, word in enumerate(words[:15]):
                hash_val = (hash(word) + index) % size
                vector[hash_val] += 0.5

        # Normalize
        magnitude = math.sqrt(sum(x*x for x in vector))
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        return vector

    def upsert_question_vector(self, question_id: str, skills: List[str], statement: str) -> bool:
        vector = self._generate_mock_embedding(skills, statement)
        if not self.client:
            return True # Mock success
            
        try:
            from qdrant_client.http.models import PointStruct
            self.client.upsert(
                collection_name="questions",
                points=[
                    PointStruct(
                        id=question_id,
                        vector=vector,
                        payload={"skills": skills, "statement": statement}
                    )
                ]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vector: {e}")
            return False

    def search_similar_questions(
        self,
        query_skills: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        query_vector = self._generate_mock_embedding(query_skills)
        if not self.client:
            return []

        try:
            search_result = self.client.search(
                collection_name="questions",
                query_vector=query_vector,
                limit=limit
            )
            return [
                {
                    "question_id": hit.id,
                    "score": hit.score,
                    "skills": hit.payload.get("skills", []),
                    "statement": hit.payload.get("statement", "")
                }
                for hit in search_result
            ]
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []
