from typing import Annotated
from pydantic import BaseModel, Field, field_validator


class Expense(BaseModel):
    """Model representing an existing or recurring user expense."""

    category: Annotated[str, Field(min_length=1, max_length=50, description="Expense category")]
    amount: Annotated[float, Field(ge=0, description="Expense amount in specified currency")]
    description: Annotated[str | None, Field(default=None, max_length=200, description="Optional note or context")]

    @field_validator("category")
    @classmethod
    def clean_category(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Expense category cannot be empty or whitespace only.")
        return clean


class PlanningRequest(BaseModel):
    """Input payload for generating an intelligent financial budget plan."""

    budget: Annotated[float, Field(gt=0, description="Total budget amount (must be positive)")]
    currency: Annotated[str, Field(min_length=1, max_length=10, description="Currency code or symbol (e.g. PKR, USD)")]
    people: Annotated[int, Field(ge=1, description="Number of people in household or planning group")]
    duration_days: Annotated[int, Field(ge=1, description="Planning duration in days (e.g. 30 for monthly)")]
    goal: Annotated[str, Field(min_length=3, max_length=500, description="User's primary financial planning goal")]
    categories: Annotated[list[str], Field(min_length=1, description="List of budget categories")]
    preferences: Annotated[list[str], Field(default_factory=list, description="User preferences or constraints")]
    existing_expenses: Annotated[list[Expense], Field(default_factory=list, description="Known or fixed expenses")]

    @field_validator("currency")
    @classmethod
    def clean_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Currency cannot be empty.")
        return clean

    @field_validator("goal")
    @classmethod
    def clean_goal(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 3:
            raise ValueError("Goal must contain at least 3 characters.")
        return clean

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str]) -> list[str]:
        cleaned = [cat.strip() for cat in v if cat.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty category is required.")
        return list(dict.fromkeys(cleaned))  # Deduplicate preserving order

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, v: list[str]) -> list[str]:
        return [p.strip() for p in v if p.strip()]

