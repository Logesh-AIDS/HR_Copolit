import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath("services/recruiter-platform"))

from app.main import app
from app.delivery.http.candidate_router import get_candidate_service
from app.delivery.http.comparison_router import get_comparison_service
from app.delivery.http.search_router import get_search_service
from app.delivery.http.report_router import get_reporting_service

client = TestClient(app)

class MockRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "recruiter-platform"}

def test_get_candidate_profile():
    mock_service = MagicMock()
    mock_service.get_unified_profile.return_value = {
        "candidate_id": "c_123",
        "name": "Jane Doe",
        "skills": ["Python", "React"],
        "match_score": 0.95,
        "interview_status": "Completed"
    }
    app.dependency_overrides[get_candidate_service] = lambda: mock_service

    response = client.get("/api/v1/candidates/c_123/profile")
    assert response.status_code == 200
    assert response.json()["name"] == "Jane Doe"
    
    app.dependency_overrides.clear()

def test_compare_candidates():
    mock_service = MagicMock()
    mock_record = MockRecord(
        session_id="session_abc",
        comparison_data={
            "c_123": {"skills_match": 0.9},
            "c_456": {"skills_match": 0.8}
        }
    )
    mock_service.generate_comparison.return_value = mock_record
    app.dependency_overrides[get_comparison_service] = lambda: mock_service

    payload = {
        "recruiter_id": "r_999",
        "candidate_ids": ["c_123", "c_456"]
    }

    response = client.post("/api/v1/comparisons", json=payload)
    assert response.status_code == 200
    assert response.json()["session_id"] == "session_abc"
    
    app.dependency_overrides.clear()

def test_semantic_search():
    mock_service = MagicMock()
    mock_service.semantic_search.return_value = [
        {"candidate_id": "c_101", "name": "Alice Backend", "relevance_score": 0.94, "matched_skills": ["Python"]}
    ]
    app.dependency_overrides[get_search_service] = lambda: mock_service

    payload = {
        "query": "senior python developer",
        "filters": {}
    }

    response = client.post("/api/v1/search", json=payload)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["candidate_id"] == "c_101"
    
    app.dependency_overrides.clear()

def test_generate_report():
    mock_service = MagicMock()
    mock_record = MockRecord(
        report_id="rep_1",
        report_type="summary",
        content={"summary": "Report generated"},
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.generate_report.return_value = mock_record
    app.dependency_overrides[get_reporting_service] = lambda: mock_service

    payload = {
        "recruiter_id": "r_999",
        "report_type": "summary"
    }

    response = client.post("/api/v1/reports", json=payload)
    assert response.status_code == 200
    assert response.json()["report_id"] == "rep_1"
    
    app.dependency_overrides.clear()
