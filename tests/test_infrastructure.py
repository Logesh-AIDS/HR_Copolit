# tests/test_infrastructure.py
import pytest
from services.common import settings
from services.common.exceptions import BaseAppException, register_exception_handlers
from services.common.responses import make_success_response, make_paginated_response
from fastapi import FastAPI
from fastapi.testclient import TestClient

def test_config_loading():
    """Verify settings defaults are loaded."""
    assert settings.PROJECT_NAME == "AI Interview Platform"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.DB_POOL_SIZE == 10
    assert settings.ENV == "development"


def test_standard_response_formatters():
    """Verify success and paginated response dictionary builders."""
    success_resp = make_success_response(data={"item": "value"})
    assert success_resp["success"] is True
    assert success_resp["data"]["item"] == "value"

    paginated_resp = make_paginated_response(
        data=[{"id": 1}],
        total=50,
        skip=10,
        limit=10
    )
    assert paginated_resp["success"] is True
    assert paginated_resp["meta"]["total"] == 50
    assert paginated_resp["meta"]["skip"] == 10
    assert paginated_resp["meta"]["limit"] == 10
    assert paginated_resp["meta"]["has_next"] is True


def test_centralized_exception_handling():
    """Verify custom exception mapper handles custom app exceptions."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/error")
    def trigger_error():
        raise BaseAppException(
            message="Test custom application error",
            code="TEST_ERROR",
            status_code=400,
            details={"reason": "Testing exception registration"}
        )

    client = TestClient(app)
    response = client.get("/error")
    
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "TEST_ERROR"
    assert json_data["error"]["message"] == "Test custom application error"
    assert json_data["error"]["details"]["reason"] == "Testing exception registration"
