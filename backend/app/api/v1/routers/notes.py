"""Note endpoints: CRUD, full-text search, server-side checkbox toggling, and
note<->task linking.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.note import Note
from app.models.user import User
from app.schemas.achievements import AchievementOut
from app.schemas.notes import (
    CheckboxToggleRequest,
    LinkedTaskOut,
    NoteCreate,
    NoteOut,
    NoteSummaryOut,
    NoteUpdate,
)
from app.schemas.tags import TagOut
from app.services import note_service
from app.services.gamification.achievements import EarnedAchievement

router = APIRouter(prefix="/notes", tags=["notes"])


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


def _to_summary(note: Note) -> NoteSummaryOut:
    return NoteSummaryOut(
        id=note.id,
        title=note.title,
        excerpt=note_service.make_excerpt(note.body_md),
        is_pinned=note.is_pinned,
        updated_at=note.updated_at,
        tags=[TagOut.model_validate(t) for t in note.tags],
    )


def _to_out(
    note: Note, newly_earned: list[EarnedAchievement] | None = None
) -> NoteOut:
    return NoteOut(
        id=note.id,
        title=note.title,
        body_md=note.body_md,
        is_pinned=note.is_pinned,
        archived_at=note.archived_at,
        tags=[TagOut.model_validate(t) for t in note.tags],
        linked_tasks=[LinkedTaskOut.model_validate(t) for t in note.linked_tasks],
        size_bytes=len(note.body_md.encode()),
        created_at=note.created_at,
        updated_at=note.updated_at,
        newly_earned_achievements=[_to_achievement_out(a) for a in (newly_earned or [])],
    )


@router.get("", response_model=list[NoteSummaryOut])
async def list_notes(
    q: str | None = None,
    tag: list[str] = Query(default=[]),
    include_archived: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NoteSummaryOut]:
    notes = await note_service.list_notes(
        db, current_user, q=q, tag_slugs=tag, include_archived=include_archived, limit=limit
    )
    return [_to_summary(n) for n in notes]


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteOut:
    try:
        result = await note_service.create_note(db, current_user, data)
    except note_service.TaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Linked task not found"
        ) from exc
    return _to_out(result.note, result.newly_earned_achievements)


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteOut:
    try:
        note = await note_service.get_note(db, current_user, note_id)
    except note_service.NoteNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found") from exc
    return _to_out(note)


@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: uuid.UUID,
    data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteOut:
    try:
        note = await note_service.update_note(db, current_user, note_id, data)
    except note_service.NoteNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found") from exc
    return _to_out(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await note_service.archive_note(db, current_user, note_id)
    except note_service.NoteNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found") from exc


@router.patch("/{note_id}/checkbox", response_model=NoteOut)
async def toggle_checkbox(
    note_id: uuid.UUID,
    data: CheckboxToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteOut:
    try:
        note = await note_service.toggle_checkbox(
            db, current_user, note_id, data.line_index, data.checked
        )
    except note_service.NoteNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found") from exc
    except note_service.LineIndexOutOfRange as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Line index out of range"
        ) from exc
    except note_service.NotACheckboxLine as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="That line is not a checkbox"
        ) from exc
    return _to_out(note)


@router.post("/{note_id}/tasks/{task_id}", response_model=NoteOut)
async def link_task(
    note_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteOut:
    try:
        note = await note_service.link_task(db, current_user, note_id, task_id)
    except note_service.NoteNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found") from exc
    except note_service.TaskNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    return _to_out(note)


@router.delete("/{note_id}/tasks/{task_id}", response_model=NoteOut)
async def unlink_task(
    note_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteOut:
    try:
        note = await note_service.unlink_task(db, current_user, note_id, task_id)
    except note_service.NoteNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found") from exc
    return _to_out(note)
