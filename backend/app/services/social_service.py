"""Leaderboard and public activity feed. Both read existing tables — this
phase writes nothing but a preference flag.

The `outerjoin(UserPreferences)` + `coalesce(..., True)` in `_opted_in` is
**load-bearing**: prefs rows are created lazily on first *write* (see
`preferences_service.get_preferences`, which returns a transient object on
read), so an inner join would silently hide every user who has never opened
Settings — which, on day one, is all of them. There is a dedicated
regression test for exactly this.
"""

from __future__ import annotations

import uuid
from typing import NamedTuple

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import UserProgress, XPEvent
from app.models.preferences import UserPreferences
from app.models.user import User


def _opted_in() -> ColumnElement[bool]:
    """The single visibility predicate — D8-9. `coalesce` because the prefs
    row may not exist yet."""
    return func.coalesce(UserPreferences.leaderboard_opt_in, True).is_(True)


class LeaderboardRow(NamedTuple):
    rank: int
    user: User
    progress: UserProgress


async def list_leaderboard(
    db: AsyncSession, *, limit: int, offset: int
) -> tuple[list[LeaderboardRow], int]:
    rank_col = func.rank().over(order_by=UserProgress.total_xp.desc()).label("rank")
    base = (
        select(rank_col, User, UserProgress)
        .select_from(UserProgress)
        .join(User, User.id == UserProgress.user_id)
        .outerjoin(UserPreferences, UserPreferences.user_id == UserProgress.user_id)
        .where(User.is_active.is_(True), _opted_in(), UserProgress.total_xp > 0)
    )
    paged = base.order_by(UserProgress.total_xp.desc(), User.handle.asc()).limit(limit).offset(
        offset
    )
    rows = (await db.execute(paged)).all()

    total = (
        await db.scalar(
            select(func.count())
            .select_from(UserProgress)
            .join(User, User.id == UserProgress.user_id)
            .outerjoin(UserPreferences, UserPreferences.user_id == UserProgress.user_id)
            .where(User.is_active.is_(True), _opted_in(), UserProgress.total_xp > 0)
        )
    ) or 0

    return [LeaderboardRow(rank=r, user=u, progress=p) for r, u, p in rows], total


async def get_my_rank(db: AsyncSession, user: User) -> int | None:
    """D8-11: a separate `COUNT(*) + 1` query, never derived from a page —
    the current user is usually not on page 1. Returns `None` when the
    caller is opted out, inactive, or has no XP."""
    progress = await db.get(UserProgress, user.id)
    prefs = await db.get(UserPreferences, user.id)
    opted_in = prefs.leaderboard_opt_in if prefs is not None else True
    if progress is None or progress.total_xp <= 0 or not opted_in or not user.is_active:
        return None

    higher_ranked = (
        await db.scalar(
            select(func.count())
            .select_from(UserProgress)
            .join(User, User.id == UserProgress.user_id)
            .outerjoin(UserPreferences, UserPreferences.user_id == UserProgress.user_id)
            .where(
                User.is_active.is_(True),
                _opted_in(),
                UserProgress.total_xp > 0,
                UserProgress.total_xp > progress.total_xp,
            )
        )
    ) or 0
    return higher_ranked + 1


class FeedRow(NamedTuple):
    event: XPEvent
    user: User


async def list_feed(
    db: AsyncSession, *, limit: int, before: uuid.UUID | None
) -> tuple[list[FeedRow], uuid.UUID | None]:
    stmt = (
        select(XPEvent, User)
        .join(User, User.id == XPEvent.user_id)
        .outerjoin(UserPreferences, UserPreferences.user_id == XPEvent.user_id)
        .where(XPEvent.awarded_xp > 0, User.is_active.is_(True), _opted_in())
    )
    if before is not None:
        stmt = stmt.where(XPEvent.id < before)
    stmt = stmt.order_by(XPEvent.id.desc()).limit(limit + 1)

    rows = (await db.execute(stmt)).all()
    has_more = len(rows) > limit
    items = rows[:limit]
    next_before = items[-1][0].id if has_more and items else None
    return [FeedRow(event=e, user=u) for e, u in items], next_before


# Recorded, not built — a future `?scope=me` personal feed. There, D8-4's
# privacy objection vanishes and titles can be resolved: fetch the page
# first, `defaultdict(list)`-group `source_id` by `source_type`, issue **at
# most four** `WHERE id = ANY(:ids)` queries, merge to a dict. Deleted rows
# are normal, not exceptional — `source_id` has no FK precisely so the
# ledger survives deletion. A miss renders "a deleted quest", never an
# error, and **never a filtered-out row** (which would corrupt the totals
# the feed sums to).
