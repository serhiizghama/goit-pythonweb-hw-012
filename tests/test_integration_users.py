import pytest

from src.services.users import UserService
from tests.test_helpers import TEST_USER, HEADERS_TEMPLATE


@pytest.mark.asyncio
async def test_get_current_user(client):
    login = await client.post(
        "/auth/login",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"],
        },
    )
    token = login.json()["access_token"]

    response = await client.get("/users/me", headers=HEADERS_TEMPLATE(token))
    assert response.status_code == 200
    assert response.json()["username"] == TEST_USER["username"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_me_with_real_redis(client, auth_token):
    response = await client.get("/users/me", headers=HEADERS_TEMPLATE(auth_token))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client):
    response = await client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
