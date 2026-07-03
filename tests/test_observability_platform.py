import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath("services/observability-platform"))

from app.main import app
from app.delivery.http.tracing_router import get_tracing_service
from app.delivery.http.metrics_router import get_metrics_service
from app.delivery.http.alerting_router import get_alerting_service
from app.delivery.http.incident_router import get_incident_service

client = TestClient(app)

class MockRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "observability-platform"}

def test_record_span():
    mock_service = MagicMock()
    mock_record = MockRecord(
        id="trace_1",
        trace_id="t_123",
        span_id="s_456",
        service_name="api-gateway",
        duration_ms=45.5,
        status="ok",
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.record_span.return_value = mock_record
    app.dependency_overrides[get_tracing_service] = lambda: mock_service

    payload = {
        "trace_id": "t_123",
        "span_id": "s_456",
        "service_name": "api-gateway",
        "duration_ms": 45.5,
        "status": "ok"
    }

    response = client.post("/api/v1/traces", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == "trace_1"
    
    app.dependency_overrides.clear()

def test_record_metric():
    mock_service = MagicMock()
    mock_record = MockRecord(
        id="met_1",
        metric_name="model_drift",
        value=0.6,
        labels={"model": "ranker", "version": "v1"},
        timestamp="2026-07-03T00:00:00Z"
    )
    mock_service.record_metric.return_value = mock_record
    app.dependency_overrides[get_metrics_service] = lambda: mock_service

    payload = {
        "metric_name": "model_drift",
        "value": 0.6,
        "labels": {"model": "ranker", "version": "v1"}
    }

    response = client.post("/api/v1/metrics", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == "met_1"
    
    app.dependency_overrides.clear()

def test_trigger_alert():
    mock_service = MagicMock()
    mock_record = MockRecord(
        id="alert_1",
        severity="critical",
        message="Model latency > 1000ms",
        status="active",
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.trigger_alert.return_value = mock_record
    app.dependency_overrides[get_alerting_service] = lambda: mock_service

    payload = {
        "severity": "critical",
        "message": "Model latency > 1000ms"
    }

    response = client.post("/api/v1/alerts", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == "alert_1"
    
    app.dependency_overrides.clear()

def test_create_incident():
    mock_service = MagicMock()
    mock_record = MockRecord(
        id="inc_1",
        incident_id="inc_1",
        severity="high",
        root_cause="Database crash",
        timeline=[{"time": "now", "event": "crash"}],
        status="open",
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.create_incident.return_value = mock_record
    app.dependency_overrides[get_incident_service] = lambda: mock_service

    payload = {
        "incident_id": "inc_1",
        "severity": "high",
        "root_cause": "Database crash",
        "timeline": [{"time": "now", "event": "crash"}]
    }

    response = client.post("/api/v1/incidents", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "open"
    
    app.dependency_overrides.clear()
