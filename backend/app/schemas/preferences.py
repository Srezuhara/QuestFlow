"""Pydantic v2 schemas for `/me/preferences`."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    focus_minutes: int
    short_break_minutes: int
    long_break_minutes: int
    sessions_before_long_break: int
    sound_enabled: bool
    leaderboard_opt_in: bool


class PreferencesUpdate(BaseModel):
    focus_minutes: int | None = Field(default=None, ge=1, le=180)
    short_break_minutes: int | None = Field(default=None, ge=1, le=60)
    long_break_minutes: int | None = Field(default=None, ge=1, le=60)
    sessions_before_long_break: int | None = Field(default=None, ge=2, le=12)
    sound_enabled: bool | None = None
    leaderboard_opt_in: bool | None = None
