import uuid
import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Float, JSON, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

from app.config import settings
from app.domain.models import TraceSpanCreate, MetricEventCreate, AlertTriggeredCreate, IncidentReportCreate

engine = create_engine(settings.POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TraceRecord(Base):
    __tablename__ = "obs_traces"
    id = Column(String, primary_key=True, index=True)
    trace_id = Column(String, index=True)
    span_id = Column(String, index=True)
    service_name = Column(String, index=True)
    duration_ms = Column(Float)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MetricRecord(Base):
    __tablename__ = "obs_metrics"
    id = Column(String, primary_key=True, index=True)
    metric_name = Column(String, index=True)
    value = Column(Float)
    labels = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AlertRecord(Base):
    __tablename__ = "obs_alerts"
    id = Column(String, primary_key=True, index=True)
    severity = Column(String, index=True)
    message = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class IncidentRecord(Base):
    __tablename__ = "obs_incidents"
    id = Column(String, primary_key=True, index=True)
    severity = Column(String, index=True)
    root_cause = Column(String)
    status = Column(String, default="open")
    timeline = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PostgresRepository:
    def __init__(self, db_session):
        self.db = db_session

    def add_trace(self, trace: TraceSpanCreate):
        record = TraceRecord(
            id=str(uuid.uuid4()),
            trace_id=trace.trace_id,
            span_id=trace.span_id,
            service_name=trace.service_name,
            duration_ms=trace.duration_ms,
            status=trace.status
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def add_metric(self, metric: MetricEventCreate):
        record = MetricRecord(
            id=str(uuid.uuid4()),
            metric_name=metric.metric_name,
            value=metric.value,
            labels=metric.labels,
            timestamp=metric.timestamp
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def add_alert(self, alert: AlertTriggeredCreate):
        record = AlertRecord(
            id=str(uuid.uuid4()),
            severity=alert.severity,
            message=alert.message,
            status="active"
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def add_incident(self, incident: IncidentReportCreate):
        record = IncidentRecord(
            id=incident.incident_id,
            severity=incident.severity,
            root_cause=incident.root_cause,
            status="open",
            timeline=incident.timeline
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
