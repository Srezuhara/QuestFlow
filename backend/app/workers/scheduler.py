"""APScheduler worker entrypoint — polls for due reminders and dispatches
Web Push (D7-3/D7-4: `AsyncIOScheduler` + the default in-memory job store; see
the module-level docstring precedent argued in `PHASE_7_8_9_PLAN.md` §B.0).

`datetime.now(UTC)` appears exactly once in this whole feature — in `tick`'s
default argument. That is the entire testability story: every test passes an
explicit `now`, no freezegun, no sleeping, no new dependency.

*Deliberately out of scope*: the "streak at risk" nudge job — it needs
per-user-timezone local-hour bucketing (group users by `timezone`, fire each
group at its local 20:00). Left for a future phase.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.enums import ReminderChannel
from app.services import reminder_service
from app.workers import push
from app.workers.push import NullSender, PushSender, WebPushSender

logging.basicConfig(level=logging.INFO, format="%(asctime)s worker %(levelname)s %(message)s")
logger = logging.getLogger("questflow.worker")


async def tick(sender: PushSender, now: datetime | None = None) -> int:
    """One poll cycle: claim due reminders (durable, transactional — see
    `reminder_service.claim_due_reminders`), then best-effort push each one
    outside that transaction. Returns the number of reminders claimed, so
    tests can assert on it directly."""
    now = now or datetime.now(UTC)
    try:
        async with AsyncSessionLocal() as db:
            due = await reminder_service.claim_due_reminders(
                db, now=now, limit=settings.reminder_batch_size
            )
    except ProgrammingError:
        # A fresh clone with unrun migrations — log and retry next tick
        # rather than crash-looping the whole worker.
        logger.exception("reminders table not ready yet (migrations not applied?)")
        return 0

    for reminder in due:
        if ReminderChannel.PUSH in reminder.channels and not reminder_service.is_stale(
            reminder, now
        ):
            async with AsyncSessionLocal() as db:
                await push.dispatch(
                    db,
                    sender,
                    reminder.user_id,
                    {
                        "reminder_id": str(reminder.id),
                        "message": reminder.message,
                        "url": "/reminders",
                    },
                )
    return len(due)


async def _tick_job(sender: PushSender) -> None:
    try:
        await tick(sender)
    except Exception:
        # One bad reminder must not kill the scheduler.
        logger.exception("reminder poll tick failed")


async def _main_async() -> None:
    push_enabled = settings.push_enabled
    sender: PushSender = WebPushSender() if push_enabled else NullSender()
    if not push_enabled:
        logger.info("push disabled: placeholder VAPID keys")

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        _tick_job,
        "interval",
        seconds=settings.reminder_poll_seconds,
        args=[sender],
        id="poll_due_reminders",
        coalesce=True,
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler started (push_enabled=%s)", push_enabled)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _handle_sigterm() -> None:
        logger.info("SIGTERM received, shutting down scheduler")
        scheduler.shutdown(wait=True)
        stop_event.set()

    # Not every platform supports signal handlers on the event loop (e.g.
    # native Windows); the container runtime is always Linux, so this is a
    # defensive no-op rather than a real gap.
    with contextlib.suppress(NotImplementedError):
        loop.add_signal_handler(signal.SIGTERM, _handle_sigterm)

    await stop_event.wait()


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
