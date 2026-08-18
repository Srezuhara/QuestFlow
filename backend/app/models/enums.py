"""Shared enum types used across domain models and schemas.

Kept in one place (rather than per-model) since several of these — notably
`TaskPriority` and `XPSourceType` — are referenced from more than one model
or service module.
"""

from __future__ import annotations

import enum


class SkillBranch(enum.StrEnum):
    FOCUS = "focus"
    HEALTH = "health"
    DISCIPLINE = "discipline"
    GROWTH = "growth"
    WEALTH = "wealth"


class TaskStatus(enum.StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class TaskPriority(enum.StrEnum):
    URGENT = "urgent"
    IMPORTANT = "important"
    WARNING = "warning"
    LATER = "later"


class XPSourceType(enum.StrEnum):
    TASK_COMPLETE = "task_complete"
    HABIT_LOG = "habit_log"
    STREAK_BONUS = "streak_bonus"
    FOCUS_SESSION = "focus_session"
    ACHIEVEMENT = "achievement"
