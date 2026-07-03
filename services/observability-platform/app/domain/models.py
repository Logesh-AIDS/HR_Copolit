from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class TraceSpanCreate(BaseModel):
    trace_id: str
    span_id: str
    service_name: str
    duration_ms: float
    status: str

class TraceSpanResponse(TraceSpanCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MetricEventCreate(BaseModel):
    metric_name: str
    value: float
    labels: Dict[str, str]
    timestamp: Optional[datetime] = None

class MetricEventResponse(MetricEventCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)

class AlertTriggeredCreate(BaseModel):
    severity: str
    message: str

class AlertTriggeredResponse(AlertTriggeredCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IncidentReportCreate(BaseModel):
    incident_id: str
    severity: str
    root_cause: str
    timeline: List[Dict[str, Any]]

class IncidentReportResponse(IncidentReportCreate):
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
