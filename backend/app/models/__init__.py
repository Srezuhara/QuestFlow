"""SQLAlchemy 2.0 declarative models, one file per aggregate.

Every model module must be imported here so `Base.metadata` (and therefore
Alembic autogenerate) sees it.
"""

from app.models.achievement import Achievement, UserAchievement
from app.models.focus import FocusSession
from app.models.gamification import UserProgress, XPEvent
from app.models.habit import Habit, HabitLog, HabitStreak
from app.models.note import Note, NoteTag, NoteTaskLink
from app.models.preferences import UserPreferences
from app.models.project import Project
from app.models.reminder import Notification, PushSubscription, Reminder
from app.models.skilltree import SkillNode, UserSkillNode
from app.models.tag import Tag, TaskTag
from app.models.task import Task
from app.models.user import RefreshToken, User

__all__ = [
    "Achievement",
    "FocusSession",
    "Habit",
    "HabitLog",
    "HabitStreak",
    "Note",
    "NoteTag",
    "NoteTaskLink",
    "Notification",
    "Project",
    "PushSubscription",
    "RefreshToken",
    "Reminder",
    "SkillNode",
    "Tag",
    "Task",
    "TaskTag",
    "User",
    "UserAchievement",
    "UserPreferences",
    "UserProgress",
    "UserSkillNode",
    "XPEvent",
]
