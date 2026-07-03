from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class DatasetVersionCreate(BaseModel):
    name: str
    version: str
    location: str
    schema_hash: str

class DatasetVersionResponse(DatasetVersionCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ExperimentRunCreate(BaseModel):
    model_name: str
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, Any]
    status: str

class ExperimentRunResponse(ExperimentRunCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ModelVersionCreate(BaseModel):
    name: str
    version: str
    status: str
    artifact_uri: str

class ModelVersionResponse(ModelVersionCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TrainingRequest(BaseModel):
    model_name: str
    dataset_version_id: str
    hyperparameters: Optional[Dict[str, Any]] = None
