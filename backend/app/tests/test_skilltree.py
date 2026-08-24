"""Skill-tree API tests: state derivation (D13), the unlock gate, the
`newly_available` diff, and the bounded query count of `GET /me/skill-tree`.
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import event, select

from app.models.gamification import XPEvent
from app.models.user import User
from app.services.gamification import skilltree
from app.tests.conftest import TestSessionLocal as AsyncSessionLocal
from app.tests.conftest import test_engine


async def _me_id(client: AsyncClient) -> uuid.UUID:
    resp = await client.get("/api/v1/auth/me")
    return uuid.UUID(resp.json()["id"])


async def _create_focus_project(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "Focus Track", "slug": "focus-track", "skill_branch": "focus"},
    )
    assert resp.status_code == 201
    project_id: str = resp.json()["id"]
    return project_id


async def _complete_task_worth(client: AsyncClient, project_id: str | None, xp_value: int) -> None:
    created = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Grind",
            "priority": "later",
            "xp_value": xp_value,
            "project_id": project_id,
        },
    )
    task_id = created.json()["id"]
    resp = await client.patch(f"/api/v1/tasks/{task_id}/complete")
    assert resp.status_code == 200


async def _unlock_core_nexus(client: AsyncClient) -> None:
    # core_nexus has no prerequisites and costs 0 XP, so it's always
    # AVAILABLE — but D13's rule still requires an actual unlock row before
    # it counts as UNLOCKED for downstream prerequisite checks (see the
    # browser-verification flow in §6.14, which unlocks it before earning
    # branch XP).
    resp = await client.post("/api/v1/skill-nodes/core_nexus/unlock")
    assert resp.status_code == 200


async def test_fresh_user_has_core_nexus_available_and_tier_one_locked(
    auth_client: AsyncClient,
) -> None:
    tree = await auth_client.get("/api/v1/me/skill-tree")
    assert tree.status_code == 200
    body = tree.json()

    assert all(xp == 0 for xp in body["branch_xp"].values())
    nodes = {n["code"]: n for n in body["nodes"]}
    assert nodes["core_nexus"]["state"] == "available"
    for code in ("deep_work", "hydration", "early_rise", "daily_reading", "expense_log"):
        assert nodes[code]["state"] == "locked"


async def test_earning_branch_xp_makes_tier_one_available_but_not_tier_two(
    auth_client: AsyncClient,
) -> None:
    await _unlock_core_nexus(auth_client)
    project_id = await _create_focus_project(auth_client)
    await _complete_task_worth(auth_client, project_id, 500)

    tree = await auth_client.get("/api/v1/me/skill-tree")
    nodes = {n["code"]: n for n in tree.json()["nodes"]}
    assert tree.json()["branch_xp"]["focus"] == 500
    assert nodes["deep_work"]["state"] == "available"
    assert nodes["time_block"]["state"] == "locked"


async def test_unlock_marks_node_but_time_block_not_newly_available_at_500_xp(
    auth_client: AsyncClient,
) -> None:
    await _unlock_core_nexus(auth_client)
    project_id = await _create_focus_project(auth_client)
    await _complete_task_worth(auth_client, project_id, 500)

    resp = await auth_client.post("/api/v1/skill-nodes/deep_work/unlock")
    assert resp.status_code == 200
    body = resp.json()
    assert body["node"]["code"] == "deep_work"
    assert body["node"]["state"] == "unlocked"
    # time_block's prerequisite (deep_work) is now met, but its 2000 XP
    # threshold isn't — it must NOT be listed as newly available. This
    # catches conflating "prereq met" with "available".
    assert "time_block" not in body["newly_available"]

    tree = await auth_client.get("/api/v1/me/skill-tree")
    nodes = {n["code"]: n for n in tree.json()["nodes"]}
    assert nodes["deep_work"]["state"] == "unlocked"
    assert nodes["time_block"]["state"] == "locked"


async def test_unlocking_twice_is_rejected_with_no_second_xp_event(
    auth_client: AsyncClient,
) -> None:
    await _unlock_core_nexus(auth_client)
    project_id = await _create_focus_project(auth_client)
    await _complete_task_worth(auth_client, project_id, 500)
    await auth_client.post("/api/v1/skill-nodes/deep_work/unlock")

    second = await auth_client.post("/api/v1/skill-nodes/deep_work/unlock")
    assert second.status_code == 409

    user_id = await _me_id(auth_client)
    async with AsyncSessionLocal() as db:
        rows = list(
            await db.scalars(
                select(XPEvent).where(
                    XPEvent.user_id == user_id, XPEvent.idempotency_key.like("skill_unlock:%")
                )
            )
        )
    # One event for core_nexus's own unlock, one for deep_work's first
    # (successful) unlock — the second, rejected, attempt adds no third.
    assert len(rows) == 2


async def test_unlock_blocked_when_prerequisite_missing_even_if_xp_suffices(
    auth_client: AsyncClient,
) -> None:
    project_id = await _create_focus_project(auth_client)
    # Clear tier-2's XP threshold (2000) without ever unlocking deep_work.
    await _complete_task_worth(auth_client, project_id, 2000)

    resp = await auth_client.post("/api/v1/skill-nodes/time_block/unlock")
    assert resp.status_code == 409


async def test_unlock_does_not_deduct_xp(auth_client: AsyncClient) -> None:
    await _unlock_core_nexus(auth_client)
    project_id = await _create_focus_project(auth_client)
    await _complete_task_worth(auth_client, project_id, 500)

    before = await auth_client.get("/api/v1/me/progress")
    before_xp = before.json()["total_xp"]

    unlock = await auth_client.post("/api/v1/skill-nodes/deep_work/unlock")
    xp_delta = unlock.json()["xp_delta"]

    after = await auth_client.get("/api/v1/me/progress")
    after_xp = after.json()["total_xp"]
    assert after_xp == before_xp + xp_delta
    assert after_xp >= before_xp  # D13 — never decreases


async def test_get_skill_tree_issues_bounded_query_count(auth_client: AsyncClient) -> None:
    user_id = await _me_id(auth_client)

    statements: list[str] = []

    def _capture(conn: object, cursor: object, statement: str, *args: object) -> None:
        statements.append(statement)

    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        assert user is not None

        event.listen(test_engine.sync_engine, "before_cursor_execute", _capture)
        try:
            await skilltree.get_tree(db, user)
        finally:
            event.remove(test_engine.sync_engine, "before_cursor_execute", _capture)

    assert len(statements) == 3


async def test_branch_xp_attribution_habit_vs_branchless_task(auth_client: AsyncClient) -> None:
    habit = await auth_client.post(
        "/api/v1/habits",
        json={"name": "Cardio", "cadence": "daily", "xp_value": 500, "skill_branch": "health"},
    )
    habit_id = habit.json()["id"]
    await auth_client.post(f"/api/v1/habits/{habit_id}/log", json={})

    await _complete_task_worth(auth_client, None, 250)

    tree = await auth_client.get("/api/v1/me/skill-tree")
    branch_xp = tree.json()["branch_xp"]
    assert branch_xp["health"] == 500
    assert branch_xp["focus"] == 0

    progress = await auth_client.get("/api/v1/me/progress")
    # 500 (habit) + 250 (branch-less task) + 100 (first_blood, first
    # completed task) all count toward total_xp regardless of branch.
    assert progress.json()["total_xp"] == 850


async def test_skill_node_not_found(auth_client: AsyncClient) -> None:
    resp = await auth_client.post("/api/v1/skill-nodes/does-not-exist/unlock")
    assert resp.status_code == 404
