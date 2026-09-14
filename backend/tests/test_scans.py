from pathlib import Path

import pytest

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


def upload_spec(client, headers: dict[str, str], filename: str, name: str | None = None):
    content = (FIXTURES_DIR / filename).read_bytes()
    files = {"file": (filename, content, "application/yaml")}
    data = {"name": name} if name is not None else {}
    return client.post("/api/v1/scans", files=files, data=data, headers=headers)


def test_upload_valid_openapi_spec(client) -> None:
    headers = register_and_login(client, "scanuser1", "scanuser1@example.com")
    response = upload_spec(client, headers, "demo_store.yaml", name="Demo Store Scan")

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "PENDING"
    assert payload["name"] == "Demo Store Scan"

    scan_id = payload["scan_id"]
    detail_response = client.get(f"/api/v1/scans/{scan_id}", headers=headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["title"] == "Demo Store API"
    assert detail["version"] == "1.0.0"
    assert detail["specification_version"] == "3.0.3"
    assert detail["endpoint_count"] == 3
    assert detail["status"] == "PENDING"
    assert detail["summary"]["endpoint_count"] == 3

    endpoints_response = client.get(f"/api/v1/scans/{scan_id}/endpoints", headers=headers)
    assert endpoints_response.status_code == 200
    endpoints = endpoints_response.json()["items"]
    assert len(endpoints) == 3

    discovered = {(item["method"], item["path"]) for item in endpoints}
    assert discovered == {
        ("GET", "/users"),
        ("GET", "/users/{id}"),
        ("POST", "/login"),
    }


def test_reject_invalid_json(client) -> None:
    headers = register_and_login(client, "scanuser2", "scanuser2@example.com")
    files = {"file": ("invalid.json", b"{not-json", "application/json")}
    response = client.post("/api/v1/scans", files=files, headers=headers)

    assert response.status_code == 400
    assert "Invalid JSON or YAML" in response.json()["detail"]


def test_reject_invalid_yaml(client) -> None:
    headers = register_and_login(client, "scanuser3", "scanuser3@example.com")
    files = {"file": ("invalid.yaml", b"openapi: [\n  bad yaml", "application/yaml")}
    response = client.post("/api/v1/scans", files=files, headers=headers)

    assert response.status_code == 400
    assert "Invalid YAML" in response.json()["detail"]


def test_reject_non_openapi_document(client) -> None:
    headers = register_and_login(client, "scanuser4", "scanuser4@example.com")
    files = {"file": ("not-openapi.json", b'{"hello": "world"}', "application/json")}
    response = client.post("/api/v1/scans", files=files, headers=headers)

    assert response.status_code == 400
    assert "Not a valid OpenAPI or Swagger specification" in response.json()["detail"]


def test_unauthenticated_user_cannot_create_scan(client) -> None:
    content = (FIXTURES_DIR / "demo_store.yaml").read_bytes()
    files = {"file": ("demo_store.yaml", content, "application/yaml")}
    response = client.post("/api/v1/scans", files=files)

    assert response.status_code == 401


def test_scan_ownership(client) -> None:
    user_a_headers = register_and_login(client, "usera", "usera@example.com")
    user_b_headers = register_and_login(client, "userb", "userb@example.com")

    create_response = upload_spec(client, user_a_headers, "demo_store.yaml")
    scan_id = create_response.json()["scan_id"]

    forbidden_response = client.get(f"/api/v1/scans/{scan_id}", headers=user_b_headers)
    assert forbidden_response.status_code == 404

    endpoints_response = client.get(
        f"/api/v1/scans/{scan_id}/endpoints",
        headers=user_b_headers,
    )
    assert endpoints_response.status_code == 404


def test_endpoint_extraction_for_multiple_methods(client) -> None:
    headers = register_and_login(client, "scanuser5", "scanuser5@example.com")
    response = upload_spec(client, headers, "multi_method.yaml")
    scan_id = response.json()["scan_id"]

    endpoints_response = client.get(f"/api/v1/scans/{scan_id}/endpoints", headers=headers)
    methods = {item["method"] for item in endpoints_response.json()["items"]}

    assert methods == {"GET", "POST", "PUT", "PATCH", "DELETE"}


def test_security_metadata_extraction(client) -> None:
    headers = register_and_login(client, "scanuser6", "scanuser6@example.com")
    response = upload_spec(client, headers, "security_metadata.yaml")
    scan_id = response.json()["scan_id"]

    endpoints_response = client.get(f"/api/v1/scans/{scan_id}/endpoints", headers=headers)
    endpoints = {
        f"{item['method']} {item['path']}": item
        for item in endpoints_response.json()["items"]
    }

    assert endpoints["GET /public/status"]["security_defined"] is False
    assert endpoints["GET /users"]["security_defined"] is True
    assert endpoints["GET /admin/users"]["security_defined"] is True
    assert endpoints["GET /admin/users"]["security_requirements"] == [{"bearerAuth": ["admin"]}]


@pytest.mark.parametrize(
    ("filename", "content", "content_type"),
    [
        ("empty.json", b"", "application/json"),
    ],
)
def test_reject_empty_file(client, filename, content, content_type) -> None:
    headers = register_and_login(client, f"empty-{filename}", f"{filename}@example.com")
    files = {"file": (filename, content, content_type)}
    response = client.post("/api/v1/scans", files=files, headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"
