from fastapi.testclient import TestClient

from app.api import deps
from app.utils.rate_limiter import InMemorySlidingWindowRateLimiter


def test_in_memory_rate_limiter_logic():
    limiter = InMemorySlidingWindowRateLimiter(requests_limit=3, window_seconds=60)
    assert limiter.is_allowed("user-1") is True
    assert limiter.is_allowed("user-1") is True
    assert limiter.is_allowed("user-1") is True
    # 4th request in window should be denied
    assert limiter.is_allowed("user-1") is False

    # Different key should still be allowed
    assert limiter.is_allowed("user-2") is True

    # Reset
    limiter.reset()
    assert limiter.is_allowed("user-1") is True


def test_api_rate_limiting_enforcement(client: TestClient, valid_planning_payload: dict):
    # Temporarily set rate limiter to a small threshold
    original_limiter = deps._rate_limiter
    deps._rate_limiter = InMemorySlidingWindowRateLimiter(requests_limit=2, window_seconds=60)

    try:
        r1 = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
        assert r1.status_code == 200

        r2 = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
        assert r2.status_code == 200

        # Third request should exceed rate limit (429)
        r3 = client.post("/api/v1/ai/generate-plan", json=valid_planning_payload)
        assert r3.status_code == 429
        data = r3.json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        deps._rate_limiter = original_limiter
