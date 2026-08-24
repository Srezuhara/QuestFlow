from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy import event

from app.models.enums import HabitCadence
from app.schemas.auth import RegisterRequest
from app.schemas.habits import HabitCreate
from app.services import auth_service, habit_service
from app.tests.conftest import TestSessionLocal as AsyncSessionLocal
from app.tests.conftest import test_engine


def _habit_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": "Morning Run", "cadence": "daily", "xp_value": 100}
    payload.update(overrides)
    return payload


async def test_create_then_log_awards_xp_and_advances_progress(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/habits", json=_habit_payload())
    assert created.status_code == 201
    habit_id = created.json()["id"]
    assert created.json()["due_today"] is True

    logged = await auth_client.post(f"/api/v1/habits/{habit_id}/log", json={})
    assert logged.status_code == 200
    body = logged.json()
    assert body["xp_delta"] == 100
    assert body["progress"]["total_xp"] == 100
    assert body["streak"]["current_streak"] == 1


async def test_logging_same_day_twice_increments_count_but_awards_once(
    auth_client: AsyncClient,
) -> None:
    created = await auth_client.post("/api/v1/habits", json=_habit_payload())
    habit_id = created.json()["id"]

    await auth_client.post(f"/api/v1/habits/{habit_id}/log", json={})
    second = await auth_client.post(f"/api/v1/habits/{habit_id}/log", json={})
    assert second.json()["xp_delta"] == 0
    assert second.json()["log"]["count"] == 2

    progress = await auth_client.get("/api/v1/me/progress")
    assert progress.json()["total_xp"] == 100


async def test_unlog_reverses_xp_net_zero(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/habits", json=_habit_payload())
    habit_id = created.json()["id"]
    today = date.today().isoformat()

    await auth_client.post(f"/api/v1/habits/{habit_id}/log", json={})
    unlogged = await auth_client.delete(f"/api/v1/habits/{habit_id}/log/{today}")
    assert unlogged.status_code == 200
    assert unlogged.json()["xp_delta"] == -100

    progress = await auth_client.get("/api/v1/me/progress")
    assert progress.json()["total_xp"] == 0


async def test_custom_cadence_is_rejected(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/api/v1/habits", json=_habit_payload(cadence="custom"))
    assert response.status_code == 422


async def test_milestone_streak_bonus_fires_once(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/habits", json=_habit_payload(xp_value=10))
    habit_id = created.json()["id"]
    today = date.today()

    # Drive the streak to 7 via backdated logs, then break and re-reach it.
    for i in range(6, -1, -1):
        await auth_client.post(
            f"/api/v1/habits/{habit_id}/log",
            json={"logged_for": (today - timedelta(days=i)).isoformat()},
        )

    events = await auth_client.get("/api/v1/me/xp-events", params={"limit": 50})
    bonus_events = [e for e in events.json()["items"] if e["source_type"] == "streak_bonus"]
    assert len(bonus_events) == 1

    # Break the streak (skip a day), then rebuild past 7 again.
    for i in range(15, 8, -1):
        await auth_client.post(
            f"/api/v1/habits/{habit_id}/log",
            json={"logged_for": (today - timedelta(days=i)).isoformat()},
        )
    events_after = await auth_client.get("/api/v1/me/xp-events", params={"limit": 50})
    bonus_events_after = [
        e for e in events_after.json()["items"] if e["source_type"] == "streak_bonus"
    ]
    assert len(bonus_events_after) == 1  # no second bonus for the same milestone


async def test_matrix_returns_exactly_days_cells(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/habits", json=_habit_payload())
    habit_id = created.json()["id"]
    await auth_client.post(f"/api/v1/habits/{habit_id}/log", json={})

    matrix = await auth_client.get(f"/api/v1/habits/{habit_id}/matrix", params={"days": 30})
    assert matrix.status_code == 200
    body = matrix.json()
    assert body["days"] == 30
    assert len(body["cells"]) == 30
    assert body["cells"][-1]["status"] == "hit"


async def test_weekly_habit_not_yet_hit_shows_partial_progress(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/habits", json=_habit_payload(cadence="weekly", target_per_period=3)
    )
    habit_id = created.json()["id"]

    await auth_client.post(f"/api/v1/habits/{habit_id}/log", json={})
    second = await auth_client.post(f"/api/v1/habits/{habit_id}/log", json={})

    assert second.json()["log"]["count"] == 2

    listed = await auth_client.get("/api/v1/habits")
    habit = next(h for h in listed.json() if h["id"] == habit_id)
    assert habit["current_period"]["count"] == 2
    assert habit["current_period"]["target"] == 3
    assert habit["current_period"]["is_hit"] is False
    assert habit["due_today"] is True


async def test_get_habits_includes_streak_and_current_period_without_n_plus_one(
    auth_client: AsyncClient,
) -> None:
    for i in range(3):
        await auth_client.post("/api/v1/habits", json=_habit_payload(name=f"Habit {i}"))

    listed = await auth_client.get("/api/v1/habits")
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 3
    for habit in body:
        assert "streak" in habit
        assert "current_period" in habit
        assert "due_today" in habit


async def _query_count_for_habit_count(email: str, habit_count: int) -> int:
    """Registers a fresh user with `habit_count` habits and returns the
    number of SQL statements `list_habit_views` issues to serve them."""
    async with AsyncSessionLocal() as db:
        user = await auth_service.register_user(
            db,
            RegisterRequest(
                email=email,
                password="correct-horse-battery-staple",
                handle=email.split("@")[0],
                display_name="Query Count User",
                timezone="UTC",
            ),
        )
        for i in range(habit_count):
            await habit_service.create_habit(
                db, user, HabitCreate(name=f"Habit {i}", cadence=HabitCadence.DAILY, xp_value=50)
            )

        statements: list[str] = []

        def _capture(conn: object, cursor: object, statement: str, *args: object) -> None:
            statements.append(statement)

        event.listen(test_engine.sync_engine, "before_cursor_execute", _capture)
        try:
            await habit_service.list_habit_views(db, user)
        finally:
            event.remove(test_engine.sync_engine, "before_cursor_execute", _capture)

        return len(statements)


async def test_list_habit_views_query_count_is_constant_not_n_plus_one() -> None:
    """`list_habit_views` is already N+1-free (three queries regardless of
    habit count, per its own docstring) — this test makes that a real,
    breakable assertion instead of only asserting response shape, so a
    future edit that reintroduces the N+1 fails a test rather than just
    disagreeing with a comment. PHASE_8_9_PLAN.md §9.4.2 item 3."""
    count_with_3 = await _query_count_for_habit_count("qcount3@example.com", 3)
    count_with_6 = await _query_count_for_habit_count("qcount6@example.com", 6)
    assert count_with_3 == count_with_6


async def test_cross_user_habit_is_not_visible(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "owner1",
            "display_name": "Owner",
            "timezone": "UTC",
        },
    )
    created = await client.post("/api/v1/habits", json=_habit_payload())
    habit_id = created.json()["id"]
    await client.post("/api/v1/auth/logout")

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "intruder1",
            "display_name": "Intruder",
            "timezone": "UTC",
        },
    )
    log_attempt = await client.post(f"/api/v1/habits/{habit_id}/log", json={})
    assert log_attempt.status_code == 404

    matrix_attempt = await client.get(f"/api/v1/habits/{habit_id}/matrix")
    assert matrix_attempt.status_code == 404
