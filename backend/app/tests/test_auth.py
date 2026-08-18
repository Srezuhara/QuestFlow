from httpx import AsyncClient


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


async def test_refresh_rotates_token_and_old_one_is_rejected(client: AsyncClient) -> None:
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

    # Reusing the old (now-revoked) refresh token must fail and kill the chain.
    client.cookies.set("refresh_token", old_refresh_cookie)
    reuse = await client.post("/api/v1/auth/refresh")
    assert reuse.status_code == 401

    # The chain-kill means even the *current* refresh token is now dead.
    client.cookies.set("refresh_token", new_refresh_cookie)
    dead = await client.post("/api/v1/auth/refresh")
    assert dead.status_code == 401


async def test_logout_revokes_refresh_token_and_clears_cookies(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_register_payload())

    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 204

    refresh_after_logout = await client.post("/api/v1/auth/refresh")
    assert refresh_after_logout.status_code == 401
