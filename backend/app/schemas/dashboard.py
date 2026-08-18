"""Pydantic v2 schema for the aggregated `GET /dashboard` payload — the
Command Center is a five-panel screen; one round trip avoids a request
waterfall on every load."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.progress import LevelProgressOut, XPEventOut
from app.schemas.tasks import TaskOut


class PipelineOut(BaseModel):
    due_tomorrow: list[TaskOut]
    due_next_week: list[TaskOut]


class DashboardOut(BaseModel):
    objectives: list[TaskOut]
    active_count: int
    pipeline: PipelineOut
    progress: LevelProgressOut
    recent_activity: list[XPEventOut]
