"""SQLAlchemy 2.0 declarative models, one file per aggregate.

Every model module must be imported here so `Base.metadata` (and therefore
Alembic autogenerate) sees it.
"""

from app.models.gamification import UserProgress, XPEvent
from app.models.project import Project
from app.models.tag import Tag, TaskTag
from app.models.task import Task
from app.models.user import RefreshToken, User

__all__ = [
    "Project",
    "RefreshToken",
    "Tag",
    "Task",
    "TaskTag",
    "User",
    "UserProgress",
    "XPEvent",
]
