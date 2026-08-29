import asyncio


async def test_create_link_success(client, auth_headers):
    response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["short_code"]


async def test_create_link_requires_auth(client):
    response = await client.post(
        "/api/v1/links", json={"original_url": "https://example.com"}
    )

    assert response.status_code == 401


async def test_get_owned_link(client, auth_headers):
    create_response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com"},
        headers=auth_headers,
    )
    link_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/links/{link_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == link_id


async def test_get_link_not_owned_returns_404(client, auth_headers):
    create_response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com"},
        headers=auth_headers,
    )
    link_id = create_response.json()["id"]

    await client.post(
        "/api/v1/auth/register",
        json={"email": "otherowner@example.com", "password": "Passw0rd!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "otherowner@example.com", "password": "Passw0rd!"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get(f"/api/v1/links/{link_id}", headers=other_headers)

    assert response.status_code == 404


async def test_delete_link(client, auth_headers):
    create_response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com"},
        headers=auth_headers,
    )
    link_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/links/{link_id}", headers=auth_headers)
    get_response = await client.get(f"/api/v1/links/{link_id}", headers=auth_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


async def test_custom_alias_race_condition_only_one_succeeds(client, auth_headers):
    async def try_create():
        return await client.post(
            "/api/v1/links",
            json={"original_url": "https://example.com", "custom_alias": "racealias"},
            headers=auth_headers,
        )

    responses = await asyncio.gather(*[try_create() for _ in range(5)])
    status_codes = [r.status_code for r in responses]

    assert status_codes.count(201) == 1
    assert status_codes.count(409) == 4
