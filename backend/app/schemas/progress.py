"""Pydantic v2 schemas for the progress router and the dashboard's
embedded progress widget."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import XPSourceType
from app.schemas.tasks import TaskOut


class LevelProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    level: int
    total_xp: int
    xp_into_level: int
    xp_for_next_level: int
    percent: float


class UserProgressOut(LevelProgressOut):
    current_streak_days: int
    longest_streak_days: int
    last_active_on: date | None


class XPEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: XPSourceType
    source_id: uuid.UUID
    awarded_xp: int
    occurred_on: date
    created_at: datetime


class TaskCompleteResponse(BaseModel):
    task: TaskOut
    xp_delta: int
    progress: LevelProgressOut
