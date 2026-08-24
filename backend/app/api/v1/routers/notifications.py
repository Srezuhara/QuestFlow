"""Notification-centre endpoints: paginated list, mark-read, mark-all-read."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.reminder import Notification
from app.models.user import User
from app.schemas.notifications import MarkAllReadResponse, NotificationOut, NotificationPageOut
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_out(n: Notification) -> NotificationOut:
    return NotificationOut(
        id=n.id, type=n.type, payload=n.payload, read_at=n.read_at, created_at=n.created_at
    )


@router.get("", response_model=NotificationPageOut)
async def list_notifications(
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    before: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationPageOut:
    items, next_before, unread_count = await notification_service.list_notifications(
        db, current_user, unread_only=unread_only, limit=limit, before=before
    )
    return NotificationPageOut(
        items=[_to_out(n) for n in items], next_before=next_before, unread_count=unread_count
    )


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationOut:
    try:
        notification = await notification_service.mark_read(db, current_user, notification_id)
    except notification_service.NotificationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        ) from exc
    return _to_out(notification)


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MarkAllReadResponse:
    count = await notification_service.mark_all_read(db, current_user)
    return MarkAllReadResponse(marked_count=count)
