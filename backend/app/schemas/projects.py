"""Pydantic v2 schemas for the projects router."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SkillBranch


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    color_token: str = "neon-lime"
    icon: str | None = None
    skill_branch: SkillBranch = SkillBranch.FOCUS
    position: int = 0


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    slug: str | None = Field(default=None, min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    color_token: str | None = None
    icon: str | None = None
    skill_branch: SkillBranch | None = None
    position: int | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    color_token: str
    icon: str | None
    skill_branch: SkillBranch
    position: int
    archived_at: datetime | None
