"""Pydantic v2 schemas for the notifications router."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import NotificationType


class NotificationOut(BaseModel):
    id: uuid.UUID
    type: NotificationType
    payload: dict[str, Any]
    read_at: datetime | None
    created_at: datetime


class NotificationPageOut(BaseModel):
    items: list[NotificationOut]
    next_before: uuid.UUID | None
    unread_count: int


class MarkAllReadResponse(BaseModel):
    marked_count: int
