from httpx import AsyncClient


def _task_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"title": "Deploy Mainframe Patch", "priority": "urgent"}
    payload.update(overrides)
    return payload


async def test_create_task_defaults_xp_by_priority(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/api/v1/tasks", json=_task_payload(priority="urgent"))
    assert response.status_code == 201
    body = response.json()
    assert body["xp_value"] == 500
    assert body["status"] == "todo"


async def test_create_task_explicit_xp_value_overrides_default(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/tasks", json=_task_payload(priority="later", xp_value=999)
    )
    assert response.status_code == 201
    assert response.json()["xp_value"] == 999


async def test_list_tasks_filters_by_status(auth_client: AsyncClient) -> None:
    await auth_client.post("/api/v1/tasks", json=_task_payload(priority="urgent"))
    todo = await auth_client.post("/api/v1/tasks", json=_task_payload(priority="later"))
    await auth_client.patch(f"/api/v1/tasks/{todo.json()['id']}/complete")

    done = await auth_client.get("/api/v1/tasks", params={"status_filter": "done"})
    assert done.status_code == 200
    assert len(done.json()) == 1

    todo_only = await auth_client.get("/api/v1/tasks", params={"status_filter": "todo"})
    assert len(todo_only.json()) == 1


async def test_complete_task_awards_xp_and_updates_progress(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/tasks", json=_task_payload(priority="important"))
    task_id = created.json()["id"]

    complete = await auth_client.patch(f"/api/v1/tasks/{task_id}/complete")
    assert complete.status_code == 200
    body = complete.json()
    assert body["xp_delta"] == 250
    assert body["task"]["status"] == "done"
    assert body["task"]["completed_at"] is not None
    # 250 for the task + 100 for the `first_blood` achievement (this is the
    # user's first completed task), evaluated synchronously per D17.
    assert body["progress"]["total_xp"] == 350

    progress = await auth_client.get("/api/v1/me/progress")
    assert progress.json()["total_xp"] == 350


async def test_double_complete_does_not_double_award(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/tasks", json=_task_payload(priority="warning"))
    task_id = created.json()["id"]

    first = await auth_client.patch(f"/api/v1/tasks/{task_id}/complete")
    second = await auth_client.patch(f"/api/v1/tasks/{task_id}/complete")

    assert first.json()["xp_delta"] == 150
    assert second.json()["xp_delta"] == 0
    # 150 for the task + 100 for `first_blood`.
    assert second.json()["progress"]["total_xp"] == 250


async def test_complete_uncomplete_complete_nets_single_award(auth_client: AsyncClient) -> None:
    """The plan's highest-value XP-ledger test: rapid toggling must not let
    the user farm XP, and re-completing must not lose it either."""
    created = await auth_client.post("/api/v1/tasks", json=_task_payload(priority="urgent"))
    task_id = created.json()["id"]

    await auth_client.patch(f"/api/v1/tasks/{task_id}/complete")
    uncompleted = await auth_client.patch(f"/api/v1/tasks/{task_id}/uncomplete")
    assert uncompleted.json()["xp_delta"] == -500
    assert uncompleted.json()["task"]["status"] == "todo"
    # The one-time `first_blood` achievement (100 XP) is never reversed by
    # uncompleting the task that earned it — only the task's own 500 XP is.
    assert uncompleted.json()["progress"]["total_xp"] == 100

    recompleted = await auth_client.patch(f"/api/v1/tasks/{task_id}/complete")
    assert recompleted.json()["xp_delta"] == 500
    assert recompleted.json()["progress"]["total_xp"] == 600

    progress = await auth_client.get("/api/v1/me/progress")
    assert progress.json()["total_xp"] == 600

    events = await auth_client.get("/api/v1/me/xp-events")
    assert len(events.json()["items"]) == 4


async def test_uncomplete_already_todo_task_is_a_noop(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/tasks", json=_task_payload())
    task_id = created.json()["id"]

    response = await auth_client.patch(f"/api/v1/tasks/{task_id}/uncomplete")
    assert response.status_code == 200
    assert response.json()["xp_delta"] == 0


async def test_subtask_cannot_itself_have_a_parent(auth_client: AsyncClient) -> None:
    parent = await auth_client.post("/api/v1/tasks", json=_task_payload())
    parent_id = parent.json()["id"]
    subtask = await auth_client.post(
        f"/api/v1/tasks/{parent_id}/subtasks", json=_task_payload(title="Subtask")
    )
    assert subtask.status_code == 201
    subtask_id = subtask.json()["id"]

    grandchild = await auth_client.post(
        f"/api/v1/tasks/{subtask_id}/subtasks", json=_task_payload(title="Too deep")
    )
    assert grandchild.status_code == 422


async def test_update_and_delete_task(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/api/v1/tasks", json=_task_payload())
    task_id = created.json()["id"]

    updated = await auth_client.patch(f"/api/v1/tasks/{task_id}", json={"title": "Renamed"})
    assert updated.json()["title"] == "Renamed"

    deleted = await auth_client.delete(f"/api/v1/tasks/{task_id}")
    assert deleted.status_code == 204

    missing = await auth_client.patch(f"/api/v1/tasks/{task_id}", json={"title": "Gone"})
    assert missing.status_code == 404


async def test_reorder_tasks(auth_client: AsyncClient) -> None:
    a = (await auth_client.post("/api/v1/tasks", json=_task_payload(title="A"))).json()
    b = (await auth_client.post("/api/v1/tasks", json=_task_payload(title="B"))).json()

    reorder = await auth_client.post(
        "/api/v1/tasks/reorder", json={"task_ids": [b["id"], a["id"]]}
    )
    assert reorder.status_code == 204

    listed = (await auth_client.get("/api/v1/tasks")).json()
    assert [t["title"] for t in listed] == ["B", "A"]


async def test_tasks_are_scoped_to_the_owning_user(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "owner",
            "display_name": "Owner",
        },
    )
    created = await client.post("/api/v1/tasks", json=_task_payload())
    task_id = created.json()["id"]
    await client.post("/api/v1/auth/logout")

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "intruder",
            "display_name": "Intruder",
        },
    )
    response = await client.patch(f"/api/v1/tasks/{task_id}", json={"title": "Hijacked"})
    assert response.status_code == 404
