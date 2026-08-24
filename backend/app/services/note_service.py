"""Note domain service — CRUD, full-text search, tag resolution, server-side
checkbox toggling, and note<->task linking. Routers stay thin and translate
the exceptions here into HTTP responses. Notes award no XP (D18) — there is
no `xp.award()` call anywhere in this module, deliberately.

`Note.tags` and `Note.linked_tasks` are mapped `lazy="selectin"` (see
`models/note.py`), so every query here is eagerly loaded automatically — no
explicit `.options(selectinload(...))` needed, and no per-note follow-up
query on `GET /notes`.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note, NoteTaskLink
from app.models.tag import Tag
from app.models.task import Task
from app.models.user import User
from app.schemas.notes import NoteCreate, NoteUpdate
from app.services.gamification import achievements

CHECKBOX_LINE_RE = re.compile(r"^(\s*[-*+]\s+)\[([ xX])\](\s.*)?$")
_MD_STRIP_RE = re.compile(r"[#*`_>\-\[\]()!]")
_ADVANCED_FTS_SYNTAX_RE = re.compile(r'["\-]')
_WORD_RE = re.compile(r"\w+", re.UNICODE)


class NoteNotFound(Exception):
    pass


class NotACheckboxLine(Exception):
    pass


class LineIndexOutOfRange(Exception):
    pass


class TaskNotFound(Exception):
    pass


@dataclass(frozen=True)
class NoteCreateResult:
    note: Note
    newly_earned_achievements: list[achievements.EarnedAchievement] = field(default_factory=list)


async def _get_owned_note(db: AsyncSession, user: User, note_id: uuid.UUID) -> Note:
    note = await db.get(Note, note_id)
    if note is None or note.user_id != user.id:
        raise NoteNotFound
    return note


async def _resolve_tags(db: AsyncSession, user: User, slugs: list[str]) -> list[Tag]:
    """Resolve tag slugs to `Tag` rows, creating any that don't exist yet for
    this user. Notes and tasks share the same `tags` table, but there's no
    existing "resolve or create by slug" helper in `tag_service` (tasks are
    never attached to tags this way) — this is the first caller of the
    pattern, kept local rather than promoted to `tag_service` until a second
    caller needs it.
    """
    if not slugs:
        return []
    existing = {
        t.slug: t
        for t in await db.scalars(select(Tag).where(Tag.user_id == user.id, Tag.slug.in_(slugs)))
    }
    tags: list[Tag] = []
    for slug in slugs:
        tag = existing.get(slug)
        if tag is None:
            tag = Tag(user_id=user.id, name=slug.replace("-", " ").title(), slug=slug)
            db.add(tag)
            existing[slug] = tag
        tags.append(tag)
    return tags


def _build_tsquery(q: str) -> ColumnElement[Any]:
    """`websearch_to_tsquery` only ever matches whole (stemmed) words, so
    typing `zeph` never finds a note containing "zephyrtoken" — no good for
    search-as-you-type. For a plain query (no quoted phrases or `-exclusion`
    syntax) build a prefix-matching `to_tsquery` instead, `word:*` per token,
    ANDed together, so partial words match. Queries that use websearch's
    advanced syntax fall back to `websearch_to_tsquery` so phrases and
    exclusions keep working. The prefix terms are built from `\\w+`-extracted
    tokens only, so the assembled `to_tsquery` string is always
    syntactically valid — never raises on arbitrary user input.

    The prefix query is parsed with the `simple` config, not `english`, even
    though `search_vector` itself is built with `english` (see the
    migration) — `@@` matching is purely lexical against whatever lexemes
    are already stored, so the query-side config doesn't need to match.
    Using `english` here was the bug: postgres's English dictionary treats
    short fragments like "he" or "no" as *stopwords* and drops them from a
    `to_tsquery` call entirely, prefix marker and all, so a 2-letter
    substring query would return nothing while 1 and 3 letters worked —
    exactly the "flickers on alternating characters while typing" symptom.
    `simple` has no stopword list and does no stemming, so every typed
    fragment reaches the query.
    """
    if _ADVANCED_FTS_SYNTAX_RE.search(q):
        return func.websearch_to_tsquery("english", q)
    words = _WORD_RE.findall(q)
    if not words:
        return func.websearch_to_tsquery("english", q)
    prefix_expr = " & ".join(f"{word}:*" for word in words)
    return func.to_tsquery("simple", prefix_expr)


def make_excerpt(body_md: str, length: int = 140) -> str:
    stripped = _MD_STRIP_RE.sub("", body_md).replace("\n", " ")
    stripped = " ".join(stripped.split())
    return stripped[:length]


async def list_notes(
    db: AsyncSession,
    user: User,
    *,
    q: str | None = None,
    tag_slugs: list[str] | None = None,
    include_archived: bool = False,
    limit: int = 50,
) -> list[Note]:
    stmt = select(Note).where(Note.user_id == user.id)
    if not include_archived:
        stmt = stmt.where(Note.archived_at.is_(None))

    q = (q or "").strip()
    if q:
        tsquery = _build_tsquery(q)
        stmt = stmt.where(Note.search_vector.op("@@")(tsquery))
        stmt = stmt.order_by(
            func.ts_rank(Note.search_vector, tsquery).desc(), Note.updated_at.desc()
        )
    else:
        stmt = stmt.order_by(Note.is_pinned.desc(), Note.updated_at.desc())

    if tag_slugs:
        for slug in tag_slugs:
            stmt = stmt.where(Note.tags.any(Tag.slug == slug))

    stmt = stmt.limit(limit)
    return list((await db.scalars(stmt)).unique())


async def get_note(db: AsyncSession, user: User, note_id: uuid.UUID) -> Note:
    return await _get_owned_note(db, user, note_id)


async def create_note(db: AsyncSession, user: User, data: NoteCreate) -> NoteCreateResult:
    tags = await _resolve_tags(db, user, data.tag_slugs)
    note = Note(user_id=user.id, title=data.title, body_md=data.body_md, is_pinned=data.is_pinned)
    note.tags = tags
    db.add(note)
    await db.flush()

    for task_id in data.task_ids:
        task = await db.get(Task, task_id)
        if task is None or task.user_id != user.id:
            raise TaskNotFound
        db.add(NoteTaskLink(note_id=note.id, task_id=task_id))

    # Notes award no XP directly (D18) — but creating one can still satisfy
    # the `archivist` achievement, which *does* award XP through the normal
    # ACHIEVEMENT-sourced ledger path, not a NOTE_CREATE source type.
    newly_earned = await achievements.evaluate(db, user)

    await db.commit()
    await db.refresh(note)
    return NoteCreateResult(note=note, newly_earned_achievements=newly_earned)


async def update_note(db: AsyncSession, user: User, note_id: uuid.UUID, data: NoteUpdate) -> Note:
    note = await _get_owned_note(db, user, note_id)
    updates = data.model_dump(exclude_unset=True, exclude={"tag_slugs"})
    for field_name, value in updates.items():
        setattr(note, field_name, value)

    if data.tag_slugs is not None:
        note.tags = await _resolve_tags(db, user, data.tag_slugs)

    await db.commit()
    await db.refresh(note)
    return note


async def archive_note(db: AsyncSession, user: User, note_id: uuid.UUID) -> None:
    note = await _get_owned_note(db, user, note_id)
    note.archived_at = datetime.now(UTC)
    await db.commit()


async def link_task(db: AsyncSession, user: User, note_id: uuid.UUID, task_id: uuid.UUID) -> Note:
    note = await _get_owned_note(db, user, note_id)
    task = await db.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise TaskNotFound
    existing = await db.scalar(
        select(NoteTaskLink).where(NoteTaskLink.note_id == note.id, NoteTaskLink.task_id == task_id)
    )
    if existing is None:
        db.add(NoteTaskLink(note_id=note.id, task_id=task_id))
        await db.commit()
        await db.refresh(note)
    return note


async def unlink_task(db: AsyncSession, user: User, note_id: uuid.UUID, task_id: uuid.UUID) -> Note:
    note = await _get_owned_note(db, user, note_id)
    link = await db.scalar(
        select(NoteTaskLink).where(NoteTaskLink.note_id == note.id, NoteTaskLink.task_id == task_id)
    )
    if link is not None:
        await db.delete(link)
        await db.commit()
        await db.refresh(note)
    return note


async def toggle_checkbox(
    db: AsyncSession, user: User, note_id: uuid.UUID, line_index: int, checked: bool
) -> Note:
    note = await _get_owned_note(db, user, note_id)
    lines = note.body_md.split("\n")
    if line_index < 0 or line_index >= len(lines):
        raise LineIndexOutOfRange

    line = lines[line_index]
    match = CHECKBOX_LINE_RE.match(line)
    if match is None:
        raise NotACheckboxLine

    prefix, rest = match.group(1), match.group(3) or ""
    lines[line_index] = f"{prefix}[{'x' if checked else ' '}]{rest}"
    note.body_md = "\n".join(lines)

    await db.commit()
    await db.refresh(note)
    return note
