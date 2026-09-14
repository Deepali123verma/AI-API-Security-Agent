from typing import Any

from app.agents.gemini_client import GeminiClient, GeminiClientError
from app.agents.models import AIAnalysisResult, FindingAIContext
from app.agents.prompts import SECURITY_AGENT_SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.agents.sanitizer import to_safe_json
from app.core.config import settings


class SecurityAgent:
    def __init__(self, client: GeminiClient | None = None) -> None:
        self.client = client or GeminiClient()

    def analyze_finding(
        self,
        finding: dict[str, Any],
        endpoint: dict[str, Any] | None = None,
        scan_metadata: dict[str, Any] | None = None,
        untrusted_openapi: dict[str, Any] | None = None,
    ) -> AIAnalysisResult:
        context = FindingAIContext(
            finding=finding,
            endpoint=endpoint,
            scan_metadata=scan_metadata,
        )
        user_prompt = USER_PROMPT_TEMPLATE.format(
            finding_json=to_safe_json(context.finding),
            endpoint_json=to_safe_json(context.endpoint or {}),
            scan_metadata_json=to_safe_json(context.scan_metadata or {}),
            untrusted_openapi_json=to_safe_json(untrusted_openapi or {}),
        )
        return self.client.generate_structured(
            system_prompt=SECURITY_AGENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=AIAnalysisResult,
        )

    @property
    def model_name(self) -> str:
        return self.client.model or settings.gemini_model
