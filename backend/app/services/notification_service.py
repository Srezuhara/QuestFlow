"""Notification domain service — keyset list on `id DESC` (uuid7 is
chronologically sortable, so it's its own cursor), unread count, and
read/read-all. `create(...)` is flush-only, never commit — same contract as
`xp.award()` — so the worker's claim transaction (see
`reminder_service.claim_due_reminders`) stays atomic.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.reminder import Notification
from app.models.user import User


class NotificationNotFound(Exception):
    pass


async def create(
    db: AsyncSession, *, user_id: uuid.UUID, type: NotificationType, payload: dict[str, Any]
) -> Notification:
    notification = Notification(user_id=user_id, type=type, payload=payload)
    db.add(notification)
    await db.flush()
    return notification


async def _unread_count(db: AsyncSession, user: User) -> int:
    return (
        await db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        )
    ) or 0


async def list_notifications(
    db: AsyncSession,
    user: User,
    *,
    unread_only: bool = False,
    limit: int = 50,
    before: uuid.UUID | None = None,
) -> tuple[list[Notification], uuid.UUID | None, int]:
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    if before is not None:
        stmt = stmt.where(Notification.id < before)
    stmt = stmt.order_by(Notification.id.desc()).limit(limit + 1)

    rows = list(await db.scalars(stmt))
    has_more = len(rows) > limit
    items = rows[:limit]
    next_before = items[-1].id if has_more and items else None
    unread_count = await _unread_count(db, user)
    return items, next_before, unread_count


async def mark_read(db: AsyncSession, user: User, notification_id: uuid.UUID) -> Notification:
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise NotificationNotFound
    if notification.read_at is None:
        notification.read_at = func.now()
        await db.commit()
        await db.refresh(notification)
    return notification


async def mark_all_read(db: AsyncSession, user: User) -> int:
    result = cast(
        "CursorResult[Any]",
        await db.execute(
            update(Notification)
            .where(Notification.user_id == user.id, Notification.read_at.is_(None))
            .values(read_at=func.now())
        ),
    )
    await db.commit()
    return result.rowcount or 0
