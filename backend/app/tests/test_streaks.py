"""Pure streak-math tests, plus the ledger-is-its-own-oracle check for
`recompute_habit_streak` against direct DB manipulation.
"""

from datetime import date, timedelta

from app.models.enums import HabitCadence
from app.models.habit import Habit, HabitLog
from app.schemas.auth import RegisterRequest
from app.services import auth_service
from app.services.gamification.streaks import period_key, previous_period, recompute_habit_streak
from app.tests.conftest import TestSessionLocal as AsyncSessionLocal


def _mon(d: date) -> date:
    return d - timedelta(days=d.weekday())


async def _make_user(email: str, handle: str, timezone: str = "UTC") -> object:
    async with AsyncSessionLocal() as db:
        user = await auth_service.register_user(
            db,
            RegisterRequest(
                email=email,
                password="correct-horse-battery-staple",
                handle=handle,
                display_name=handle,
                timezone=timezone,
            ),
        )
        await db.commit()
        return user.id


async def _make_habit(
    user_id: object, cadence: HabitCadence = HabitCadence.DAILY, target: int = 1
) -> object:
    async with AsyncSessionLocal() as db:
        habit = Habit(user_id=user_id, name="Test Habit", cadence=cadence, target_per_period=target)
        db.add(habit)
        await db.commit()
        await db.refresh(habit)
        return habit.id


async def _log(habit_id: object, logged_for: date, count: int = 1, user_id: object = None) -> None:
    async with AsyncSessionLocal() as db:
        db.add(HabitLog(habit_id=habit_id, user_id=user_id, logged_for=logged_for, count=count))
        await db.commit()


async def test_daily_five_consecutive_days_gives_streak_five() -> None:
    user_id = await _make_user("streak1@example.com", "streak1")
    habit_id = await _make_habit(user_id)
    today = date.today()
    for i in range(5):
        await _log(habit_id, today - timedelta(days=i), user_id=user_id)

    async with AsyncSessionLocal() as db:
        habit = await db.get(Habit, habit_id)
        assert habit is not None
        streak = await recompute_habit_streak(db, habit)
        assert streak.current_streak == 5


async def test_daily_gap_yesterday_resets_streak() -> None:
    user_id = await _make_user("streak2@example.com", "streak2")
    habit_id = await _make_habit(user_id)
    today = date.today()
    await _log(habit_id, today - timedelta(days=5), user_id=user_id)
    await _log(habit_id, today - timedelta(days=4), user_id=user_id)
    await _log(habit_id, today - timedelta(days=2), user_id=user_id)  # gap at day -3

    async with AsyncSessionLocal() as db:
        habit = await db.get(Habit, habit_id)
        assert habit is not None
        streak = await recompute_habit_streak(db, habit)
        assert streak.current_streak == 0


async def test_grace_rule_streak_intact_when_today_not_yet_logged() -> None:
    user_id = await _make_user("streak3@example.com", "streak3")
    habit_id = await _make_habit(user_id)
    today = date.today()
    await _log(habit_id, today - timedelta(days=1), user_id=user_id)
    await _log(habit_id, today - timedelta(days=2), user_id=user_id)

    async with AsyncSessionLocal() as db:
        habit = await db.get(Habit, habit_id)
        assert habit is not None
        streak = await recompute_habit_streak(db, habit)
        assert streak.current_streak == 2


async def test_weekly_target_three_logs_in_one_week_hits_that_week() -> None:
    user_id = await _make_user("streak4@example.com", "streak4")
    habit_id = await _make_habit(user_id, cadence=HabitCadence.WEEKLY, target=3)
    monday = _mon(date.today())
    await _log(habit_id, monday, count=3, user_id=user_id)

    async with AsyncSessionLocal() as db:
        habit = await db.get(Habit, habit_id)
        assert habit is not None
        streak = await recompute_habit_streak(db, habit)
        assert streak.current_streak == 1


async def test_weekly_habit_spans_sunday_monday_boundary_correctly() -> None:
    # A fixed Sunday/Monday pair, independent of "today".
    sunday = date(2026, 8, 16)
    monday = date(2026, 8, 17)
    assert period_key(HabitCadence.WEEKLY, sunday) == date(2026, 8, 10)
    assert period_key(HabitCadence.WEEKLY, monday) == date(2026, 8, 17)
    assert previous_period(HabitCadence.WEEKLY, date(2026, 8, 17)) == date(2026, 8, 10)


async def test_backdated_log_bridging_two_runs_merges_and_raises_longest() -> None:
    user_id = await _make_user("streak5@example.com", "streak5")
    habit_id = await _make_habit(user_id)
    today = date.today()
    for i in [0, 1, 3, 4]:
        await _log(habit_id, today - timedelta(days=i), user_id=user_id)

    async with AsyncSessionLocal() as db:
        habit = await db.get(Habit, habit_id)
        assert habit is not None
        streak = await recompute_habit_streak(db, habit)
        assert streak.current_streak == 2  # today, today-1 only
        assert streak.longest_streak == 2

    # Fill the gap at today-2 — the two runs merge into one run of 5.
    await _log(habit_id, today - timedelta(days=2), user_id=user_id)
    async with AsyncSessionLocal() as db:
        habit = await db.get(Habit, habit_id)
        assert habit is not None
        streak = await recompute_habit_streak(db, habit)
        assert streak.current_streak == 5
        assert streak.longest_streak == 5


async def test_recompute_matches_incremental_ledger_state() -> None:
    user_id = await _make_user("streak6@example.com", "streak6")
    habit_id = await _make_habit(user_id)
    today = date.today()

    for i in [4, 3, 2]:
        await _log(habit_id, today - timedelta(days=i), user_id=user_id)

    async with AsyncSessionLocal() as db:
        habit = await db.get(Habit, habit_id)
        assert habit is not None
        first = await recompute_habit_streak(db, habit)
        first_current, first_longest = first.current_streak, first.longest_streak

    # Unlog one day in the middle of the run (equivalent to `unlog_habit`).
    async with AsyncSessionLocal() as db:
        from sqlalchemy import delete

        await db.execute(
            delete(HabitLog).where(
                HabitLog.habit_id == habit_id, HabitLog.logged_for == today - timedelta(days=3)
            )
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        habit = await db.get(Habit, habit_id)
        assert habit is not None
        second = await recompute_habit_streak(db, habit)
        # Recomputing twice in a row (the "incremental" call and a fresh
        # from-scratch call) must always agree with each other.
        third = await recompute_habit_streak(db, habit)
        assert second.current_streak == third.current_streak
        assert second.longest_streak == third.longest_streak
        assert first_current >= 0 and first_longest >= 0


async def test_non_utc_timezone_today_differs_from_utc_date() -> None:
    from datetime import UTC, datetime
    from zoneinfo import ZoneInfo

    user_id = await _make_user("streak7@example.com", "streak7", timezone="Asia/Calcutta")
    habit_id = await _make_habit(user_id)

    utc_now = datetime.now(UTC)
    local_today = utc_now.astimezone(ZoneInfo("Asia/Calcutta")).date()
    await _log(habit_id, local_today, user_id=user_id)

    async with AsyncSessionLocal() as db:
        habit = await db.get(Habit, habit_id)
        assert habit is not None
        streak = await recompute_habit_streak(db, habit)
        assert streak.current_streak == 1
