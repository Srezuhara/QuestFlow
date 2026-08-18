"""Pydantic v2 schemas for the tags router."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    slug: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9-]+$")
    color_token: str = "neon-lime"


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    color_token: str | None = None


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    color_token: str
