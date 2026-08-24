"""Focus-session API tests, including the anti-cheat clamp (plan D10) and a
non-UTC timezone case for the calendar aggregation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import update

from app.models.focus import FocusSession
from app.tests.conftest import TestSessionLocal as AsyncSessionLocal


async def _backdate_start(session_id: str, minutes_ago: float) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(FocusSession)
            .where(FocusSession.id == uuid.UUID(session_id))
            .values(started_at=datetime.now(UTC) - timedelta(minutes=minutes_ago))
        )
        await db.commit()


async def test_completing_a_25_minute_focus_session_awards_25_xp(
    auth_client: AsyncClient,
) -> None:
    started = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 1500}
    )
    assert started.status_code == 201
    session_id = started.json()["id"]

    await _backdate_start(session_id, 25)
    completed = await auth_client.patch(
        f"/api/v1/focus/sessions/{session_id}", json={"action": "complete"}
    )
    assert completed.status_code == 200
    body = completed.json()
    assert body["xp_delta"] == 25
    assert body["session"]["status"] == "completed"
    # 25 for the session + 100 for the `first_focus` achievement (this is
    # the user's first qualifying focus session), evaluated per D17.
    assert body["progress"]["total_xp"] == 125


async def test_short_focus_session_awards_no_xp(auth_client: AsyncClient) -> None:
    started = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 1500}
    )
    session_id = started.json()["id"]

    await _backdate_start(session_id, 4)
    completed = await auth_client.patch(
        f"/api/v1/focus/sessions/{session_id}", json={"action": "complete"}
    )
    assert completed.json()["xp_delta"] == 0


async def test_completed_break_awards_no_xp(auth_client: AsyncClient) -> None:
    started = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "short_break", "planned_seconds": 300}
    )
    session_id = started.json()["id"]

    await _backdate_start(session_id, 25)
    completed = await auth_client.patch(
        f"/api/v1/focus/sessions/{session_id}", json={"action": "complete"}
    )
    assert completed.json()["xp_delta"] == 0


async def test_abandoned_session_awards_no_xp(auth_client: AsyncClient) -> None:
    started = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 1500}
    )
    session_id = started.json()["id"]

    await _backdate_start(session_id, 25)
    abandoned = await auth_client.patch(
        f"/api/v1/focus/sessions/{session_id}", json={"action": "abandon"}
    )
    assert abandoned.status_code == 200
    assert abandoned.json()["xp_delta"] == 0
    assert abandoned.json()["session"]["status"] == "abandoned"


async def test_actual_seconds_are_clamped_to_planned_seconds(auth_client: AsyncClient) -> None:
    started = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 60}
    )
    session_id = started.json()["id"]

    # started_at is only 10s in the past, so the anti-cheat clamp is on the
    # elapsed-time side, not the planned_seconds side — either way, a
    # freshly-started session cannot possibly clear the 5-minute XP floor.
    await _backdate_start(session_id, 10 / 60)
    completed = await auth_client.patch(
        f"/api/v1/focus/sessions/{session_id}", json={"action": "complete"}
    )
    assert completed.json()["xp_delta"] == 0
    assert completed.json()["session"]["actual_seconds"] <= 60


async def test_completing_an_already_completed_session_is_rejected(
    auth_client: AsyncClient,
) -> None:
    started = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 1500}
    )
    session_id = started.json()["id"]
    await _backdate_start(session_id, 25)
    await auth_client.patch(f"/api/v1/focus/sessions/{session_id}", json={"action": "complete"})

    second = await auth_client.patch(
        f"/api/v1/focus/sessions/{session_id}", json={"action": "complete"}
    )
    assert second.status_code == 409

    events = await auth_client.get("/api/v1/me/xp-events", params={"limit": 50})
    focus_events = [e for e in events.json()["items"] if e["source_type"] == "focus_session"]
    assert len(focus_events) == 1


async def test_starting_a_session_auto_abandons_the_stale_running_one(
    auth_client: AsyncClient,
) -> None:
    first = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 1500}
    )
    second = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 1500}
    )
    assert first.json()["id"] != second.json()["id"]

    active = await auth_client.get("/api/v1/focus/sessions/active")
    assert active.json()["id"] == second.json()["id"]


async def test_active_session_lookup_resumes_then_clears_on_completion(
    auth_client: AsyncClient,
) -> None:
    none_yet = await auth_client.get("/api/v1/focus/sessions/active")
    assert none_yet.json() is None

    started = await auth_client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 1500}
    )
    session_id = started.json()["id"]
    active = await auth_client.get("/api/v1/focus/sessions/active")
    assert active.json()["id"] == session_id

    await _backdate_start(session_id, 25)
    await auth_client.patch(f"/api/v1/focus/sessions/{session_id}", json={"action": "complete"})
    cleared = await auth_client.get("/api/v1/focus/sessions/active")
    assert cleared.json() is None


async def test_calendar_aggregates_by_the_users_local_date(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "calendar@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "calendaruser",
            "display_name": "Calendar User",
            "timezone": "Asia/Calcutta",
        },
    )
    started = await client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 1500}
    )
    session_id = started.json()["id"]

    # 23:30 UTC on 2026-01-15 is 05:00 IST on 2026-01-16 (UTC+5:30) — must
    # land on the 16th in the calendar, not the 15th.
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(FocusSession)
            .where(FocusSession.id == uuid.UUID(session_id))
            .values(started_at=datetime(2026, 1, 15, 23, 30, tzinfo=UTC))
        )
        await db.commit()

    await client.patch(f"/api/v1/focus/sessions/{session_id}", json={"action": "complete"})

    calendar = await client.get("/api/v1/focus/calendar", params={"year": 2026, "month": 1})
    days = {d["date"]: d for d in calendar.json()["days"]}
    assert days["2026-01-16"]["session_count"] == 1
    assert days["2026-01-15"]["session_count"] == 0


async def test_cross_user_cannot_patch_anothers_session(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner-f@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "ownerf",
            "display_name": "Owner",
            "timezone": "UTC",
        },
    )
    started = await client.post(
        "/api/v1/focus/sessions", json={"mode": "focus", "planned_seconds": 1500}
    )
    session_id = started.json()["id"]
    await client.post("/api/v1/auth/logout")

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder-f@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "intruderf",
            "display_name": "Intruder",
            "timezone": "UTC",
        },
    )
    attempt = await client.patch(
        f"/api/v1/focus/sessions/{session_id}", json={"action": "abandon"}
    )
    assert attempt.status_code == 404
