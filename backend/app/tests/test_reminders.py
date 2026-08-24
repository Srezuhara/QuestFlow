from datetime import UTC, datetime, timedelta

from httpx import AsyncClient


def _future_iso(minutes: int = 30) -> str:
    return (datetime.now(UTC) + timedelta(minutes=minutes)).isoformat()


def _reminder_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"message": "Take a break", "remind_at": _future_iso()}
    payload.update(overrides)
    return payload


async def test_create_reminder_with_defaults(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/api/v1/reminders", json=_reminder_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Take a break"
    assert body["status"] == "scheduled"
    assert set(body["channels"]) == {"push", "in_app"}
    assert body["target_label"] is None


async def test_naive_remind_at_is_rejected(auth_client: AsyncClient) -> None:
    naive = (datetime.now(UTC) + timedelta(minutes=30)).replace(tzinfo=None).isoformat()
    response = await auth_client.post(
        "/api/v1/reminders", json=_reminder_payload(remind_at=naive)
    )
    assert response.status_code == 422


async def test_rrule_is_rejected(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/reminders", json=_reminder_payload(rrule="FREQ=DAILY")
    )
    assert response.status_code == 422


async def test_both_targets_set_is_rejected(auth_client: AsyncClient) -> None:
    task = await auth_client.post("/api/v1/tasks", json={"title": "Do the thing"})
    task_id = task.json()["id"]
    habit = await auth_client.post(
        "/api/v1/habits", json={"name": "Run", "cadence": "daily", "xp_value": 10}
    )
    habit_id = habit.json()["id"]

    response = await auth_client.post(
        "/api/v1/reminders", json=_reminder_payload(task_id=task_id, habit_id=habit_id)
    )
    assert response.status_code == 422


async def test_another_users_task_id_is_rejected(client: AsyncClient) -> None:
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
    task = await client.post("/api/v1/tasks", json={"title": "Owner's task"})
    task_id = task.json()["id"]
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
    response = await client.post(
        "/api/v1/reminders", json=_reminder_payload(task_id=task_id)
    )
    assert response.status_code == 404


async def test_keyset_pagination_with_no_overlap(auth_client: AsyncClient) -> None:
    for i in range(3):
        await auth_client.post(
            "/api/v1/reminders", json=_reminder_payload(message=f"Reminder {i}")
        )

    first_page = await auth_client.get("/api/v1/reminders", params={"limit": 2})
    assert first_page.status_code == 200
    first_body = first_page.json()
    assert len(first_body["items"]) == 2
    assert first_body["next_before"] is not None

    second_page = await auth_client.get(
        "/api/v1/reminders", params={"limit": 2, "before": first_body["next_before"]}
    )
    second_body = second_page.json()
    assert len(second_body["items"]) == 1

    first_ids = {item["id"] for item in first_body["items"]}
    second_ids = {item["id"] for item in second_body["items"]}
    assert first_ids.isdisjoint(second_ids)


async def test_patch_another_users_reminder_is_404(client: AsyncClient) -> None:
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
    created = await client.post("/api/v1/reminders", json=_reminder_payload())
    reminder_id = created.json()["id"]
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
    response = await client.patch(
        f"/api/v1/reminders/{reminder_id}", json={"message": "Hijacked"}
    )
    assert response.status_code == 404


async def test_dismiss_reminder(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/reminders", json=_reminder_payload())
    reminder_id = created.json()["id"]

    response = await auth_client.post(f"/api/v1/reminders/{reminder_id}/dismiss")
    assert response.status_code == 200
    assert response.json()["status"] == "dismissed"


async def test_delete_sets_cancelled_row_still_present(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/reminders", json=_reminder_payload())
    reminder_id = created.json()["id"]

    response = await auth_client.delete(f"/api/v1/reminders/{reminder_id}")
    assert response.status_code == 204

    listing = await auth_client.get("/api/v1/reminders", params={"status": "cancelled"})
    ids = {item["id"] for item in listing.json()["items"]}
    assert reminder_id in ids


async def test_target_label_resolves_and_is_null_after_task_deleted(
    auth_client: AsyncClient,
) -> None:
    task = await auth_client.post("/api/v1/tasks", json={"title": "Ship the feature"})
    task_id = task.json()["id"]
    created = await auth_client.post(
        "/api/v1/reminders", json=_reminder_payload(task_id=task_id)
    )
    reminder_id = created.json()["id"]
    assert created.json()["target_label"] == "Ship the feature"

    await auth_client.delete(f"/api/v1/tasks/{task_id}")
    fetched = await auth_client.get("/api/v1/reminders", params={"limit": 50})
    reminder = next(r for r in fetched.json()["items"] if r["id"] == reminder_id)
    assert reminder["target_label"] is None
