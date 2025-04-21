from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


from src.database.models import User
from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate


def _handle_integrity_error(e: IntegrityError):
    if "unique constraint" in str(e.orig).lower() and "email" in str(e.orig).lower():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with this email already exists.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An integrity error occurred while processing your request.",
        )


class ContactService:
    def __init__(self, db: AsyncSession):
        """
        Initialize the ContactService with a database session.

        Args:
            db (AsyncSession): Asynchronous database session for executing queries.
        """
        self.repo = ContactRepository(db)

    async def create_contact(self, contact_data: ContactCreate, user: User):
        """
        Create a new contact for the authenticated user.

        Args:
            contact_data (ContactCreate): Data required to create a new contact.
            user (User): The user creating the contact.

        Returns:
            Contact: The newly created contact.

        Raises:
            HTTPException: If an integrity error occurs (e.g., duplicate email).
        """
        try:
            return await self.repo.create_contact(contact_data, user)
        except IntegrityError as e:
            await self.repo.db.rollback()
            _handle_integrity_error(e)

    async def get_contacts(
        self,
        skip: int,
        limit: int,
        first_name: Optional[str],
        last_name: Optional[str],
        email: Optional[str],
        user: User,
    ):
        """
        Retrieve a paginated and optionally filtered list of contacts for the user.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.
            first_name (Optional[str]): Filter by first name (partial match).
            last_name (Optional[str]): Filter by last name (partial match).
            email (Optional[str]): Filter by email (partial match).
            user (User): The user retrieving the contacts.

        Returns:
            dict: A dictionary containing total count, skip, limit, and the list of contacts.
        """
        return await self.repo.get_contacts(
            skip, limit, first_name, last_name, email, user
        )

    async def get_contact_by_id(self, contact_id: int, user: User):
        """
        Retrieve a specific contact by its ID for the authenticated user.

        Args:
            contact_id (int): ID of the contact to retrieve.
            user (User): The user retrieving the contact.

        Returns:
            Contact: The contact if found.

        Raises:
            HTTPException: If the contact is not found.
        """
        return await self.repo.get_contact_by_id(contact_id, user)

    async def get_upcoming_birthdays(
        self, days: int, skip: int, limit: int, user: User
    ):
        """
        Retrieve contacts with upcoming birthdays within a specified number of days.

        Args:
            days (int): Number of days to look ahead for birthdays.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.
            user (User): The user retrieving the contacts.

        Returns:
            dict: A dictionary containing total count, skip, limit, and the list of contacts with upcoming birthdays.
        """
        return await self.repo.get_upcoming_birthdays(days, skip, limit, user)

    async def update_contact(
        self, contact_id: int, contact_data: ContactUpdate, user: User
    ):
        """
        Update an existing contact for the authenticated user.

        Args:
            contact_id (int): ID of the contact to update.
            contact_data (ContactUpdate): Data to update the contact with.
            user (User): The user updating the contact.

        Returns:
            Contact: The updated contact.

        Raises:
            HTTPException: If the contact is not found or an integrity error occurs.
        """
        try:
            contact = await self.repo.update_contact(contact_id, contact_data, user)
            if contact is None:
                raise HTTPException(status_code=404, detail="Contact not found")
            return contact
        except IntegrityError as e:
            await self.repo.db.rollback()
            _handle_integrity_error(e)

    async def delete_contact(self, contact_id: int, user: User):
        """
        Delete a contact by its ID for the authenticated user.

        Args:
            contact_id (int): ID of the contact to delete.
            user (User): The user deleting the contact.

        Returns:
            Contact: The deleted contact.

        Raises:
            HTTPException: If the contact is not found or an integrity error occurs.
        """
        try:
            contact = await self.repo.delete_contact(contact_id, user)
            if contact is None:
                raise HTTPException(status_code=404, detail="Contact not found")
            return contact
        except IntegrityError as e:
            await self.repo.db.rollback()
            _handle_integrity_error(e)

    async def search_contacts(self, query: str, user: User):
        """
        Search for contacts by a query string for the authenticated user.

        Args:
            query (str): The search query string (matches first name, last name, or email).
            user (User): The user performing the search.

        Returns:
            list: A list of contacts matching the query.
        """
        return await self.repo.search_contacts(query, user)
