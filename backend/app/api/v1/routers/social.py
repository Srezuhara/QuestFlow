"""Social endpoints: the leaderboard and the global activity feed. Both
require auth (D8-8) — this is a personal-productivity app, not a public
site. An opted-out caller can still *read* both; they are only removed from
*other people's* results (their own `me` block returns `rank: null`)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.gamification import UserProgress
from app.models.preferences import UserPreferences
from app.models.user import User
from app.schemas.social import (
    ActorOut,
    FeedItemOut,
    FeedPageOut,
    LeaderboardEntryOut,
    LeaderboardMeOut,
    LeaderboardPageOut,
)
from app.services import social_service

router = APIRouter(prefix="/social", tags=["social"])


def _actor_out(user: User) -> ActorOut:
    return ActorOut(
        handle=user.handle,
        display_name=user.display_name,
        title=user.title,
        avatar_url=user.avatar_url,
    )


@router.get("/leaderboard", response_model=LeaderboardPageOut)
async def get_leaderboard(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardPageOut:
    rows, total = await social_service.list_leaderboard(db, limit=limit, offset=offset)
    my_rank = await social_service.get_my_rank(db, current_user)
    prefs = await db.get(UserPreferences, current_user.id)
    opted_in = prefs.leaderboard_opt_in if prefs is not None else True
    my_progress = await db.get(UserProgress, current_user.id)

    return LeaderboardPageOut(
        entries=[
            LeaderboardEntryOut(
                id=row.user.handle,
                rank=row.rank,
                actor=_actor_out(row.user),
                level=row.progress.level,
                total_xp=row.progress.total_xp,
                current_streak_days=row.progress.current_streak_days,
            )
            for row in rows
        ],
        total=total,
        me=LeaderboardMeOut(
            rank=my_rank,
            total_xp=my_progress.total_xp if my_progress else 0,
            level=my_progress.level if my_progress else 1,
            opted_in=opted_in,
        ),
    )


@router.get("/feed", response_model=FeedPageOut)
async def get_feed(
    limit: int = Query(default=25, ge=1, le=100),
    before: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedPageOut:
    rows, next_before = await social_service.list_feed(db, limit=limit, before=before)
    return FeedPageOut(
        items=[
            FeedItemOut(
                id=row.event.id,
                actor=_actor_out(row.user),
                source_type=row.event.source_type,
                awarded_xp=row.event.awarded_xp,
                skill_branch=row.event.skill_branch,
                created_at=row.event.created_at,
            )
            for row in rows
        ],
        next_before=next_before,
    )
