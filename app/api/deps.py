from typing import Annotated
from fastapi import Header, Request
from app.core.config import get_settings
from app.core.errors import RateLimitExceededError
from app.core.logging import logger
from app.services.planning_service import PlanningService
from app.utils.rate_limiter import InMemorySlidingWindowRateLimiter

# Global rate limiter instance
_settings = get_settings()
_rate_limiter = InMemorySlidingWindowRateLimiter(
    requests_limit=_settings.rate_limit_requests_per_minute,
    window_seconds=60,
)


def get_planning_service() -> PlanningService:
    """Dependency provider for PlanningService."""
    return PlanningService()


async def check_rate_limit(request: Request) -> None:
    """Rate limit dependency per client IP address."""
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for client IP: {client_ip}")
        raise RateLimitExceededError(
            f"Rate limit exceeded. Maximum {_settings.rate_limit_requests_per_minute} requests per minute allowed."
        )


async def get_optional_auth_user(
    authorization: Annotated[str | None, Header()] = None,
) -> str | None:
    """Placeholder dependency for user authentication.

    Matches HisabKitab's dual architecture (Guest Mode vs Cloud Mode):
    - When Bearer token is provided, this hooks into Appwrite JWT / session verification.
    - When omitted, allows guest mode requests while preserving rate limits and safety.
    """
    if not authorization:
        return None

    if authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        # In future Appwrite integration:
        # appwrite_client.account.get() using token
        return f"authenticated-user-{token[:8]}..."

    return None

