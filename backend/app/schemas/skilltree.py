"""Pydantic v2 schemas for the skill-tree endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import SkillBranch, SkillNodeState
from app.schemas.achievements import AchievementOut
from app.schemas.progress import LevelProgressOut


class SkillNodeOut(BaseModel):
    id: uuid.UUID
    code: str
    branch: SkillBranch | None
    name: str
    description: str
    tier: int
    xp_cost: int
    prerequisite_codes: list[str]
    icon: str
    layout_x: int
    layout_y: int
    state: SkillNodeState
    unlocked_at: datetime | None


class SkillTreeOut(BaseModel):
    nodes: list[SkillNodeOut]
    branch_xp: dict[str, int]


class UnlockResponse(BaseModel):
    node: SkillNodeOut
    newly_available: list[str]
    xp_delta: int
    progress: LevelProgressOut
    newly_earned_achievements: list[AchievementOut]
