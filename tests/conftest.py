import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_planning_service
from app.main import app
from app.schemas.ai_response import (
    BudgetAllocation,
    PlanningTip,
    RawAIPlanOutput,
    WeeklyPlan,
)
from app.services.ai_service import AIService
from app.services.planning_service import PlanningService


class MockAIProvider:
    """Mock AIProvider for deterministic testing without calling Gemini."""

    def __init__(self, raw_output: RawAIPlanOutput | None = None, raise_error: Exception | None = None):
        self.raw_output = raw_output or RawAIPlanOutput(
            summary="A balanced monthly personal plan prioritizing food and savings.",
            allocations=[
                BudgetAllocation(
                    category="food",
                    amount=45000.0,
                    percentage=30.0,
                    reason="Essential household groceries and daily meals",
                ),
                BudgetAllocation(
                    category="housing",
                    amount=35000.0,
                    percentage=23.33,
                    reason="Rent and utilities allocation",
                ),
                BudgetAllocation(
                    category="savings",
                    amount=25000.0,
                    percentage=16.67,
                    reason="Goal-oriented reserve fund",
                ),
            ],
            weekly_plan=[
                WeeklyPlan(
                    week=1,
                    budget=25000.0,
                    focus="Stock up monthly essentials",
                    recommendations=["Buy groceries in bulk to save costs"],
                ),
                WeeklyPlan(
                    week=2,
                    budget=20000.0,
                    focus="Utility bill clearances",
                    recommendations=["Pay electricity and internet on schedule"],
                ),
            ],
            tips=[
                PlanningTip(
                    title="Track Daily Purchases",
                    description="Log micro-expenses in HisabKitab to avoid silent budget leaks.",
                    priority="high",
                ),
                PlanningTip(
                    title="Batch Meal Prepping",
                    description="Prepare weekly staples in advance to reduce spontaneous food orders.",
                    priority="medium",
                ),
            ],
        )
        self.raise_error = raise_error

    async def generate_plan(self, system_instruction: str, user_prompt: str) -> RawAIPlanOutput:
        if self.raise_error:
            raise self.raise_error
        return self.raw_output


@pytest.fixture
def mock_ai_provider():
    return MockAIProvider()


@pytest.fixture
def mock_planning_service(mock_ai_provider):
    mock_ai_service = AIService(provider=mock_ai_provider)
    return PlanningService(ai_service=mock_ai_service)


@pytest.fixture
def client(mock_planning_service):
    # Override PlanningService dependency in test client
    app.dependency_overrides[get_planning_service] = lambda: mock_planning_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def valid_planning_payload():
    return {
        "budget": 150000.0,
        "currency": "PKR",
        "people": 4,
        "duration_days": 30,
        "goal": "Save for emergency fund while managing household expenses",
        "categories": ["food", "housing", "transport", "savings"],
        "preferences": ["Minimize eating out", "Prioritize emergency savings"],
        "existing_expenses": [
            {
                "category": "housing",
                "amount": 20000.0,
                "description": "Monthly apartment maintenance & electricity",
            }
        ],
    }

