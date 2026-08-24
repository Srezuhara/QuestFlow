"""Habit domain service — CRUD, per-period logging (the XP ledger's habit
entry point), and the 30-day matrix. Routers stay thin and translate the
exceptions here into HTTP responses.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutils import user_today
from app.models.enums import HabitCadence, MatrixCellStatus, XPSourceType
from app.models.habit import Habit, HabitLog, HabitStreak
from app.models.user import User
from app.schemas.habits import HabitCreate, HabitUpdate
from app.services.gamification import achievements, xp
from app.services.gamification.leveling import LevelProgress, xp_progress
from app.services.gamification.streaks import (
    STREAK_MILESTONES,
    period_key,
    recompute_habit_streak,
)


class HabitNotFound(Exception):
    pass


class HabitLogNotFound(Exception):
    pass


class UnsupportedCadence(Exception):
    pass


@dataclass(frozen=True)
class HabitView:
    habit: Habit
    streak: HabitStreak
    current_period_count: int


@dataclass(frozen=True)
class HabitLogResult:
    log: HabitLog
    streak: HabitStreak
    xp_delta: int
    progress: LevelProgress
    newly_earned_achievements: list[achievements.EarnedAchievement] = field(default_factory=list)


@dataclass(frozen=True)
class MatrixCell:
    cell_date: date
    count: int
    status: MatrixCellStatus


async def _get_owned_habit(db: AsyncSession, user: User, habit_id: uuid.UUID) -> Habit:
    habit = await db.get(Habit, habit_id)
    if habit is None or habit.user_id != user.id:
        raise HabitNotFound
    return habit


def _validate_cadence(cadence: HabitCadence | None, rrule: str | None) -> None:
    if cadence == HabitCadence.CUSTOM or rrule is not None:
        raise UnsupportedCadence


async def _current_period_counts(
    db: AsyncSession, user: User, habits: list[Habit]
) -> dict[uuid.UUID, int]:
    """One query for all habits — avoids an N+1 on `GET /habits`."""
    if not habits:
        return {}
    today = user_today(user)
    window_start = today - timedelta(days=7)
    ids = [h.id for h in habits]
    rows = (
        await db.execute(
            select(HabitLog.habit_id, HabitLog.logged_for, HabitLog.count).where(
                HabitLog.habit_id.in_(ids),
                HabitLog.logged_for >= window_start,
                HabitLog.logged_for <= today,
            )
        )
    ).all()
    by_habit: dict[uuid.UUID, list[tuple[date, int]]] = {}
    for habit_id, logged_for, count in rows:
        by_habit.setdefault(habit_id, []).append((logged_for, count))

    result: dict[uuid.UUID, int] = {}
    for habit in habits:
        current_period = period_key(habit.cadence, today)
        result[habit.id] = sum(
            count
            for logged_for, count in by_habit.get(habit.id, [])
            if period_key(habit.cadence, logged_for) == current_period
        )
    return result


async def list_habit_views(
    db: AsyncSession, user: User, *, include_archived: bool = False
) -> list[HabitView]:
    stmt = select(Habit).where(Habit.user_id == user.id)
    if not include_archived:
        stmt = stmt.where(Habit.is_active.is_(True))
    stmt = stmt.order_by(Habit.created_at)
    habits = list(await db.scalars(stmt))
    if not habits:
        return []

    ids = [h.id for h in habits]
    streaks = {
        s.habit_id: s
        for s in await db.scalars(select(HabitStreak).where(HabitStreak.habit_id.in_(ids)))
    }
    counts = await _current_period_counts(db, user, habits)

    views = []
    for habit in habits:
        streak = streaks.get(habit.id) or HabitStreak(habit_id=habit.id)
        views.append(HabitView(habit=habit, streak=streak, current_period_count=counts[habit.id]))
    return views


async def get_habit_view(db: AsyncSession, user: User, habit_id: uuid.UUID) -> HabitView:
    habit = await _get_owned_habit(db, user, habit_id)
    streak = await db.get(HabitStreak, habit.id) or HabitStreak(habit_id=habit.id)
    counts = await _current_period_counts(db, user, [habit])
    return HabitView(habit=habit, streak=streak, current_period_count=counts[habit.id])


async def create_habit(db: AsyncSession, user: User, data: HabitCreate) -> HabitView:
    _validate_cadence(data.cadence, None)
    habit = Habit(
        user_id=user.id,
        project_id=data.project_id,
        name=data.name,
        description=data.description,
        cadence=data.cadence,
        target_per_period=data.target_per_period,
        rrule=None,
        skill_branch=data.skill_branch,
        xp_value=data.xp_value,
    )
    db.add(habit)
    await db.flush()
    streak = HabitStreak(habit_id=habit.id)
    db.add(streak)
    await db.commit()
    await db.refresh(habit)
    await db.refresh(streak)
    return HabitView(habit=habit, streak=streak, current_period_count=0)


async def update_habit(
    db: AsyncSession, user: User, habit_id: uuid.UUID, data: HabitUpdate
) -> HabitView:
    habit = await _get_owned_habit(db, user, habit_id)
    updates = data.model_dump(exclude_unset=True)
    if "cadence" in updates or "rrule" in updates:
        _validate_cadence(updates.get("cadence"), updates.get("rrule"))

    cadence_or_target_changed = "cadence" in updates or "target_per_period" in updates
    for field_name, value in updates.items():
        setattr(habit, field_name, value)
    await db.flush()

    streak = await db.get(HabitStreak, habit.id) or HabitStreak(habit_id=habit.id)
    if cadence_or_target_changed:
        streak = await recompute_habit_streak(db, habit)

    await db.commit()
    await db.refresh(habit)
    counts = await _current_period_counts(db, user, [habit])
    return HabitView(habit=habit, streak=streak, current_period_count=counts[habit.id])


async def archive_habit(db: AsyncSession, user: User, habit_id: uuid.UUID) -> None:
    habit = await _get_owned_habit(db, user, habit_id)
    habit.is_active = False
    habit.archived_at = datetime.now(UTC)
    await db.commit()


async def log_habit(
    db: AsyncSession,
    user: User,
    habit_id: uuid.UUID,
    *,
    logged_for: date | None = None,
    count: int = 1,
) -> HabitLogResult:
    habit = await _get_owned_habit(db, user, habit_id)
    logged_for = logged_for or user_today(user)

    existing = await db.scalar(
        select(HabitLog).where(HabitLog.habit_id == habit.id, HabitLog.logged_for == logged_for)
    )
    if existing is None:
        log = HabitLog(habit_id=habit.id, user_id=user.id, logged_for=logged_for, count=count)
        db.add(log)
    else:
        existing.count += count
        log = existing
    await db.flush()

    total_xp_delta = 0
    log_event = await xp.award(
        db,
        user=user,
        source_type=XPSourceType.HABIT_LOG,
        source_id=habit.id,
        amount=habit.xp_value,
        idempotency_key=f"habit_log:{habit.id}:{logged_for.isoformat()}",
        occurred_on=logged_for,
        skill_branch=habit.skill_branch,
    )
    if log_event is not None:
        total_xp_delta += log_event.awarded_xp

    streak = await recompute_habit_streak(db, habit)

    for milestone in sorted(STREAK_MILESTONES):
        if streak.current_streak >= milestone:
            bonus_event = await xp.award(
                db,
                user=user,
                source_type=XPSourceType.STREAK_BONUS,
                source_id=habit.id,
                amount=STREAK_MILESTONES[milestone],
                idempotency_key=f"streak_bonus:{habit.id}:{milestone}",
                occurred_on=logged_for,
                skill_branch=habit.skill_branch,
            )
            if bonus_event is not None:
                total_xp_delta += bonus_event.awarded_xp

    newly_earned = await achievements.evaluate(db, user)
    await db.commit()
    await db.refresh(log)
    progress = await xp.get_progress(db, user)
    return HabitLogResult(
        log=log,
        streak=streak,
        xp_delta=total_xp_delta,
        progress=xp_progress(progress.total_xp),
        newly_earned_achievements=newly_earned,
    )


async def unlog_habit(
    db: AsyncSession, user: User, habit_id: uuid.UUID, logged_for: date
) -> HabitLogResult:
    habit = await _get_owned_habit(db, user, habit_id)
    log = await db.scalar(
        select(HabitLog).where(HabitLog.habit_id == habit.id, HabitLog.logged_for == logged_for)
    )
    if log is None:
        raise HabitLogNotFound
    await db.delete(log)
    await db.flush()

    xp_delta = 0
    reversal = await xp.award(
        db,
        user=user,
        source_type=XPSourceType.HABIT_LOG,
        source_id=habit.id,
        amount=-habit.xp_value,
        idempotency_key=f"habit_log:{habit.id}:{logged_for.isoformat()}:reversal",
        occurred_on=logged_for,
        skill_branch=habit.skill_branch,
    )
    if reversal is not None:
        xp_delta += reversal.awarded_xp

    streak = await recompute_habit_streak(db, habit)
    await db.commit()
    progress = await xp.get_progress(db, user)
    return HabitLogResult(
        log=log, streak=streak, xp_delta=xp_delta, progress=xp_progress(progress.total_xp)
    )


async def get_matrix(
    db: AsyncSession, user: User, habit_id: uuid.UUID, *, days: int = 30
) -> list[MatrixCell]:
    habit = await _get_owned_habit(db, user, habit_id)
    days = max(1, min(days, 365))
    today = user_today(user)
    window_start = today - timedelta(days=days - 1)

    rows = (
        await db.execute(
            select(HabitLog.logged_for, HabitLog.count).where(HabitLog.habit_id == habit.id)
        )
    ).all()

    totals: dict[date, int] = {}
    day_counts: dict[date, int] = {}
    for logged_for, count in rows:
        key = period_key(habit.cadence, logged_for)
        totals[key] = totals.get(key, 0) + count
        day_counts[logged_for] = day_counts.get(logged_for, 0) + count

    target = habit.target_per_period
    hit_periods = {key for key, total in totals.items() if total >= target}
    current_period = period_key(habit.cadence, today)

    step = timedelta(days=7) if habit.cadence == HabitCadence.WEEKLY else timedelta(days=1)
    broken_periods: set[date] = set()
    for hit in hit_periods:
        nxt = hit + step
        if nxt < current_period and nxt not in hit_periods:
            broken_periods.add(nxt)

    cells: list[MatrixCell] = []
    cursor = window_start
    while cursor <= today:
        key = period_key(habit.cadence, cursor)
        period_total = totals.get(key, 0)
        day_count = day_counts.get(cursor, 0)

        if key in broken_periods:
            status = MatrixCellStatus.BROKEN
        elif key in hit_periods:
            status = MatrixCellStatus.EXCEEDED if period_total > target else MatrixCellStatus.HIT
        elif period_total > 0:
            status = MatrixCellStatus.PARTIAL
        else:
            status = MatrixCellStatus.EMPTY

        cells.append(MatrixCell(cell_date=cursor, count=day_count, status=status))
        cursor += timedelta(days=1)

    return cells
