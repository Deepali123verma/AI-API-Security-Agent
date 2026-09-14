from pathlib import Path

from app.agents.models import AIAnalysisResult
from app.agents.security_agent import SecurityAgent
from app.services.ai_analysis_service import analyze_finding

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def register_and_login(client, username: str, email: str, password: str = "securepass123") -> dict[str, str]:
    client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    login_response = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def upload_and_scan(client, headers: dict[str, str], filename: str = "demo_store.yaml") -> tuple[int, int]:
    content = (FIXTURES_DIR / filename).read_bytes()
    create = client.post(
        "/api/v1/scans",
        files={"file": (filename, content, "application/yaml")},
        headers=headers,
    )
    scan_id = create.json()["scan_id"]
    scan_payload = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers).json()
    finding_id = scan_payload["findings"][0]["id"]
    return scan_id, finding_id


class FakeGeminiClient:
    def __init__(self) -> None:
        self.model = "gemini-2.5-flash"
        self.calls = 0

    def generate_structured(self, system_prompt: str, user_prompt: str, response_model=AIAnalysisResult):
        self.calls += 1
        return AIAnalysisResult(
            summary="Potential BOLA risk on object identifier",
            why_it_matters="Unauthorized access to user resources may be possible",
            technical_reasoning="The endpoint accepts a client-controlled object ID",
            validation_guidance="Verify authorization checks against the authenticated principal",
            remediation="Enforce object ownership and add authorization tests",
            priority="HIGH",
            limitations="Based on the provided API specification; not confirmed through runtime testing",
        )


