from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ai import router as ai_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.errors import (
    BaseAppException,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        f"Starting HisabKitab AI Backend (env={settings.app_env}, model={settings.gemini_model})"
    )
    yield
    logger.info("Shutting down HisabKitab AI Backend")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="HisabKitab AI Backend",
        description=(
            "Production-ready AI financial planning and budgeting backend "
            "powered by FastAPI and Google Gemini."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS Middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(BaseAppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Mount routers
    app.include_router(health_router)
    app.include_router(ai_router)

    @app.get(
        "/",
        tags=["General"],
        summary="API Service Information",
        description="Returns complete details, health status, supported endpoints, and AI provider metadata.",
    )
    async def root():
        current_settings = get_settings()
        return {
            "service": "HisabKitab AI Backend (حساب کتاب)",
            "version": "0.1.0",
            "status": "online",
            "tagline": "Clear hisaab, happy ghar",
            "environment": current_settings.app_env,
            "ai_provider": {
                "provider": "Google Gemini",
                "model": current_settings.gemini_model,
                "sdk": "google-genai",
                "timeout_seconds": current_settings.ai_timeout_seconds,
                "max_retries": current_settings.ai_max_retries,
            },
            "endpoints": {
                "root": {
                    "method": "GET",
                    "path": "/",
                    "description": "API status, service metadata, and endpoint directory",
                },
                "health": {
                    "method": "GET",
                    "path": "/health",
                    "description": "Service health check probe",
                },
                "docs": {
                    "method": "GET",
                    "path": "/docs",
                    "description": "Interactive OpenAPI Swagger UI documentation",
                },
                "redoc": {
                    "method": "GET",
                    "path": "/redoc",
                    "description": "ReDoc API reference documentation",
                },
                "generate_plan": {
                    "method": "POST",
                    "path": "/api/v1/ai/generate-plan",
                    "description": "Generate intelligent personalized budget plans and category allocations",
                    "auth_required": False,
                    "auth_type": "Optional Bearer token (Appwrite session / JWT)",
                },
            },
            "features": [
                "Personalized multi-category budget allocation (Food, Education, Bills, Doctor, Transport, Grocery, Others)",
                "Deterministic backend financial invariant verification & proportional auto-balancing",
                "Bilingual internationalization support (English & Urdu)",
                "Sliding-window rate limiting per client IP",
                "VisionOS Liquid Glass React Native companion architecture",
            ],
            "rate_limit": f"{current_settings.rate_limit_requests_per_minute} requests/minute per client IP",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development",
    )
