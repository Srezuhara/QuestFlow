"""Focus-session domain service — server-authoritative Pomodoro sessions.
`actual_seconds` and the resulting XP are always computed here from
`started_at`, never trusted from the client (plan D10). Routers stay thin
and translate the exceptions here into HTTP responses.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutils import user_today
from app.models.enums import FocusMode, FocusStatus, SkillBranch, XPSourceType
from app.models.focus import FocusSession
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services.gamification import achievements, xp
from app.services.gamification.leveling import LevelProgress, xp_progress

FOCUS_XP_MIN_SECONDS = 300


class FocusSessionNotFound(Exception):
    pass


class FocusSessionAlreadyEnded(Exception):
    pass


class FocusTaskNotFound(Exception):
    pass


@dataclass(frozen=True)
class FocusCompletionResult:
    session: FocusSession
    xp_delta: int
    progress: LevelProgress
    newly_earned_achievements: list[achievements.EarnedAchievement] = field(default_factory=list)


@dataclass(frozen=True)
class DaySummary:
    day: date
    focus_seconds: int
    session_count: int


def _user_local_date(user: User, dt: datetime) -> date:
    return dt.astimezone(ZoneInfo(user.timezone)).date()


async def _session_skill_branch(db: AsyncSession, session: FocusSession) -> SkillBranch:
    """The linked task's project's branch, else `SkillBranch.FOCUS` — a focus
    session with no task is focus work by definition (D15's call-site rule
    for `focus_service`)."""
    if session.task_id is not None:
        task = await db.get(Task, session.task_id)
        if task is not None and task.project_id is not None:
            project = await db.get(Project, task.project_id)
            if project is not None:
                return project.skill_branch
    return SkillBranch.FOCUS


async def _get_owned_session(db: AsyncSession, user: User, session_id: uuid.UUID) -> FocusSession:
    session = await db.get(FocusSession, session_id)
    if session is None or session.user_id != user.id:
        raise FocusSessionNotFound
    return session


async def get_active_session(db: AsyncSession, user: User) -> FocusSession | None:
    session: FocusSession | None = await db.scalar(
        select(FocusSession).where(
            FocusSession.user_id == user.id, FocusSession.status == FocusStatus.RUNNING
        )
    )
    return session


async def start_session(
    db: AsyncSession,
    user: User,
    *,
    mode: FocusMode,
    planned_seconds: int,
    task_id: uuid.UUID | None = None,
) -> FocusSession:
    if task_id is not None:
        task = await db.get(Task, task_id)
        if task is None or task.user_id != user.id:
            raise FocusTaskNotFound

    stale = await get_active_session(db, user)
    if stale is not None:
        await _abandon(db, user, stale)

    session = FocusSession(
        user_id=user.id,
        task_id=task_id,
        mode=mode,
        planned_seconds=planned_seconds,
        started_at=datetime.now(UTC),
        status=FocusStatus.RUNNING,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


def _clamp_actual_seconds(session: FocusSession, now: datetime) -> int:
    elapsed = (now - session.started_at).total_seconds()
    return max(0, min(int(elapsed), session.planned_seconds))


async def _abandon(db: AsyncSession, user: User, session: FocusSession) -> FocusSession:
    now = datetime.now(UTC)
    session.actual_seconds = _clamp_actual_seconds(session, now)
    session.ended_at = now
    session.status = FocusStatus.ABANDONED
    await db.flush()
    return session


async def abandon_session(db: AsyncSession, user: User, session_id: uuid.UUID) -> FocusSession:
    session = await _get_owned_session(db, user, session_id)
    if session.status != FocusStatus.RUNNING:
        raise FocusSessionAlreadyEnded
    session = await _abandon(db, user, session)
    await db.commit()
    await db.refresh(session)
    return session


async def complete_session(
    db: AsyncSession, user: User, session_id: uuid.UUID
) -> FocusCompletionResult:
    session = await _get_owned_session(db, user, session_id)
    if session.status != FocusStatus.RUNNING:
        raise FocusSessionAlreadyEnded

    now = datetime.now(UTC)
    actual_seconds = _clamp_actual_seconds(session, now)
    session.actual_seconds = actual_seconds
    session.ended_at = now
    session.status = FocusStatus.COMPLETED

    xp_delta = 0
    if session.mode == FocusMode.FOCUS and actual_seconds >= FOCUS_XP_MIN_SECONDS:
        amount = math.floor(actual_seconds / 60)
        event = await xp.award(
            db,
            user=user,
            source_type=XPSourceType.FOCUS_SESSION,
            source_id=session.id,
            amount=amount,
            idempotency_key=f"focus_session:{session.id}",
            occurred_on=user_today(user),
            skill_branch=await _session_skill_branch(db, session),
        )
        if event is not None:
            xp_delta = event.awarded_xp

    session.xp_awarded = xp_delta
    newly_earned = await achievements.evaluate(db, user)
    await db.commit()
    await db.refresh(session)
    progress = await xp.get_progress(db, user)
    return FocusCompletionResult(
        session=session,
        xp_delta=xp_delta,
        progress=xp_progress(progress.total_xp),
        newly_earned_achievements=newly_earned,
    )


async def list_sessions(
    db: AsyncSession, user: User, *, on_date: date | None = None, limit: int = 50
) -> list[FocusSession]:
    stmt = (
        select(FocusSession)
        .where(FocusSession.user_id == user.id)
        .order_by(FocusSession.started_at.desc())
    )
    if on_date is not None:
        # Widen by a day on each side to cover any UTC/local offset, then
        # filter precisely against the user's local date in Python.
        window_start = datetime.combine(
            on_date - timedelta(days=1), datetime.min.time(), tzinfo=UTC
        )
        window_end = datetime.combine(on_date + timedelta(days=1), datetime.max.time(), tzinfo=UTC)
        stmt = stmt.where(
            FocusSession.started_at >= window_start, FocusSession.started_at <= window_end
        )
    sessions = list(await db.scalars(stmt.limit(min(limit, 200) if on_date is None else 10_000)))
    if on_date is not None:
        sessions = [s for s in sessions if _user_local_date(user, s.started_at) == on_date][:limit]
    return sessions


async def month_summary(db: AsyncSession, user: User, year: int, month: int) -> list[DaySummary]:
    month_start = date(year, month, 1)
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    window_start = datetime.combine(
        month_start - timedelta(days=1), datetime.min.time(), tzinfo=UTC
    )
    window_end = datetime.combine(next_month, datetime.min.time(), tzinfo=UTC)
    rows = (
        await db.execute(
            select(FocusSession.started_at, FocusSession.actual_seconds).where(
                FocusSession.user_id == user.id,
                FocusSession.started_at >= window_start,
                FocusSession.started_at < window_end,
                FocusSession.status == FocusStatus.COMPLETED,
            )
        )
    ).all()

    totals: dict[date, int] = {}
    counts: dict[date, int] = {}
    for started_at, actual_seconds in rows:
        local_day = _user_local_date(user, started_at)
        if not (month_start <= local_day < next_month):
            continue
        totals[local_day] = totals.get(local_day, 0) + (actual_seconds or 0)
        counts[local_day] = counts.get(local_day, 0) + 1

    summaries: list[DaySummary] = []
    cursor = month_start
    while cursor < next_month:
        summaries.append(
            DaySummary(
                day=cursor,
                focus_seconds=totals.get(cursor, 0),
                session_count=counts.get(cursor, 0),
            )
        )
        cursor += timedelta(days=1)
    return summaries
