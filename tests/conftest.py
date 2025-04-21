import pytest_asyncio
import redis.asyncio as redis
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.database.models import Base
from src.conf.config import config as app_config
from src.database.db import get_db
from src.services import auth
from main import app

DATABASE_TEST_URL = app_config.DATABASE_URL

engine_test = create_async_engine(DATABASE_TEST_URL, poolclass=NullPool)
AsyncSessionTest = async_sessionmaker(engine_test, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_test_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session():
    async with AsyncSessionTest() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture()
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
def mock_redis(request):
    if "integration" in request.keywords:
        return
    auth.redis_client.get = AsyncMock(return_value=None)
    auth.redis_client.set = AsyncMock(return_value=True)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_redis(request):
    if "integration" not in request.keywords:
        yield
        return

    client = redis.Redis.from_url(app_config.REDIS_URL)
    await client.flushdb()
    yield
    await client.flushdb()


@pytest_asyncio.fixture
async def auth_token(client):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123",
    }

    await client.post("/auth/register", json=user_data)
    await client.get(f"/auth/confirm_email/{user_data['email']}")  # Optional if mock

    response = await client.post(
        "/auth/login",
        data={"username": user_data["username"], "password": user_data["password"]},
    )

    assert response.status_code == 200, response.text
    return response.json()["access_token"]
