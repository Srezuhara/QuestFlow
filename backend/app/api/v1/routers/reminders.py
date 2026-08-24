"""Reminder endpoints: CRUD, dismiss, and cancel (soft-delete)."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.enums import ReminderStatus
from app.models.user import User
from app.schemas.reminders import ReminderCreate, ReminderOut, ReminderPageOut, ReminderUpdate
from app.services import reminder_service

router = APIRouter(prefix="/reminders", tags=["reminders"])


def _to_out(view: reminder_service.ReminderView) -> ReminderOut:
    r = view.reminder
    return ReminderOut(
        id=r.id,
        message=r.message,
        remind_at=r.remind_at,
        task_id=r.task_id,
        habit_id=r.habit_id,
        target_label=view.target_label,
        rrule=r.rrule,
        channels=list(r.channels),
        status=r.status,
        sent_at=r.sent_at,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get("", response_model=ReminderPageOut)
async def list_reminders(
    reminder_status: ReminderStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    before: datetime | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReminderPageOut:
    views, next_before = await reminder_service.list_reminders(
        db, current_user, status=reminder_status, limit=limit, before=before
    )
    return ReminderPageOut(items=[_to_out(v) for v in views], next_before=next_before)


@router.post("", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReminderOut:
    try:
        view = await reminder_service.create_reminder(db, current_user, data)
    except reminder_service.TargetNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task or habit not found"
        ) from exc
    return _to_out(view)


@router.patch("/{reminder_id}", response_model=ReminderOut)
async def update_reminder(
    reminder_id: uuid.UUID,
    data: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReminderOut:
    try:
        view = await reminder_service.update_reminder(db, current_user, reminder_id, data)
    except reminder_service.ReminderNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        ) from exc
    except reminder_service.TargetNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task or habit not found"
        ) from exc
    return _to_out(view)


@router.post("/{reminder_id}/dismiss", response_model=ReminderOut)
async def dismiss_reminder(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReminderOut:
    try:
        view = await reminder_service.dismiss_reminder(db, current_user, reminder_id)
    except reminder_service.ReminderNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        ) from exc
    return _to_out(view)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await reminder_service.cancel_reminder(db, current_user, reminder_id)
    except reminder_service.ReminderNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        ) from exc
