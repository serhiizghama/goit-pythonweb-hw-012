from typing import Optional, Sequence

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
        """
        Initialize the ContactRepository with a database session.

        Args:
            db (AsyncSession): Asynchronous database session for executing queries.
        """
        self.db = db

    async def _execute_and_fetch(self, stmt):
        """
        Execute a SQLAlchemy statement and fetch all results.

        Args:
            stmt: SQLAlchemy statement to execute.

        Returns:
            List: A list of results from the query.
        """
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _execute_and_count(self, stmt):
        """
        Execute a SQLAlchemy statement and return the count result.

        Args:
            stmt: SQLAlchemy statement to execute.

        Returns:
            int: The count result from the query.
        """
        result = await self.db.execute(stmt)
        return result.scalar()

    async def create_contact(self, contact_data: ContactCreate, user: User) -> Contact:
        """
        Create a new contact for the given user.

        Args:
            contact_data (ContactCreate): Data for the new contact.
            user (User): The user to associate the contact with.

        Returns:
            Contact: The created contact.

        Raises:
            ValueError: If a contact with the same email already exists.
        """
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
        """
        Retrieve a paginated and optionally filtered list of contacts for a user.

        Args:
            skip (int): Number of records to skip. Defaults to 0.
            limit (int): Maximum number of records to return. Defaults to 100.
            first_name (Optional[str]): Filter by first name. Defaults to None.
            last_name (Optional[str]): Filter by last name. Defaults to None.
            email (Optional[str]): Filter by email. Defaults to None.
            user (User): The user whose contacts are being retrieved.

        Returns:
            dict: A dictionary containing total count, skip, limit, and the list of contacts.
        """
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
        """
        Retrieve a contact by its ID for a specific user.

        Args:
            contact_id (int): ID of the contact to retrieve.
            user (User): The user who owns the contact.

        Returns:
            Optional[Contact]: The contact if found, otherwise None.
        """
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_contact(
        self, contact_id: int, contact_data: ContactUpdate, user: User
    ) -> Optional[Contact]:
        """
        Update an existing contact for a user.

        Args:
            contact_id (int): ID of the contact to update.
            contact_data (ContactUpdate): Data to update the contact with.
            user (User): The user who owns the contact.

        Returns:
            Optional[Contact]: The updated contact if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact is None:
            return None

        for key, value in contact_data.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)

        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Delete a contact by its ID for a specific user.

        Args:
            contact_id (int): ID of the contact to delete.
            user (User): The user who owns the contact.

        Returns:
            Optional[Contact]: The deleted contact if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact is None:
            return None

        await self.db.delete(contact)
        await self.db.commit()
        return contact

    async def search_contacts(self, query: str, user: User) -> Sequence[Contact]:
        """
        Search for contacts by a query string for a specific user.

        Args:
            query (str): The search query string (matches first name, last name, or email).
            user (User): The user whose contacts are being searched.

        Returns:
            Sequence[Contact]: A list of contacts matching the query.
        """
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
        """
        Retrieve contacts with upcoming birthdays within a specified number of days.

        Args:
            days (int): Number of days to look ahead for birthdays.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.
            user (User): The user whose contacts are being retrieved.

        Returns:
            dict: A dictionary containing total count, skip, limit, and the list of contacts with upcoming birthdays.
        """
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
