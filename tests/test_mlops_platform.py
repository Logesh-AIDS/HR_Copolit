import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath("services/mlops-platform"))

from app.main import app
from app.delivery.http.dataset_router import get_dataset_service
from app.delivery.http.experiment_router import get_registry_service as get_exp_registry_service
from app.delivery.http.model_router import get_registry_service as get_model_registry_service
from app.delivery.http.model_router import get_deployment_service
from app.delivery.http.training_router import get_training_pipeline

client = TestClient(app)

class MockRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "mlops-platform"}

def test_register_dataset():
    mock_service = MagicMock()
    mock_record = MockRecord(
        id="ds_123",
        name="training_data_v1",
        version="v1",
        location="s3://datasets/train.csv",
        schema_hash="abc123hash",
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.register_dataset.return_value = mock_record
    app.dependency_overrides[get_dataset_service] = lambda: mock_service

    payload = {
        "name": "training_data_v1",
        "version": "v1",
        "location": "s3://datasets/train.csv",
        "schema_hash": "abc123hash"
    }

    response = client.post("/api/v1/datasets", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == "ds_123"
    assert response.json()["name"] == "training_data_v1"
    
    app.dependency_overrides.clear()

def test_log_experiment():
    mock_service = MagicMock()
    mock_record = MockRecord(
        id="exp_123",
        model_name="resume-ranker",
        hyperparameters={"learning_rate": 0.01},
        metrics={"accuracy": 0.96},
        status="completed",
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.log_experiment.return_value = mock_record
    app.dependency_overrides[get_exp_registry_service] = lambda: mock_service

    payload = {
        "model_name": "resume-ranker",
        "hyperparameters": {"learning_rate": 0.01},
        "metrics": {"accuracy": 0.96},
        "status": "completed"
    }

    response = client.post("/api/v1/experiments/runs", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == "exp_123"
    
    app.dependency_overrides.clear()

def test_register_model():
    mock_service = MagicMock()
    mock_record = MockRecord(
        id="mod_123",
        name="resume-ranker",
        version="v1.0",
        status="Staged",
        artifact_uri="s3://models/ranker/v1.pkl",
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.register_model.return_value = mock_record
    app.dependency_overrides[get_model_registry_service] = lambda: mock_service

    payload = {
        "name": "resume-ranker",
        "version": "v1.0",
        "status": "Staged",
        "artifact_uri": "s3://models/ranker/v1.pkl"
    }

    response = client.post("/api/v1/models", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == "mod_123"
    
    app.dependency_overrides.clear()

def test_promote_model():
    mock_service = MagicMock()
    mock_record = MockRecord(
        id="mod_123",
        name="resume-ranker",
        version="v1.0",
        status="Production",
        artifact_uri="s3://models/ranker/v1.pkl",
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.promote_model.return_value = mock_record
    app.dependency_overrides[get_deployment_service] = lambda: mock_service

    response = client.post("/api/v1/models/mod_123/promote")
    assert response.status_code == 200
    assert response.json()["new_status"] == "Production"
    
    app.dependency_overrides.clear()
