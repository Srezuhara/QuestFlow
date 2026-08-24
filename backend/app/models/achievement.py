"""`Achievement` (global catalog, seeded by an Alembic data migration) and
`UserAchievement` (earned rows). Evaluated by
`services/gamification/achievements.py::evaluate`, called synchronously at
the end of the domain service calls listed there — never from
`xp.award()` itself (D17, no recursion).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7

from app.db.base import Base
from app.models.enums import AchievementTier


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[AchievementTier] = mapped_column(
        SAEnum(
            AchievementTier, name="achievement_tier", values_callable=lambda e: [m.value for m in e]
        ),
        nullable=False,
    )
    icon: Mapped[str] = mapped_column(String(40), nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    criteria: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    achievement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True
    )
    earned_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
