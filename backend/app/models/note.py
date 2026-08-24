"""`Note`, the `note_tags` join table, and `note_task_links`.

`Note.search_vector` is a Postgres `GENERATED ALWAYS AS ... STORED` tsvector
column — the database maintains it, never the ORM. It's mapped read-only here
(never assigned in Python) purely so `NoteService` can filter/order on it; see
the migration for the raw-SQL `ALTER TABLE` that actually creates it, and
`alembic/env.py`'s `include_object` filter that keeps autogenerate from
fighting over it.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Computed, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_extensions import uuid7

from app.db.base import Base
from app.models.tag import Tag
from app.models.task import Task


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    archived_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    # `Computed(...)` here is purely to tell SQLAlchemy this column is
    # server-maintained (so it's excluded from INSERT/UPDATE statements) —
    # the actual DDL is hand-written raw SQL in the migration, since Alembic
    # autogenerate can't emit `GENERATED ALWAYS AS ... STORED` itself. Keep
    # this expression in sync with the migration's.
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(body_md, '')), 'B')",
            persisted=True,
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tags: Mapped[list[Tag]] = relationship(secondary="note_tags", lazy="selectin")
    linked_tasks: Mapped[list[Task]] = relationship(secondary="note_task_links", lazy="selectin")


class NoteTag(Base):
    __tablename__ = "note_tags"

    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class NoteTaskLink(Base):
    __tablename__ = "note_task_links"

    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
