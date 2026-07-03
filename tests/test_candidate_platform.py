import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath("services/candidate-platform"))

from app.main import app
from app.delivery.http.candidate_router import get_candidate_service
from app.delivery.http.coaching_router import get_coaching_service
from app.delivery.http.mock_router import get_mock_service

client = TestClient(app)

class MockRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "candidate-platform"}

def test_get_dashboard():
    mock_service = MagicMock()
    mock_service.get_dashboard.return_value = {
        "upcoming_interviews": 2,
        "readiness_score": 0.88,
        "recent_feedback": "Great communication",
        "recommended_topics": ["Kafka"]
    }
    app.dependency_overrides[get_candidate_service] = lambda: mock_service

    response = client.get("/api/v1/candidates/c_123/dashboard")
    assert response.status_code == 200
    assert response.json()["upcoming_interviews"] == 2
    
    app.dependency_overrides.clear()

def test_generate_learning_plan():
    mock_service = MagicMock()
    mock_record = MockRecord(
        plan_id="plan_1",
        candidate_id="c_123",
        plan_content={"week_1": "Python basics"},
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.generate_learning_plan.return_value = mock_record
    app.dependency_overrides[get_coaching_service] = lambda: mock_service

    payload = {
        "candidate_id": "c_123",
        "target_role": "Backend Engineer",
        "focus_areas": ["Python"]
    }

    response = client.post("/api/v1/coach/learning-plan", json=payload)
    assert response.status_code == 200
    assert response.json()["plan_id"] == "plan_1"
    
    app.dependency_overrides.clear()

def test_get_coach_feedback():
    mock_service = MagicMock()
    mock_service.get_coach_feedback.return_value = {
        "summary": "Good effort.",
        "strengths": ["Clean code"],
        "improvement_areas": ["Optimization"],
        "practice_recommendations": ["DP"]
    }
    app.dependency_overrides[get_coaching_service] = lambda: mock_service

    payload = {
        "candidate_id": "c_123",
        "interview_session_id": "sess_1"
    }

    response = client.post("/api/v1/coach/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["summary"] == "Good effort."
    
    app.dependency_overrides.clear()

def test_start_mock_session():
    mock_service = MagicMock()
    mock_record = MockRecord(
        session_id="mock_1",
        questions=["Explain Python"],
        status="started",
        created_at="2026-07-03T00:00:00Z"
    )
    mock_service.start_mock_session.return_value = mock_record
    app.dependency_overrides[get_mock_service] = lambda: mock_service

    payload = {
        "candidate_id": "c_123",
        "topic": "Python",
        "difficulty": "medium"
    }

    response = client.post("/api/v1/mock-interviews/start", json=payload)
    assert response.status_code == 200
    assert response.json()["session_id"] == "mock_1"
    
    app.dependency_overrides.clear()
