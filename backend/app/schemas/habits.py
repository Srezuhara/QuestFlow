"""Pydantic v2 schemas for the habits router."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import HabitCadence, MatrixCellStatus, SkillBranch
from app.schemas.achievements import AchievementOut
from app.schemas.progress import LevelProgressOut


class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    cadence: HabitCadence = HabitCadence.DAILY
    target_per_period: int = Field(default=1, ge=1)
    skill_branch: SkillBranch = SkillBranch.FOCUS
    xp_value: int = Field(default=50, ge=0)
    project_id: uuid.UUID | None = None


class HabitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    cadence: HabitCadence | None = None
    target_per_period: int | None = Field(default=None, ge=1)
    skill_branch: SkillBranch | None = None
    xp_value: int | None = Field(default=None, ge=0)
    project_id: uuid.UUID | None = None


class HabitStreakOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_streak: int
    longest_streak: int
    last_completed_on: date | None


class HabitPeriodOut(BaseModel):
    period_start: date
    count: int
    target: int
    is_hit: bool


class HabitOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID | None
    name: str
    description: str | None
    cadence: HabitCadence
    target_per_period: int
    skill_branch: SkillBranch
    xp_value: int
    is_active: bool
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    streak: HabitStreakOut
    current_period: HabitPeriodOut
    due_today: bool


class HabitLogRequest(BaseModel):
    logged_for: date | None = None
    count: int = Field(default=1, ge=1)


class HabitLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    habit_id: uuid.UUID
    logged_for: date
    count: int
    created_at: datetime


class HabitLogResponse(BaseModel):
    log: HabitLogOut
    streak: HabitStreakOut
    xp_delta: int
    progress: LevelProgressOut
    newly_earned_achievements: list[AchievementOut] = []


class HabitMatrixCellOut(BaseModel):
    date: date
    count: int
    status: MatrixCellStatus


class HabitMatrixOut(BaseModel):
    habit_id: uuid.UUID
    days: int
    cells: list[HabitMatrixCellOut]
