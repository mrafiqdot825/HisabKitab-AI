import time
from collections import defaultdict
from typing import Protocol


class RateLimiterProtocol(Protocol):
    def is_allowed(self, key: str) -> bool:
        """Check if request for key is permitted under rate limit."""
        ...


class InMemorySlidingWindowRateLimiter:
    """In-memory sliding window rate limiter.

    Suitable for single-instance deployments and local development.
    Can easily be replaced with a Redis-backed implementation for distributed systems.
    """

    def __init__(self, requests_limit: int = 15, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds

        # Clean old timestamps
        timestamps = [t for t in self._history[key] if t > cutoff]
        self._history[key] = timestamps

        if len(timestamps) >= self.requests_limit:
            return False

        self._history[key].append(now)
        return True

    def reset(self) -> None:
        """Reset all rate limit counters (useful for unit testing)."""
        self._history.clear()
