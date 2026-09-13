from app.core.logging import logger
from app.schemas.ai_response import PlanningResponse
from app.schemas.planning import PlanningRequest
from app.services.ai_service import AIService
from app.services.prompt_service import PromptService
from app.utils.validation import process_and_validate_financials


class PlanningService:
    """Orchestrates financial planning generation and deterministic verification."""

    def __init__(
        self,
        ai_service: AIService | None = None,
        prompt_service: PromptService | None = None,
    ):
        self.ai_service = ai_service or AIService()
        self.prompt_service = prompt_service or PromptService()

    async def generate_plan(self, request: PlanningRequest) -> PlanningResponse:
        """Create a personalized plan from user input with strict backend financial verification."""
        logger.info(
            f"PlanningService: Starting plan generation for budget={request.budget} {request.currency}, "
            f"people={request.people}, days={request.duration_days}"
        )

        # 1. Build prompt components
        system_instruction = self.prompt_service.get_system_instruction()
        user_prompt = self.prompt_service.create_planning_prompt(request)

        # 2. Call AI service
        raw_plan = await self.ai_service.generate_plan(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
        )

        # 3. Deterministic backend validation and calculation
        validated_plan = process_and_validate_financials(
            raw_plan=raw_plan,
            total_budget=request.budget,
        )

        logger.info(
            f"PlanningService: Plan successfully generated and verified for budget={request.budget} {request.currency}"
        )
        return validated_plan
