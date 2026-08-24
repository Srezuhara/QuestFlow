"""The important test file (per PHASE_7_8_9_PLAN.md §B.8): exercises the
worker's whole entry point directly against the real (test) DB, with an
injected clock and a fake `PushSender`, no APScheduler involved."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import select

import app.workers.scheduler as scheduler_module
from app.core.config import settings
from app.models.enums import ReminderChannel, ReminderStatus
from app.models.reminder import Notification, PushSubscription, Reminder
from app.schemas.auth import RegisterRequest
from app.services import auth_service, reminder_service
from app.tests.conftest import TestSessionLocal as AsyncSessionLocal
from app.workers import push
from app.workers.scheduler import tick


@pytest.fixture(autouse=True)
def _worker_uses_the_test_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """`tick()` opens its own sessions (the worker is a standalone process,
    not part of the FastAPI app, so there's no `get_db` dependency to
    override) — point its module-level `AsyncSessionLocal` at the dedicated
    test database for the duration of these tests, same database every
    other test in this suite runs against."""
    monkeypatch.setattr(scheduler_module, "AsyncSessionLocal", AsyncSessionLocal)


@dataclass
class RecordingSender:
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    gone_endpoints: set[str] = field(default_factory=set)
    raises: bool = False

    async def send(
        self, subscription: PushSubscription, payload: dict[str, Any]
    ) -> push.PushResult:
        if self.raises:
            raise RuntimeError("boom")
        self.calls.append((subscription.endpoint, payload))
        if subscription.endpoint in self.gone_endpoints:
            return push.PushResult(ok=False, gone=True)
        return push.PushResult(ok=True)


async def _make_user(handle: str) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        user = await auth_service.register_user(
            db,
            RegisterRequest(
                email=f"{handle}@example.com",
                password="correct-horse-battery-staple",
                handle=handle,
                display_name=handle,
                timezone="UTC",
            ),
        )
        await db.commit()
        return user.id


async def _make_reminder(
    user_id: uuid.UUID,
    remind_at: datetime,
    *,
    channels: list[ReminderChannel] | None = None,
    status: ReminderStatus = ReminderStatus.SCHEDULED,
) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        reminder = Reminder(
            user_id=user_id,
            message="Test reminder",
            remind_at=remind_at,
            channels=channels or [ReminderChannel.PUSH, ReminderChannel.IN_APP],
            status=status,
        )
        db.add(reminder)
        await db.commit()
        await db.refresh(reminder)
        return reminder.id


async def _make_subscription(user_id: uuid.UUID, endpoint: str) -> None:
    async with AsyncSessionLocal() as db:
        db.add(
            PushSubscription(
                user_id=user_id, endpoint=endpoint, p256dh="p256dh", auth="auth"
            )
        )
        await db.commit()


async def _notification_count(user_id: uuid.UUID) -> int:
    async with AsyncSessionLocal() as db:
        rows = list(
            await db.scalars(select(Notification).where(Notification.user_id == user_id))
        )
        return len(rows)


async def test_claims_only_due_and_scheduled_rows() -> None:
    user_id = await _make_user("player_due")
    now = datetime.now(UTC)
    due_id = await _make_reminder(user_id, now - timedelta(seconds=1))
    await _make_reminder(user_id, now + timedelta(hours=1))  # not due yet
    await _make_reminder(user_id, now - timedelta(hours=1), status=ReminderStatus.CANCELLED)

    claimed = await tick(RecordingSender(), now=now)
    assert claimed == 1

    async with AsyncSessionLocal() as db:
        reminder = await db.get(Reminder, due_id)
        assert reminder is not None
        assert reminder.status == ReminderStatus.SENT
        assert reminder.sent_at is not None


async def test_creates_exactly_one_notification_and_tick_twice_is_idempotent() -> None:
    user_id = await _make_user("player_once")
    now = datetime.now(UTC)
    await _make_reminder(user_id, now - timedelta(seconds=1))

    await tick(RecordingSender(), now=now)
    await tick(RecordingSender(), now=now + timedelta(seconds=5))

    assert await _notification_count(user_id) == 1


async def test_push_goes_to_owners_subscriptions_only() -> None:
    owner_id = await _make_user("owner_push")
    other_id = await _make_user("other_push")
    await _make_subscription(owner_id, "https://push.example.com/owner")
    await _make_subscription(other_id, "https://push.example.com/other")
    now = datetime.now(UTC)
    await _make_reminder(owner_id, now - timedelta(seconds=1))

    sender = RecordingSender()
    await tick(sender, now=now)

    endpoints = {endpoint for endpoint, _ in sender.calls}
    assert endpoints == {"https://push.example.com/owner"}


async def test_in_app_only_channel_never_calls_sender() -> None:
    user_id = await _make_user("player_inapp")
    await _make_subscription(user_id, "https://push.example.com/inapp")
    now = datetime.now(UTC)
    await _make_reminder(user_id, now - timedelta(seconds=1), channels=[ReminderChannel.IN_APP])

    sender = RecordingSender()
    await tick(sender, now=now)

    assert sender.calls == []
    assert await _notification_count(user_id) == 1


async def test_gone_subscription_is_deleted_notification_survives() -> None:
    user_id = await _make_user("player_gone")
    await _make_subscription(user_id, "https://push.example.com/gone")
    now = datetime.now(UTC)
    await _make_reminder(user_id, now - timedelta(seconds=1))

    sender = RecordingSender(gone_endpoints={"https://push.example.com/gone"})
    await tick(sender, now=now)

    async with AsyncSessionLocal() as db:
        subs = list(
            await db.scalars(select(PushSubscription).where(PushSubscription.user_id == user_id))
        )
        assert subs == []
    assert await _notification_count(user_id) == 1


async def test_sender_raising_still_commits_the_notification() -> None:
    user_id = await _make_user("player_raise")
    await _make_subscription(user_id, "https://push.example.com/raise")
    now = datetime.now(UTC)
    await _make_reminder(user_id, now - timedelta(seconds=1))

    sender = RecordingSender(raises=True)
    await tick(sender, now=now)

    assert await _notification_count(user_id) == 1


async def test_past_misfire_grace_gets_notification_but_no_push() -> None:
    user_id = await _make_user("player_stale")
    await _make_subscription(user_id, "https://push.example.com/stale")
    now = datetime.now(UTC)
    stale_at = now - timedelta(minutes=settings.reminder_misfire_grace_minutes + 1)
    await _make_reminder(user_id, stale_at)

    sender = RecordingSender()
    await tick(sender, now=now)

    assert sender.calls == []
    assert await _notification_count(user_id) == 1


async def test_no_due_rows_returns_zero() -> None:
    user_id = await _make_user("player_none")
    now = datetime.now(UTC)
    await _make_reminder(user_id, now + timedelta(hours=1))

    claimed = await tick(RecordingSender(), now=now)
    assert claimed == 0


async def test_is_stale_reflects_the_misfire_grace_setting() -> None:
    user_id = await _make_user("player_helper")
    now = datetime.now(UTC)
    reminder_id = await _make_reminder(
        user_id, now - timedelta(minutes=settings.reminder_misfire_grace_minutes + 5)
    )
    async with AsyncSessionLocal() as db:
        reminder = await db.get(Reminder, reminder_id)
        assert reminder is not None
        assert reminder_service.is_stale(reminder, now) is True
        assert reminder_service.is_stale(reminder, reminder.remind_at) is False
