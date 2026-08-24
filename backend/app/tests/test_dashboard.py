from datetime import UTC, datetime, timedelta

from httpx import AsyncClient


async def test_dashboard_aggregates_objectives_pipeline_and_progress(
    auth_client: AsyncClient,
) -> None:
    now = datetime.now(UTC)
    tomorrow = (now + timedelta(days=1)).isoformat()
    next_week = (now + timedelta(days=3)).isoformat()

    urgent = await auth_client.post(
        "/api/v1/tasks", json={"title": "Urgent now", "priority": "urgent"}
    )
    await auth_client.post(
        "/api/v1/tasks",
        json={"title": "Due tomorrow", "priority": "later", "due_at": tomorrow},
    )
    await auth_client.post(
        "/api/v1/tasks",
        json={"title": "Due next week", "priority": "later", "due_at": next_week},
    )
    await auth_client.patch(f"/api/v1/tasks/{urgent.json()['id']}/complete")

    dashboard = await auth_client.get("/api/v1/dashboard")
    assert dashboard.status_code == 200
    body = dashboard.json()

    # The completed task is excluded from active objectives/pipeline.
    assert body["active_count"] == 2
    titles = {t["title"] for t in body["objectives"]}
    assert titles == {"Due tomorrow", "Due next week"}
    assert [t["title"] for t in body["pipeline"]["due_tomorrow"]] == ["Due tomorrow"]
    assert [t["title"] for t in body["pipeline"]["due_next_week"]] == ["Due next week"]

    # 500 for the urgent task + 100 for the `first_blood` achievement (this
    # is the user's first completed task), evaluated per D17.
    assert body["progress"]["total_xp"] == 600
    assert len(body["recent_activity"]) == 2
    assert {e["awarded_xp"] for e in body["recent_activity"]} == {500, 100}


async def test_dashboard_works_for_a_real_non_utc_timezone(client: AsyncClient) -> None:
    """Regression test: `zoneinfo.ZoneInfo` needs the `tzdata` package to
    resolve real IANA keys on Windows and on minimal Docker images (neither
    ships an OS-level timezone database) — this broke `user_today()` for any
    browser-registered user whose auto-detected timezone wasn't "UTC"."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "mumbai@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "mumbaiuser",
            "display_name": "Mumbai User",
            "timezone": "Asia/Calcutta",
        },
    )
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 200
