"""Pure period/streak math for habits (no HTTP concerns).

A "period" is a day (daily cadence) or an ISO week identified by its Monday
(weekly cadence, per plan D8). `recompute_habit_streak` is both the
incrementally-callable updater and, since it always recomputes from the
`habit_logs` ledger, the test oracle its own incremental use must match.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutils import user_today
from app.models.enums import HabitCadence
from app.models.habit import Habit, HabitLog, HabitStreak
from app.models.user import User

# Milestones are periods, not days (plan D3) — 7/30/100 consecutive hit periods.
STREAK_MILESTONES: dict[int, int] = {7: 250, 30: 1000, 100: 5000}


def period_key(cadence: HabitCadence, d: date) -> date:
    """The identifying date for the period `d` falls in."""
    if cadence == HabitCadence.WEEKLY:
        return d - timedelta(days=d.weekday())  # Monday of that ISO week
    return d


def period_start(cadence: HabitCadence, d: date) -> date:
    return period_key(cadence, d)


def previous_period(cadence: HabitCadence, d: date) -> date:
    """`d` must already be a period key. Returns the immediately preceding one."""
    step = timedelta(days=7) if cadence == HabitCadence.WEEKLY else timedelta(days=1)
    return d - step


async def recompute_habit_streak(db: AsyncSession, habit: Habit) -> HabitStreak:
    user = await db.get(User, habit.user_id)
    assert user is not None  # invariant: a habit always has an owning user
    today = user_today(user)

    rows = (
        await db.execute(
            select(HabitLog.logged_for, HabitLog.count).where(HabitLog.habit_id == habit.id)
        )
    ).all()

    totals: dict[date, int] = {}
    last_completed_on: date | None = None
    for logged_for, count in rows:
        key = period_key(habit.cadence, logged_for)
        totals[key] = totals.get(key, 0) + count
        if last_completed_on is None or logged_for > last_completed_on:
            last_completed_on = logged_for

    hit_periods = {key for key, total in totals.items() if total >= habit.target_per_period}

    # Longest run in history: a run continues only when the *immediately
    # preceding period* (by cadence, not just "next logged period") was also
    # hit — this correctly treats an unlogged period as a break even though
    # it has no row in `totals`.
    longest_from_history = 0
    run = 0
    prev_key: date | None = None
    for key in sorted(hit_periods):
        if prev_key is not None and previous_period(habit.cadence, key) == prev_key:
            run += 1
        else:
            run = 1
        longest_from_history = max(longest_from_history, run)
        prev_key = key

    # Current streak: count backwards from "now", with the grace rule — an
    # unhit *current* period doesn't break the streak, since it hasn't
    # elapsed yet. It just isn't counted until it's hit.
    current_period = period_key(habit.cadence, today)
    cursor = current_period if current_period in hit_periods else previous_period(
        habit.cadence, current_period
    )
    current_streak = 0
    while cursor in hit_periods:
        current_streak += 1
        cursor = previous_period(habit.cadence, cursor)

    streak = await db.get(HabitStreak, habit.id)
    if streak is None:
        streak = HabitStreak(habit_id=habit.id)
        db.add(streak)

    # Monotonic per plan rule 4 — never lower it, even if history was deleted.
    streak.longest_streak = max(streak.longest_streak or 0, longest_from_history, current_streak)
    streak.current_streak = current_streak
    streak.last_completed_on = last_completed_on

    await db.flush()
    return streak
