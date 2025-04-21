import pytest
from unittest.mock import AsyncMock
from sqlalchemy import select

from src.database.models import User
from tests.test_helpers import TEST_USER, HEADERS_TEMPLATE


@pytest.mark.asyncio
async def test_signup(client, monkeypatch):
    mock_send_email = AsyncMock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    response = await client.post("/auth/register", json=TEST_USER)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == TEST_USER["username"]
    assert data["email"] == TEST_USER["email"]
    assert "hashed_password" not in data
    assert "avatar" in data


@pytest.mark.asyncio
async def test_repeat_signup(client, db_session, monkeypatch):
    mock_send_email = AsyncMock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    # Register the user
    await client.post("/auth/register", json=TEST_USER)

    # Attempt to register the same user again
    response = await client.post("/auth/register", json=TEST_USER)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "User with this email already exist"


@pytest.mark.asyncio
async def test_not_confirmed_login(client, db_session):
    # Register the user
    await client.post("/auth/register", json=TEST_USER)

    # Attempt to log in without confirming email
    response = await client.post(
        "/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Please confirm your email"


@pytest.mark.asyncio
async def test_login(client, db_session):
    # Register the user
    await client.post("/auth/register", json=TEST_USER)

    user = await db_session.execute(
        select(User).where(User.email == TEST_USER["email"])
    )
    user = user.scalar_one_or_none()
    user.confirmed = True
    await db_session.commit()

    # Log in with valid credentials
    response = await client.post(
        "/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


@pytest.mark.asyncio
async def test_wrong_password_login(client, db_session):
    # Register the user
    await client.post("/auth/register", json=TEST_USER)

    user = await db_session.execute(
        select(User).where(User.email == TEST_USER["email"])
    )
    user = user.scalar_one_or_none()
    user.confirmed = True
    await db_session.commit()

    # Attempt to log in with the wrong password
    response = await client.post(
        "/auth/login",
        data={"username": TEST_USER["username"], "password": "wrongpassword"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Incorrect login or password"


@pytest.mark.asyncio
async def test_wrong_username_login(client, db_session):
    # Register the user
    await client.post("/auth/register", json=TEST_USER)

    user = await db_session.execute(
        select(User).where(User.email == TEST_USER["email"])
    )
    user = user.scalar_one_or_none()
    user.confirmed = True
    await db_session.commit()

    # Attempt to log in with the wrong username
    response = await client.post(
        "/auth/login",
        data={"username": "wrongusername", "password": TEST_USER["password"]},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Incorrect login or password"


@pytest.mark.asyncio
async def test_validation_error_login(client):
    # Attempt to log in without providing a username
    response = await client.post(
        "/auth/login", data={"password": TEST_USER["password"]}
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data
