"""Focus-session endpoints: start/complete/abandon (the XP ledger's focus
entry point), the active-session resume lookup, the Mission Log listing,
and the month calendar aggregation.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.focus import FocusSession
from app.models.task import Task
from app.models.user import User
from app.schemas.achievements import AchievementOut
from app.schemas.focus import (
    FocusCompleteResponse,
    FocusDaySummaryOut,
    FocusMonthOut,
    FocusSessionOut,
    FocusSessionStart,
    FocusSessionUpdate,
)
from app.schemas.progress import LevelProgressOut
from app.services import focus_service
from app.services.gamification import xp
from app.services.gamification.achievements import EarnedAchievement
from app.services.gamification.leveling import xp_progress

router = APIRouter(prefix="/focus", tags=["focus"])


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


async def _task_titles(db: AsyncSession, task_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not task_ids:
        return {}
    rows = (await db.execute(select(Task.id, Task.title).where(Task.id.in_(task_ids)))).all()
    return {task_id: title for task_id, title in rows}  # noqa: C416 — Row isn't a plain tuple


async def _to_session_out(db: AsyncSession, session: FocusSession) -> FocusSessionOut:
    titles = await _task_titles(db, {session.task_id} if session.task_id else set())
    return FocusSessionOut(
        id=session.id,
        task_id=session.task_id,
        task_title=titles.get(session.task_id) if session.task_id else None,
        mode=session.mode,
        planned_seconds=session.planned_seconds,
        actual_seconds=session.actual_seconds,
        started_at=session.started_at,
        ended_at=session.ended_at,
        status=session.status,
        xp_awarded=session.xp_awarded,
        created_at=session.created_at,
    )


async def _to_session_out_list(
    db: AsyncSession, sessions: list[FocusSession]
) -> list[FocusSessionOut]:
    titles = await _task_titles(db, {s.task_id for s in sessions if s.task_id is not None})
    return [
        FocusSessionOut(
            id=s.id,
            task_id=s.task_id,
            task_title=titles.get(s.task_id) if s.task_id else None,
            mode=s.mode,
            planned_seconds=s.planned_seconds,
            actual_seconds=s.actual_seconds,
            started_at=s.started_at,
            ended_at=s.ended_at,
            status=s.status,
            xp_awarded=s.xp_awarded,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=FocusSessionOut, status_code=status.HTTP_201_CREATED)
async def start_session(
    data: FocusSessionStart,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FocusSessionOut:
    try:
        session = await focus_service.start_session(
            db,
            current_user,
            mode=data.mode,
            planned_seconds=data.planned_seconds,
            task_id=data.task_id,
        )
    except focus_service.FocusTaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        ) from exc
    return await _to_session_out(db, session)


@router.get("/sessions/active", response_model=FocusSessionOut | None)
async def get_active_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FocusSessionOut | None:
    session = await focus_service.get_active_session(db, current_user)
    if session is None:
        return None
    return await _to_session_out(db, session)


@router.get("/calendar", response_model=FocusMonthOut)
async def get_calendar(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FocusMonthOut:
    summaries = await focus_service.month_summary(db, current_user, year, month)
    return FocusMonthOut(
        year=year,
        month=month,
        days=[
            FocusDaySummaryOut(
                date=s.day, focus_seconds=s.focus_seconds, session_count=s.session_count
            )
            for s in summaries
        ],
    )


@router.get("/sessions", response_model=list[FocusSessionOut])
async def list_sessions(
    on_date: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FocusSessionOut]:
    sessions = await focus_service.list_sessions(db, current_user, on_date=on_date, limit=limit)
    return await _to_session_out_list(db, sessions)


@router.patch("/sessions/{session_id}", response_model=FocusCompleteResponse)
async def update_session(
    session_id: uuid.UUID,
    data: FocusSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FocusCompleteResponse:
    try:
        if data.action == "complete":
            result = await focus_service.complete_session(db, current_user, session_id)
            session_out = await _to_session_out(db, result.session)
            return FocusCompleteResponse(
                session=session_out,
                xp_delta=result.xp_delta,
                progress=LevelProgressOut.model_validate(result.progress),
                newly_earned_achievements=[
                    _to_achievement_out(a) for a in result.newly_earned_achievements
                ],
            )
        session = await focus_service.abandon_session(db, current_user, session_id)
        session_out = await _to_session_out(db, session)
        progress = await xp.get_progress(db, current_user)
        return FocusCompleteResponse(
            session=session_out,
            xp_delta=0,
            progress=LevelProgressOut.model_validate(xp_progress(progress.total_xp)),
        )
    except focus_service.FocusSessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Focus session not found"
        ) from exc
    except focus_service.FocusSessionAlreadyEnded as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Focus session already ended"
        ) from exc
