"""Progress endpoints: the sidebar XP bar's data source and the raw ledger."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.gamification import XPEvent
from app.models.user import User
from app.schemas.progress import UserProgressOut, XPEventOut
from app.services.gamification import xp
from app.services.gamification.leveling import xp_progress

router = APIRouter(prefix="/me", tags=["progress"])


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


@router.get("/xp-events", response_model=list[XPEventOut])
async def list_xp_events(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[XPEvent]:
    stmt = (
        select(XPEvent)
        .where(XPEvent.user_id == current_user.id)
        .order_by(XPEvent.occurred_on.desc(), XPEvent.created_at.desc())
        .limit(min(limit, 200))
    )
    return list(await db.scalars(stmt))
