from app.agents.gemini_client import GeminiClient, GeminiClientError
from app.agents.models import AIAnalysisResult
from app.core.config import settings


def test_gemini_client_uses_configured_model() -> None:
    client = GeminiClient(api_key="test-key", model="gemini-2.5-flash", temperature=0.1)
    assert client.model == "gemini-2.5-flash"
    assert client.temperature == 0.1


def test_gemini_client_missing_api_key_raises() -> None:
    client = GeminiClient(api_key=None)
    try:
        client.ensure_configured()
        raised = False
    except GeminiClientError:
        raised = True
    assert raised


def test_gemini_client_successful_mocked_response(mocker) -> None:
    expected = AIAnalysisResult(
        summary="Potential authorization risk",
        why_it_matters="Object IDs may allow unauthorized access",
        technical_reasoning="The endpoint accepts a client-controlled id",
        validation_guidance="Verify object-level authorization at runtime",
        remediation="Enforce ownership checks for resource IDs",
        priority="HIGH",
        limitations="Based on static OpenAPI analysis only",
    )
    mock_response = mocker.Mock()
    mock_response.parsed = expected
    mock_response.text = expected.model_dump_json()

    mock_models = mocker.Mock()
    mock_models.generate_content.return_value = mock_response
    mock_client = mocker.Mock()
    mock_client.models = mock_models
    mocker.patch("app.agents.gemini_client.genai.Client", return_value=mock_client)

    client = GeminiClient(api_key="test-key", model=settings.gemini_model)
    result = client.generate_structured("system", "user")

    assert result.summary == expected.summary
    mock_models.generate_content.assert_called_once()


def test_gemini_client_api_failure(mocker) -> None:
    mock_models = mocker.Mock()
    mock_models.generate_content.side_effect = RuntimeError("network down")
    mock_client = mocker.Mock()
    mock_client.models = mock_models
    mocker.patch("app.agents.gemini_client.genai.Client", return_value=mock_client)

    client = GeminiClient(api_key="test-key")
    try:
        client.generate_structured("system", "user")
        raised = False
    except GeminiClientError as exc:
        raised = True
        assert "failed" in str(exc).lower()
    assert raised


def test_gemini_client_malformed_response(mocker) -> None:
    mock_response = mocker.Mock()
    mock_response.parsed = None
    mock_response.text = '{"summary": "incomplete"}'
    mock_models = mocker.Mock()
    mock_models.generate_content.return_value = mock_response
    mock_client = mocker.Mock()
    mock_client.models = mock_models
    mocker.patch("app.agents.gemini_client.genai.Client", return_value=mock_client)

    client = GeminiClient(api_key="test-key")
    try:
        client.generate_structured("system", "user")
        raised = False
    except GeminiClientError as exc:
        raised = True
        assert "malformed" in str(exc).lower()
    assert raised
