from app.prompts.planning import SYSTEM_INSTRUCTION, build_user_planning_prompt
from app.schemas.planning import PlanningRequest


class PromptService:
    """Service responsible for constructing safe, structured prompts for AI providers."""

    @staticmethod
    def get_system_instruction() -> str:
        return SYSTEM_INSTRUCTION

    @staticmethod
    def create_planning_prompt(request: PlanningRequest) -> str:
        existing_expenses = [exp.model_dump() for exp in request.existing_expenses]
        return build_user_planning_prompt(
            budget=request.budget,
            currency=request.currency,
            people=request.people,
            duration_days=request.duration_days,
            goal=request.goal,
            categories=request.categories,
            preferences=request.preferences,
            existing_expenses=existing_expenses,
        )

