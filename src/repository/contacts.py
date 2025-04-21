from typing import Optional, Sequence

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, extract, or_
from datetime import date, timedelta

from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate


def _birthday_filter_conditions(today, future_date):
    if today.month == future_date.month:
        return and_(
            extract("month", Contact.birthday) == today.month,
            extract("day", Contact.birthday) >= today.day,
            extract("day", Contact.birthday) <= future_date.day,
        )
    else:
        return or_(
            and_(
                extract("month", Contact.birthday) == today.month,
                extract("day", Contact.birthday) >= today.day,
            ),
            and_(
                extract("month", Contact.birthday) == future_date.month,
                extract("day", Contact.birthday) <= future_date.day,
            ),
            and_(
                extract("month", Contact.birthday) > today.month,
                extract("month", Contact.birthday) < future_date.month,
            ),
        )


class ContactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _execute_and_fetch(self, stmt):
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _execute_and_count(self, stmt):
        result = await self.db.execute(stmt)
        return result.scalar()

    async def create_contact(self, contact_data: ContactCreate, user: User) -> Contact:
        existing_contact_stmt = select(Contact).filter_by(email=contact_data.email)
        existing_contact_result = await self.db.execute(existing_contact_stmt)
        existing_contact = existing_contact_result.scalar_one_or_none()

        if existing_contact:
            raise ValueError(f"Contact with email {contact_data.email} already exists.")

        contact = Contact(**contact_data.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def get_contacts(
        self,
        skip: int = 0,
        limit: int = 100,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        user: User = None,
    ):
        stmt = select(Contact).filter_by(user=user)

        filters = []
        if first_name:
            filters.append(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            filters.append(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            filters.append(Contact.email.ilike(f"%{email}%"))

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.offset(skip).limit(limit)

        total_count_stmt = (
            select(func.count()).select_from(Contact).filter_by(user=user)
        )
        if filters:
            total_count_stmt = total_count_stmt.where(and_(*filters))

        total_count = await self._execute_and_count(total_count_stmt)
        contacts = await self._execute_and_fetch(stmt)

        return {
            "total_count": total_count,
            "skip": skip,
            "limit": limit,
            "contacts": contacts,
        }

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_contact(
        self, contact_id: int, contact_data: ContactUpdate, user: User
    ) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact is None:
            return None

        for key, value in contact_data.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)

        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact is None:
            return None

        await self.db.delete(contact)
        await self.db.commit()
        return contact

    async def search_contacts(self, query: str, user: User) -> Sequence[Contact]:
        stmt = select(Contact).filter(
            and_(
                Contact.user == user,
                or_(
                    Contact.first_name.ilike(f"%{query}%"),
                    Contact.last_name.ilike(f"%{query}%"),
                    Contact.email.ilike(f"%{query}%"),
                ),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_upcoming_birthdays(
        self, days: int, skip: int, limit: int, user: User
    ):
        today = date.today()
        future_date = today + timedelta(days=days)
        conditions = _birthday_filter_conditions(today, future_date)

        stmt = (
            select(Contact)
            .filter(Contact.user_id == user.id, conditions)
            .offset(skip)
            .limit(limit)
        )

        total_count_stmt = (
            select(func.count())
            .select_from(Contact)
            .filter(Contact.user_id == user.id, conditions)
        )

        total_count = await self._execute_and_count(total_count_stmt)
        contacts = await self._execute_and_fetch(stmt)

        return {
            "total_count": total_count,
            "skip": skip,
            "limit": limit,
            "contacts": contacts,
        }
