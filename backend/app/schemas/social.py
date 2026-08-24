"""Pydantic v2 schemas for `/social`. Note what is deliberately absent from
`FeedItemOut`: no `source_id`, no title, no email. See D8-4 — task and habit
titles are user-authored free text and are never published."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SkillBranch, XPSourceType


class ActorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    handle: str
    display_name: str
    title: str
    avatar_url: str | None


class LeaderboardEntryOut(BaseModel):
    id: str  # = handle; `DataGrid<Row extends {id: string}>` needs a stable key
    rank: int
    actor: ActorOut
    level: int
    total_xp: int
    current_streak_days: int


class LeaderboardMeOut(BaseModel):
    rank: int | None  # null when opted out or when total_xp == 0
    total_xp: int
    level: int
    opted_in: bool


class LeaderboardPageOut(BaseModel):
    entries: list[LeaderboardEntryOut]
    total: int
    me: LeaderboardMeOut


class FeedItemOut(BaseModel):
    id: uuid.UUID
    actor: ActorOut
    source_type: XPSourceType
    awarded_xp: int
    skill_branch: SkillBranch | None
    created_at: datetime


class FeedPageOut(BaseModel):
    items: list[FeedItemOut]
    next_before: uuid.UUID | None
