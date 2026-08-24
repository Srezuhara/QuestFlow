"""Reminder domain service — CRUD, target-label resolution, and the worker's
whole entry point (`claim_due_reminders`). Mirrors `habit_service.py`'s
shape: module-level async functions, domain exceptions at the top, ownership
miss -> `ReminderNotFound` -> router 404.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import NotificationType, ReminderStatus
from app.models.habit import Habit
from app.models.reminder import Notification, Reminder
from app.models.task import Task
from app.models.user import User
from app.schemas.reminders import ReminderCreate, ReminderUpdate


class ReminderNotFound(Exception):
    pass


class TargetNotFound(Exception):
    """Raised when `task_id`/`habit_id` doesn't exist or belongs to another
    user — the router translates this to 404, same as every other
    cross-user ownership miss in this codebase."""


async def _assert_target_owned(
    db: AsyncSession, user: User, *, task_id: uuid.UUID | None, habit_id: uuid.UUID | None
) -> None:
    if task_id is not None:
        task = await db.get(Task, task_id)
        if task is None or task.user_id != user.id:
            raise TargetNotFound
    if habit_id is not None:
        habit = await db.get(Habit, habit_id)
        if habit is None or habit.user_id != user.id:
            raise TargetNotFound


@dataclass(frozen=True)
class ReminderView:
    reminder: Reminder
    target_label: str | None


async def _get_owned_reminder(db: AsyncSession, user: User, reminder_id: uuid.UUID) -> Reminder:
    reminder = await db.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user.id:
        raise ReminderNotFound
    return reminder


async def _resolve_target_labels(
    db: AsyncSession, reminders: list[Reminder]
) -> dict[uuid.UUID, str | None]:
    """Batches task and habit lookups into two `WHERE id IN (...)` queries
    (never N+1), returning `None` for rows that vanished (task/habit deleted
    since the reminder was created — `task_id`/`habit_id` are `SET NULL` on
    delete, but a reminder created just before a delete could still be
    in-flight)."""
    task_ids = [r.task_id for r in reminders if r.task_id is not None]
    habit_ids = [r.habit_id for r in reminders if r.habit_id is not None]

    task_titles: dict[uuid.UUID, str] = {}
    if task_ids:
        rows = (await db.execute(select(Task.id, Task.title).where(Task.id.in_(task_ids)))).all()
        task_titles = {row[0]: row[1] for row in rows}

    habit_names: dict[uuid.UUID, str] = {}
    if habit_ids:
        rows = (
            await db.execute(select(Habit.id, Habit.name).where(Habit.id.in_(habit_ids)))
        ).all()
        habit_names = {row[0]: row[1] for row in rows}

    labels: dict[uuid.UUID, str | None] = {}
    for r in reminders:
        if r.task_id is not None:
            labels[r.id] = task_titles.get(r.task_id)
        elif r.habit_id is not None:
            labels[r.id] = habit_names.get(r.habit_id)
        else:
            labels[r.id] = None
    return labels


async def list_reminders(
    db: AsyncSession,
    user: User,
    *,
    status: ReminderStatus | None = None,
    limit: int = 50,
    before: datetime | None = None,
) -> tuple[list[ReminderView], datetime | None]:
    stmt = select(Reminder).where(Reminder.user_id == user.id)
    if status is not None:
        stmt = stmt.where(Reminder.status == status)
    if before is not None:
        stmt = stmt.where(Reminder.created_at < before)
    stmt = stmt.order_by(Reminder.created_at.desc()).limit(limit + 1)

    rows = list(await db.scalars(stmt))
    has_more = len(rows) > limit
    items = rows[:limit]
    next_before = items[-1].created_at if has_more and items else None

    labels = await _resolve_target_labels(db, items)
    views = [ReminderView(reminder=r, target_label=labels[r.id]) for r in items]
    return views, next_before


async def get_reminder(db: AsyncSession, user: User, reminder_id: uuid.UUID) -> ReminderView:
    reminder = await _get_owned_reminder(db, user, reminder_id)
    labels = await _resolve_target_labels(db, [reminder])
    return ReminderView(reminder=reminder, target_label=labels[reminder.id])


async def create_reminder(db: AsyncSession, user: User, data: ReminderCreate) -> ReminderView:
    await _assert_target_owned(db, user, task_id=data.task_id, habit_id=data.habit_id)
    reminder = Reminder(
        user_id=user.id,
        task_id=data.task_id,
        habit_id=data.habit_id,
        message=data.message,
        remind_at=data.remind_at,
        rrule=None,
        channels=data.channels,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    labels = await _resolve_target_labels(db, [reminder])
    return ReminderView(reminder=reminder, target_label=labels[reminder.id])


async def update_reminder(
    db: AsyncSession, user: User, reminder_id: uuid.UUID, data: ReminderUpdate
) -> ReminderView:
    reminder = await _get_owned_reminder(db, user, reminder_id)
    updates = data.model_dump(exclude_unset=True, exclude={"rrule"})
    if "task_id" in updates or "habit_id" in updates:
        await _assert_target_owned(
            db,
            user,
            task_id=updates.get("task_id", reminder.task_id),
            habit_id=updates.get("habit_id", reminder.habit_id),
        )
    for field_name, value in updates.items():
        setattr(reminder, field_name, value)
    await db.commit()
    await db.refresh(reminder)
    labels = await _resolve_target_labels(db, [reminder])
    return ReminderView(reminder=reminder, target_label=labels[reminder.id])


async def dismiss_reminder(db: AsyncSession, user: User, reminder_id: uuid.UUID) -> ReminderView:
    reminder = await _get_owned_reminder(db, user, reminder_id)
    reminder.status = ReminderStatus.DISMISSED
    await db.commit()
    await db.refresh(reminder)
    labels = await _resolve_target_labels(db, [reminder])
    return ReminderView(reminder=reminder, target_label=labels[reminder.id])


async def cancel_reminder(db: AsyncSession, user: User, reminder_id: uuid.UUID) -> None:
    """Sets `status = cancelled` rather than deleting — preserves the
    delivery log, mirroring `HabitService.archive_habit`'s soft-delete
    shape."""
    reminder = await _get_owned_reminder(db, user, reminder_id)
    reminder.status = ReminderStatus.CANCELLED
    await db.commit()


def is_stale(reminder: Reminder, now: datetime) -> bool:
    """True once a reminder is past `reminder_misfire_grace_minutes` late.
    Stale reminders still get their in-app `Notification` (nothing is
    silently lost) but skip push (D7-5) — nobody wants a phone buzz for
    something due six hours ago because the worker was down."""
    grace = timedelta(minutes=settings.reminder_misfire_grace_minutes)
    return now - reminder.remind_at > grace


async def claim_due_reminders(
    db: AsyncSession, *, now: datetime, limit: int
) -> list[Reminder]:
    """The worker's whole entry point (D7-5). Claims due+scheduled rows with
    `FOR UPDATE SKIP LOCKED` (double-claiming is impossible across restarts
    or a second worker), marks them sent, and writes one `Notification` per
    claimed row — all inside this one transaction, so in-app delivery is
    exactly-once and durable. Push (lossy by nature) happens by the caller,
    after commit, with no lock held.
    """
    stmt = (
        select(Reminder)
        .where(Reminder.status == ReminderStatus.SCHEDULED, Reminder.remind_at <= now)
        .order_by(Reminder.remind_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    rows = list(await db.scalars(stmt))
    if not rows:
        return []

    labels = await _resolve_target_labels(db, rows)
    for reminder in rows:
        reminder.status = ReminderStatus.SENT
        reminder.sent_at = now
        db.add(
            Notification(
                user_id=reminder.user_id,
                type=NotificationType.REMINDER,
                payload={
                    "reminder_id": str(reminder.id),
                    "message": reminder.message,
                    "remind_at": reminder.remind_at.isoformat(),
                    "target_label": labels.get(reminder.id),
                    "url": "/reminders",
                },
            )
        )
    await db.commit()
    for reminder in rows:
        await db.refresh(reminder)
    return rows
