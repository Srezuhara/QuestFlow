"""Tag endpoints: CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tags import TagCreate, TagOut, TagUpdate
from app.services import tag_service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
async def list_tags(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[Tag]:
    return await tag_service.list_tags(db, current_user)


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tag:
    try:
        return await tag_service.create_tag(db, current_user, data)
    except tag_service.TagSlugTaken as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Tag slug already in use"
        ) from exc


@router.patch("/{tag_id}", response_model=TagOut)
async def update_tag(
    tag_id: uuid.UUID,
    data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tag:
    try:
        return await tag_service.update_tag(db, current_user, tag_id, data)
    except tag_service.TagNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found") from exc


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await tag_service.delete_tag(db, current_user, tag_id)
    except tag_service.TagNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found") from exc
