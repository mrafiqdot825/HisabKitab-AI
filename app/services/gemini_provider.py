import asyncio
import json
import re
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.core.errors import AIProviderError, AITimeoutError
from app.core.logging import logger
from app.schemas.ai_response import RawAIPlanOutput


class GeminiProvider:
    """Implementation of AIProvider backed by Google GenAI SDK with structured output."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._client = genai.Client(api_key=api_key)

    async def generate_plan(
        self,
        system_instruction: str,
        user_prompt: str,
    ) -> RawAIPlanOutput:
        """Call Gemini to generate a structured budget plan, with timeout and retry handling."""
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=RawAIPlanOutput,
            temperature=0.2,
        )

        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"Calling Gemini API (model={self.model_name}, attempt={attempt + 1}/{self.max_retries + 1})"
                )

                response = await asyncio.wait_for(
                    self._client.aio.models.generate_content(
                        model=self.model_name,
                        contents=user_prompt,
                        config=config,
                    ),
                    timeout=self.timeout_seconds,
                )

                if not response.text:
                    raise AIProviderError("Gemini returned an empty response.")

                return self._parse_response(response.text)

            except asyncio.TimeoutError as exc:
                logger.warning(
                    f"Gemini call timed out after {self.timeout_seconds}s (attempt {attempt + 1})"
                )
                last_exception = AITimeoutError(
                    f"AI planning request timed out after {self.timeout_seconds} seconds."
                )
                if attempt == self.max_retries:
                    raise last_exception
                await asyncio.sleep(0.5 * (2**attempt))

            except genai_errors.ClientError as exc:
                # 4xx client errors (e.g. invalid API key, model not found) should NOT be retried
                logger.error(f"Gemini client error (non-retryable): {exc.message}")
                raise AIProviderError(f"AI service configuration error: {exc.message}") from exc

            except (genai_errors.ServerError, genai_errors.APIError) as exc:
                # 5xx server errors or transient API errors can be retried
                logger.warning(f"Gemini API transient error (attempt {attempt + 1}): {exc.message}")
                last_exception = AIProviderError(
                    "The AI service is temporarily unavailable. Please try again shortly."
                )
                if attempt == self.max_retries:
                    raise last_exception from exc
                await asyncio.sleep(0.5 * (2**attempt))

            except (ValidationError, json.JSONDecodeError) as exc:
                logger.error(f"Failed to validate Gemini structured output: {str(exc)}")
                raise AIProviderError("Received malformed plan data from AI service.") from exc

            except Exception as exc:
                logger.error(f"Unexpected error calling Gemini: {str(exc)}")
                raise AIProviderError("Failed to communicate with AI service.") from exc

        if last_exception:
            raise last_exception
        raise AIProviderError("Failed to generate plan after retries.")

    def _parse_response(self, text: str) -> RawAIPlanOutput:
        """Parse and sanitize JSON response into RawAIPlanOutput."""
        cleaned = text.strip()
        # Remove Markdown code fences if model enclosed JSON
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        data = json.loads(cleaned)
        return RawAIPlanOutput.model_validate(data)

