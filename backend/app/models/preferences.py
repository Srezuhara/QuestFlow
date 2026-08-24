"""`UserPreferences` — 1:1 with `users`, mirrors the `user_progress` pattern
(one row per user, created on first read with defaults if absent)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    focus_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="25")
    short_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    long_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="15")
    sessions_before_long_break: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="4"
    )
    sound_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    # D8-2/D8-3 — the leaderboard visibility flag. Opt-out by default: an
    # opt-in leaderboard is empty on day one and therefore dead. What this
    # exposes is deliberately narrow — see `social_service` and the
    # PUBLIC PROFILE copy on the Settings page.
    leaderboard_opt_in: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
