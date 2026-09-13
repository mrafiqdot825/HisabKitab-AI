from typing import Annotated
from fastapi import APIRouter, Depends, status
from app.api.deps import check_rate_limit, get_optional_auth_user, get_planning_service
from app.core.logging import logger
from app.schemas.ai_response import PlanningResponse
from app.schemas.planning import PlanningRequest
from app.services.planning_service import PlanningService

router = APIRouter(prefix="/api/v1/ai", tags=["AI Planning"])


@router.post(
    "/generate-plan",
    response_model=PlanningResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Intelligent Financial Plan",
    description=(
        "Generates a personalized, structured budget allocation, weekly breakdown, "
        "and strategic savings tips based on validated user financial goals and constraints."
    ),
    dependencies=[Depends(check_rate_limit)],
)
async def generate_plan(
    request: PlanningRequest,
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    user_id: Annotated[str | None, Depends(get_optional_auth_user)],
) -> PlanningResponse:
    logger.info(
        f"Received generate-plan request from {user_id or 'guest'} for {request.budget} {request.currency}"
    )
    return await planning_service.generate_plan(request)

