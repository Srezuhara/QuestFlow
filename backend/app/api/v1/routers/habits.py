"""Habit endpoints: CRUD, logging/unlogging (the XP ledger's habit entry
point), and the 30-day matrix.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.timeutils import user_today
from app.models.user import User
from app.schemas.achievements import AchievementOut
from app.schemas.habits import (
    HabitCreate,
    HabitLogOut,
    HabitLogRequest,
    HabitLogResponse,
    HabitMatrixCellOut,
    HabitMatrixOut,
    HabitOut,
    HabitPeriodOut,
    HabitStreakOut,
    HabitUpdate,
)
from app.schemas.progress import LevelProgressOut
from app.services import habit_service
from app.services.gamification.achievements import EarnedAchievement
from app.services.gamification.streaks import period_key

router = APIRouter(prefix="/habits", tags=["habits"])


def _to_achievement_out(earned: EarnedAchievement) -> AchievementOut:
    a = earned.achievement
    return AchievementOut(
        id=a.id,
        code=a.code,
        name=a.name,
        description=a.description,
        tier=a.tier,
        icon=a.icon,
        xp_reward=a.xp_reward,
        earned_at=earned.earned_at,
        progress_percent=100.0,
    )


def _to_habit_out(view: habit_service.HabitView, today: date) -> HabitOut:
    habit = view.habit
    current_period = period_key(habit.cadence, today)
    is_hit = view.current_period_count >= habit.target_per_period
    return HabitOut(
        id=habit.id,
        project_id=habit.project_id,
        name=habit.name,
        description=habit.description,
        cadence=habit.cadence,
        target_per_period=habit.target_per_period,
        skill_branch=habit.skill_branch,
        xp_value=habit.xp_value,
        is_active=habit.is_active,
        archived_at=habit.archived_at,
        created_at=habit.created_at,
        updated_at=habit.updated_at,
        streak=HabitStreakOut.model_validate(view.streak),
        current_period=HabitPeriodOut(
            period_start=current_period,
            count=view.current_period_count,
            target=habit.target_per_period,
            is_hit=is_hit,
        ),
        due_today=(not is_hit) and habit.is_active,
    )


def _to_log_response(result: habit_service.HabitLogResult) -> HabitLogResponse:
    return HabitLogResponse(
        log=HabitLogOut.model_validate(result.log),
        streak=HabitStreakOut.model_validate(result.streak),
        xp_delta=result.xp_delta,
        progress=LevelProgressOut.model_validate(result.progress),
        newly_earned_achievements=[
            _to_achievement_out(a) for a in result.newly_earned_achievements
        ],
    )


@router.get("", response_model=list[HabitOut])
async def list_habits(
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[HabitOut]:
    views = await habit_service.list_habit_views(
        db, current_user, include_archived=include_archived
    )
    today = user_today(current_user)
    return [_to_habit_out(v, today) for v in views]


@router.post("", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
async def create_habit(
    data: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HabitOut:
    try:
        view = await habit_service.create_habit(db, current_user, data)
    except habit_service.UnsupportedCadence as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Custom cadence is not supported yet",
        ) from exc
    return _to_habit_out(view, user_today(current_user))


@router.patch("/{habit_id}", response_model=HabitOut)
async def update_habit(
    habit_id: uuid.UUID,
    data: HabitUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HabitOut:
    try:
        view = await habit_service.update_habit(db, current_user, habit_id, data)
    except habit_service.HabitNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found"
        ) from exc
    except habit_service.UnsupportedCadence as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Custom cadence is not supported yet",
        ) from exc
    return _to_habit_out(view, user_today(current_user))


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_habit(
    habit_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await habit_service.archive_habit(db, current_user, habit_id)
    except habit_service.HabitNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found"
        ) from exc


@router.post("/{habit_id}/log", response_model=HabitLogResponse)
async def log_habit(
    habit_id: uuid.UUID,
    data: HabitLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HabitLogResponse:
    try:
        result = await habit_service.log_habit(
            db, current_user, habit_id, logged_for=data.logged_for, count=data.count
        )
    except habit_service.HabitNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found"
        ) from exc
    return _to_log_response(result)


@router.delete("/{habit_id}/log/{logged_for}", response_model=HabitLogResponse)
async def unlog_habit(
    habit_id: uuid.UUID,
    logged_for: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HabitLogResponse:
    try:
        result = await habit_service.unlog_habit(db, current_user, habit_id, logged_for)
    except habit_service.HabitNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found"
        ) from exc
    except habit_service.HabitLogNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Log not found"
        ) from exc
    return _to_log_response(result)


@router.get("/{habit_id}/matrix", response_model=HabitMatrixOut)
async def get_habit_matrix(
    habit_id: uuid.UUID,
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HabitMatrixOut:
    try:
        cells = await habit_service.get_matrix(db, current_user, habit_id, days=days)
    except habit_service.HabitNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found"
        ) from exc
    return HabitMatrixOut(
        habit_id=habit_id,
        days=days,
        cells=[
            HabitMatrixCellOut(date=c.cell_date, count=c.count, status=c.status) for c in cells
        ],
    )
