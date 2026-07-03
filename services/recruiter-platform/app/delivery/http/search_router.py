from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.domain.models import SearchQuery
from app.domain.services.search_service import SearchService
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/search", tags=["Search"])

def get_search_service():
    kafka = KafkaPublisher()
    return SearchService(kafka)

@router.post("", response_model=List[Dict[str, Any]])
def semantic_search(req: SearchQuery, service: SearchService = Depends(get_search_service)):
    return service.semantic_search(req)
