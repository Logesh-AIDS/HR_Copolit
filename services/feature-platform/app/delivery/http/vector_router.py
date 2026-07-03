from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.domain.models import EmbeddingRequest, EmbeddingSearch
from app.domain.services.vector_service import VectorService
from app.adapter.vector.qdrant_repo import QdrantRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/vectors", tags=["Vectors"])

def get_vector_service():
    qdrant = QdrantRepository()
    kafka = KafkaPublisher()
    return VectorService(qdrant, kafka)

@router.post("/generate/{collection_name}")
def generate_and_save_embedding(collection_name: str, req: EmbeddingRequest, service: VectorService = Depends(get_vector_service)):
    # In a real scenario, we'd call an LLM here to generate the vector. 
    # For now, we accept a mock vector generation simulation or just fail.
    # To simulate, we'll assume the client passed the vector, but our API spec in model doesn't have it.
    # Let's mock a vector for testing
    import random
    mock_vector = [random.uniform(-1, 1) for _ in range(1536)]
    
    success = service.save_embedding(collection_name, req.entity_id, mock_vector, req.metadata or {})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save embedding")
    return {"status": "success", "entity_id": req.entity_id}

@router.post("/search/{collection_name}")
def search_embeddings(collection_name: str, req: EmbeddingSearch, service: VectorService = Depends(get_vector_service)):
    # Mocking vector generation for query
    import random
    mock_query_vector = [random.uniform(-1, 1) for _ in range(1536)]
    
    results = service.search_similar(collection_name, mock_query_vector, limit=req.top_k)
    return {"results": [{"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in results]}
