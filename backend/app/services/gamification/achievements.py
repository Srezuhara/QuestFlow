"""Achievement evaluator (D17). `evaluate()` is called synchronously at the
end of the domain service call that might have just satisfied a criterion —
`task_service.complete_task`, `habit_service.log_habit`,
`focus_service.complete_session`, `skilltree.unlock_node`,
`note_service.create_note` — and **never** from `xp.award()` itself, which
would create unbounded recursion (an achievement award calls `award()`).

`criteria` is a fixed, closed set of kinds (`{"kind": ..., "value": N}`),
matched in `_meets()`/`_current_value()` — deliberately not an eval'd
expression language.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.achievement import Achievement, UserAchievement
from app.models.enums import FocusMode, FocusStatus, XPSourceType
from app.models.focus import FocusSession
from app.models.gamification import XPEvent
from app.models.habit import Habit, HabitStreak
from app.models.note import Note
from app.models.skilltree import UserSkillNode
from app.models.user import User
from app.services.gamification import xp


@dataclass(frozen=True)
class EarnedAchievement:
    achievement: Achievement
    earned_at: datetime


async def _branch_xp_totals(db: AsyncSession, user_id: uuid.UUID) -> dict[str, int]:
    rows = (
        await db.execute(
            select(XPEvent.skill_branch, func.coalesce(func.sum(XPEvent.awarded_xp), 0))
            .where(XPEvent.user_id == user_id, XPEvent.skill_branch.is_not(None))
            .group_by(XPEvent.skill_branch)
        )
    ).all()
    return {branch.value: int(total) for branch, total in rows}


async def compute_metrics(db: AsyncSession, user: User) -> dict[str, Any]:
    """One batched pass — a handful of aggregate queries, not one per
    achievement."""
    progress = await xp.get_progress(db, user)

    tasks_completed = (
        await db.scalar(
            select(func.count())
            .select_from(XPEvent)
            .where(
                XPEvent.user_id == user.id,
                XPEvent.source_type == XPSourceType.TASK_COMPLETE,
                XPEvent.awarded_xp > 0,
            )
        )
    ) or 0

    habit_streak_max = (
        await db.scalar(
            select(func.max(HabitStreak.longest_streak))
            .select_from(HabitStreak)
            .join(Habit, Habit.id == HabitStreak.habit_id)
            .where(Habit.user_id == user.id)
        )
    ) or 0

    focus_seconds = (
        await db.scalar(
            select(func.coalesce(func.sum(FocusSession.actual_seconds), 0)).where(
                FocusSession.user_id == user.id,
                FocusSession.status == FocusStatus.COMPLETED,
                FocusSession.mode == FocusMode.FOCUS,
            )
        )
    ) or 0

    notes_created = (
        await db.scalar(
            select(func.count())
            .select_from(Note)
            .where(Note.user_id == user.id, Note.archived_at.is_(None))
        )
    ) or 0

    skill_nodes_unlocked = (
        await db.scalar(
            select(func.count())
            .select_from(UserSkillNode)
            .where(UserSkillNode.user_id == user.id)
        )
    ) or 0

    return {
        "total_xp": progress.total_xp,
        "level": progress.level,
        "longest_streak_days": progress.longest_streak_days,
        "tasks_completed": tasks_completed,
        "habit_streak_max": habit_streak_max,
        "focus_minutes": focus_seconds // 60,
        "notes_created": notes_created,
        "skill_nodes_unlocked": skill_nodes_unlocked,
        "branch_xp": await _branch_xp_totals(db, user.id),
    }


def _current_value(criteria: dict[str, Any], metrics: dict[str, Any]) -> float:
    kind = criteria["kind"]
    match kind:
        case "total_xp_at_least":
            return float(metrics["total_xp"])
        case "level_at_least":
            return float(metrics["level"])
        case "daily_streak_at_least":
            return float(metrics["longest_streak_days"])
        case "tasks_completed_at_least":
            return float(metrics["tasks_completed"])
        case "habit_streak_at_least":
            return float(metrics["habit_streak_max"])
        case "focus_minutes_at_least":
            return float(metrics["focus_minutes"])
        case "notes_created_at_least":
            return float(metrics["notes_created"])
        case "skill_nodes_unlocked_at_least":
            return float(metrics["skill_nodes_unlocked"])
        case "branch_xp_at_least":
            branch_xp: dict[str, int] = metrics["branch_xp"]
            return float(branch_xp.get(criteria["branch"], 0))
        case _:
            return 0.0


def _meets(criteria: dict[str, Any], metrics: dict[str, Any]) -> bool:
    return _current_value(criteria, metrics) >= float(criteria["value"])


def progress_percent(criteria: dict[str, Any], metrics: dict[str, Any]) -> float:
    target = float(criteria["value"])
    if target <= 0:
        return 100.0
    current = _current_value(criteria, metrics)
    return min(100.0, round((current / target) * 100, 1))


async def evaluate(db: AsyncSession, user: User) -> list[EarnedAchievement]:
    catalog = list(await db.scalars(select(Achievement).order_by(Achievement.sort_order)))
    if not catalog:
        return []

    earned_ids = set(
        await db.scalars(
            select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)
        )
    )
    metrics = await compute_metrics(db, user)

    newly_earned: list[EarnedAchievement] = []
    for achievement in catalog:
        if achievement.id in earned_ids:
            continue
        if not _meets(achievement.criteria, metrics):
            continue
        now = datetime.now(UTC)
        db.add(UserAchievement(user_id=user.id, achievement_id=achievement.id, earned_at=now))
        await db.flush()
        await xp.award(
            db,
            user=user,
            source_type=XPSourceType.ACHIEVEMENT,
            source_id=achievement.id,
            amount=achievement.xp_reward,
            idempotency_key=f"achievement:{achievement.id}:{user.id}",
            skill_branch=None,
        )
        newly_earned.append(EarnedAchievement(achievement=achievement, earned_at=now))
    return newly_earned


@dataclass(frozen=True)
class AchievementProgress:
    achievement: Achievement
    earned_at: datetime | None
    progress_percent: float


async def list_with_progress(db: AsyncSession, user: User) -> list[AchievementProgress]:
    catalog = list(await db.scalars(select(Achievement).order_by(Achievement.sort_order)))
    earned = {
        ua.achievement_id: ua.earned_at
        for ua in await db.scalars(
            select(UserAchievement).where(UserAchievement.user_id == user.id)
        )
    }
    metrics = await compute_metrics(db, user)

    result: list[AchievementProgress] = []
    for achievement in catalog:
        earned_at = earned.get(achievement.id)
        pct = 100.0 if earned_at is not None else progress_percent(achievement.criteria, metrics)
        result.append(
            AchievementProgress(achievement=achievement, earned_at=earned_at, progress_percent=pct)
        )
    return result


__all__ = [
    "AchievementProgress",
    "EarnedAchievement",
    "compute_metrics",
    "evaluate",
    "list_with_progress",
    "progress_percent",
]
