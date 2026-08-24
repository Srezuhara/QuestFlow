"""Pydantic v2 schemas for the reminders router.

`remind_at` uses `AwareDatetime` — naive input 422s automatically with no
custom validator needed (D7-7: the browser knows the user's real offset
better than the stored `users.timezone` string, so firing is a plain UTC
comparison).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from app.models.enums import ReminderChannel, ReminderStatus


class ReminderCreate(BaseModel):
    message: str = Field(min_length=1, max_length=200)
    remind_at: AwareDatetime
    task_id: uuid.UUID | None = None
    habit_id: uuid.UUID | None = None
    rrule: str | None = None
    channels: list[ReminderChannel] = Field(
        default_factory=lambda: [ReminderChannel.PUSH, ReminderChannel.IN_APP]
    )

    @model_validator(mode="after")
    def _validate_target_and_rrule(self) -> ReminderCreate:
        if self.task_id is not None and self.habit_id is not None:
            raise ValueError("A reminder can target a task or a habit, not both")
        if self.rrule is not None:
            raise ValueError("Recurring reminders are not supported yet")
        return self


class ReminderUpdate(BaseModel):
    message: str | None = Field(default=None, min_length=1, max_length=200)
    remind_at: AwareDatetime | None = None
    task_id: uuid.UUID | None = None
    habit_id: uuid.UUID | None = None
    rrule: str | None = None
    channels: list[ReminderChannel] | None = None

    @model_validator(mode="after")
    def _validate_target_and_rrule(self) -> ReminderUpdate:
        if self.task_id is not None and self.habit_id is not None:
            raise ValueError("A reminder can target a task or a habit, not both")
        if self.rrule is not None:
            raise ValueError("Recurring reminders are not supported yet")
        return self


class ReminderOut(BaseModel):
    id: uuid.UUID
    message: str
    remind_at: datetime
    task_id: uuid.UUID | None
    habit_id: uuid.UUID | None
    target_label: str | None
    rrule: str | None
    channels: list[ReminderChannel]
    status: ReminderStatus
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReminderPageOut(BaseModel):
    items: list[ReminderOut]
    next_before: datetime | None
