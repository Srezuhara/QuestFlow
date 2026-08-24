"""Progress endpoints: the sidebar XP bar's data source, the XP ledger
(keyset-paginated), the XP-history summary charts, the achievement wall, and
(per the plan's preferred placement — this router already owns `/me`) the
skill-tree read.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.timeutils import user_today
from app.models.gamification import XPEvent
from app.models.user import User
from app.schemas.achievements import (
    AchievementOut,
    XPBranchSummary,
    XPDaySummary,
    XPSourceSummary,
    XPSummaryOut,
)
from app.schemas.preferences import PreferencesOut, PreferencesUpdate
from app.schemas.progress import UserProgressOut, XPEventOut, XPEventPageOut
from app.schemas.skilltree import SkillNodeOut, SkillTreeOut
from app.services import preferences_service
from app.services.gamification import achievements, skilltree, xp
from app.services.gamification.leveling import xp_progress

router = APIRouter(prefix="/me", tags=["progress"])


@router.get("/preferences", response_model=PreferencesOut)
async def get_preferences(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> PreferencesOut:
    prefs = await preferences_service.get_preferences(db, current_user)
    return PreferencesOut.model_validate(prefs)


@router.patch("/preferences", response_model=PreferencesOut)
async def update_preferences(
    data: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PreferencesOut:
    prefs = await preferences_service.update_preferences(db, current_user, data)
    return PreferencesOut.model_validate(prefs)


@router.get("/progress", response_model=UserProgressOut)
async def get_progress(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> UserProgressOut:
    progress = await xp.get_progress(db, current_user)
    level = xp_progress(progress.total_xp)
    return UserProgressOut(
        **level.__dict__,
        current_streak_days=progress.current_streak_days,
        longest_streak_days=progress.longest_streak_days,
        last_active_on=progress.last_active_on,
    )


@router.get("/xp-events", response_model=XPEventPageOut)
async def list_xp_events(
    limit: int = Query(default=50, ge=1, le=200),
    before: datetime | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> XPEventPageOut:
    """Keyset-paginated on `(occurred_on desc, created_at desc)`. `before`
    filters `created_at < before`; the response's `next_before` is the last
    row's `created_at` when there may be more, else `null`."""
    stmt = (
        select(XPEvent)
        .where(XPEvent.user_id == current_user.id)
        .order_by(XPEvent.occurred_on.desc(), XPEvent.created_at.desc())
    )
    if before is not None:
        stmt = stmt.where(XPEvent.created_at < before)
    rows = list(await db.scalars(stmt.limit(limit + 1)))
    has_more = len(rows) > limit
    items = rows[:limit]
    next_before = items[-1].created_at if has_more and items else None
    return XPEventPageOut(
        items=[XPEventOut.model_validate(e) for e in items], next_before=next_before
    )


@router.get("/xp-summary", response_model=XPSummaryOut)
async def get_xp_summary(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> XPSummaryOut:
    # `occurred_on` is already the user's *local* calendar day (stamped at
    # award time via `user_today(user)`/the caller's `logged_for`), so
    # grouping by it directly is correct for a non-UTC user without any
    # further timezone conversion here.
    today = user_today(current_user)
    window_start = today - timedelta(days=days - 1)
    base_filter = (
        XPEvent.user_id == current_user.id,
        XPEvent.occurred_on >= window_start,
        XPEvent.occurred_on <= today,
    )

    day_rows = (
        await db.execute(
            select(XPEvent.occurred_on, func.coalesce(func.sum(XPEvent.awarded_xp), 0))
            .where(*base_filter)
            .group_by(XPEvent.occurred_on)
        )
    ).all()
    by_day = {d: int(total) for d, total in day_rows}
    days_out = []
    cursor = window_start
    while cursor <= today:
        days_out.append(XPDaySummary(date=cursor, xp=by_day.get(cursor, 0)))
        cursor += timedelta(days=1)

    branch_rows = (
        await db.execute(
            select(XPEvent.skill_branch, func.coalesce(func.sum(XPEvent.awarded_xp), 0))
            .where(*base_filter, XPEvent.skill_branch.is_not(None))
            .group_by(XPEvent.skill_branch)
        )
    ).all()
    by_branch = [XPBranchSummary(branch=b, xp=int(total)) for b, total in branch_rows]

    source_rows = (
        await db.execute(
            select(XPEvent.source_type, func.coalesce(func.sum(XPEvent.awarded_xp), 0))
            .where(*base_filter)
            .group_by(XPEvent.source_type)
        )
    ).all()
    by_source = [XPSourceSummary(source_type=s, xp=int(total)) for s, total in source_rows]

    return XPSummaryOut(days=days_out, by_branch=by_branch, by_source=by_source)


@router.get("/achievements", response_model=list[AchievementOut])
async def list_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AchievementOut]:
    rows = await achievements.list_with_progress(db, current_user)
    return [
        AchievementOut(
            id=r.achievement.id,
            code=r.achievement.code,
            name=r.achievement.name,
            description=r.achievement.description,
            tier=r.achievement.tier,
            icon=r.achievement.icon,
            xp_reward=r.achievement.xp_reward,
            earned_at=r.earned_at,
            progress_percent=r.progress_percent,
        )
        for r in rows
    ]


@router.get("/skill-tree", response_model=SkillTreeOut)
async def get_skill_tree(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillTreeOut:
    tree = await skilltree.get_tree(db, current_user)
    return SkillTreeOut(
        nodes=[
            SkillNodeOut(
                id=v.node.id,
                code=v.node.code,
                branch=v.node.branch,
                name=v.node.name,
                description=v.node.description,
                tier=v.node.tier,
                xp_cost=v.node.xp_cost,
                prerequisite_codes=v.node.prerequisite_codes,
                icon=v.node.icon,
                layout_x=v.node.layout_x,
                layout_y=v.node.layout_y,
                state=v.state,
                unlocked_at=v.unlocked_at,
            )
            for v in tree.nodes
        ],
        branch_xp={branch.value: total for branch, total in tree.branch_xp.items()},
    )
