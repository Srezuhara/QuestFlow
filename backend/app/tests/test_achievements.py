"""Achievement evaluator tests (D17): synchronous evaluation at the end of
domain service calls, the closed criteria-kind set, and the wall's
per-achievement progress.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select, update

from app.models.focus import FocusSession
from app.models.gamification import XPEvent
from app.models.user import User
from app.services.gamification import achievements
from app.tests.conftest import TestSessionLocal as AsyncSessionLocal


async def _me_id(client: AsyncClient) -> uuid.UUID:
    resp = await client.get("/api/v1/auth/me")
    return uuid.UUID(resp.json()["id"])


async def test_first_blood_fires_once_on_first_completed_task(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/tasks", json={"title": "Quest 1", "priority": "later"}
    )
    task_id = created.json()["id"]
    complete = await auth_client.patch(f"/api/v1/tasks/{task_id}/complete")
    assert complete.status_code == 200
    codes = {a["code"] for a in complete.json()["newly_earned_achievements"]}
    assert "first_blood" in codes

    created2 = await auth_client.post(
        "/api/v1/tasks", json={"title": "Quest 2", "priority": "later"}
    )
    task_id2 = created2.json()["id"]
    complete2 = await auth_client.patch(f"/api/v1/tasks/{task_id2}/complete")
    assert complete2.json()["newly_earned_achievements"] == []

    user_id = await _me_id(auth_client)
    async with AsyncSessionLocal() as db:
        rows = list(
            await db.scalars(
                select(XPEvent).where(
                    XPEvent.user_id == user_id, XPEvent.idempotency_key.like("achievement:%")
                )
            )
        )
    assert len(rows) == 1


async def test_focus_minutes_achievement_ignores_abandoned_sessions(
    auth_client: AsyncClient,
) -> None:
    started = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 3600}
    )
    session_id = started.json()["id"]
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(FocusSession)
            .where(FocusSession.id == uuid.UUID(session_id))
            .values(started_at=datetime.now(UTC) - timedelta(minutes=60))
        )
        await db.commit()

    abandoned = await auth_client.patch(
        f"/api/v1/focus/sessions/{session_id}", json={"action": "abandon"}
    )
    assert abandoned.status_code == 200

    wall = await auth_client.get("/api/v1/me/achievements")
    first_focus = next(a for a in wall.json() if a["code"] == "first_focus")
    assert first_focus["earned_at"] is None
    assert first_focus["progress_percent"] == 0.0


async def test_branch_xp_at_least_criterion_respects_the_branch(auth_client: AsyncClient) -> None:
    project = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Wealth Track", "slug": "wealth-track", "skill_branch": "wealth"},
    )
    project_id = project.json()["id"]
    task = await auth_client.post(
        "/api/v1/tasks",
        json={
            "title": "Invoice",
            "priority": "later",
            "xp_value": 1000,
            "project_id": project_id,
        },
    )
    task_id = task.json()["id"]
    await auth_client.patch(f"/api/v1/tasks/{task_id}/complete")

    user_id = await _me_id(auth_client)
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        assert user is not None
        metrics = await achievements.compute_metrics(db, user)

    met_wealth = achievements._meets(
        {"kind": "branch_xp_at_least", "value": 1000, "branch": "wealth"}, metrics
    )
    met_focus = achievements._meets(
        {"kind": "branch_xp_at_least", "value": 1000, "branch": "focus"}, metrics
    )
    assert met_wealth is True
    assert met_focus is False


async def test_achievements_wall_returns_whole_catalog_with_null_earned_at(
    auth_client: AsyncClient,
) -> None:
    wall = await auth_client.get("/api/v1/me/achievements")
    assert wall.status_code == 200
    body = wall.json()
    assert len(body) == 16
    assert all(a["earned_at"] is None for a in body)
    assert all(0.0 <= a["progress_percent"] <= 100.0 for a in body)


async def test_achievement_xp_reward_lands_in_ledger_exactly_once(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/tasks", json={"title": "Quest 1", "priority": "later"}
    )
    task_id = created.json()["id"]
    complete = await auth_client.patch(f"/api/v1/tasks/{task_id}/complete")
    earned = complete.json()["newly_earned_achievements"]
    assert any(a["code"] == "first_blood" for a in earned)

    user_id = await _me_id(auth_client)
    async with AsyncSessionLocal() as db:
        rows = list(
            await db.scalars(
                select(XPEvent).where(
                    XPEvent.user_id == user_id,
                    XPEvent.idempotency_key.like("achievement:%"),
                )
            )
        )
    assert len(rows) == 1
    assert rows[0].awarded_xp == 100
