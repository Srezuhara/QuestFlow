"""Pydantic v2 schemas for the push-subscriptions router."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(min_length=1)
    p256dh: str = Field(min_length=1)
    auth: str = Field(min_length=1)
    user_agent: str | None = None


class PushSubscriptionOut(BaseModel):
    id: uuid.UUID
    endpoint: str
    user_agent: str | None
    last_seen_at: datetime


class PublicKeyOut(BaseModel):
    public_key: str | None
    push_enabled: bool
