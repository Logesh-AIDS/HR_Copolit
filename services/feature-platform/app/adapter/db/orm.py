from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class FeatureRecord(Base):
    __tablename__ = 'features'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    entity_type = Column(String, index=True, nullable=False) # e.g. "candidate", "job"
    entity_id = Column(String, index=True, nullable=False)
    value = Column(JSON, nullable=False)
    data_type = Column(String, nullable=False) # e.g. "float", "string", "json"
    source_service = Column(String, nullable=False)
    confidence_score = Column(Float, default=1.0)
    version = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)

class FeatureGroup(Base):
    __tablename__ = 'feature_groups'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    description = Column(String)

class KGNode(Base):
    """Knowledge Graph Node (e.g. Skill, Concept)"""
    __tablename__ = 'kg_nodes'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_type = Column(String, index=True) # "skill", "technology", "concept"
    name = Column(String, index=True)
    metadata_json = Column(JSON, nullable=True)

class KGEdge(Base):
    """Knowledge Graph Edge (e.g. REQUIRES, RELATED_TO)"""
    __tablename__ = 'kg_edges'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String, ForeignKey('kg_nodes.id'), index=True)
    target_id = Column(String, ForeignKey('kg_nodes.id'), index=True)
    relation_type = Column(String, index=True) # e.g. "RELATED_TO"
    weight = Column(Float, default=1.0)
