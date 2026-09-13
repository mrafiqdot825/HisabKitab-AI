from typing import Protocol

from app.schemas.ai_response import RawAIPlanOutput


class AIProvider(Protocol):
    """Abstract interface for AI model providers."""

    async def generate_plan(
        self,
        system_instruction: str,
        user_prompt: str,
    ) -> RawAIPlanOutput:
        """Generate a structured planning response using the underlying AI model."""
        ...
