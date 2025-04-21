from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.db import get_db
from src.database.models import User
from src.schemas import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListResponse,
)
from src.services.auth import get_current_user
from src.services.contacts import ContactService

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post(
    "/",
    response_model=ContactResponse,
    responses={
        400: {"description": "Bad Request"},
        409: {"description": "Conflict: Contact with this email already exists"},
        422: {"description": "Validation Error"},
    },
)
async def create_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ContactService(db)
    try:
        return await service.create_contact(contact, user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=ContactListResponse)
async def get_contacts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, le=500, description="Max number of records to return"),
    first_name: Optional[str] = Query(None, description="Filter by first name"),
    last_name: Optional[str] = Query(None, description="Filter by last name"),
    email: Optional[str] = Query(None, description="Filter by email"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.get_contacts(skip, limit, first_name, last_name, email, user)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ContactService(db)
    contact = await service.get_contact_by_id(contact_id, user)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.get("/birthdays/", response_model=ContactListResponse)
async def get_upcoming_birthdays(
    days: int = Query(
        7, ge=1, le=365, description="Number of days ahead to check for birthdays"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, le=500, description="Max number of records to return"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.get_upcoming_birthdays(days, skip, limit, user)


@router.patch(
    "/{contact_id}",
    response_model=ContactResponse,
    responses={400: {"description": "Bad Request"}, 404: {"description": "Not Found"}},
)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ContactService(db)
    updated_contact = await service.update_contact(contact_id, contact, user)
    if updated_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated_contact


@router.delete(
    "/{contact_id}",
    response_model=ContactResponse,
    responses={400: {"description": "Bad Request"}, 404: {"description": "Not Found"}},
)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ContactService(db)
    deleted_contact = await service.delete_contact(contact_id, user)
    if deleted_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return deleted_contact
