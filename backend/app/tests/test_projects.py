from httpx import AsyncClient


def _project_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": "Deep Work", "slug": "deep-work"}
    payload.update(overrides)
    return payload


async def test_create_and_list_projects(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/projects", json=_project_payload())
    assert created.status_code == 201
    assert created.json()["skill_branch"] == "focus"

    listed = await auth_client.get("/api/v1/projects")
    assert len(listed.json()) == 1


async def test_duplicate_slug_conflicts(auth_client: AsyncClient) -> None:
    await auth_client.post("/api/v1/projects", json=_project_payload())
    dup = await auth_client.post("/api/v1/projects", json=_project_payload(name="Deep Work 2"))
    assert dup.status_code == 409


async def test_archive_project_excludes_it_from_default_list(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/projects", json=_project_payload())
    project_id = created.json()["id"]

    archived = await auth_client.delete(f"/api/v1/projects/{project_id}")
    assert archived.status_code == 204

    active = await auth_client.get("/api/v1/projects")
    assert active.json() == []

    with_archived = await auth_client.get("/api/v1/projects", params={"include_archived": True})
    assert len(with_archived.json()) == 1
