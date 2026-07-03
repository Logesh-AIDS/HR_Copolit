from fastapi import APIRouter, Depends
from typing import List
from app.domain.models import KGNodeCreate, KGEdgeCreate
from app.domain.services.kg_service import KGService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])

def get_kg_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return KGService(pg_repo, kafka)

@router.post("/nodes")
def create_node(node: KGNodeCreate, service: KGService = Depends(get_kg_service)):
    record = service.add_node(node)
    return {"id": record.id}

@router.post("/edges")
def create_edge(edge: KGEdgeCreate, service: KGService = Depends(get_kg_service)):
    record = service.add_edge(edge)
    return {"id": record.id}

@router.get("/nodes/{node_id}/related")
def get_related_nodes(node_id: str, service: KGService = Depends(get_kg_service)):
    edges = service.get_related_nodes(node_id)
    return {"edges": edges}
