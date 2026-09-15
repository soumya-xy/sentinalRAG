from fastapi.testclient import TestClient


def test_demo_login_and_me(client: TestClient) -> None:
    login = client.post(
        "/api/auth/login",
        json={"email": "demo@sentinelrag.dev", "password": "demo1234"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "demo@sentinelrag.dev"


def test_register_duplicate_conflict(client: TestClient) -> None:
    payload = {
        "email": "ops@example.com",
        "password": "password1",
        "display_name": "Ops",
    }
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409


def test_logout_revokes_token(client: TestClient) -> None:
    login = client.post(
        "/api/auth/login",
        json={"email": "demo@sentinelrag.dev", "password": "demo1234"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
