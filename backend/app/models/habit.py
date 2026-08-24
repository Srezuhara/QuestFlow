"""`Habit`, `HabitLog`, `HabitStreak` — habit CRUD, per-period logging, and a
denormalised streak cache reproducible by
`services/gamification/streaks.py::recompute_habit_streak`.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7

from app.db.base import Base
from app.models.enums import HabitCadence, SkillBranch


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cadence: Mapped[HabitCadence] = mapped_column(
        SAEnum(HabitCadence, name="habit_cadence", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        server_default=HabitCadence.DAILY.value,
    )
    target_per_period: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    # Always NULL in phase 3 — see plan D2. Column exists for future custom cadences.
    rrule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skill_branch: Mapped[SkillBranch] = mapped_column(
        SAEnum(SkillBranch, name="skill_branch", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        server_default=SkillBranch.FOCUS.value,
    )
    xp_value: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    archived_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class HabitLog(Base):
    __tablename__ = "habit_logs"
    __table_args__ = (UniqueConstraint("habit_id", "logged_for", name="uq_habit_logs_habit_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    habit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    logged_for: Mapped[date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class HabitStreak(Base):
    __tablename__ = "habit_streaks"

    habit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), primary_key=True
    )
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_completed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
