"""Tag domain service — plain CRUD."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.models.user import User
from app.schemas.tags import TagCreate, TagUpdate


class TagNotFound(Exception):
    pass


class TagSlugTaken(Exception):
    pass


async def _get_owned_tag(db: AsyncSession, user: User, tag_id: uuid.UUID) -> Tag:
    tag = await db.get(Tag, tag_id)
    if tag is None or tag.user_id != user.id:
        raise TagNotFound
    return tag


async def list_tags(db: AsyncSession, user: User) -> list[Tag]:
    return list(await db.scalars(select(Tag).where(Tag.user_id == user.id).order_by(Tag.name)))


async def create_tag(db: AsyncSession, user: User, data: TagCreate) -> Tag:
    tag = Tag(user_id=user.id, **data.model_dump())
    db.add(tag)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise TagSlugTaken from exc
    await db.refresh(tag)
    return tag


async def update_tag(db: AsyncSession, user: User, tag_id: uuid.UUID, data: TagUpdate) -> Tag:
    tag = await _get_owned_tag(db, user, tag_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, user: User, tag_id: uuid.UUID) -> None:
    tag = await _get_owned_tag(db, user, tag_id)
    await db.delete(tag)
    await db.commit()
