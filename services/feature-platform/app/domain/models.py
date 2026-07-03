from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

class FeatureBase(BaseModel):
    name: str
    description: Optional[str] = None
    entity_type: str
    entity_id: str
    value: Any
    data_type: str
    source_service: str
    confidence_score: float = 1.0
    version: int = 1

class FeatureCreate(FeatureBase):
    pass

class FeatureResponse(FeatureBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True

class EmbeddingRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None
    entity_type: str
    entity_id: str

class EmbeddingSearch(BaseModel):
    query_text: str
    top_k: int = 5
    metadata_filter: Optional[Dict[str, Any]] = None

class KGNodeCreate(BaseModel):
    node_type: str
    name: str
    metadata_json: Optional[Dict[str, Any]] = None

class KGEdgeCreate(BaseModel):
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
