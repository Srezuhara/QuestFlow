from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import func, select, update

from app.models.gamification import XPEvent
from app.models.task import Task
from app.models.user import RefreshToken
from app.services.auth_service import REFRESH_REUSE_GRACE_SECONDS
from app.tests.conftest import TestSessionLocal


def _register_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "email": "player1@example.com",
        "password": "correct-horse-battery-staple",
        "handle": "player1",
        "display_name": "Player One",
        "timezone": "UTC",
    }
    payload.update(overrides)
    return payload


async def test_register_sets_cookies_and_returns_user(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/register", json=_register_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "player1@example.com"
    assert body["handle"] == "player1"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    response = await client.post(
        "/api/v1/auth/register", json=_register_payload(handle="player2")
    )
    assert response.status_code == 409


async def test_login_then_me(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "player1@example.com", "password": "correct-horse-battery-staple"},
    )
    assert login.status_code == 200

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["handle"] == "player1"


async def test_login_wrong_password_rejected(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "player1@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_me_without_cookie_is_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_refresh_rotates_token(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    old_refresh_cookie = client.cookies.get("refresh_token")
    assert old_refresh_cookie is not None

    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 204
    new_refresh_cookie = client.cookies.get("refresh_token")
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != old_refresh_cookie

    # Confirm the new access token still authenticates.
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200


async def test_refresh_reuse_within_grace_window_is_not_treated_as_theft(
    client: AsyncClient,
) -> None:
    """Two racing tabs can both present the same (about-to-be-rotated) refresh
    token within moments of each other — this must not revoke the session."""
    await client.post("/api/v1/auth/register", json=_register_payload())
    old_refresh_cookie = client.cookies.get("refresh_token")
    assert old_refresh_cookie is not None

    first = await client.post("/api/v1/auth/refresh")
    assert first.status_code == 204
    new_refresh_cookie = client.cookies.get("refresh_token")
    assert new_refresh_cookie is not None

    async with TestSessionLocal() as db:
        count_before = len(
            (await db.scalars(select(RefreshToken).where(RefreshToken.revoked_at.is_(None)))).all()
        )

    # A second, racing presentation of the *old* token, moments later.
    del client.cookies["refresh_token"]
    client.cookies.set("refresh_token", old_refresh_cookie)
    second = await client.post("/api/v1/auth/refresh")
    assert second.status_code == 204
    # Grace path: a fresh access token is issued, but no new refresh cookie —
    # the raw successor value isn't recoverable, so the existing refresh
    # cookie (the real browser's, already the successor since both tabs
    # share one cookie jar) is left untouched rather than overwritten.
    set_cookie_headers = second.headers.get_list("set-cookie")
    assert any(h.startswith("access_token=") for h in set_cookie_headers)
    assert not any(h.startswith("refresh_token=") for h in set_cookie_headers)

    # No other session was revoked by the race.
    async with TestSessionLocal() as db:
        count_after = len(
            (await db.scalars(select(RefreshToken).where(RefreshToken.revoked_at.is_(None)))).all()
        )
    assert count_after == count_before

    # The still-live successor token keeps working.
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200


async def test_refresh_reuse_after_grace_window_kills_the_chain(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    old_refresh_cookie = client.cookies.get("refresh_token")
    assert old_refresh_cookie is not None

    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 204
    new_refresh_cookie = client.cookies.get("refresh_token")
    assert new_refresh_cookie is not None

    # Simulate the grace window having elapsed.
    async with TestSessionLocal() as db:
        stale = datetime.now(UTC) - timedelta(seconds=REFRESH_REUSE_GRACE_SECONDS + 5)
        await db.execute(
            update(RefreshToken).where(RefreshToken.revoked_at.is_not(None)).values(revoked_at=stale)
        )
        await db.commit()

    # Reusing the old (now long-revoked) refresh token must fail and kill the chain.
    del client.cookies["refresh_token"]
    client.cookies.set("refresh_token", old_refresh_cookie)
    reuse = await client.post("/api/v1/auth/refresh")
    assert reuse.status_code == 401

    # The chain-kill means even the *current* refresh token is now dead.
    client.cookies.set("refresh_token", new_refresh_cookie)
    dead = await client.post("/api/v1/auth/refresh")
    assert dead.status_code == 401


async def test_refresh_with_invalid_token_clears_cookies(client: AsyncClient) -> None:
    client.cookies.set("refresh_token", "not-a-real-token")
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401

    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any(h.startswith("access_token=") and "Max-Age=0" in h for h in set_cookie_headers)
    assert any(h.startswith("refresh_token=") and "Max-Age=0" in h for h in set_cookie_headers)


async def test_refresh_with_no_cookie_clears_cookies(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any(h.startswith("access_token=") and "Max-Age=0" in h for h in set_cookie_headers)
    assert any(h.startswith("refresh_token=") and "Max-Age=0" in h for h in set_cookie_headers)


async def test_logout_revokes_refresh_token_and_clears_cookies(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())

    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 204

    refresh_after_logout = await client.post("/api/v1/auth/refresh")
    assert refresh_after_logout.status_code == 401


async def test_delete_account_returns_204(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    response = await client.delete("/api/v1/auth/me")
    assert response.status_code == 204


async def test_delete_account_then_me_is_unauthorized(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    await client.delete("/api/v1/auth/me")

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 401


async def test_delete_account_cascades_to_owned_rows(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    created = await client.post(
        "/api/v1/tasks", json={"title": "Cascade Check", "priority": "later"}
    )
    task_id = created.json()["id"]
    await client.patch(f"/api/v1/tasks/{task_id}/complete")

    await client.delete("/api/v1/auth/me")

    async with TestSessionLocal() as db:
        task_count = await db.scalar(select(func.count()).select_from(Task))
        xp_event_count = await db.scalar(select(func.count()).select_from(XPEvent))
        assert task_count == 0
        assert xp_event_count == 0


async def test_delete_account_unauthenticated_is_rejected(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/auth/me")
    assert response.status_code == 401


async def test_patch_me_persists_a_valid_preset_avatar(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    response = await client.patch("/api/v1/auth/me", json={"avatar_url": "/avatars/avatar-01.svg"})
    assert response.status_code == 200
    assert response.json()["avatar_url"] == "/avatars/avatar-01.svg"

    refetched = await client.get("/api/v1/auth/me")
    assert refetched.json()["avatar_url"] == "/avatars/avatar-01.svg"


async def test_patch_me_rejects_an_off_allowlist_avatar_url(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    response = await client.patch(
        "/api/v1/auth/me", json={"avatar_url": "https://evil.example.com/tracker.png"}
    )
    assert response.status_code == 422


async def test_patch_me_null_avatar_url_clears_it(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())
    await client.patch("/api/v1/auth/me", json={"avatar_url": "/avatars/avatar-02.svg"})

    cleared = await client.patch("/api/v1/auth/me", json={"avatar_url": None})
    assert cleared.status_code == 200
    assert cleared.json()["avatar_url"] is None
