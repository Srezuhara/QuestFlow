"""Pydantic v2 schemas for the tasks router."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskPriority, TaskStatus
from app.schemas.tags import TagOut


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority = TaskPriority.LATER
    due_at: datetime | None = None
    project_id: uuid.UUID | None = None
    parent_task_id: uuid.UUID | None = None
    xp_value: int | None = Field(default=None, ge=0)
    position: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority | None = None
    due_at: datetime | None = None
    project_id: uuid.UUID | None = None
    xp_value: int | None = Field(default=None, ge=0)
    position: int | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    parent_task_id: uuid.UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_at: datetime | None
    completed_at: datetime | None
    xp_value: int
    position: int
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime


class ReorderRequest(BaseModel):
    task_ids: list[uuid.UUID]
