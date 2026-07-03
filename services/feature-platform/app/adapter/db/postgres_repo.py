from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from app.config import settings
from app.adapter.db.orm import Base, FeatureRecord, KGNode, KGEdge
from app.domain.models import FeatureCreate, KGNodeCreate, KGEdgeCreate
import logging

logger = logging.getLogger(__name__)

engine = create_engine(settings.POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PostgresRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_feature(self, feature: FeatureCreate) -> FeatureRecord:
        record = FeatureRecord(**feature.model_dump())
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
        
    def get_features_by_entity(self, entity_type: str, entity_id: str) -> List[FeatureRecord]:
        return self.db.query(FeatureRecord).filter(
            FeatureRecord.entity_type == entity_type,
            FeatureRecord.entity_id == entity_id
        ).all()

    def add_kg_node(self, node: KGNodeCreate) -> KGNode:
        record = KGNode(**node.model_dump())
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def add_kg_edge(self, edge: KGEdgeCreate) -> KGEdge:
        record = KGEdge(**edge.model_dump())
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_node_edges(self, node_id: str) -> List[KGEdge]:
        return self.db.query(KGEdge).filter(
            (KGEdge.source_id == node_id) | (KGEdge.target_id == node_id)
        ).all()
