from httpx import AsyncClient


async def test_create_list_update_delete_tag(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/tags", json={"name": "Deep Work", "slug": "deep-work"}
    )
    assert created.status_code == 201
    tag_id = created.json()["id"]

    listed = await auth_client.get("/api/v1/tags")
    assert len(listed.json()) == 1

    updated = await auth_client.patch(f"/api/v1/tags/{tag_id}", json={"name": "Focus"})
    assert updated.json()["name"] == "Focus"

    deleted = await auth_client.delete(f"/api/v1/tags/{tag_id}")
    assert deleted.status_code == 204
    assert (await auth_client.get("/api/v1/tags")).json() == []
