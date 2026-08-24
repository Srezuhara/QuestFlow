"""Pydantic v2 schemas for the achievements wall and XP-history endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AchievementTier, SkillBranch, XPSourceType


class AchievementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str
    tier: AchievementTier
    icon: str
    xp_reward: int
    earned_at: datetime | None
    progress_percent: float


class XPDaySummary(BaseModel):
    date: date
    xp: int


class XPBranchSummary(BaseModel):
    branch: SkillBranch
    xp: int


class XPSourceSummary(BaseModel):
    source_type: XPSourceType
    xp: int


class XPSummaryOut(BaseModel):
    days: list[XPDaySummary]
    by_branch: list[XPBranchSummary]
    by_source: list[XPSourceSummary]
