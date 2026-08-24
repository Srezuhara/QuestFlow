"""Pomodoro preferences API tests."""

from __future__ import annotations

from httpx import AsyncClient


async def test_preferences_defaults_on_first_read(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/me/preferences")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "focus_minutes": 25,
        "short_break_minutes": 5,
        "long_break_minutes": 15,
        "sessions_before_long_break": 4,
        "sound_enabled": True,
        "leaderboard_opt_in": True,
    }


async def test_patch_persists_preferences(auth_client: AsyncClient) -> None:
    patched = await auth_client.patch(
        "/api/v1/me/preferences", json={"focus_minutes": 50, "sound_enabled": False}
    )
    assert patched.status_code == 200
    assert patched.json()["focus_minutes"] == 50
    assert patched.json()["sound_enabled"] is False

    refetched = await auth_client.get("/api/v1/me/preferences")
    assert refetched.json()["focus_minutes"] == 50
    assert refetched.json()["sound_enabled"] is False
    # Untouched fields keep their previous value.
    assert refetched.json()["short_break_minutes"] == 5


async def test_out_of_range_preferences_are_rejected(auth_client: AsyncClient) -> None:
    response = await auth_client.patch("/api/v1/me/preferences", json={"focus_minutes": 0})
    assert response.status_code == 422

    response = await auth_client.patch(
        "/api/v1/me/preferences", json={"sessions_before_long_break": 1}
    )
    assert response.status_code == 422
