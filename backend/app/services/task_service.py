"""Task domain service — CRUD plus completion, which is the entry point
into the XP ledger (`services/gamification/xp.award`). Routers stay thin
and translate the exceptions here into HTTP responses.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutils import user_today
from app.models.enums import TaskPriority, TaskStatus, XPSourceType
from app.models.task import Task
from app.models.user import User
from app.schemas.tasks import TaskCreate, TaskUpdate
from app.services.gamification import xp
from app.services.gamification.leveling import LevelProgress, xp_progress

# The mockup's own priority -> XP numbers (plan §3 "Award rules").
DEFAULT_XP_BY_PRIORITY: dict[TaskPriority, int] = {
    TaskPriority.URGENT: 500,
    TaskPriority.IMPORTANT: 250,
    TaskPriority.WARNING: 150,
    TaskPriority.LATER: 50,
}


class TaskNotFound(Exception):
    pass


class SubtaskNestingTooDeep(Exception):
    """One level of nesting only — a subtask cannot itself have a parent."""


@dataclass(frozen=True)
class TaskCompletionResult:
    task: Task
    xp_delta: int
    progress: LevelProgress


async def _get_owned_task(db: AsyncSession, user: User, task_id: uuid.UUID) -> Task:
    task = await db.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise TaskNotFound
    return task


async def _next_position(db: AsyncSession, user: User, project_id: uuid.UUID | None) -> int:
    max_pos = await db.scalar(
        select(func.max(Task.position)).where(
            Task.user_id == user.id, Task.project_id == project_id
        )
    )
    return (max_pos or 0) + 1


async def list_tasks(
    db: AsyncSession,
    user: User,
    *,
    status: TaskStatus | None = None,
    project_id: uuid.UUID | None = None,
) -> list[Task]:
    stmt = select(Task).where(Task.user_id == user.id).order_by(Task.position, Task.created_at)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    return list(await db.scalars(stmt))


async def create_task(db: AsyncSession, user: User, data: TaskCreate) -> Task:
    if data.parent_task_id is not None:
        parent = await _get_owned_task(db, user, data.parent_task_id)
        if parent.parent_task_id is not None:
            raise SubtaskNestingTooDeep

    xp_value = (
        data.xp_value if data.xp_value is not None else DEFAULT_XP_BY_PRIORITY[data.priority]
    )
    position = (
        data.position
        if data.position is not None
        else await _next_position(db, user, data.project_id)
    )
    task = Task(
        user_id=user.id,
        project_id=data.project_id,
        parent_task_id=data.parent_task_id,
        title=data.title,
        description=data.description,
        status=TaskStatus.TODO,
        priority=data.priority,
        due_at=data.due_at,
        xp_value=xp_value,
        position=position,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def create_subtask(
    db: AsyncSession, user: User, parent_id: uuid.UUID, data: TaskCreate
) -> Task:
    data = data.model_copy(update={"parent_task_id": parent_id})
    return await create_task(db, user, data)


async def update_task(db: AsyncSession, user: User, task_id: uuid.UUID, data: TaskUpdate) -> Task:
    task = await _get_owned_task(db, user, task_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, user: User, task_id: uuid.UUID) -> None:
    task = await _get_owned_task(db, user, task_id)
    await db.delete(task)
    await db.commit()


async def reorder_tasks(db: AsyncSession, user: User, ordered_ids: list[uuid.UUID]) -> None:
    tasks = {t.id: t for t in await list_tasks(db, user)}
    for position, task_id in enumerate(ordered_ids):
        task = tasks.get(task_id)
        if task is not None:
            task.position = position
    await db.commit()


async def complete_task(db: AsyncSession, user: User, task_id: uuid.UUID) -> TaskCompletionResult:
    task = await _get_owned_task(db, user, task_id)
    if task.status == TaskStatus.DONE:
        # Idempotent no-op: a duplicate/racing "complete" click shouldn't
        # award XP twice. The real defense is this status check, not the
        # ledger's unique constraint (see xp.py's idempotency-key note).
        progress = await xp.get_progress(db, user)
        return TaskCompletionResult(task, 0, xp_progress(progress.total_xp))

    now = datetime.now(UTC)
    task.status = TaskStatus.DONE
    task.completed_at = now

    await xp.award(
        db,
        user=user,
        source_type=XPSourceType.TASK_COMPLETE,
        source_id=task.id,
        amount=task.xp_value,
        idempotency_key=f"task_complete:{task.id}:{now.isoformat()}",
        occurred_on=user_today(user),
    )
    await db.commit()
    await db.refresh(task)

    progress = await xp.get_progress(db, user)
    return TaskCompletionResult(task, task.xp_value, xp_progress(progress.total_xp))


async def uncomplete_task(db: AsyncSession, user: User, task_id: uuid.UUID) -> TaskCompletionResult:
    task = await _get_owned_task(db, user, task_id)
    if task.status != TaskStatus.DONE:
        progress = await xp.get_progress(db, user)
        return TaskCompletionResult(task, 0, xp_progress(progress.total_xp))

    completed_at = task.completed_at
    assert completed_at is not None  # invariant: DONE tasks always have completed_at
    xp_delta = -task.xp_value

    task.status = TaskStatus.TODO
    task.completed_at = None

    await xp.award(
        db,
        user=user,
        source_type=XPSourceType.TASK_COMPLETE,
        source_id=task.id,
        amount=xp_delta,
        idempotency_key=f"task_complete:{task.id}:{completed_at.isoformat()}:reversal",
        occurred_on=user_today(user),
    )
    await db.commit()
    await db.refresh(task)

    progress = await xp.get_progress(db, user)
    return TaskCompletionResult(task, xp_delta, xp_progress(progress.total_xp))
