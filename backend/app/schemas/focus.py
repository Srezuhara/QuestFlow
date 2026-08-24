"""Pydantic v2 schemas for the focus-session router. Note there is
deliberately no client-supplied duration field anywhere here (plan D10) —
`actual_seconds`/`xp_awarded` are always server-computed."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FocusMode, FocusStatus
from app.schemas.achievements import AchievementOut
from app.schemas.progress import LevelProgressOut


class FocusSessionStart(BaseModel):
    mode: FocusMode
    planned_seconds: int = Field(ge=60, le=14400)
    task_id: uuid.UUID | None = None


class FocusSessionUpdate(BaseModel):
    action: Literal["complete", "abandon"]


class FocusSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID | None
    task_title: str | None
    mode: FocusMode
    planned_seconds: int
    actual_seconds: int | None
    started_at: datetime
    ended_at: datetime | None
    status: FocusStatus
    xp_awarded: int
    created_at: datetime


class FocusCompleteResponse(BaseModel):
    session: FocusSessionOut
    xp_delta: int
    progress: LevelProgressOut
    newly_earned_achievements: list[AchievementOut] = []


class FocusDaySummaryOut(BaseModel):
    date: date
    focus_seconds: int
    session_count: int


class FocusMonthOut(BaseModel):
    year: int
    month: int
    days: list[FocusDaySummaryOut]
