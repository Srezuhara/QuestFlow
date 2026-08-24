"""RFC 7807 + X-Request-ID tests (PHASE_8_9_PLAN.md §9.6). D9-6: `detail`
keeps its exact current value and shape — every other test in the suite
already proves that by continuing to pass unchanged; these tests pin the
new envelope specifically.
"""

from __future__ import annotations

from httpx import AsyncClient


async def test_404_is_problem_json_with_unchanged_detail(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["detail"] == "Not authenticated"
    assert body["status"] == 401
    assert body["title"] == "Unauthorized"
    assert "type" in body
    assert body["request_id"]


async def test_422_validation_error_is_problem_json_with_list_detail(
    client: AsyncClient,
) -> None:
    response = await client.post("/api/v1/auth/register", json={"email": "not-an-email"})
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert isinstance(body["detail"], list)
    assert body["status"] == 422


async def test_x_request_id_header_present_and_echoed(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers

    supplied = "test-request-id-123"
    echoed = await client.get("/health", headers={"X-Request-ID": supplied})
    assert echoed.headers["x-request-id"] == supplied


async def test_request_id_in_problem_body_matches_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["request_id"] == response.headers["x-request-id"]
