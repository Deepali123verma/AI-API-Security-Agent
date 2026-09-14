from google import genai
from google.genai import types
from pydantic import ValidationError

from app.agents.models import AIAnalysisResult
from app.core.config import settings


class GeminiClientError(Exception):
    """Raised when Gemini is unavailable or returns an unusable response."""


class GeminiClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model if model is not None else settings.gemini_model
        self.temperature = (
            temperature if temperature is not None else settings.gemini_temperature
        )
        self._client: genai.Client | None = None

    def ensure_configured(self) -> None:
        if not self.api_key:
            raise GeminiClientError("Gemini API key is not configured")

    def _get_client(self) -> genai.Client:
        self.ensure_configured()
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[AIAnalysisResult] = AIAnalysisResult,
    ) -> AIAnalysisResult:
        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=self.temperature,
                    response_mime_type="application/json",
                    response_schema=response_model,
                ),
            )
        except GeminiClientError:
            raise
        except Exception as exc:
            raise GeminiClientError("Gemini request failed") from exc

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, response_model):
            return parsed

        text = getattr(response, "text", None)
        if not text:
            raise GeminiClientError("Gemini returned an empty response")

        try:
            return response_model.model_validate_json(text)
        except ValidationError as exc:
            raise GeminiClientError("Gemini returned malformed structured output") from exc
