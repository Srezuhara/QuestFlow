import pytest
from httpx import AsyncClient

from app.core.config import settings


def _sub_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "endpoint": "https://push.example.com/abc123",
        "p256dh": "fake-p256dh-key",
        "auth": "fake-auth-secret",
        "user_agent": "Mozilla/5.0 (test)",
    }
    payload.update(overrides)
    return payload


async def test_create_subscription(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/api/v1/push/subscriptions", json=_sub_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["endpoint"] == "https://push.example.com/abc123"


async def test_same_endpoint_twice_upserts_one_row(auth_client: AsyncClient) -> None:
    first = await auth_client.post("/api/v1/push/subscriptions", json=_sub_payload())
    second = await auth_client.post(
        "/api/v1/push/subscriptions",
        json=_sub_payload(p256dh="updated-key", user_agent="Chrome/999"),
    )
    assert first.status_code == 201
    assert second.status_code == 201

    listing = await auth_client.get("/api/v1/push/subscriptions")
    rows = listing.json()
    assert len(rows) == 1
    assert rows[0]["user_agent"] == "Chrome/999"


async def test_list_is_own_only(client: AsyncClient) -> None:
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
    await client.post("/api/v1/push/subscriptions", json=_sub_payload())
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
    listing = await client.get("/api/v1/push/subscriptions")
    assert listing.json() == []


async def test_delete_another_users_subscription_is_404(client: AsyncClient) -> None:
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
    created = await client.post("/api/v1/push/subscriptions", json=_sub_payload())
    sub_id = created.json()["id"]
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
    response = await client.delete(f"/api/v1/push/subscriptions/{sub_id}")
    assert response.status_code == 404


async def test_create_subscription_503s_when_push_disabled(
    auth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "vapid_private_key", "placeholder-vapid-private-key")
    response = await auth_client.post("/api/v1/push/subscriptions", json=_sub_payload())
    assert response.status_code == 503
