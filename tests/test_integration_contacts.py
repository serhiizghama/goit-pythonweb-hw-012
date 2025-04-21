import pytest
from tests.test_helpers import CONTACT_EXAMPLE, HEADERS_TEMPLATE, TEST_USER
from src.services.users import UserService


@pytest.mark.asyncio
async def test_create_contact(client, db_session):
    await client.post("/auth/register", json=TEST_USER)
    user_service = UserService(db_session)
    await user_service.confirm_email(TEST_USER["email"])
    login = await client.post(
        "/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
    )
    token = login.json()["access_token"]

    response = await client.post(
        "/contacts/", json=CONTACT_EXAMPLE, headers=HEADERS_TEMPLATE(token)
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == CONTACT_EXAMPLE["email"]
    assert "id" in data
    CONTACT_EXAMPLE["id"] = data["id"]  # Save for reuse


@pytest.mark.asyncio
async def test_get_contacts(client, auth_token):
    response = await client.get("/contacts/", headers=HEADERS_TEMPLATE(auth_token))
    assert response.status_code == 200, response.text
    data = response.json()
    assert "contacts" in data
    assert isinstance(data["contacts"], list)
    if data["contacts"]:
        assert "id" in data["contacts"][0]


@pytest.mark.asyncio
async def test_get_contact_not_found(client, auth_token):
    response = await client.get("/contacts/999", headers=HEADERS_TEMPLATE(auth_token))
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


@pytest.mark.asyncio
async def test_update_contact(client, auth_token):
    contact_id = CONTACT_EXAMPLE.get("id", 1)
    updated = CONTACT_EXAMPLE.copy()
    updated["first_name"] = "Updated"
    response = await client.patch(
        f"/contacts/{contact_id}", json=updated, headers=HEADERS_TEMPLATE(auth_token)
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "Updated"
    assert "id" in data


@pytest.mark.asyncio
async def test_update_contact_not_found(client, auth_token):
    response = await client.patch(
        "/contacts/999", json=CONTACT_EXAMPLE, headers=HEADERS_TEMPLATE(auth_token)
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


@pytest.mark.asyncio
async def test_delete_contact(client, auth_token):
    contact_id = CONTACT_EXAMPLE.get("id", 1)
    response = await client.delete(
        f"/contacts/{contact_id}", headers=HEADERS_TEMPLATE(auth_token)
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_repeat_delete_contact(client, auth_token):
    response = await client.delete(
        "/contacts/999", headers=HEADERS_TEMPLATE(auth_token)
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"
