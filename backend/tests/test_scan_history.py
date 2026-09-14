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
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def upload_spec(client, headers: dict[str, str], filename: str = "demo_store.yaml"):
    content = (FIXTURES_DIR / filename).read_bytes()
    return client.post(
        "/api/v1/scans",
        files={"file": (filename, content, "application/yaml")},
        headers=headers,
    )


def test_scan_history_shows_only_own_scans_newest_first(client) -> None:
    user_a = register_and_login(client, "hist_a", "hist_a@example.com")
    user_b = register_and_login(client, "hist_b", "hist_b@example.com")

    first = upload_spec(client, user_a).json()["scan_id"]
    second = upload_spec(client, user_a).json()["scan_id"]
    other = upload_spec(client, user_b).json()["scan_id"]

    history = client.get("/api/v1/scans", headers=user_a).json()
    assert history["total"] == 2
    assert history["page"] == 1
    assert history["page_size"] == 20
    assert history["total_pages"] == 1
    assert [item["id"] for item in history["items"]] == [second, first]
    assert all(item["id"] != other for item in history["items"])
    assert all(item["status"] == "PENDING" for item in history["items"])


def test_scan_history_pagination(client) -> None:
    headers = register_and_login(client, "hist_page", "hist_page@example.com")
    for _ in range(3):
        upload_spec(client, headers)

    page1 = client.get("/api/v1/scans", params={"page": 1, "page_size": 2}, headers=headers).json()
    page2 = client.get("/api/v1/scans", params={"page": 2, "page_size": 2}, headers=headers).json()

    assert page1["total"] == 3
    assert page1["total_pages"] == 2
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 1
    assert {item["id"] for item in page1["items"]}.isdisjoint({item["id"] for item in page2["items"]})


def test_scan_history_status_and_risk_filters(client) -> None:
    headers = register_and_login(client, "hist_filter", "hist_filter@example.com")
    pending_id = upload_spec(client, headers).json()["scan_id"]
    completed_id = upload_spec(client, headers).json()["scan_id"]
    client.post(f"/api/v1/scans/{completed_id}/security-scan", headers=headers)

    pending = client.get("/api/v1/scans", params={"status": "PENDING"}, headers=headers).json()
    completed = client.get("/api/v1/scans", params={"status": "COMPLETED"}, headers=headers).json()

    assert [item["id"] for item in pending["items"]] == [pending_id]
    assert [item["id"] for item in completed["items"]] == [completed_id]
    assert completed["items"][0]["overall_risk_score"] is not None
    assert completed["items"][0]["risk_level"] is not None

    risk_level = completed["items"][0]["risk_level"]
    filtered = client.get(
        "/api/v1/scans",
        params={"risk_level": risk_level},
        headers=headers,
    ).json()
    assert all(item["risk_level"] == risk_level for item in filtered["items"])


def test_scan_detail_summary_and_ownership(client) -> None:
    user_a = register_and_login(client, "detail_a", "detail_a@example.com")
    user_b = register_and_login(client, "detail_b", "detail_b@example.com")
    scan_id = upload_spec(client, user_a).json()["scan_id"]
    client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=user_a)

    detail = client.get(f"/api/v1/scans/{scan_id}", headers=user_a).json()
    assert detail["status"] == "COMPLETED"
    assert detail["completed_at"] is not None
    assert detail["summary"]["endpoint_count"] == 3
    assert detail["summary"]["finding_count"] == 4
    assert detail["summary"]["overall_risk_score"] >= 0
    assert detail["spec_metadata"]["title"] == "Demo Store API"

    forbidden = client.get(f"/api/v1/scans/{scan_id}", headers=user_b)
    assert forbidden.status_code == 404


def test_endpoint_history_includes_finding_counts_and_pagination(client) -> None:
    headers = register_and_login(client, "ep_hist", "ep_hist@example.com")
    scan_id = upload_spec(client, headers).json()["scan_id"]
    client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers)

    response = client.get(
        f"/api/v1/scans/{scan_id}/endpoints",
        params={"page": 1, "page_size": 2},
        headers=headers,
    ).json()
    assert response["total"] == 3
    assert len(response["items"]) == 2
    assert all("finding_count" in item for item in response["items"])
    assert any(item["finding_count"] > 0 for item in response["items"])


def test_findings_history_paginated_and_keeps_ai_fields(client) -> None:
    headers = register_and_login(client, "find_hist", "find_hist@example.com")
    scan_id = upload_spec(client, headers).json()["scan_id"]
    scan_payload = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers).json()

    page = client.get(
        f"/api/v1/scans/{scan_id}/findings",
        params={"page": 1, "page_size": 2},
        headers=headers,
    ).json()
    assert page["total"] == scan_payload["findings_count"]
    assert len(page["items"]) == 2
    assert "risk_score" in page["items"][0]
    assert "ai_analysis" in page["items"][0]


def test_delete_scan_cascades_and_enforces_ownership(client) -> None:
    user_a = register_and_login(client, "del_a", "del_a@example.com")
    user_b = register_and_login(client, "del_b", "del_b@example.com")
    scan_id = upload_spec(client, user_a).json()["scan_id"]
    client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=user_a)

    forbidden = client.delete(f"/api/v1/scans/{scan_id}", headers=user_b)
    assert forbidden.status_code == 404

    deleted = client.delete(f"/api/v1/scans/{scan_id}", headers=user_a)
    assert deleted.status_code == 204

    assert client.get(f"/api/v1/scans/{scan_id}", headers=user_a).status_code == 404
    assert client.get(f"/api/v1/scans/{scan_id}/endpoints", headers=user_a).status_code == 404
    assert client.get(f"/api/v1/scans/{scan_id}/findings", headers=user_a).status_code == 404

    missing = client.get("/api/v1/scans", headers=user_a).json()
    assert all(item["id"] != scan_id for item in missing["items"])


def test_delete_nonexistent_scan_returns_404(client) -> None:
    headers = register_and_login(client, "del_missing", "del_missing@example.com")
    response = client.delete("/api/v1/scans/99999", headers=headers)
    assert response.status_code == 404


def test_security_scan_sets_completed_status_and_timestamp(client) -> None:
    headers = register_and_login(client, "status_ok", "status_ok@example.com")
    scan_id = upload_spec(client, headers).json()["scan_id"]

    before = client.get(f"/api/v1/scans/{scan_id}", headers=headers).json()
    assert before["status"] == "PENDING"
    assert before["completed_at"] is None

    scan_response = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers)
    assert scan_response.status_code == 200

    after = client.get(f"/api/v1/scans/{scan_id}", headers=headers).json()
    assert after["status"] == "COMPLETED"
    assert after["completed_at"] is not None
    assert after["summary"]["finding_count"] > 0


def test_failed_security_scan_marks_failed(client, mocker) -> None:
    headers = register_and_login(client, "status_fail", "status_fail@example.com")
    scan_id = upload_spec(client, headers).json()["scan_id"]

    mocker.patch(
        "app.services.security_scan_service.ScannerEngine.run",
        side_effect=RuntimeError("boom"),
    )
    response = client.post(f"/api/v1/scans/{scan_id}/security-scan", headers=headers)
    assert response.status_code == 500

    detail = client.get(f"/api/v1/scans/{scan_id}", headers=headers).json()
    assert detail["status"] == "FAILED"
    assert detail["completed_at"] is None
