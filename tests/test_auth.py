async def test_register_returns_user_and_token(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "Passw0rd!"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "test@example.com"
    assert "access_token" in body["token"]


async def test_register_duplicate_email_returns_409(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "Passw0rd!"},
    )

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "Passw0rd!"},
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "user_already_exists"


async def test_login_success_returns_token(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "logintest@example.com", "password": "Passw0rd!"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "logintest@example.com", "password": "Passw0rd!"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password_returns_401(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpass@example.com", "password": "Passw0rd!"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrongpass@example.com", "password": "WrongPassword1!"},
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_credentials"
