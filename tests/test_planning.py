from fastapi.testclient import TestClient

from app.api.deps import get_planning_service
from app.core.errors import AIProviderError, AITimeoutError
from app.main import app
from app.services.ai_service import AIService
from app.services.planning_service import PlanningService
from tests.conftest import MockAIProvider


def test_generate_plan_success(client: TestClient, valid_planning_payload: dict):
    response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["total_budget"] == 150000.0
    assert "summary" in data
    assert "allocated_budget" in data
    assert "remaining_budget" in data
    assert len(data["allocations"]) == 3
    assert len(data["weekly_plan"]) == 2
    assert len(data["tips"]) == 2

    # Verify arithmetic invariants
    assert round(data["allocated_budget"] + data["remaining_budget"], 2) == data["total_budget"]


def test_generate_plan_with_auth_header(client: TestClient, valid_planning_payload: dict):
    headers = {"Authorization": "Bearer sample_appwrite_jwt_token_12345"}
    response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["total_budget"] == 150000.0


def test_validation_negative_budget(client: TestClient, valid_planning_payload: dict):
    valid_planning_payload["budget"] = -500.0
    response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_validation_zero_budget(client: TestClient, valid_planning_payload: dict):
    valid_planning_payload["budget"] = 0
    response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_validation_zero_people(client: TestClient, valid_planning_payload: dict):
    valid_planning_payload["people"] = 0
    response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_validation_invalid_duration(client: TestClient, valid_planning_payload: dict):
    valid_planning_payload["duration_days"] = 0
    response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_validation_empty_goal(client: TestClient, valid_planning_payload: dict):
    valid_planning_payload["goal"] = "  "
    response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_validation_empty_categories(client: TestClient, valid_planning_payload: dict):
    valid_planning_payload["categories"] = [" ", ""]
    response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_ai_provider_error_handling(client: TestClient, valid_planning_payload: dict):
    mock_error_service = PlanningService(
        ai_service=AIService(
            provider=MockAIProvider(raise_error=AIProviderError("The AI service is unavailable."))
        )
    )
    app.dependency_overrides[get_planning_service] = lambda: mock_error_service
    try:
        response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
        assert response.status_code == 502
        data = response.json()
        assert data["error"]["code"] == "AI_PROVIDER_ERROR"
        assert "The AI service is unavailable" in data["error"]["message"]
    finally:
        app.dependency_overrides.clear()


def test_ai_timeout_error_handling(client: TestClient, valid_planning_payload: dict):
    mock_timeout_service = PlanningService(
        ai_service=AIService(
            provider=MockAIProvider(raise_error=AITimeoutError("AI service request timed out."))
        )
    )
    app.dependency_overrides[get_planning_service] = lambda: mock_timeout_service
    try:
        response = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
        assert response.status_code == 504
        data = response.json()
        assert data["error"]["code"] == "AI_PROVIDER_TIMEOUT"
        assert "timed out" in data["error"]["message"]
    finally:
        app.dependency_overrides.clear()

