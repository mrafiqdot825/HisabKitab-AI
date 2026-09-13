from typing import Literal

from pydantic import BaseModel, Field


class BudgetAllocation(BaseModel):
    """Allocation breakdown for a single category."""

    category: str = Field(description="Expense category name")
    amount: float = Field(ge=0, description="Allocated amount in request currency")
    percentage: float = Field(ge=0, le=100, description="Percentage of total budget allocated")
    reason: str = Field(description="Explanation and rationale for this allocation")


class WeeklyPlan(BaseModel):
    """Weekly execution breakdown and milestone."""

    week: int = Field(ge=1, description="Week sequence number (1, 2, 3...)")
    budget: float = Field(ge=0, description="Budget target for this specific week")
    focus: str = Field(description="Core financial focus or milestone for this week")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable steps or tips for the week",
    )


class PlanningTip(BaseModel):
    """Personalized strategic savings or planning advice."""

    title: str = Field(description="Concise tip title")
    description: str = Field(description="Detailed actionable recommendation")
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Priority level: high, medium, or low",
    )


class PlanningResponse(BaseModel):
    """Final, validated response returned to the React Native client."""

    summary: str = Field(description="High-level executive summary of the financial plan")
    total_budget: float = Field(ge=0, description="Total budget provided in the request")
    allocated_budget: float = Field(ge=0, description="Sum of all category allocations")
    remaining_budget: float = Field(
        ge=0,
        description="Unallocated reserve or surplus buffer (total_budget - allocated_budget)",
    )
    allocations: list[BudgetAllocation] = Field(
        default_factory=list,
        description="Itemized category allocations",
    )
    weekly_plan: list[WeeklyPlan] = Field(
        default_factory=list,
        description="Chronological weekly breakdown",
    )
    tips: list[PlanningTip] = Field(
        default_factory=list,
        description="Strategic money-saving and budgeting tips",
    )


class RawAIPlanOutput(BaseModel):
    """Schema enforced when receiving structured output from Gemini."""

    summary: str = Field(description="Executive summary of the financial plan")
    allocations: list[BudgetAllocation] = Field(
        description="Suggested allocations with category, amount, percentage, and rationale"
    )
    weekly_plan: list[WeeklyPlan] = Field(
        default_factory=list,
        description="Weekly spending breakdown",
    )
    tips: list[PlanningTip] = Field(
        default_factory=list,
        description="Personalized practical tips",
    )
