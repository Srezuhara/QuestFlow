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


class HabitCadence(enum.StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    # Schema/forward-compat only — phase 3's API rejects this (see plan D2).
    CUSTOM = "custom"


class MatrixCellStatus(enum.StrEnum):
    EMPTY = "empty"
    PARTIAL = "partial"
    HIT = "hit"
    EXCEEDED = "exceeded"
    BROKEN = "broken"


class FocusMode(enum.StrEnum):
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class FocusStatus(enum.StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SkillNodeState(enum.StrEnum):
    LOCKED = "locked"
    AVAILABLE = "available"
    UNLOCKED = "unlocked"


class AchievementTier(enum.StrEnum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    LEGENDARY = "legendary"


class ReminderStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    DISMISSED = "dismissed"
    CANCELLED = "cancelled"


class ReminderChannel(enum.StrEnum):
    PUSH = "push"
    IN_APP = "in_app"


class NotificationType(enum.StrEnum):
    REMINDER = "reminder"
    ACHIEVEMENT = "achievement"
    LEVEL_UP = "level_up"
    STREAK_RISK = "streak_risk"
    SYSTEM = "system"
