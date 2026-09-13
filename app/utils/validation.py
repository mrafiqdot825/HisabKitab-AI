from app.core.logging import logger
from app.schemas.ai_response import BudgetAllocation, PlanningResponse, RawAIPlanOutput


def process_and_validate_financials(
    raw_plan: RawAIPlanOutput,
    total_budget: float,
) -> PlanningResponse:
    """Deterministically calculate, balance, and validate financial amounts from AI suggestions.

    Backend is the single source of truth:
    1. Guarantees sum(allocation.amount) <= total_budget.
    2. Recalculates exact percentages from amounts against total_budget.
    3. Guarantees allocated_budget + remaining_budget == total_budget.
    4. Handles floating point rounding cleanly.
    """
    total_budget = round(float(total_budget), 2)
    adjusted_allocations: list[BudgetAllocation] = []

    raw_allocations = raw_plan.allocations or []
    current_sum = sum(max(0.0, float(a.amount)) for a in raw_allocations)

    # If AI allocated zero across all or gave empty, allocate safely
    if not raw_allocations:
        logger.warning("AI produced no allocations; generating balanced allocation.")
        return PlanningResponse(
            summary=raw_plan.summary,
            total_budget=total_budget,
            allocated_budget=0.0,
            remaining_budget=total_budget,
            allocations=[],
            weekly_plan=raw_plan.weekly_plan,
            tips=raw_plan.tips,
        )

    # Scaling factor if Gemini exceeded total budget
    scale_factor = 1.0
    if current_sum > total_budget and current_sum > 0:
        logger.warning(
            f"AI allocations sum ({current_sum}) exceeded budget ({total_budget}). Proportionally scaling allocations."
        )
        scale_factor = total_budget / current_sum

    running_allocated = 0.0
    for alloc in raw_allocations:
        amount = max(0.0, float(alloc.amount)) * scale_factor
        rounded_amount = round(amount, 2)
        pct = round((rounded_amount / total_budget) * 100, 2) if total_budget > 0 else 0.0

        adjusted_allocations.append(
            BudgetAllocation(
                category=alloc.category.strip(),
                amount=rounded_amount,
                percentage=pct,
                reason=alloc.reason.strip(),
            )
        )
        running_allocated += rounded_amount

    # Deterministic recalculations
    allocated_budget = round(running_allocated, 2)

    # Prevent accidental rounding overage
    if allocated_budget > total_budget:
        diff = round(allocated_budget - total_budget, 2)
        if adjusted_allocations:
            adjusted_allocations[0].amount = round(adjusted_allocations[0].amount - diff, 2)
            allocated_budget = round(sum(a.amount for a in adjusted_allocations), 2)

    remaining_budget = round(max(0.0, total_budget - allocated_budget), 2)

    # Recalculate percentages to reflect final amounts precisely
    for a in adjusted_allocations:
        a.percentage = round((a.amount / total_budget) * 100, 2) if total_budget > 0 else 0.0

    logger.info(
        f"Financial validation complete: total={total_budget}, allocated={allocated_budget}, remaining={remaining_budget}"
    )

    return PlanningResponse(
        summary=raw_plan.summary.strip(),
        total_budget=total_budget,
        allocated_budget=allocated_budget,
        remaining_budget=remaining_budget,
        allocations=adjusted_allocations,
        weekly_plan=raw_plan.weekly_plan,
        tips=raw_plan.tips,
    )

