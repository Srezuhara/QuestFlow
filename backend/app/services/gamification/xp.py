"""The single entry point for awarding XP — `award()`. Called from
`TaskService` (and, in later phases, `HabitService`/`FocusService`) *inside
the caller's own transaction*: this module only ever `flush()`es, it never
commits, so the XP event and the domain change that earned it land
atomically or not at all. Nothing else writes to `xp_events`.

**Idempotency key note:** the plan sketches the default key shape as
`f"{source_type}:{source_id}:{occurred_on}"`. That's exactly right for
sources where one calendar day can only ever produce one legitimate award
(e.g. a habit log — `habit_logs` already has a `(habit_id, logged_for)`
unique constraint of its own). Task completion doesn't fit that shape: a
task can be completed, uncompleted, and re-completed several times in one
day, and each cycle is a legitimate, separately-awarded action. So instead
of hardcoding the key format here, callers pass a fully-formed
`idempotency_key` — `TaskService` builds one from the task id plus the
completion timestamp (not just the date), which keeps genuine re-completions
distinct while still catching an exact duplicate call.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from itertools import pairwise

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutils import user_today
from app.models.enums import SkillBranch, XPSourceType
from app.models.gamification import UserProgress, XPEvent
from app.models.user import User
from app.services.gamification.leveling import level_for_xp


async def _streak_days_from_ledger(db: AsyncSession, user_id: uuid.UUID) -> tuple[int, int]:
    """Derives (current_streak_days, longest_streak_days) from the distinct
    sorted `occurred_on` dates in `xp_events`. This is the oracle both
    `award()`'s incremental update and `recompute_progress()` must agree
    with — computing it the same way in both places guarantees that."""
    dates = list(
        await db.scalars(
            select(XPEvent.occurred_on)
            .where(XPEvent.user_id == user_id)
            .distinct()
            .order_by(XPEvent.occurred_on)
        )
    )
    if not dates:
        return 0, 0

    longest = 1
    run = 1
    for prev, curr in pairwise(dates):
        run = run + 1 if curr - prev == timedelta(days=1) else 1
        longest = max(longest, run)

    current = 1
    for i in range(len(dates) - 1, 0, -1):
        if dates[i] - dates[i - 1] == timedelta(days=1):
            current += 1
        else:
            break

    return current, longest


async def award(
    db: AsyncSession,
    *,
    user: User,
    source_type: XPSourceType,
    source_id: uuid.UUID,
    amount: int,
    idempotency_key: str,
    occurred_on: date | None = None,
    skill_branch: SkillBranch | None = None,
) -> XPEvent | None:
    """Records a (possibly negative, i.e. compensating) XP event and updates
    the `user_progress` projection in the same flush. Returns `None` without
    writing anything if `idempotency_key` has already been used — safe to
    call more than once for what should be the same logical action.
    """
    occurred_on = occurred_on or user_today(user)

    existing = await db.scalar(select(XPEvent).where(XPEvent.idempotency_key == idempotency_key))
    if existing is not None:
        return None

    event = XPEvent(
        user_id=user.id,
        source_type=source_type,
        source_id=source_id,
        base_xp=abs(amount),
        multiplier=1,
        awarded_xp=amount,
        occurred_on=occurred_on,
        idempotency_key=idempotency_key,
        skill_branch=skill_branch,
    )
    db.add(event)
    await db.flush()  # the streak-days query below must see this event

    progress = await db.get(UserProgress, user.id)
    if progress is None:
        progress = UserProgress(user_id=user.id, total_xp=0, level=1)
        db.add(progress)
    progress.total_xp = progress.total_xp + amount
    progress.level = level_for_xp(progress.total_xp)

    if progress.last_active_on is None or occurred_on > progress.last_active_on:
        progress.last_active_on = occurred_on

    current_streak_days, longest_from_ledger = await _streak_days_from_ledger(db, user.id)
    progress.current_streak_days = current_streak_days
    # Monotonic — never lower it, even if history is later deleted.
    progress.longest_streak_days = max(progress.longest_streak_days, longest_from_ledger)

    await db.flush()
    return event


async def get_progress(db: AsyncSession, user: User) -> UserProgress:
    """Read-only lookup — returns a transient (not session-added) default
    row for users who haven't earned any XP yet, so callers don't need to
    special-case "no progress row exists"."""
    progress = await db.get(UserProgress, user.id)
    if progress is not None:
        return progress
    # Transient (never added/flushed) — server_defaults only populate on a
    # real INSERT, so every field is set explicitly here.
    return UserProgress(
        user_id=user.id,
        total_xp=0,
        level=1,
        current_streak_days=0,
        longest_streak_days=0,
        last_active_on=None,
    )


async def recompute_progress(db: AsyncSession, user_id: uuid.UUID) -> UserProgress:
    """Rebuilds `user_progress` from the `xp_events` ledger from scratch.
    The ledger is the single source of truth, so this doubles as both the
    repair tool and the test oracle for the incrementally-maintained
    projection that `award()` writes on every call.
    """
    total_xp = (
        await db.scalar(
            select(func.coalesce(func.sum(XPEvent.awarded_xp), 0)).where(XPEvent.user_id == user_id)
        )
    ) or 0
    last_active_on = await db.scalar(
        select(func.max(XPEvent.occurred_on)).where(XPEvent.user_id == user_id)
    )
    current_streak_days, longest_streak_days = await _streak_days_from_ledger(db, user_id)

    progress = await db.get(UserProgress, user_id)
    if progress is None:
        progress = UserProgress(user_id=user_id)
        db.add(progress)
    progress.total_xp = total_xp
    progress.level = level_for_xp(total_xp)
    progress.last_active_on = last_active_on
    progress.current_streak_days = current_streak_days
    progress.longest_streak_days = longest_streak_days

    await db.flush()
    return progress
