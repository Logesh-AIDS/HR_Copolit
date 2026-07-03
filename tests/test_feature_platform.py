import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath("services/feature-platform"))

# Mock Kafka and Redis and DB before importing main to avoid actual connections during unit tests
with patch('app.adapter.messaging.kafka_publisher.KafkaPublisher'), \
     patch('app.adapter.redis.redis_repo.RedisRepository'), \
     patch('app.adapter.db.postgres_repo.PostgresRepository'), \
     patch('app.adapter.vector.qdrant_repo.QdrantRepository'):
    from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "feature-platform"}

class MockRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def get_mock_feature_service():
    mock_service = MagicMock()
    mock_record = MockRecord(
        id="123",
        name="coding_score",
        description=None,
        entity_type="candidate",
        entity_id="cand_1",
        value=95.5,
        data_type="float",
        source_service="grading-service",
        confidence_score=1.0,
        version=1,
        timestamp="2026-07-03T00:00:00Z"
    )
    mock_service.create_feature.return_value = mock_record
    return mock_service

def test_create_feature():
    from app.delivery.http.feature_router import get_feature_service
    app.dependency_overrides[get_feature_service] = get_mock_feature_service

    payload = {
        "name": "coding_score",
        "entity_type": "candidate",
        "entity_id": "cand_1",
        "value": 95.5,
        "data_type": "float",
        "source_service": "grading-service"
    }
    
    response = client.post("/api/v1/features", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "coding_score"
    assert response.json()["id"] == "123"
    app.dependency_overrides.clear()

def get_mock_vector_service():
    mock_service = MagicMock()
    mock_service.save_embedding.return_value = True
    return mock_service

def test_generate_vector():
    from app.delivery.http.vector_router import get_vector_service
    app.dependency_overrides[get_vector_service] = get_mock_vector_service

    payload = {
        "text": "Expert in Python and Kubernetes",
        "entity_type": "resume",
        "entity_id": "res_1",
        "metadata": {"source": "candidate_upload"}
    }
    
    response = client.post("/api/v1/vectors/generate/resumes", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    app.dependency_overrides.clear()

def get_mock_kg_service():
    mock_service = MagicMock()
    mock_record = MockRecord(id="node_1")
    mock_service.add_node.return_value = mock_record
    return mock_service

def test_create_kg_node():
    from app.delivery.http.kg_router import get_kg_service
    app.dependency_overrides[get_kg_service] = get_mock_kg_service
    
    payload = {
        "node_type": "skill",
        "name": "Python"
    }
    
    response = client.post("/api/v1/graph/nodes", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == "node_1"
    app.dependency_overrides.clear()
