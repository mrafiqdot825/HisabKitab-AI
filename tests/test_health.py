import os

from fastapi.testclient import TestClient

from app.core.config import Settings


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "HisabKitab AI Backend (حساب کتاب)"
    assert data["status"] == "online"
    assert "endpoints" in data
    assert "ai_provider" in data
    assert "features" in data
    assert data["endpoints"]["health"]["path"] == "/health"
    assert data["endpoints"]["generate_plan"]["path"] == "/api/v1/ai/generate-plan"


def test_settings_handles_empty_environment_strings():
    """Simulates Vercel environment where unset variables are passed as empty strings."""
    empty_env = {
        "AI_TIMEOUT_SECONDS": "",
        "AI_MAX_RETRIES": "",
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "",
        "PORT": "",
        "CORS_ORIGINS": "",
    }
    for k, v in empty_env.items():
        os.environ[k] = v

    try:
        settings = Settings()
        assert settings.ai_timeout_seconds == 30.0
        assert settings.ai_max_retries == 2
        assert settings.rate_limit_requests_per_minute == 15
        assert settings.port == 8000
        assert settings.cors_origins == ["*"]
    finally:
        for k in empty_env:
            os.environ.pop(k, None)
