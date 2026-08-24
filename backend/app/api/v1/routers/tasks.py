"""Task endpoints: CRUD, completion (the XP ledger's entry point), subtasks,
and reorder.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.enums import TaskStatus
from app.models.task import Task
from app.models.user import User
from app.schemas.achievements import AchievementOut
from app.schemas.progress import LevelProgressOut, TaskCompleteResponse
from app.schemas.tasks import ReorderRequest, TaskCreate, TaskOut, TaskUpdate
from app.services import task_service
from app.services.gamification.achievements import EarnedAchievement

router = APIRouter(prefix="/tasks", tags=["tasks"])


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


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    status_filter: TaskStatus | None = None,
    project_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Task]:
    return await task_service.list_tasks(
        db, current_user, status=status_filter, project_id=project_id
    )


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    try:
        return await task_service.create_task(db, current_user, data)
    except task_service.TaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parent task not found"
        ) from exc
    except task_service.SubtaskNestingTooDeep as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Subtasks cannot themselves have a parent",
        ) from exc


@router.post("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_tasks(
    data: ReorderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await task_service.reorder_tasks(db, current_user, data.task_ids)


@router.post("/{task_id}/subtasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_subtask(
    task_id: uuid.UUID,
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    try:
        return await task_service.create_subtask(db, current_user, task_id, data)
    except task_service.TaskNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    except task_service.SubtaskNestingTooDeep as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Subtasks cannot themselves have a parent",
        ) from exc


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    try:
        return await task_service.update_task(db, current_user, task_id, data)
    except task_service.TaskNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await task_service.delete_task(db, current_user, task_id)
    except task_service.TaskNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc


@router.patch("/{task_id}/complete", response_model=TaskCompleteResponse)
async def complete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskCompleteResponse:
    try:
        result = await task_service.complete_task(db, current_user, task_id)
    except task_service.TaskNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    return TaskCompleteResponse(
        task=TaskOut.model_validate(result.task),
        xp_delta=result.xp_delta,
        progress=LevelProgressOut.model_validate(result.progress),
        newly_earned_achievements=[
            _to_achievement_out(a) for a in result.newly_earned_achievements
        ],
    )


@router.patch("/{task_id}/uncomplete", response_model=TaskCompleteResponse)
async def uncomplete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskCompleteResponse:
    try:
        result = await task_service.uncomplete_task(db, current_user, task_id)
    except task_service.TaskNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    return TaskCompleteResponse(
        task=TaskOut.model_validate(result.task),
        xp_delta=result.xp_delta,
        progress=LevelProgressOut.model_validate(result.progress),
    )
