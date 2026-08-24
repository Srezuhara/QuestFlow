"""`SkillNode` (global catalog, seeded by an Alembic data migration — D16)
and `UserSkillNode` (only unlocked nodes get a row; `locked`/`available` are
*derived* per request in `services/gamification/skilltree.py`, never stored —
see D13).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7

from app.db.base import Base
from app.models.enums import SkillBranch


class SkillNode(Base):
    __tablename__ = "skill_nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False, index=True)
    # Nullable only for `core_nexus` (tier 0, no branch).
    branch: Mapped[SkillBranch | None] = mapped_column(
        SAEnum(SkillBranch, name="skill_branch", values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    prerequisite_codes: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    icon: Mapped[str] = mapped_column(String(40), nullable=False)
    layout_x: Mapped[int] = mapped_column(Integer, nullable=False)
    layout_y: Mapped[int] = mapped_column(Integer, nullable=False)


class UserSkillNode(Base):
    __tablename__ = "user_skill_nodes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_nodes.id", ondelete="CASCADE"), primary_key=True
    )
    unlocked_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
