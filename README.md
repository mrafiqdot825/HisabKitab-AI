# HisabKitab AI Backend (حساب کتاب)

> Production-ready AI financial planning and budget recommendation backend for the **HisabKitab** React Native mobile application, built with **FastAPI**, **uv**, and **Google Gemini** (via the official `google-genai` SDK).

---

## Architecture Overview

```text
React Native App (HisabKitab)
       │
       │ HTTPS / JSON (POST /api/v1/ai/generate-plan)
       ▼
FastAPI Backend (app.main)
       │
       ├── Rate Limiting & Auth Header Validation (app.api.deps)
       │
       ├── Input Validation (Pydantic: PlanningRequest)
       │
       ├── Planning Service (app.services.planning_service)
       │       │
       │       ├── Prompt Service (app.services.prompt_service)
       │       │
       │       └── AI Service / Provider Abstraction (app.services.ai_service)
       │               │
       │               ▼
       │         GeminiProvider (google-genai SDK + Structured JSON Output)
       │               │
       │               ▼
       │         Google Gemini API
       │
       ├── Deterministic Business Verification (app.utils.validation)
       │       * sum(allocations) <= budget
       │       * allocated_budget + remaining_budget == total_budget
       │       * exact percentage recalculation & proportional scaling
       │
       ▼
Structured PlanningResponse JSON
       │
       ▼
React Native App
```

> [!IMPORTANT]
> **Key Security Guarantee**: The React Native client **never** communicates directly with Google Gemini and **never** has access to the `GEMINI_API_KEY`. All Gemini credentials, timeout configurations, and retries remain strictly server-side.

---

## Project Structure

```text
ai/
├── app/
│   ├── __init__.py
│   ├── main.py                           # FastAPI entrypoint, lifespan, CORS, middleware
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                       # Rate limiter and authentication dependencies
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py                 # GET /health
│   │       └── ai.py                     # POST /api/v1/ai/generate-plan
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                     # Pydantic Settings (.env configuration)
│   │   ├── errors.py                     # Standardized error codes & exception handlers
│   │   └── logging.py                    # Structured logging with safe masking
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── planning.py                   # System instructions and user prompt builder
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── planning.py                   # PlanningRequest & Expense input models
│   │   └── ai_response.py                # PlanningResponse, BudgetAllocation, WeeklyPlan, Tips
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_provider.py                # Abstract AIProvider protocol
│   │   ├── gemini_provider.py            # Concrete Google GenAI SDK implementation
│   │   ├── ai_service.py                 # AI service dispatcher
│   │   ├── planning_service.py           # End-to-end plan orchestrator
│   │   └── prompt_service.py             # Prompt builder
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py               # In-memory sliding window rate limiter
│       └── validation.py                 # Deterministic financial math calculations
├── tests/
│   ├── __init__.py
│   ├── conftest.py                       # Test fixtures and MockAIProvider
│   ├── test_ai_response.py               # Math validation & JSON fence stripping tests
│   ├── test_health.py                    # Health check tests
│   ├── test_planning.py                  # API routes, Pydantic validation, and errors
│   └── test_rate_limiter.py              # Rate limiting tests
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Prerequisites

- **Python**: `3.12+` (tested on Python 3.14)
- **Package & Environment Manager**: [uv](https://docs.astral.sh/uv/)
- **Google Gemini API Key**: Obtainable from [Google AI Studio](https://aistudio.google.com/)

---

## Environment Setup

1. Copy the sample environment file:

   ```bash
   cp .env.example .env
   ```

2. Configure `.env` with your actual Google Gemini credentials:
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_api_key...
   GEMINI_MODEL=gemini-3.8-flash
   APP_ENV=development
   LOG_LEVEL=INFO
   AI_TIMEOUT_SECONDS=30.0
   AI_MAX_RETRIES=2
   RATE_LIMIT_REQUESTS_PER_MINUTE=15
   HOST=0.0.0.0
   PORT=8000
   ```

---

## Virtual Environment & Dependency Installation

Always activate the project virtual environment before running commands:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Sync all production and development dependencies using uv
uv sync
```

---

## Running the Server

### Development Mode (with hot-reload):

```bash
source .venv/bin/activate
uv run fastapi dev app/main.py --port 8000
```

Or directly with `uvicorn`:

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Interactive API Documentation

Once the server is running, explore and test the endpoints directly:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## API Endpoints

### 1. Health Check

- **Method**: `GET /health`
- **Description**: Verifies service availability without making external Gemini calls.
- **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

### 2. Generate Intelligent Financial Plan

- **Method**: `POST /api/v1/ai/generate-plan`
- **Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` _(Optional: supports authenticated cloud sync or guest mode)_

#### Sample Request (`curl`):

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-plan \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 150000.0,
    "currency": "PKR",
    "people": 4,
    "duration_days": 30,
    "goal": "Build an emergency fund while managing household expenses",
    "categories": [
      "food",
      "housing",
      "transport",
      "education",
      "savings"
    ],
    "preferences": [
      "Minimize dining out",
      "Keep fuel expenses disciplined"
    ],
    "existing_expenses": [
      {
        "category": "housing",
        "amount": 25000.0,
        "description": "Apartment maintenance & electricity"
      }
    ]
  }'
