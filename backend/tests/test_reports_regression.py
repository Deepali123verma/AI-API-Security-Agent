from datetime import UTC, datetime
from pathlib import Path

from app.core.database import SessionLocal
from app.models.finding import Finding
from app.models.scan import Scan
from app.reports.helpers import finding_fingerprint
from app.services.regression_service import classify_posture

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
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def upload_and_scan(client, headers: dict[str, str], filename: str = "demo_store.yaml") -> int:
    content = (FIXTURES_DIR / filename).read_bytes()
    created = client.post(
        "/api/v1/scans",
        files={"file": (filename, content, "application/yaml")},
        headers=headers,
    )
    scan_id = created.json()["scan_id"]
    scan_response = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers)
    assert scan_response.status_code == 200
    return scan_id


def test_report_requires_auth(client) -> None:
    response = client.get("/api/v1/scans/1/report/pdf")
    assert response.status_code == 401


def test_report_pdf_generation_and_content_type(client) -> None:
    headers = register_and_login(client, "report_user", "report_user@example.com")
    scan_id = upload_and_scan(client, headers)

    response = client.get(f"/api/v1/scans/{scan_id}/report/pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert f"security-report-{scan_id}.pdf" in response.headers.get("content-disposition", "")
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 500


def test_report_without_and_with_ai_analysis(client) -> None:
    headers = register_and_login(client, "report_ai", "report_ai@example.com")
    scan_id = upload_and_scan(client, headers)

    without_ai = client.get(f"/api/v1/scans/{scan_id}/report/pdf", headers=headers)
    assert without_ai.status_code == 200
    assert without_ai.content[:4] == b"%PDF"

    with SessionLocal() as db:
        finding = db.query(Finding).filter(Finding.scan_id == scan_id).first()
        assert finding is not None
        finding.ai_summary = "Missing authentication increases exposure."
        finding.ai_why_it_matters = "Unauthorized callers may reach the endpoint."
        finding.ai_technical_reasoning = "No security requirements were declared."
        finding.ai_validation_guidance = "Confirm auth middleware in runtime."
        finding.ai_remediation = "Require bearer authentication."
        finding.ai_priority = "HIGH"
        finding.ai_limitations = "Static analysis only."
        finding.ai_model = "gemini-2.5-flash"
        finding.ai_analyzed_at = datetime.now(UTC)
        db.commit()

    with_ai = client.get(f"/api/v1/scans/{scan_id}/report/pdf", headers=headers)
    assert with_ai.status_code == 200
    assert with_ai.content[:4] == b"%PDF"
    assert len(with_ai.content) >= len(without_ai.content)


def test_report_ownership_and_missing_scan(client) -> None:
    user_a = register_and_login(client, "report_a", "report_a@example.com")
    user_b = register_and_login(client, "report_b", "report_b@example.com")
    scan_id = upload_and_scan(client, user_a)

    forbidden = client.get(f"/api/v1/scans/{scan_id}/report/pdf", headers=user_b)
    assert forbidden.status_code == 404

    missing = client.get("/api/v1/scans/999999/report/pdf", headers=user_a)
    assert missing.status_code == 404


def test_regression_identical_scans_are_persistent(client) -> None:
    headers = register_and_login(client, "reg_same", "reg_same@example.com")
    baseline_id = upload_and_scan(client, headers)
    current_id = upload_and_scan(client, headers)

    response = client.get(
        f"/api/v1/scans/{current_id}/compare/{baseline_id}",
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["new_findings"] == []
    assert body["resolved_findings"] == []
    assert len(body["persistent_findings"]) > 0
    assert body["risk_score_change"] == 0
    assert body["posture"] == "UNCHANGED"
    assert body["baseline_risk_level"] == body["current_risk_level"]


def test_regression_new_resolved_and_score_changes(client) -> None:
    headers = register_and_login(client, "reg_delta", "reg_delta@example.com")
    baseline_id = upload_and_scan(client, headers)
    current_id = upload_and_scan(client, headers)

    with SessionLocal() as db:
        baseline = db.get(Scan, baseline_id)
        current = db.get(Scan, current_id)
        assert baseline is not None and current is not None

        baseline_findings = list(db.query(Finding).filter(Finding.scan_id == baseline_id).all())
        current_findings = list(db.query(Finding).filter(Finding.scan_id == current_id).all())
        assert baseline_findings and current_findings

        # Create a resolved finding: remove one from current by renaming fingerprint
        current_findings[0].title = "Unique current-only finding title"
        # Create an extra new finding on current
        clone = Finding(
            scan_id=current_id,
            endpoint_id=current_findings[0].endpoint_id,
            title="Brand new regression finding",
            description="Injected for regression test",
            severity="CRITICAL",
            category="test-regression",
            owasp_category=None,
            evidence="Synthetic evidence",
            remediation="N/A",
            confidence="HIGH",
            structured_evidence=current_findings[0].structured_evidence,
            risk_score=95,
            risk_level="CRITICAL",
            risk_factors={"test": True},
        )
        db.add(clone)

        # Force score decrease (improvement)
        baseline.overall_risk_score = 90
        baseline.overall_risk_level = "CRITICAL"
        current.overall_risk_score = 60
        current.overall_risk_level = "MEDIUM"
        db.commit()

    response = client.get(
        f"/api/v1/scans/{current_id}/compare/{baseline_id}",
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["risk_score_change"] == -30
    assert body["posture"] == "IMPROVED"
    assert body["baseline_risk_level"] == "CRITICAL"
    assert body["current_risk_level"] == "MEDIUM"
    assert any(item["title"] == "Brand new regression finding" for item in body["new_findings"])
    assert body["new_critical_count"] >= 1
    assert len(body["resolved_findings"]) >= 1
    assert len(body["persistent_findings"]) >= 1
    assert "Improved" in body["summary"]


def test_regression_worsened_score(client) -> None:
    headers = register_and_login(client, "reg_worse", "reg_worse@example.com")
    baseline_id = upload_and_scan(client, headers)
    current_id = upload_and_scan(client, headers)

    with SessionLocal() as db:
        baseline = db.get(Scan, baseline_id)
        current = db.get(Scan, current_id)
        baseline.overall_risk_score = 40
        baseline.overall_risk_level = "MEDIUM"
        current.overall_risk_score = 80
        current.overall_risk_level = "HIGH"
        db.commit()

    body = client.get(
        f"/api/v1/scans/{current_id}/compare/{baseline_id}",
        headers=headers,
    ).json()
    assert body["risk_score_change"] == 40
    assert body["posture"] == "WORSENED"
    assert "Worsened" in body["summary"]


def test_regression_ownership_and_missing(client) -> None:
    user_a = register_and_login(client, "reg_own_a", "reg_own_a@example.com")
    user_b = register_and_login(client, "reg_own_b", "reg_own_b@example.com")
    baseline_id = upload_and_scan(client, user_a)
    current_id = upload_and_scan(client, user_a)
    other_id = upload_and_scan(client, user_b)

    forbidden = client.get(
        f"/api/v1/scans/{current_id}/compare/{other_id}",
        headers=user_a,
    )
    assert forbidden.status_code == 404

    missing = client.get(
        f"/api/v1/scans/{current_id}/compare/999999",
        headers=user_a,
    )
    assert missing.status_code == 404

    same = client.get(
        f"/api/v1/scans/{current_id}/compare/{current_id}",
        headers=user_a,
    )
    assert same.status_code == 400

    # baseline belonging to A cannot be compared by B
    other_forbidden = client.get(
        f"/api/v1/scans/{other_id}/compare/{baseline_id}",
        headers=user_b,
    )
    assert other_forbidden.status_code == 404


def test_comparison_pdf_download(client) -> None:
    headers = register_and_login(client, "reg_pdf", "reg_pdf@example.com")
    baseline_id = upload_and_scan(client, headers)
    current_id = upload_and_scan(client, headers)

    response = client.get(
        f"/api/v1/scans/{current_id}/compare/{baseline_id}/report/pdf",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content[:4] == b"%PDF"


def test_finding_fingerprint_is_deterministic(client) -> None:
    headers = register_and_login(client, "fp_user", "fp_user@example.com")
    scan_id = upload_and_scan(client, headers)

    with SessionLocal() as db:
        findings = list(
            db.query(Finding).filter(Finding.scan_id == scan_id).all()
        )
        assert findings
        for finding in findings:
            # ensure endpoint loaded
            _ = finding.endpoint
            first = finding_fingerprint(finding)
            second = finding_fingerprint(finding)
            assert first == second
            assert "|" in first


def test_classify_posture_helpers() -> None:
    assert classify_posture(-5) == "IMPROVED"
    assert classify_posture(5) == "WORSENED"
    assert classify_posture(0) == "UNCHANGED"
