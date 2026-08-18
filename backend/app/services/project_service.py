"""Project domain service — plain CRUD plus soft-archive (never a hard
delete, since tasks may still reference an archived project)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.user import User
from app.schemas.projects import ProjectCreate, ProjectUpdate


class ProjectNotFound(Exception):
    pass


class ProjectSlugTaken(Exception):
    pass


async def _get_owned_project(db: AsyncSession, user: User, project_id: uuid.UUID) -> Project:
    project = await db.get(Project, project_id)
    if project is None or project.user_id != user.id:
        raise ProjectNotFound
    return project


async def list_projects(
    db: AsyncSession, user: User, *, include_archived: bool = False
) -> list[Project]:
    stmt = select(Project).where(Project.user_id == user.id).order_by(Project.position)
    if not include_archived:
        stmt = stmt.where(Project.archived_at.is_(None))
    return list(await db.scalars(stmt))


async def create_project(db: AsyncSession, user: User, data: ProjectCreate) -> Project:
    project = Project(user_id=user.id, **data.model_dump())
    db.add(project)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ProjectSlugTaken from exc
    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession, user: User, project_id: uuid.UUID, data: ProjectUpdate
) -> Project:
    project = await _get_owned_project(db, user, project_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ProjectSlugTaken from exc
    await db.refresh(project)
    return project


async def archive_project(db: AsyncSession, user: User, project_id: uuid.UUID) -> None:
    project = await _get_owned_project(db, user, project_id)
    project.archived_at = datetime.now(UTC)
    await db.commit()
