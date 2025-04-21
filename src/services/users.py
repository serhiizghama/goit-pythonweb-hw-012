from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas import UserCreate


class UserService:
    def __init__(self, db: AsyncSession):
        """
        Initialize UserService with a database session.

        Args:
            db (AsyncSession): Asynchronous database session.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """
        Create a new user with a Gravatar avatar if available.

        Args:
            body (UserCreate): User creation data.

        Returns:
            User: The created user.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception:
            pass
        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        """
        Retrieve a user by ID.

        Args:
            user_id (int): User's ID.

        Returns:
            User | None: The user or None if not found.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        """
        Retrieve a user by username.

        Args:
            username (str): Username.

        Returns:
            User | None: The user or None if not found.
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: EmailStr):
        """
        Retrieve a user by email address.

        Args:
            email (str): Email address.

        Returns:
            User | None: The user or None if not found.
        """
        return await self.repository.get_user_by_email(email)

    async def confirm_email(self, email: EmailStr):
        """
        Confirm the user's email.

        Args:
            email (str): Email to confirm.

        Returns:
            None
        """
        return await self.repository.confirm_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """
        Update user's avatar URL.

        Args:
            email (str): User's email.
            url (str): New avatar URL.

        Returns:
            User: Updated user.
        """
        return await self.repository.update_avatar_url(email, url)

    async def update_password(self, email: str, hashed_password: str):
        return await self.repository.update_password(email, hashed_password)
