from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.models.enums import NotificationType
from app.models.reminder import Notification
from app.services import reminder_service
from app.tests.conftest import TestSessionLocal


async def test_empty_list(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/notifications")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["unread_count"] == 0
    assert body["next_before"] is None


async def test_populated_after_a_tick_with_the_right_payload(auth_client: AsyncClient) -> None:
    reminder = await auth_client.post(
        "/api/v1/reminders",
        json={
            "message": "Stretch break",
            "remind_at": (datetime.now(UTC) + timedelta(seconds=1)).isoformat(),
        },
    )
    reminder_id = reminder.json()["id"]

    async with TestSessionLocal() as db:
        due = await reminder_service.claim_due_reminders(
            db, now=datetime.now(UTC) + timedelta(minutes=1), limit=100
        )
        assert len(due) == 1

    response = await auth_client.get("/api/v1/notifications")
    body = response.json()
    assert len(body["items"]) == 1
    assert body["unread_count"] == 1
    item = body["items"][0]
    assert item["type"] == "reminder"
    assert item["payload"]["reminder_id"] == reminder_id
    assert item["payload"]["message"] == "Stretch break"
    assert item["payload"]["url"] == "/reminders"


async def test_unread_only_filters(auth_client: AsyncClient) -> None:
    me = await auth_client.get("/api/v1/auth/me")
    user_id = me.json()["id"]
    async with TestSessionLocal() as db:
        db.add(
            Notification(user_id=user_id, type=NotificationType.SYSTEM, payload={"note": "a"})
        )
        n2 = Notification(user_id=user_id, type=NotificationType.SYSTEM, payload={"note": "b"})
        n2.read_at = datetime.now(UTC)
        db.add(n2)
        await db.commit()

    response = await auth_client.get("/api/v1/notifications", params={"unread_only": True})
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["payload"]["note"] == "a"


async def test_read_is_idempotent(auth_client: AsyncClient) -> None:
    me = await auth_client.get("/api/v1/auth/me")
    user_id = me.json()["id"]
    async with TestSessionLocal() as db:
        n = Notification(user_id=user_id, type=NotificationType.SYSTEM, payload={})
        db.add(n)
        await db.commit()
        await db.refresh(n)
        notification_id = n.id

    first = await auth_client.patch(f"/api/v1/notifications/{notification_id}/read")
    second = await auth_client.patch(f"/api/v1/notifications/{notification_id}/read")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["read_at"] == second.json()["read_at"]


async def test_read_all_returns_a_count(auth_client: AsyncClient) -> None:
    me = await auth_client.get("/api/v1/auth/me")
    user_id = me.json()["id"]
    async with TestSessionLocal() as db:
        for _ in range(3):
            db.add(Notification(user_id=user_id, type=NotificationType.SYSTEM, payload={}))
        await db.commit()

    response = await auth_client.post("/api/v1/notifications/read-all")
    assert response.status_code == 200
    assert response.json()["marked_count"] == 3

    listing = await auth_client.get("/api/v1/notifications")
    assert listing.json()["unread_count"] == 0


async def test_another_users_notification_is_404(client: AsyncClient) -> None:
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
    me = await client.get("/api/v1/auth/me")
    user_id = me.json()["id"]
    async with TestSessionLocal() as db:
        n = Notification(user_id=user_id, type=NotificationType.SYSTEM, payload={})
        db.add(n)
        await db.commit()
        await db.refresh(n)
        notification_id = n.id
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
    response = await client.patch(f"/api/v1/notifications/{notification_id}/read")
    assert response.status_code == 404
