"""Aggregates the Command Center's five panels into one payload — see
plan §4 on why `GET /dashboard` exists as a single endpoint rather than a
request waterfall.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutils import user_today
from app.models.enums import TaskPriority, TaskStatus
from app.models.gamification import XPEvent
from app.models.task import Task
from app.models.user import User
from app.services.gamification import xp
from app.services.gamification.leveling import LevelProgress, xp_progress

_PRIORITY_RANK: dict[TaskPriority, int] = {
    TaskPriority.URGENT: 0,
    TaskPriority.IMPORTANT: 1,
    TaskPriority.WARNING: 2,
    TaskPriority.LATER: 3,
}

OBJECTIVES_LIMIT = 20
RECENT_ACTIVITY_LIMIT = 10


@dataclass(frozen=True)
class Pipeline:
    due_tomorrow: list[Task]
    due_next_week: list[Task]


@dataclass(frozen=True)
class Dashboard:
    objectives: list[Task]
    active_count: int
    pipeline: Pipeline
    progress: LevelProgress
    recent_activity: list[XPEvent]


async def get_dashboard(db: AsyncSession, user: User) -> Dashboard:
    today = user_today(user)
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)

    active_tasks = list(
        await db.scalars(
            select(Task)
            .where(
                Task.user_id == user.id,
                Task.status.not_in([TaskStatus.DONE, TaskStatus.ARCHIVED]),
            )
            .order_by(Task.position, Task.created_at)
        )
    )
    # Tasks with no due date sort after ones with a due date within the same
    # priority; the `datetime.max` fallback avoids comparing `None` values
    # against each other (which raises) once the priority/has-due-date
    # tuple elements are equal.
    active_tasks.sort(
        key=lambda t: (
            _PRIORITY_RANK[t.priority],
            t.due_at is None,
            t.due_at or datetime.max.replace(tzinfo=UTC),
        )
    )

    due_tomorrow = [t for t in active_tasks if t.due_at is not None and t.due_at.date() == tomorrow]
    due_next_week = [
        t for t in active_tasks if t.due_at is not None and tomorrow < t.due_at.date() <= week_end
    ]

    recent_activity = list(
        await db.scalars(
            select(XPEvent)
            .where(XPEvent.user_id == user.id)
            .order_by(XPEvent.created_at.desc())
            .limit(RECENT_ACTIVITY_LIMIT)
        )
    )

    progress = await xp.get_progress(db, user)

    return Dashboard(
        objectives=active_tasks[:OBJECTIVES_LIMIT],
        active_count=len(active_tasks),
        pipeline=Pipeline(due_tomorrow=due_tomorrow, due_next_week=due_next_week),
        progress=xp_progress(progress.total_xp),
        recent_activity=recent_activity,
    )
