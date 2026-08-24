"""`FocusSession` — server-authoritative Pomodoro/focus sessions. XP is
always computed from `started_at`/`ended_at` at completion time, never from
a client-supplied duration (plan D10).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7

from app.db.base import Base
from app.models.enums import FocusMode, FocusStatus


class FocusSession(Base):
    __tablename__ = "focus_sessions"
    __table_args__ = (Index("ix_focus_sessions_user_started", "user_id", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), index=True, nullable=True
    )
    mode: Mapped[FocusMode] = mapped_column(
        SAEnum(FocusMode, name="focus_mode", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    planned_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    status: Mapped[FocusStatus] = mapped_column(
        SAEnum(FocusStatus, name="focus_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        server_default=FocusStatus.RUNNING.value,
    )
    xp_awarded: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