def test_authenticated_user_can_analyze_own_finding(client, mocker) -> None:
    headers = register_and_login(client, "aiuser1", "aiuser1@example.com")
    scan_id, finding_id = upload_and_scan(client, headers)

    fake_client = FakeGeminiClient()
    mocker.patch(
        "app.services.ai_analysis_service.SecurityAgent",
        return_value=SecurityAgent(client=fake_client),  # type: ignore[arg-type]
    )

    response = client.post(
        f"/api/v1/scans/{scan_id}/findings/{finding_id}/analyze",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["finding_id"] == finding_id
    assert payload["cached"] is False
    assert payload["ai_analysis"]["summary"]
    assert payload["model"] == "gemini-2.5-flash"
    assert fake_client.calls == 1

    findings = client.get(f"/api/v1/scans/{scan_id}/findings", headers=headers).json()["items"]
    analyzed = next(item for item in findings if item["id"] == finding_id)
    assert analyzed["ai_analysis"]["summary"]
    # Deterministic fields remain present
    assert "risk_score" in analyzed
    assert "severity" in analyzed


def test_repeated_analysis_uses_cache(client, mocker) -> None:
    headers = register_and_login(client, "aiuser2", "aiuser2@example.com")
    scan_id, finding_id = upload_and_scan(client, headers)

    fake_client = FakeGeminiClient()
    mocker.patch(
        "app.services.ai_analysis_service.SecurityAgent",
        return_value=SecurityAgent(client=fake_client),  # type: ignore[arg-type]
    )

    first = client.post(
        f"/api/v1/scans/{scan_id}/findings/{finding_id}/analyze",
        headers=headers,
    )
    second = client.post(
        f"/api/v1/scans/{scan_id}/findings/{finding_id}/analyze",
        headers=headers,
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert fake_client.calls == 1


def test_force_refresh_calls_gemini_again(client, mocker) -> None:
    headers = register_and_login(client, "aiuser3", "aiuser3@example.com")
    scan_id, finding_id = upload_and_scan(client, headers)

    fake_client = FakeGeminiClient()
    mocker.patch(
        "app.services.ai_analysis_service.SecurityAgent",
        return_value=SecurityAgent(client=fake_client),  # type: ignore[arg-type]
    )

    client.post(f"/api/v1/scans/{scan_id}/findings/{finding_id}/analyze", headers=headers)
    refreshed = client.post(
        f"/api/v1/scans/{scan_id}/findings/{finding_id}/analyze",
        params={"force_refresh": True},
        headers=headers,
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["cached"] is False
    assert fake_client.calls == 2


def test_unauthenticated_analysis_rejected(client) -> None:
    response = client.post("/api/v1/scans/1/findings/1/analyze")
    assert response.status_code == 401


def test_user_cannot_analyze_another_users_finding(client, mocker) -> None:
    user_a = register_and_login(client, "aiownera", "aiownera@example.com")
    user_b = register_and_login(client, "aiownerb", "aiownerb@example.com")
    scan_id, finding_id = upload_and_scan(client, user_a)

    fake_client = FakeGeminiClient()
    mocker.patch(
        "app.services.ai_analysis_service.SecurityAgent",
        return_value=SecurityAgent(client=fake_client),  # type: ignore[arg-type]
    )

    response = client.post(
        f"/api/v1/scans/{scan_id}/findings/{finding_id}/analyze",
        headers=user_b,
    )
    assert response.status_code == 404
    assert fake_client.calls == 0


def test_finding_from_another_scan_is_rejected(client, mocker) -> None:
    headers = register_and_login(client, "aiuser4", "aiuser4@example.com")
    scan_a, finding_a = upload_and_scan(client, headers)
    scan_b, _finding_b = upload_and_scan(client, headers)

    fake_client = FakeGeminiClient()
    mocker.patch(
        "app.services.ai_analysis_service.SecurityAgent",
        return_value=SecurityAgent(client=fake_client),  # type: ignore[arg-type]
    )

    response = client.post(
        f"/api/v1/scans/{scan_b}/findings/{finding_a}/analyze",
        headers=headers,
    )
    assert response.status_code == 404
    assert fake_client.calls == 0


def test_gemini_failure_preserves_deterministic_finding(client, mocker) -> None:
    headers = register_and_login(client, "aiuser5", "aiuser5@example.com")
    scan_id, finding_id = upload_and_scan(client, headers)

    before = client.get(f"/api/v1/scans/{scan_id}/findings", headers=headers).json()["items"]
    target = next(item for item in before if item["id"] == finding_id)

    from app.agents.gemini_client import GeminiClientError

    class FailingClient(FakeGeminiClient):
        def generate_structured(self, system_prompt: str, user_prompt: str, response_model=AIAnalysisResult):
            self.calls += 1
            raise GeminiClientError("Gemini API key is not configured")

    failing = FailingClient()
    mocker.patch(
        "app.services.ai_analysis_service.SecurityAgent",
        return_value=SecurityAgent(client=failing),  # type: ignore[arg-type]
    )

    response = client.post(
        f"/api/v1/scans/{scan_id}/findings/{finding_id}/analyze",
        headers=headers,
    )
    assert response.status_code == 503

    after = client.get(f"/api/v1/scans/{scan_id}/findings", headers=headers).json()["items"]
    still_there = next(item for item in after if item["id"] == finding_id)
    assert still_there["title"] == target["title"]
    assert still_there["risk_score"] == target["risk_score"]
    assert still_there["ai_analysis"] is None


def test_bulk_ai_analysis_is_capped_and_skips_existing(client, mocker) -> None:
    headers = register_and_login(client, "aiuser6", "aiuser6@example.com")
    scan_id, finding_id = upload_and_scan(client, headers)

    fake_client = FakeGeminiClient()
    mocker.patch(
        "app.services.ai_analysis_service.SecurityAgent",
        return_value=SecurityAgent(client=fake_client),  # type: ignore[arg-type]
    )

    client.post(f"/api/v1/scans/{scan_id}/findings/{finding_id}/analyze", headers=headers)
    bulk = client.post(
        f"/api/v1/scans/{scan_id}/ai-analysis",
        params={"limit": 2},
        headers=headers,
    )
    assert bulk.status_code == 200
    payload = bulk.json()
    assert payload["scan_id"] == scan_id
    assert payload["skipped_existing_count"] >= 1
    assert payload["analyzed_count"] <= 2
