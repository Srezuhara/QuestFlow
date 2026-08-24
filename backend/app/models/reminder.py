"""`Reminder`, `PushSubscription`, and `Notification` — mirrors `note.py`'s
convention of three related classes in one module.

`Reminder.rrule` is stored but always `NULL`, written-rejected by the API
(422) — the same forward-compat-only pattern as `Habit.rrule` /
`HabitCadence.CUSTOM` from phase 3. Correct RRULE expansion needs
`dateutil`, DST-aware local expansion, and a materialisation strategy; none
of that is built here.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, desc, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP, UUID
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7

from app.db.base import Base
from app.models.enums import NotificationType, ReminderChannel, ReminderStatus

# The same `postgresql.ENUM` object (name-bound) is reused between the
# `ARRAY(ENUM)` column here and the migration's explicit `.create()` call —
# see D7-2 in PHASE_7_8_9_PLAN.md for why autogenerate can't create this type
# itself when it's nested inside an ARRAY.
_reminder_channel_pg_enum = PGEnum(
    ReminderChannel,
    name="reminder_channel",
    values_callable=lambda e: [m.value for m in e],
    create_type=False,
)


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (
        Index("ix_reminders_due", "remind_at", postgresql_where=text("status = 'scheduled'")),
        Index("ix_reminders_user_remind_at", "user_id", "remind_at"),
        CheckConstraint(
            "NOT (task_id IS NOT NULL AND habit_id IS NOT NULL)",
            name="ck_reminders_single_target",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), index=True, nullable=True
    )
    habit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("habits.id", ondelete="SET NULL"), index=True, nullable=True
    )
    message: Mapped[str] = mapped_column(String(200), nullable=False)
    remind_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    # Written-rejected (422) by the API — see the module docstring.
    rrule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channels: Mapped[list[ReminderChannel]] = mapped_column(
        ARRAY(_reminder_channel_pg_enum),
        nullable=False,
        server_default=text("'{push,in_app}'::reminder_channel[]"),
    )
    status: Mapped[ReminderStatus] = mapped_column(
        PGEnum(
            ReminderStatus, name="reminder_status", values_callable=lambda e: [m.value for m in e]
        ),
        nullable=False,
        server_default=ReminderStatus.SCHEDULED.value,
    )
    sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Globally unique per browser per VAPID key — re-subscribing must upsert
    # via `ON CONFLICT (endpoint)`, never insert a duplicate row.
    endpoint: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id_desc", "user_id", desc("id")),
        Index(
            "ix_notifications_unread",
            "user_id",
            postgresql_where=text("read_at IS NULL"),
        ),
    )

    # uuid7 PK — chronologically sortable, unique, and IS the keyset cursor
    # (no separate `created_at` tiebreaker needed).
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        PGEnum(
            NotificationType,
            name="notification_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    read_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

