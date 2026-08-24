"""Pydantic v2 schemas for the notes router."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskStatus
from app.schemas.achievements import AchievementOut
from app.schemas.tags import TagOut


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body_md: str = ""
    is_pinned: bool = False
    tag_slugs: list[str] = Field(default_factory=list)
    task_ids: list[uuid.UUID] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body_md: str | None = None
    is_pinned: bool | None = None
    tag_slugs: list[str] | None = None


class LinkedTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: TaskStatus


class NoteSummaryOut(BaseModel):
    """The list-panel shape — never ships the whole body."""

    id: uuid.UUID
    title: str
    excerpt: str
    is_pinned: bool
    updated_at: datetime
    tags: list[TagOut]


class NoteOut(BaseModel):
    id: uuid.UUID
    title: str
    body_md: str
    is_pinned: bool
    archived_at: datetime | None
    tags: list[TagOut]
    linked_tasks: list[LinkedTaskOut]
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    newly_earned_achievements: list[AchievementOut] = []


class CheckboxToggleRequest(BaseModel):
    line_index: int = Field(ge=0)
    checked: bool
