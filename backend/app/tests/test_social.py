"""Leaderboard + activity feed tests. XP is always earned through the real
API (task create -> complete), never by inserting `XPEvent` rows by hand, so
these tests prove the real path works end to end.

Note: completing a user's *first* task also fires the `first_blood`
achievement (+100 XP, see `test_tasks.py`), so every fresh user who
completes exactly one task lands at `task_xp_value + 100` total. Tests that
need exact ties or exact totals account for that constant.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User
from app.tests.conftest import TestSessionLocal

FIRST_BLOOD_BONUS = 100


async def _earn_xp(client: AsyncClient, xp_value: int) -> None:
    created = await client.post(
        "/api/v1/tasks", json={"title": "Quest", "priority": "later", "xp_value": xp_value}
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    completed = await client.patch(f"/api/v1/tasks/{task_id}/complete")
    assert completed.status_code == 200


async def _set_inactive(handle: str) -> None:
    async with TestSessionLocal() as db:
        user = (await db.execute(select(User).where(User.handle == handle))).scalar_one()
        user.is_active = False
        await db.commit()


async def test_empty_leaderboard_when_nobody_has_xp(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/social/leaderboard")
    assert response.status_code == 200
    body = response.json()
    assert body["entries"] == []
    assert body["total"] == 0
    assert body["me"]["rank"] is None


async def test_three_users_ordered_by_xp(
    make_client: Callable[..., Awaitable[AsyncClient]],
) -> None:
    p1 = await make_client("racer1")
    p2 = await make_client("racer2")
    p3 = await make_client("racer3")
    await _earn_xp(p1, 300)
    await _earn_xp(p2, 200)
    await _earn_xp(p3, 100)

    response = await p1.get("/api/v1/social/leaderboard")
    entries = response.json()["entries"]
    assert [e["id"] for e in entries] == ["racer1", "racer2", "racer3"]
    assert [e["rank"] for e in entries] == [1, 2, 3]


async def test_ties_give_standard_competition_ranking(
    make_client: Callable[..., Awaitable[AsyncClient]],
) -> None:
    """RANK(), not DENSE_RANK(): equal XP -> 1, 1, 3 — never 1, 2, 3 and never 1, 1, 2."""
    p1 = await make_client("tiea")
    p2 = await make_client("tieb")
    p3 = await make_client("tiec")
    await _earn_xp(p1, 200)
    await _earn_xp(p2, 200)
    await _earn_xp(p3, 50)

    response = await p1.get("/api/v1/social/leaderboard")
    entries = response.json()["entries"]
    ranks = {e["id"]: e["rank"] for e in entries}
    assert ranks["tiea"] == 1
    assert ranks["tieb"] == 1
    assert ranks["tiec"] == 3


async def test_user_with_no_preferences_row_still_appears(auth_client: AsyncClient) -> None:
    """The outerjoin regression test — prefs rows only exist after a first
    *write*, so an inner join would silently hide every user who never
    opened Settings."""
    await _earn_xp(auth_client, 100)
    response = await auth_client.get("/api/v1/social/leaderboard")
    handles = [e["id"] for e in response.json()["entries"]]
    assert "player1" in handles


async def test_opting_out_removes_user_from_leaderboard_and_feed(
    auth_client: AsyncClient,
) -> None:
    await _earn_xp(auth_client, 150)
    patched = await auth_client.patch(
        "/api/v1/me/preferences", json={"leaderboard_opt_in": False}
    )
    assert patched.status_code == 200

    board = await auth_client.get("/api/v1/social/leaderboard")
    assert board.json()["entries"] == []

    feed = await auth_client.get("/api/v1/social/feed")
    assert feed.json()["items"] == []


async def test_inactive_user_excluded_from_both(
    make_client: Callable[..., Awaitable[AsyncClient]],
) -> None:
    """`get_current_user` already 401s an inactive user's own requests, so
    visibility is checked from a second, still-active observer."""
    target = await make_client("benched")
    observer = await make_client("observer1")
    await _earn_xp(target, 150)
    await _set_inactive("benched")

    board = await observer.get("/api/v1/social/leaderboard")
    handles = [e["id"] for e in board.json()["entries"]]
    assert "benched" not in handles

    feed = await observer.get("/api/v1/social/feed")
    feed_handles = {item["actor"]["handle"] for item in feed.json()["items"]}
    assert "benched" not in feed_handles


async def test_me_block_reports_correct_rank_and_none_when_opted_out(
    make_client: Callable[..., Awaitable[AsyncClient]],
) -> None:
    p1 = await make_client("midtable1")
    p2 = await make_client("midtable2")
    p3 = await make_client("midtable3")
    await _earn_xp(p1, 300)
    await _earn_xp(p2, 200)
    await _earn_xp(p3, 100)

    response = await p2.get("/api/v1/social/leaderboard")
    me = response.json()["me"]
    assert me["rank"] == 2
    assert me["opted_in"] is True

    await p2.patch("/api/v1/me/preferences", json={"leaderboard_opt_in": False})
    response2 = await p2.get("/api/v1/social/leaderboard")
    me2 = response2.json()["me"]
    assert me2["rank"] is None
    assert me2["opted_in"] is False


async def test_pagination_bounds(
    make_client: Callable[..., Awaitable[AsyncClient]],
) -> None:
    for i, xp_value in enumerate([400, 300, 200, 100]):
        client = await make_client(f"pager{i}")
        await _earn_xp(client, xp_value)

    page = await make_client("pageviewer")
    response = await page.get("/api/v1/social/leaderboard", params={"limit": 2, "offset": 2})
    entries = response.json()["entries"]
    assert [e["rank"] for e in entries] == [3, 4]

    too_big = await page.get("/api/v1/social/leaderboard", params={"limit": 101})
    assert too_big.status_code == 422

    too_far = await page.get("/api/v1/social/leaderboard", params={"offset": 1001})
    assert too_far.status_code == 422


async def test_feed_ordering_and_cursor_have_no_overlap(
    make_client: Callable[..., Awaitable[AsyncClient]],
) -> None:
    client = await make_client("feeduser")
    for i in range(3):
        await _earn_xp(client, 50 + i)

    page1 = await client.get("/api/v1/social/feed", params={"limit": 2})
    body1 = page1.json()
    assert len(body1["items"]) == 2
    assert body1["next_before"] is not None

    page2 = await client.get(
        "/api/v1/social/feed", params={"limit": 2, "before": body1["next_before"]}
    )
    body2 = page2.json()
    ids1 = {item["id"] for item in body1["items"]}
    ids2 = {item["id"] for item in body2["items"]}
    assert ids1.isdisjoint(ids2)
    assert body2["next_before"] is None


async def test_feed_excludes_reversals(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/habits", json={"name": "Morning Run", "cadence": "daily", "xp_value": 100}
    )
    habit_id = created.json()["id"]
    logged = await auth_client.post(f"/api/v1/habits/{habit_id}/log", json={})
    logged_for = logged.json()["log"]["logged_for"]

    unlogged = await auth_client.delete(f"/api/v1/habits/{habit_id}/log/{logged_for}")
    assert unlogged.status_code == 200
    assert unlogged.json()["xp_delta"] < 0

    feed = await auth_client.get("/api/v1/social/feed")
    xp_values = [item["awarded_xp"] for item in feed.json()["items"]]
    assert all(v > 0 for v in xp_values)
    assert 100 in xp_values


async def test_feed_item_has_no_source_id_and_no_title(auth_client: AsyncClient) -> None:
    """Privacy contract test — assert the keys are *absent*, not empty."""
    await _earn_xp(auth_client, 100)
    feed = await auth_client.get("/api/v1/social/feed")
    item = feed.json()["items"][0]
    assert "source_id" not in item
    assert "title" not in item
    assert set(item.keys()) == {
        "id",
        "actor",
        "source_type",
        "awarded_xp",
        "skill_branch",
        "created_at",
    }
    assert set(item["actor"].keys()) == {"handle", "display_name", "title", "avatar_url"}


async def test_feed_spans_users(
    make_client: Callable[..., Awaitable[AsyncClient]],
) -> None:
    p1 = await make_client("spanner1")
    p2 = await make_client("spanner2")
    await _earn_xp(p1, 100)
    await _earn_xp(p2, 100)

    feed = await p1.get("/api/v1/social/feed")
    handles = {item["actor"]["handle"] for item in feed.json()["items"]}
    assert {"spanner1", "spanner2"}.issubset(handles)


async def test_unauthenticated_access_is_rejected(client: AsyncClient) -> None:
    board = await client.get("/api/v1/social/leaderboard")
    assert board.status_code == 401
    feed = await client.get("/api/v1/social/feed")
    assert feed.status_code == 401


async def test_opted_out_user_can_still_read_the_leaderboard(
    make_client: Callable[..., Awaitable[AsyncClient]],
) -> None:
    p1 = await make_client("reader1")
    p2 = await make_client("reader2")
    await _earn_xp(p1, 100)
    await _earn_xp(p2, 100)
    await p1.patch("/api/v1/me/preferences", json={"leaderboard_opt_in": False})

    response = await p1.get("/api/v1/social/leaderboard")
    assert response.status_code == 200
    handles = [e["id"] for e in response.json()["entries"]]
    assert "reader2" in handles
    assert "reader1" not in handles