```

#### Sample Response:

```json
{
  "summary": "A balanced 30-day plan prioritizing staple household essentials and a 15% emergency savings allocation.",
  "total_budget": 150000.0,
  "allocated_budget": 127500.0,
  "remaining_budget": 22500.0,
  "allocations": [
    {
      "category": "food",
      "amount": 45000.0,
      "percentage": 30.0,
      "reason": "Wholesome groceries and cooking at home for 4 people"
    },
    {
      "category": "housing",
      "amount": 35000.0,
      "percentage": 23.33,
      "reason": "Covers fixed 25,000 PKR utilities plus discretionary home upkeep"
    },
    {
      "category": "savings",
      "amount": 22500.0,
      "percentage": 15.0,
      "reason": "Emergency reserve fund deposit"
    },
    {
      "category": "transport",
      "amount": 15000.0,
      "percentage": 10.0,
      "reason": "Monthly fuel and commute allowance"
    },
    {
      "category": "education",
      "amount": 10000.0,
      "percentage": 6.67,
      "reason": "School fees and course materials"
    }
  ],
  "weekly_plan": [
    {
      "week": 1,
      "budget": 35000.0,
      "focus": "Stock up monthly essentials & pay utility bills",
      "recommendations": [
        "Purchase monthly dry rations in bulk to save on unit costs",
        "Clear utility bills early to avoid late fees"
      ]
    },
    {
      "week": 2,
      "budget": 20000.0,
      "focus": "Commute and routine mid-month expenses",
      "recommendations": ["Track daily travel costs in HisabKitab"]
    }
  ],
  "tips": [
    {
      "title": "Log Daily Cash Transactions",
      "description": "Log cash hisaab in HisabKitab every evening to prevent unaccounted leakage.",
      "priority": "high"
    },
    {
      "title": "Emergency Transfer on Day 1",
      "description": "Transfer the 22,500 PKR savings immediately to an inaccessible savings vault.",
      "priority": "high"
    }
  ]
}
```

---

## Error Handling

All error responses adhere to a consistent structure:

```json
{
  "error": {
    "code": "AI_PROVIDER_ERROR",
    "message": "The AI service is temporarily unavailable."
  }
}
```

Standard HTTP status codes used:

- `200 OK`: Successful plan generation
- `400 Bad Request`: Business rule violation
- `422 Unprocessable Content`: Pydantic input validation failure
- `429 Too Many Requests`: Client exceeded request limit (15 req/min default)
- `502 Bad Gateway`: Upstream AI provider issue
- `504 Gateway Timeout`: Gemini request exceeded configured timeout (`AI_TIMEOUT_SECONDS`)

---

## Deterministic Budget Calculations

The backend serves as the **source of truth** for all financial arithmetic:

1. **Budget Invariant**: `allocated_budget + remaining_budget == total_budget` is strictly verified.
2. **Proportional Scaling**: If the LLM generates allocations totaling more than the user's budget, the backend deterministically scales down all allocations proportionally so `sum(allocations) <= total_budget`.
3. **Exact Percentages**: Every category percentage is calculated directly by the backend: `(amount / total_budget) * 100`.

---

## Running Automated Tests

Deterministic unit and integration tests run **offline without consuming Gemini API tokens** (all AI responses are mocked via `MockAIProvider`):

```bash
# 1. Activate venv
source .venv/bin/activate

# 2. Run pytest
uv run pytest -v
```

---

## Code Quality & Linting

```bash
# 1. Activate venv
source .venv/bin/activate

# 2. Run Ruff check
uv run ruff check .

# 3. Run Ruff formatting check
uv run ruff format --check .
```

---

## React Native Integration Example

Inside the React Native application (e.g. `src/services/aiPlanService.ts`):

```typescript
// src/services/aiPlanService.ts

export interface PlanningRequestPayload {
  budget: number;
  currency: string;
  people: number;
  duration_days: number;
  goal: string;
  categories: string[];
  preferences?: string[];
  existing_expenses?: Array<{
    category: string;
    amount: number;
    description?: string;
  }>;
}

export interface BudgetAllocation {
  category: string;
  amount: number;
  percentage: number;
  reason: string;
}

export interface WeeklyPlan {
  week: number;
  budget: number;
  focus: string;
  recommendations: string[];
}

export interface PlanningTip {
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
}

export interface PlanningResponse {
  summary: string;
  total_budget: number;
  allocated_budget: number;
  remaining_budget: number;
  allocations: BudgetAllocation[];
  weekly_plan: WeeklyPlan[];
  tips: PlanningTip[];
}

const BACKEND_API_URL =
  process.env.EXPO_PUBLIC_AI_API_URL || "http://localhost:8000";

export async function generateAIPlan(
  payload: PlanningRequestPayload,
  userToken?: string | null,
): Promise<PlanningResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (userToken) {
    headers["Authorization"] = `Bearer ${userToken}`;
  }

  const response = await fetch(`${BACKEND_API_URL}/api/v1/ai/generate-plan`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const errorMessage =
      errorBody?.error?.message ||
      `Request failed with status ${response.status}`;
    throw new Error(errorMessage);
  }

  return await response.json();
}
```
