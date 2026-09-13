from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = "ok"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns service health status without calling external dependencies.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
