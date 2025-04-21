import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.services.contacts import ContactService
from src.schemas import ContactCreate, ContactUpdate

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def contact_service(mock_session):
    return ContactService(mock_session)


@pytest.fixture
def user():
    return User(id=1, username="testuser")


@pytest.mark.asyncio
async def test_create_contact(contact_service, mock_session, user):
    # Setup
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="1234567890",
    )
    mock_repo = MagicMock()
    mock_repo.create_contact = AsyncMock(
        return_value=Contact(**contact_data.model_dump(), user=user)
    )
    contact_service.repo = mock_repo

    # Call method
    result = await contact_service.create_contact(contact_data, user)

    # Assertions
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.email == "john.doe@example.com"
    assert result.phone_number == "1234567890"
    mock_repo.create_contact.assert_awaited_once_with(contact_data, user)


@pytest.mark.asyncio
async def test_get_contacts(contact_service, mock_session, user):
    # Setup
    mock_repo = MagicMock()
    mock_repo.get_contacts = AsyncMock(
        return_value={
            "total_count": 1,
            "contacts": [
                Contact(
                    id=1,
                    first_name="John",
                    last_name="Doe",
                    email="john.doe@example.com",
                    user=user,
                )
            ],
        }
    )
    contact_service.repo = mock_repo

    # Call method
    result = await contact_service.get_contacts(0, 10, None, None, None, user)

    # Assertions
    assert result["total_count"] == 1
    assert len(result["contacts"]) == 1
    assert result["contacts"][0].first_name == "John"
    mock_repo.get_contacts.assert_awaited_once_with(0, 10, None, None, None, user)


@pytest.mark.asyncio
async def test_update_contact(contact_service, mock_session, user):
    # Setup
    contact_data = ContactUpdate(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        phone_number="0987654321",  # Added required field
    )
    mock_repo = MagicMock()
    mock_repo.update_contact = AsyncMock(
        return_value=Contact(
            id=1,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone_number="0987654321",
            user=user,
        )
    )
    contact_service.repo = mock_repo

    # Call method
    result = await contact_service.update_contact(1, contact_data, user)

    # Assertions
    assert result.first_name == "Jane"
    assert result.last_name == "Smith"
    assert result.email == "jane.smith@example.com"
    assert result.phone_number == "0987654321"  # Assert the updated field
    mock_repo.update_contact.assert_awaited_once_with(1, contact_data, user)


@pytest.mark.asyncio
async def test_delete_contact(contact_service, mock_session, user):
    # Setup
    mock_repo = MagicMock()
    mock_repo.delete_contact = AsyncMock(
        return_value=Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            user=user,
        )
    )
    contact_service.repo = mock_repo

    # Call method
    result = await contact_service.delete_contact(1, user)

    # Assertions
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.email == "john.doe@example.com"
    mock_repo.delete_contact.assert_awaited_once_with(1, user)


@pytest.mark.asyncio
async def test_search_contacts(contact_service, mock_session, user):
    # Setup
    mock_repo = MagicMock()
    mock_repo.search_contacts = AsyncMock(
        return_value=[
            Contact(
                id=1,
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                user=user,
            )
        ]
    )
    contact_service.repo = mock_repo

    # Call method
    result = await contact_service.search_contacts("John", user)

    # Assertions
    assert len(result) == 1
    assert result[0].first_name == "John"
    mock_repo.search_contacts.assert_awaited_once_with("John", user)


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(contact_service, mock_session, user):
    # Setup
    mock_repo = MagicMock()
    mock_repo.get_upcoming_birthdays = AsyncMock(
        return_value={
            "total_count": 1,
            "contacts": [
                Contact(
                    id=1,
                    first_name="John",
                    last_name="Doe",
                    email="john.doe@example.com",
                    user=user,
                    birthday="2025-04-15",
                )
            ],
        }
    )
    contact_service.repo = mock_repo

    # Call method
    result = await contact_service.get_upcoming_birthdays(7, 0, 10, user)

    # Assertions
    assert result["total_count"] == 1
    assert len(result["contacts"]) == 1
    assert result["contacts"][0].first_name == "John"
    mock_repo.get_upcoming_birthdays.assert_awaited_once_with(7, 0, 10, user)


@pytest.mark.asyncio
async def test_create_contact_integrity_error(contact_service, mock_session, user):
    # Setup mocked repository
    mock_repo = MagicMock()
    mock_repo.create_contact.side_effect = IntegrityError("mock", "mock", "mock")
    mock_repo.db = AsyncMock()

    contact_service.repo = mock_repo

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await contact_service.create_contact(
            ContactCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                phone_number="123",
            ),
            user,
        )

    assert exc.value.status_code in {400, 409}


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_service, user):
    contact = Contact(
        id=1, first_name="John", last_name="Doe", email="john@example.com", user=user
    )
    mock_repo = MagicMock()
    mock_repo.get_contact_by_id = AsyncMock(return_value=contact)
    contact_service.repo = mock_repo

    result = await contact_service.get_contact_by_id(1, user)
    assert result.id == 1
    assert result.email == "john@example.com"
