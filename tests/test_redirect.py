from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.link import Link
from tests.conftest import TestSessionLocal


async def test_redirect_not_found_returns_404(client):
    response = await client.get("/doesnotexist", follow_redirects=False)

    assert response.status_code == 404


async def test_redirect_success_returns_307(client, auth_headers):
    create_response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com"},
        headers=auth_headers,
    )
    short_code = create_response.json()["short_code"]

    response = await client.get(f"/{short_code}", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"


async def test_redirect_disabled_link_returns_410(client, auth_headers):
    create_response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com"},
        headers=auth_headers,
    )
    link_id = create_response.json()["id"]
    short_code = create_response.json()["short_code"]

    await client.post(f"/api/v1/links/{link_id}/deactivate", headers=auth_headers)

    response = await client.get(f"/{short_code}", follow_redirects=False)

    assert response.status_code == 410


async def test_redirect_expired_link_returns_410(client, auth_headers):
    create_response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com"},
        headers=auth_headers,
    )
    short_code = create_response.json()["short_code"]

    # the API rejects a past expires_at at creation time -- expiry has to be
    # backdated directly in the DB to test the redirect's own expiry check
    async with TestSessionLocal() as db:
        result = await db.execute(select(Link).where(Link.short_code == short_code))
        link = result.scalar_one()
        link.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await db.commit()

    response = await client.get(f"/{short_code}", follow_redirects=False)

    assert response.status_code == 410


async def test_redirect_over_click_limit_returns_410(client, auth_headers):
    create_response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com", "max_clicks": 1},
        headers=auth_headers,
    )
    short_code = create_response.json()["short_code"]

    first = await client.get(f"/{short_code}", follow_redirects=False)
    second = await client.get(f"/{short_code}", follow_redirects=False)

    assert first.status_code == 307
    assert second.status_code == 410
