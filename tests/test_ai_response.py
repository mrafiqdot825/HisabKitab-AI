import pytest

from app.schemas.ai_response import BudgetAllocation, RawAIPlanOutput
from app.services.gemini_provider import GeminiProvider
from app.utils.validation import process_and_validate_financials


def test_validation_proportional_scaling_when_overbudget():
    """Verify backend scales down allocations if Gemini's sum exceeds budget."""
    raw = RawAIPlanOutput(
        summary="Plan with inflated allocations",
        allocations=[
            BudgetAllocation(category="Food", amount=80000.0, percentage=40.0, reason="Food"),
            BudgetAllocation(category="Rent", amount=70000.0, percentage=35.0, reason="Rent"),
            BudgetAllocation(category="Bills", amount=50000.0, percentage=25.0, reason="Bills"),
        ],
        weekly_plan=[],
        tips=[],
    )
    # Sum is 200,000 but budget is only 100,000
    res = process_and_validate_financials(raw, total_budget=100000.0)

    assert res.total_budget == 100000.0
    assert res.allocated_budget <= 100000.0
    assert round(res.allocated_budget + res.remaining_budget, 2) == 100000.0

    # Ensure allocations were scaled proportionally
    # 80k/200k = 40%, so amount should be 40k
    food_alloc = next(a for a in res.allocations if a.category == "Food")
    assert food_alloc.amount == 40000.0
    assert food_alloc.percentage == 40.0


def test_validation_underbudget_calculates_remaining():
    """Verify backend calculates remaining buffer when allocated < total."""
    raw = RawAIPlanOutput(
        summary="Plan with savings room",
        allocations=[
            BudgetAllocation(category="Food", amount=30000.0, percentage=30.0, reason="Groceries"),
            BudgetAllocation(category="Transport", amount=15000.0, percentage=15.0, reason="Fuel"),
        ],
        weekly_plan=[],
        tips=[],
    )
    res = process_and_validate_financials(raw, total_budget=100000.0)

    assert res.total_budget == 100000.0
    assert res.allocated_budget == 45000.0
    assert res.remaining_budget == 55000.0
    assert round(res.allocated_budget + res.remaining_budget, 2) == 100000.0


def test_validation_empty_allocations():
    """Verify graceful handling when AI produces no allocations."""
    raw = RawAIPlanOutput(
        summary="Empty allocations plan",
        allocations=[],
        weekly_plan=[],
        tips=[],
    )
    res = process_and_validate_financials(raw, total_budget=50000.0)
    assert res.total_budget == 50000.0
    assert res.allocated_budget == 0.0
    assert res.remaining_budget == 50000.0
    assert res.allocations == []


def test_gemini_provider_json_fence_stripping():
    """Verify markdown fences (```json ... ```) are cleanly stripped."""
    provider = GeminiProvider(api_key="dummy-key")
    raw_markdown = """```json
    {
        "summary": "Clean plan",
        "allocations": [
            {"category": "Food", "amount": 1000, "percentage": 100, "reason": "Meals"}
        ],
        "weekly_plan": [],
        "tips": []
    }
    ```"""
    parsed = provider._parse_response(raw_markdown)
    assert parsed.summary == "Clean plan"
    assert len(parsed.allocations) == 1
    assert parsed.allocations[0].category == "Food"


def test_gemini_provider_malformed_json_raises():
    """Verify malformed JSON raises appropriate exception."""
    import json

    provider = GeminiProvider(api_key="dummy-key")
    with pytest.raises(json.JSONDecodeError):
        provider._parse_response("This is not JSON at all")
