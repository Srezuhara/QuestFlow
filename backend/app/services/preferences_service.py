"""User Pomodoro preferences — one row per user, created on first write;
reads before any write return a transient in-memory default (same
create-on-read pattern as `gamification.xp.get_progress`).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preferences import UserPreferences
from app.models.user import User
from app.schemas.preferences import PreferencesUpdate


async def get_preferences(db: AsyncSession, user: User) -> UserPreferences:
    prefs = await db.get(UserPreferences, user.id)
    if prefs is not None:
        return prefs
    return UserPreferences(
        user_id=user.id,
        focus_minutes=25,
        short_break_minutes=5,
        long_break_minutes=15,
        sessions_before_long_break=4,
        sound_enabled=True,
        leaderboard_opt_in=True,
    )


async def update_preferences(
    db: AsyncSession, user: User, data: PreferencesUpdate
) -> UserPreferences:
    prefs = await db.get(UserPreferences, user.id)
    if prefs is None:
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
        await db.flush()
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    await db.commit()
    await db.refresh(prefs)
    return prefs
