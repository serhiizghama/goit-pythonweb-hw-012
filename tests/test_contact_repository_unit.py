import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def contact_repository(mock_session):
    return ContactRepository(mock_session)


@pytest.fixture
def user():
    return User(id=1, username="testuser")


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session, user):
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="1234567890",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.create_contact(
        contact_data=contact_data, user=user
    )

    assert isinstance(result, Contact)
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.email == "john.doe@example.com"
    assert result.phone_number == "1234567890"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        user=user,
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    contact = await contact_repository.get_contact_by_id(contact_id=1, user=user)

    assert contact is not None
    assert contact.id == 1
    assert contact.first_name == "John"
    assert contact.last_name == "Doe"
    assert contact.email == "john.doe@example.com"


@pytest.mark.asyncio
async def test_update_contact(contact_repository, mock_session, user):
    contact_data = ContactCreate(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        phone_number="0987654321",  # Added required field
    )
    existing_contact = Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="1234567890",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.update_contact(
        contact_id=1, contact_data=contact_data, user=user
    )

    assert result is not None
    assert result.first_name == "Jane"
    assert result.last_name == "Smith"
    assert result.email == "jane.smith@example.com"
    assert result.phone_number == "0987654321"  # Assert the updated field
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_contact)


@pytest.mark.asyncio
async def test_delete_contact(contact_repository, mock_session, user):
    existing_contact = Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        user=user,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.delete_contact(contact_id=1, user=user)

    assert result is not None
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.email == "john.doe@example.com"
    mock_session.delete.assert_awaited_once_with(existing_contact)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_contacts(contact_repository, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            user=user,
        ),
    ]  # Adjusted to include only one matching contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    contacts = await contact_repository.search_contacts(query="John", user=user)

    # Assertions
    assert len(contacts) == 1
    assert contacts[0].first_name == "John"
    assert contacts[0].email == "john.doe@example.com"


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(contact_repository, mock_session, user):
    # Setup mock for fetching contacts
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [
        Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            user=user,
            birthday="2025-04-15",
        ),
        Contact(
            id=2,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            user=user,
            birthday="2025-04-16",
        ),
    ]
    mock_result.scalars.return_value = mock_scalars

    # Setup mock for counting total contacts
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2

    # Configure mock_session.execute to return the correct results
    async def execute_side_effect(stmt):
        if "count" in str(stmt):
            return mock_count_result
        return mock_result

    mock_session.execute.side_effect = execute_side_effect

    # Call method
    result = await contact_repository.get_upcoming_birthdays(
        days=7, skip=0, limit=10, user=user
    )

    # Assertions
    assert len(result["contacts"]) == 2
    assert result["contacts"][0].first_name == "John"
    assert result["contacts"][1].first_name == "Jane"
    assert result["total_count"] == 2


@pytest.mark.asyncio
async def test_create_contact_duplicate_email(contact_repository, mock_session, user):
    # Setup mock
    existing_contact = Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        user=user,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="1234567890",
    )

    # Call method and assert exception
    with pytest.raises(
        ValueError, match="Contact with email john.doe@example.com already exists."
    ):
        await contact_repository.create_contact(contact_data=contact_data, user=user)


@pytest.mark.asyncio
async def test_update_contact_not_found(contact_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    contact_data = ContactUpdate(
        first_name="Ghost",
        last_name="User",
        email="ghost@example.com",
        phone_number="0000000000",
    )

    result = await contact_repository.update_contact(99, contact_data, user)

    assert result is None


@pytest.mark.asyncio
async def test_delete_contact_not_found(contact_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.delete_contact(99, user)

    assert result is None


@pytest.mark.asyncio
async def test_search_contacts_no_match(contact_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    contacts = await contact_repository.search_contacts(query="NotExist", user=user)

    assert contacts == []
