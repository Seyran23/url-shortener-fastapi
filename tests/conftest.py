import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.services.link as link_service_module
from app.core.config import settings
from app.core.redis_client import redis_client
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.analytics import Analytics  # noqa: F401 -- registers on Base.metadata
from app.models.link import Link  # noqa: F401 -- registers on Base.metadata
from app.models.user import User  # noqa: F401 -- registers on Base.metadata

test_engine = create_async_engine(settings.TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db

link_service_module.SessionLocal = TestSessionLocal


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_rate_limits():
    keys = [key async for key in redis_client.scan_iter("rate_limit:*")]
    if keys:
        await redis_client.delete(*keys)

    yield


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "linktestuser@example.com", "password": "Passw0rd!"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "linktestuser@example.com", "password": "Passw0rd!"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
