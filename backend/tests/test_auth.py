EMAIL = "user@example.com"
PASSWORD = "strongpass123"


def register(client, email=EMAIL, password=PASSWORD):
    return client.post("/auth/register", json={"email": email, "password": password})


def login(client, email=EMAIL, password=PASSWORD):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_register_success(client):
    res = register(client)
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == EMAIL
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email(client):
    register(client)
    res = register(client)
    assert res.status_code == 409


def test_register_invalid_input(client):
    assert register(client, password="short").status_code == 422
    assert register(client, email="not-an-email").status_code == 422


def test_login_success(client):
    register(client)
    res = login(client)
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert res.json()["access_token"]


def test_login_wrong_password(client):
    register(client)
    res = login(client, password="wrongpassword")
    assert res.status_code == 401


def test_me_with_valid_token(client):
    register(client)
    token = login(client).json()["access_token"]
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == EMAIL


def test_me_without_token(client):
    res = client.get("/auth/me")
    assert res.status_code == 401