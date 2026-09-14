def test_register_login_and_me(client) -> None:
    register_response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123",
        },
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "test@example.com"
    assert user_data["role"] == "user"
    assert user_data["is_active"] is True
    assert "hashed_password" not in user_data
    assert "password" not in user_data

    login_response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "securepass123"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "testuser"


def test_register_duplicate_username(client) -> None:
    payload = {
        "username": "duplicate",
        "email": "first@example.com",
        "password": "securepass123",
    }
    client.post("/auth/register", json=payload)

    response = client.post(
        "/auth/register",
        json={
            "username": "duplicate",
            "email": "second@example.com",
            "password": "securepass123",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


def test_login_with_wrong_password(client) -> None:
    client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "securepass123",
        },
    )

    response = client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_me_without_token(client) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401
