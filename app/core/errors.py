from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import logger


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class BaseAppException(Exception):
    def __init__(
        self, code: str, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class AIProviderError(BaseAppException):
    def __init__(self, message: str = "The AI service is temporarily unavailable."):
        super().__init__(
            code="AI_PROVIDER_ERROR",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class AITimeoutError(BaseAppException):
    def __init__(self, message: str = "The AI service request timed out."):
        super().__init__(
            code="AI_PROVIDER_TIMEOUT",
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )


class RateLimitExceededError(BaseAppException):
    def __init__(self, message: str = "Rate limit exceeded. Please try again shortly."):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class BusinessValidationError(BaseAppException):
    def __init__(self, message: str):
        super().__init__(
            code="BUSINESS_VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    logger.warning(
        f"Application error on {request.method} {request.url.path}: {exc.code} - {exc.message}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    first_error = exc.errors()[0] if exc.errors() else {}
    msg = first_error.get("msg", "Invalid request parameters")
    loc = " -> ".join(str(l) for l in first_error.get("loc", []))
    formatted_msg = f"{loc}: {msg}" if loc else msg

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": formatted_msg,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled server error on {request.method} {request.url.path}: {exc!s}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred.",
            }
        },
    )
