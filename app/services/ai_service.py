from app.core.config import get_settings
from app.core.logging import logger
from app.schemas.ai_response import RawAIPlanOutput
from app.services.ai_provider import AIProvider
from app.services.gemini_provider import GeminiProvider


class AIService:
    """Service encapsulating AI provider communication."""

    def __init__(self, provider: AIProvider | None = None):
        settings = get_settings()
        self.provider = provider or GeminiProvider(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
            timeout_seconds=settings.ai_timeout_seconds,
            max_retries=settings.ai_max_retries,
        )

    async def generate_plan(
        self,
        system_instruction: str,
        user_prompt: str,
    ) -> RawAIPlanOutput:
        """Execute AI plan generation via configured provider."""
        logger.info("AIService: Dispatching prompt to AI provider.")
        return await self.provider.generate_plan(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
        )

