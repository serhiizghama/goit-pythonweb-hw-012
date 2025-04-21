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
        self.repo = ContactRepository(db)

    async def create_contact(self, contact_data: ContactCreate, user: User):
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
        return await self.repo.get_contacts(
            skip, limit, first_name, last_name, email, user
        )

    async def get_contact_by_id(self, contact_id: int, user: User):
        return await self.repo.get_contact_by_id(contact_id, user)

    async def get_upcoming_birthdays(
        self, days: int, skip: int, limit: int, user: User
    ):
        return await self.repo.get_upcoming_birthdays(days, skip, limit, user)

    async def update_contact(
        self, contact_id: int, contact_data: ContactUpdate, user: User
    ):
        try:
            contact = await self.repo.update_contact(contact_id, contact_data, user)
            if contact is None:
                raise HTTPException(status_code=404, detail="Contact not found")
            return contact
        except IntegrityError as e:
            await self.repo.db.rollback()
            _handle_integrity_error(e)

    async def delete_contact(self, contact_id: int, user: User):
        try:
            contact = await self.repo.delete_contact(contact_id, user)
            if contact is None:
                raise HTTPException(status_code=404, detail="Contact not found")
            return contact
        except IntegrityError as e:
            await self.repo.db.rollback()
            _handle_integrity_error(e)

    async def search_contacts(self, query: str, user: User):
        return await self.repo.search_contacts(query, user)
