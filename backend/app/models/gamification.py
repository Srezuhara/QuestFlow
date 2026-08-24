"""The gamification ledger: `XPEvent` (append-only, single source of truth)
and `UserProgress` (a pure projection of it — see
`services/gamification/xp.py::recompute_progress`, which can always rebuild
this table from scratch).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7

from app.db.base import Base
from app.models.enums import SkillBranch, XPSourceType


class XPEvent(Base):
    __tablename__ = "xp_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_type: Mapped[XPSourceType] = mapped_column(
        SAEnum(XPSourceType, name="xp_source_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    base_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    multiplier: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, server_default="1")
    awarded_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    # D15 — nullable, stamped at award time. NULL = branch-less XP (counts
    # toward total_xp, toward no branch). Reuses the `skill_branch` Postgres
    # enum type created by the phase-2 projects migration — the migration
    # that adds this column must use `create_type=False` (see PHASE_3_4_PLAN
    # §3.4 for the exact failure mode this avoids).
    skill_branch: Mapped[SkillBranch | None] = mapped_column(
        SAEnum(SkillBranch, name="skill_branch", values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class UserProgress(Base):
    __tablename__ = "user_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    level: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    current_streak_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    longest_streak_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_active_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# --- Phase 8 indexes -------------------------------------------------------
# 1. Serves *both* `/me/xp-events`'s keyset order and `/me/xp-summary`'s range
#    scan. Before this, only the bare `user_id` index existed, so both
#    endpoints filter-and-then-sort the whole user partition.
Index(
    "ix_xp_events_user_occurred_created",
    XPEvent.user_id,
    XPEvent.occurred_on.desc(),
    XPEvent.created_at.desc(),
)
# 2. The global feed's backward scan. Partial on `awarded_xp > 0` so it never
#    touches reversal rows (habit unlog writes a negative event).
Index(
    "ix_xp_events_feed",
    XPEvent.id.desc(),
    postgresql_where=text("awarded_xp > 0"),
)
# 3. The leaderboard's sort key.
Index("ix_user_progress_total_xp", UserProgress.total_xp.desc())
