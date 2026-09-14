from pathlib import Path

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


def upload_spec(client, headers: dict[str, str], filename: str):
    content = (FIXTURES_DIR / filename).read_bytes()
    files = {"file": (filename, content, "application/yaml")}
    return client.post("/api/v1/scans", files=files, headers=headers)


def test_security_scan_on_demo_spec_persists_findings(client) -> None:
    headers = register_and_login(client, "secscan1", "secscan1@example.com")
    create_response = upload_spec(client, headers, "demo_store.yaml")
    scan_id = create_response.json()["scan_id"]

    scan_response = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers)
    assert scan_response.status_code == 200
    payload = scan_response.json()
    assert payload["scan_id"] == scan_id
    assert payload["findings_count"] > 0
    assert payload["total_findings"] == payload["findings_count"]
    assert len(payload["findings"]) == payload["findings_count"]
    assert "overall_risk_score" in payload
    assert "risk_level" in payload
    assert isinstance(payload["overall_risk_score"], int)
    assert 0 <= payload["overall_risk_score"] <= 100

    first_finding = payload["findings"][0]
    assert "risk_score" in first_finding
    assert "risk_level" in first_finding
    assert "risk_factors" in first_finding
    assert "structured_evidence" in first_finding

    titles = {finding["title"] for finding in payload["findings"]}
    assert "Potential Missing Authentication" in titles
    assert "Potential BOLA / IDOR Risk" in titles
    assert "Potential Missing Rate Limiting" in titles

    findings_response = client.get(f"/api/v1/scans/{scan_id}/findings", headers=headers)
    assert findings_response.status_code == 200
    assert len(findings_response.json()["items"]) == payload["findings_count"]


def test_running_security_scan_twice_does_not_duplicate_findings(client) -> None:
    headers = register_and_login(client, "secscan2", "secscan2@example.com")
    scan_id = upload_spec(client, headers, "demo_store.yaml").json()["scan_id"]

    first = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers)
    second = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers)

    assert first.json()["findings_count"] == second.json()["findings_count"]
    assert len(first.json()["findings"]) == len(second.json()["findings"])
    assert first.json()["overall_risk_score"] == second.json()["overall_risk_score"]
    assert first.json()["risk_level"] == second.json()["risk_level"]


def test_user_cannot_run_security_scan_on_another_users_scan(client) -> None:
    user_a = register_and_login(client, "owner1", "owner1@example.com")
    user_b = register_and_login(client, "owner2", "owner2@example.com")

    scan_id = upload_spec(client, user_a, "demo_store.yaml").json()["scan_id"]
    response = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=user_b)

    assert response.status_code == 404


def test_user_cannot_retrieve_another_users_findings(client) -> None:
    user_a = register_and_login(client, "owner3", "owner3@example.com")
    user_b = register_and_login(client, "owner4", "owner4@example.com")

    scan_id = upload_spec(client, user_a, "demo_store.yaml").json()["scan_id"]
    client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=user_a)

    response = client.get(f"/api/v1/scans/{scan_id}/findings", headers=user_b)
    assert response.status_code == 404


def test_unauthenticated_user_cannot_run_security_scan(client) -> None:
    headers = register_and_login(client, "secscan3", "secscan3@example.com")
    scan_id = upload_spec(client, headers, "demo_store.yaml").json()["scan_id"]

    response = client.post(f"/api/v1/scans/{scan_id}/security-scan")
    assert response.status_code == 401


def test_findings_filter_by_severity(client) -> None:
    headers = register_and_login(client, "secscan4", "secscan4@example.com")
    scan_id = upload_spec(client, headers, "demo_store.yaml").json()["scan_id"]
    client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers)

    response = client.get(
        f"/api/v1/scans/{scan_id}/findings",
        params={"severity": "HIGH"},
        headers=headers,
    )
    assert response.status_code == 200
    assert all(item["severity"] == "HIGH" for item in response.json()["items"])


def test_findings_filter_by_risk_level(client) -> None:
    headers = register_and_login(client, "secscan5", "secscan5@example.com")
    scan_id = upload_spec(client, headers, "demo_store.yaml").json()["scan_id"]
    scan_payload = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers).json()
    risk_level = scan_payload["findings"][0]["risk_level"]

    response = client.get(
        f"/api/v1/scans/{scan_id}/findings",
        params={"risk_level": risk_level},
        headers=headers,
    )
    assert response.status_code == 200
    assert all(item["risk_level"] == risk_level for item in response.json()["items"])


def test_findings_filter_by_min_risk_score(client) -> None:
    headers = register_and_login(client, "secscan6", "secscan6@example.com")
    scan_id = upload_spec(client, headers, "demo_store.yaml").json()["scan_id"]
    client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers)

    response = client.get(
        f"/api/v1/scans/{scan_id}/findings",
        params={"min_risk_score": 70},
        headers=headers,
    )
    assert response.status_code == 200
    assert all(item["risk_score"] >= 70 for item in response.json()["items"])
