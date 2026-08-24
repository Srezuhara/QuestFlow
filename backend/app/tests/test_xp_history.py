"""XP history endpoint tests: keyset pagination on `/me/xp-events` and the
`/me/xp-summary` aggregates, including the mandatory non-UTC case (a 23:30
UTC event must land on the correct *local* calendar day)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from httpx import AsyncClient

from app.models.enums import XPSourceType
from app.models.gamification import XPEvent
from app.tests.conftest import TestSessionLocal as AsyncSessionLocal


async def _me_id(client: AsyncClient) -> uuid.UUID:
    resp = await client.get("/api/v1/auth/me")
    return uuid.UUID(resp.json()["id"])


async def _seed_events(user_id: uuid.UUID, count: int) -> None:
    base = datetime.now(UTC)
    async with AsyncSessionLocal() as db:
        for i in range(count):
            db.add(
                XPEvent(
                    user_id=user_id,
                    source_type=XPSourceType.TASK_COMPLETE,
                    source_id=uuid.uuid4(),
                    base_xp=10,
                    multiplier=1,
                    awarded_xp=10,
                    occurred_on=base.date(),
                    idempotency_key=f"seed-history:{user_id}:{i}",
                    created_at=base + timedelta(seconds=i),
                )
            )
        await db.commit()


async def test_xp_events_keyset_pagination_has_no_dupes_or_gaps(auth_client: AsyncClient) -> None:
    user_id = await _me_id(auth_client)
    await _seed_events(user_id, 60)

    seen: list[str] = []
    before: str | None = None
    pages = 0
    while True:
        params: dict[str, str | int] = {"limit": 25}
        if before is not None:
            params["before"] = before
        resp = await auth_client.get("/api/v1/me/xp-events", params=params)
        assert resp.status_code == 200
        body = resp.json()
        seen.extend(item["id"] for item in body["items"])
        pages += 1
        before = body["next_before"]
        assert pages <= 5  # safety valve against an infinite loop on a bug
        if before is None:
            break

    assert pages == 3
    assert len(seen) == 60
    assert len(set(seen)) == 60


async def test_xp_events_next_before_is_null_when_exhausted(auth_client: AsyncClient) -> None:
    user_id = await _me_id(auth_client)
    await _seed_events(user_id, 5)

    resp = await auth_client.get("/api/v1/me/xp-events", params={"limit": 50})
    body = resp.json()
    assert len(body["items"]) == 5
    assert body["next_before"] is None


async def test_xp_summary_sums_per_day_branch_and_source_for_non_utc_user(
    client: AsyncClient,
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "history-tz@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "historytz",
            "display_name": "History TZ",
            "timezone": "Asia/Calcutta",
        },
    )
    me = await client.get("/api/v1/auth/me")
    user_id = uuid.UUID(me.json()["id"])

    # A moment 2 days ago at 23:30 UTC is 05:00 IST the *next* day
    # (UTC+5:30) — this must land on the local day, not the UTC day.
    event_moment = (datetime.now(UTC) - timedelta(days=2)).replace(
        hour=23, minute=30, second=0, microsecond=0
    )
    local_day = event_moment.astimezone(ZoneInfo("Asia/Calcutta")).date()
    utc_day = event_moment.date()
    assert local_day != utc_day

    async with AsyncSessionLocal() as db:
        db.add(
            XPEvent(
                user_id=user_id,
                source_type=XPSourceType.HABIT_LOG,
                source_id=uuid.uuid4(),
                base_xp=42,
                multiplier=1,
                awarded_xp=42,
                skill_branch=None,
                occurred_on=local_day,
                idempotency_key=f"seed-tz:{user_id}",
                created_at=event_moment,
            )
        )
        await db.commit()

    summary = await client.get("/api/v1/me/xp-summary", params={"days": 30})
    assert summary.status_code == 200
    body = summary.json()

    days_by_date = {d["date"]: d["xp"] for d in body["days"]}
    assert days_by_date[local_day.isoformat()] == 42
    if utc_day.isoformat() in days_by_date:
        assert days_by_date[utc_day.isoformat()] == 0

    by_source = {row["source_type"]: row["xp"] for row in body["by_source"]}
    assert by_source["habit_log"] == 42


async def test_xp_summary_branch_totals(auth_client: AsyncClient) -> None:
    project = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Growth Track", "slug": "growth-track", "skill_branch": "growth"},
    )
    project_id = project.json()["id"]
    task = await auth_client.post(
        "/api/v1/tasks",
        json={
            "title": "Read a book",
            "priority": "later",
            "xp_value": 75,
            "project_id": project_id,
        },
    )
    task_id = task.json()["id"]
    await auth_client.patch(f"/api/v1/tasks/{task_id}/complete")

    summary = await auth_client.get("/api/v1/me/xp-summary", params={"days": 30})
    by_branch = {row["branch"]: row["xp"] for row in summary.json()["by_branch"]}
    assert by_branch["growth"] == 75
