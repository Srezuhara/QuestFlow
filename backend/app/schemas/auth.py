"""Pydantic v2 request/response schemas for the auth router."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    handle: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    display_name: str = Field(min_length=1, max_length=80)
    timezone: str = "UTC"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    handle: str
    display_name: str
    title: str
    avatar_url: str | None
    timezone: str


# The whole preset picker (D9-3, PHASE_8_9_PLAN.md §9.7). Rejecting anything
# off this list is the entire security story: an unvalidated `avatar_url`
# is a tracking-pixel and mixed-content vector rendered in every other
# user's leaderboard row, not just the owner's own screen.
ALLOWED_AVATAR_URLS: frozenset[str] = frozenset(
    f"/avatars/avatar-{i:02d}.svg" for i in range(1, 13)
)


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    title: str | None = Field(default=None, min_length=1, max_length=40)
    avatar_url: str | None = Field(default=None)

    @field_validator("avatar_url")
    @classmethod
    def _avatar_url_must_be_allowlisted(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_AVATAR_URLS:
            raise ValueError("avatar_url must be one of the preset avatars")
        return value
