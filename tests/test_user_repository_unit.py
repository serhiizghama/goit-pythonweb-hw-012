import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.users import UserRepository
from src.schemas import UserCreate
from src.services.users import UserService
from tests.test_helpers import TEST_USER, HEADERS_TEMPLATE


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session):
    # Setup
    user_data = UserCreate(
        username="testuser", email="test@example.com", password="StrongPass123"
    )

    # Call method
    result = await user_repository.create_user(
        body=user_data, avatar="http://example.com/avatar.png"
    )

    # Assertions
    assert isinstance(result, User)
    assert result.username == "testuser"
    assert result.email == "test@example.com"
    assert result.avatar == "http://example.com/avatar.png"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_get_user_by_id(user_repository, mock_session):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User(
        id=1, username="testuser", email="test@example.com"
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    user = await user_repository.get_user_by_id(user_id=1)

    # Assertions
    assert user is not None
    assert user.id == 1
    assert user.username == "testuser"
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User(
        id=1, username="testuser", email="test@example.com"
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    user = await user_repository.get_user_by_email(email="test@example.com")

    # Assertions
    assert user is not None
    assert user.id == 1
    assert user.username == "testuser"
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_confirm_email(user_repository, mock_session):
    # Setup mock
    user = User(id=1, username="testuser", email="test@example.com", confirmed=False)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    await user_repository.confirm_email(email="test@example.com")

    # Assertions
    assert user.confirmed is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repository, mock_session):
    # Setup mock
    user = User(id=1, username="testuser", email="test@example.com", avatar=None)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    updated_user = await user_repository.update_avatar_url(
        email="test@example.com", url="http://example.com/new_avatar.png"
    )

    # Assertions
    assert updated_user.avatar == "http://example.com/new_avatar.png"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(user)
