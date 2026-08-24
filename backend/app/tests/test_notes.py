"""Notes API tests: CRUD, full-text search, tag filtering, checkbox
toggling, note<->task linking, and the D18 "notes award no XP" invariant.
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import func, select

from app.models.gamification import XPEvent
from app.tests.conftest import TestSessionLocal


def _note_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"title": "Mission Brief", "body_md": "Some content."}
    payload.update(overrides)
    return payload


async def _xp_event_count() -> int:
    async with TestSessionLocal() as db:
        return (await db.scalar(select(func.count()).select_from(XPEvent))) or 0


async def test_create_then_get_note_computes_size_and_excerpt(auth_client: AsyncClient) -> None:
    body = "# Heading\n\nSome **bold** text with `code` and a [link](url)."
    created = await auth_client.post("/api/v1/notes", json=_note_payload(body_md=body))
    assert created.status_code == 201
    note_id = created.json()["id"]
    assert created.json()["size_bytes"] == len(body.encode())

    fetched = await auth_client.get(f"/api/v1/notes/{note_id}")
    assert fetched.status_code == 200
    fetched_body = fetched.json()
    assert fetched_body["size_bytes"] == len(body.encode())

    listed = await auth_client.get("/api/v1/notes")
    assert listed.status_code == 200
    summary = next(n for n in listed.json() if n["id"] == note_id)
    assert "#" not in summary["excerpt"]
    assert "**" not in summary["excerpt"]
    assert len(summary["excerpt"]) <= 140


async def test_fts_matches_title_and_body_and_ranks_title_above_body(
    auth_client: AsyncClient,
) -> None:
    await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="Zephyr Protocol", body_md="unrelated content")
    )
    await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="Unrelated", body_md="mentions zephyr here")
    )
    await auth_client.post("/api/v1/notes", json=_note_payload(title="Nothing", body_md="matches"))

    results = await auth_client.get("/api/v1/notes", params={"q": "zephyr"})
    assert results.status_code == 200
    titles = [n["title"] for n in results.json()]
    assert "Zephyr Protocol" in titles
    assert "Unrelated" in titles
    assert "Nothing" not in titles
    # Title match ranks above body-only match.
    assert titles.index("Zephyr Protocol") < titles.index("Unrelated")


async def test_fts_quoted_phrase_and_exclusion(auth_client: AsyncClient) -> None:
    await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="Alpha Bravo", body_md="content one")
    )
    await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="Alpha Charlie", body_md="content two")
    )

    phrase = await auth_client.get("/api/v1/notes", params={"q": '"alpha bravo"'})
    assert phrase.status_code == 200
    assert [n["title"] for n in phrase.json()] == ["Alpha Bravo"]

    excluded = await auth_client.get("/api/v1/notes", params={"q": "alpha -charlie"})
    assert excluded.status_code == 200
    titles = [n["title"] for n in excluded.json()]
    assert "Alpha Bravo" in titles
    assert "Alpha Charlie" not in titles


async def test_fts_partial_word_matches_as_prefix(auth_client: AsyncClient) -> None:
    await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="Zephyrtoken Protocol", body_md="irrelevant")
    )
    await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="Something Else", body_md="mentions zephyrtoken")
    )
    await auth_client.post("/api/v1/notes", json=_note_payload(title="Nothing", body_md="matches"))

    results = await auth_client.get("/api/v1/notes", params={"q": "zeph"})
    assert results.status_code == 200
    titles = [n["title"] for n in results.json()]
    assert "Zephyrtoken Protocol" in titles
    assert "Something Else" in titles
    assert "Nothing" not in titles


async def test_fts_partial_word_matches_short_stopword_like_prefixes(
    auth_client: AsyncClient,
) -> None:
    """`to_tsquery('english', 'he:*')` drops "he" as a stopword and returns
    an empty query, so a naive prefix search finds nothing for the 2-letter
    prefix while 1 and 3 letters both work — the exact "flickers while
    typing" bug reported against titles like "Helllo" and "Nope". The prefix
    query must use the `simple` config precisely to avoid this."""
    await auth_client.post("/api/v1/notes", json=_note_payload(title="Helllo", body_md="content"))
    await auth_client.post("/api/v1/notes", json=_note_payload(title="Nope", body_md="content"))

    for q, expected in [("h", "Helllo"), ("he", "Helllo"), ("hel", "Helllo")]:
        results = await auth_client.get("/api/v1/notes", params={"q": q})
        assert results.status_code == 200
        titles = [n["title"] for n in results.json()]
        assert expected in titles, f"q={q!r} should match {expected!r}, got {titles}"

    for q, expected in [("n", "Nope"), ("no", "Nope"), ("nop", "Nope")]:
        results = await auth_client.get("/api/v1/notes", params={"q": q})
        assert results.status_code == 200
        titles = [n["title"] for n in results.json()]
        assert expected in titles, f"q={q!r} should match {expected!r}, got {titles}"


async def test_fts_partial_word_multi_term_requires_all_prefixes(auth_client: AsyncClient) -> None:
    await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="Alpha Bravo", body_md="content")
    )
    await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="Alpha Only", body_md="content")
    )

    results = await auth_client.get("/api/v1/notes", params={"q": "alp bra"})
    assert results.status_code == 200
    assert [n["title"] for n in results.json()] == ["Alpha Bravo"]


async def test_fts_pathological_input_does_not_500(auth_client: AsyncClient) -> None:
    await auth_client.post("/api/v1/notes", json=_note_payload())
    response = await auth_client.get("/api/v1/notes", params={"q": "a & | ! ("})
    assert response.status_code == 200


async def test_tag_filter_requires_all_tags(auth_client: AsyncClient) -> None:
    both = await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="Both", tag_slugs=["red", "blue"])
    )
    assert both.status_code == 201
    only_red = await auth_client.post(
        "/api/v1/notes", json=_note_payload(title="OnlyRed", tag_slugs=["red"])
    )
    assert only_red.status_code == 201

    filtered = await auth_client.get("/api/v1/notes", params={"tag": ["red", "blue"]})
    assert filtered.status_code == 200
    titles = [n["title"] for n in filtered.json()]
    assert titles == ["Both"]


async def test_get_notes_with_many_tagged_notes_is_bounded(auth_client: AsyncClient) -> None:
    for i in range(10):
        resp = await auth_client.post(
            "/api/v1/notes",
            json=_note_payload(title=f"Note {i}", tag_slugs=["one", "two", "three"]),
        )
        assert resp.status_code == 201

    listed = await auth_client.get("/api/v1/notes")
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 10
    for note in body:
        assert len(note["tags"]) == 3


async def test_checkbox_toggle_flips_and_preserves_line(auth_client: AsyncClient) -> None:
    body = "## CORE OBJECTIVES\n- [ ] first\n  - [ ] nested item\n* [ ] star bullet\nplain line"
    created = await auth_client.post("/api/v1/notes", json=_note_payload(body_md=body))
    note_id = created.json()["id"]

    toggled = await auth_client.patch(
        f"/api/v1/notes/{note_id}/checkbox", json={"line_index": 2, "checked": True}
    )
    assert toggled.status_code == 200
    lines = toggled.json()["body_md"].split("\n")
    assert lines[2] == "  - [x] nested item"
    assert lines[1] == "- [ ] first"  # untouched
    assert lines[3] == "* [ ] star bullet"  # untouched

    back = await auth_client.patch(
        f"/api/v1/notes/{note_id}/checkbox", json={"line_index": 2, "checked": False}
    )
    assert back.status_code == 200
    assert back.json()["body_md"].split("\n")[2] == "  - [ ] nested item"


async def test_checkbox_toggle_star_bullet(auth_client: AsyncClient) -> None:
    body = "* [ ] star bullet"
    created = await auth_client.post("/api/v1/notes", json=_note_payload(body_md=body))
    note_id = created.json()["id"]
    toggled = await auth_client.patch(
        f"/api/v1/notes/{note_id}/checkbox", json={"line_index": 0, "checked": True}
    )
    assert toggled.status_code == 200
    assert toggled.json()["body_md"] == "* [x] star bullet"


async def test_checkbox_toggle_non_checkbox_line_conflicts(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/notes", json=_note_payload(body_md="plain text"))
    note_id = created.json()["id"]
    response = await auth_client.patch(
        f"/api/v1/notes/{note_id}/checkbox", json={"line_index": 0, "checked": True}
    )
    assert response.status_code == 409


async def test_checkbox_toggle_out_of_range_is_422(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/notes", json=_note_payload(body_md="- [ ] one line"))
    note_id = created.json()["id"]
    response = await auth_client.patch(
        f"/api/v1/notes/{note_id}/checkbox", json={"line_index": 99, "checked": True}
    )
    assert response.status_code == 422


async def test_checkbox_toggle_preserves_crlf_body_byte_for_byte(auth_client: AsyncClient) -> None:
    body = "line one\r\n- [ ] task\r\nline three"
    created = await auth_client.post("/api/v1/notes", json=_note_payload(body_md=body))
    note_id = created.json()["id"]

    toggled = await auth_client.patch(
        f"/api/v1/notes/{note_id}/checkbox", json={"line_index": 1, "checked": True}
    )
    assert toggled.status_code == 200
    new_body = toggled.json()["body_md"]
    expected = "line one\r\n- [x] task\r\nline three"
    assert new_body == expected


async def test_link_and_unlink_task(auth_client: AsyncClient) -> None:
    task = await auth_client.post("/api/v1/tasks", json={"title": "Do the thing"})
    assert task.status_code == 201
    task_id = task.json()["id"]

    note = await auth_client.post("/api/v1/notes", json=_note_payload())
    note_id = note.json()["id"]

    linked = await auth_client.post(f"/api/v1/notes/{note_id}/tasks/{task_id}")
    assert linked.status_code == 200
    assert [t["id"] for t in linked.json()["linked_tasks"]] == [task_id]

    await auth_client.delete(f"/api/v1/tasks/{task_id}")
    fetched = await auth_client.get(f"/api/v1/notes/{note_id}")
    assert fetched.status_code == 200
    assert fetched.json()["linked_tasks"] == []


async def test_cross_user_note_is_not_visible(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner2@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "owner2",
            "display_name": "Owner",
            "timezone": "UTC",
        },
    )
    created = await client.post("/api/v1/notes", json=_note_payload(body_md="- [ ] item"))
    note_id = created.json()["id"]
    task = await client.post("/api/v1/tasks", json={"title": "Owner task"})
    task_id = task.json()["id"]
    await client.post("/api/v1/auth/logout")

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder2@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "intruder2",
            "display_name": "Intruder",
            "timezone": "UTC",
        },
    )
    assert (await client.get(f"/api/v1/notes/{note_id}")).status_code == 404
    assert (
        await client.patch(f"/api/v1/notes/{note_id}", json={"title": "Hacked"})
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/notes/{note_id}/checkbox", json={"line_index": 0, "checked": True}
        )
    ).status_code == 404
    assert (await client.post(f"/api/v1/notes/{note_id}/tasks/{task_id}")).status_code == 404


async def test_archive_excludes_from_default_list(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/notes", json=_note_payload())
    note_id = created.json()["id"]

    archived = await auth_client.delete(f"/api/v1/notes/{note_id}")
    assert archived.status_code == 204

    default_list = await auth_client.get("/api/v1/notes")
    assert note_id not in [n["id"] for n in default_list.json()]

    with_archived = await auth_client.get("/api/v1/notes", params={"include_archived": True})
    assert note_id in [n["id"] for n in with_archived.json()]


async def test_note_operations_award_no_xp(auth_client: AsyncClient) -> None:
    before = await _xp_event_count()

    created = await auth_client.post(
        "/api/v1/notes", json=_note_payload(body_md="- [ ] task", tag_slugs=["focus"])
    )
    note_id = created.json()["id"]
    await auth_client.patch(f"/api/v1/notes/{note_id}", json={"title": "Renamed"})
    await auth_client.patch(
        f"/api/v1/notes/{note_id}/checkbox", json={"line_index": 0, "checked": True}
    )
    await auth_client.delete(f"/api/v1/notes/{note_id}")

    after = await _xp_event_count()
    assert after == before
