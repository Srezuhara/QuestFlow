"""Web Push delivery — `WebPushSender` wraps `pywebpush.webpush` behind
`asyncio.to_thread` (D7-8: pywebpush's value *is* the aes128gcm/ECDH/HKDF
payload encryption; reimplementing that by hand costs a security review to
save one context switch). `NullSender` is used when `settings.push_enabled`
is false, so the worker still does in-app delivery in a fresh clone instead
of crash-looping on a py-vapid parse error.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.reminder import PushSubscription

logger = logging.getLogger("questflow.worker.push")


@dataclass(frozen=True)
class PushResult:
    ok: bool
    gone: bool = False


class PushSender(Protocol):
    async def send(self, subscription: PushSubscription, payload: dict[str, Any]) -> PushResult: ...


_semaphore = asyncio.Semaphore(settings.push_concurrency)


class WebPushSender:
    """Real delivery via VAPID-authenticated Web Push."""

    async def send(self, subscription: PushSubscription, payload: dict[str, Any]) -> PushResult:
        async with _semaphore:
            try:
                await asyncio.to_thread(
                    webpush,
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                    },
                    data=json.dumps(payload),
                    vapid_private_key=settings.vapid_private_key,
                    vapid_claims={"sub": settings.vapid_subject},
                    timeout=settings.push_timeout_seconds,
                )
                return PushResult(ok=True)
            except WebPushException as exc:
                status_code = getattr(exc.response, "status_code", None)
                if status_code in (404, 410):
                    # The subscription no longer exists on the push
                    # service's end — prune it.
                    return PushResult(ok=False, gone=True)
                if status_code == 413:
                    logger.warning("push payload too large for %s", subscription.endpoint)
                    return PushResult(ok=False)
                if status_code == 429:
                    logger.warning("push rate-limited for %s", subscription.endpoint)
                    return PushResult(ok=False)
                logger.warning("push failed for %s: %s", subscription.endpoint, exc)
                return PushResult(ok=False)


class NullSender:
    """Used when `push_enabled` is false — logs once (at scheduler startup,
    not per-send) and never actually calls out."""

    async def send(self, subscription: PushSubscription, payload: dict[str, Any]) -> PushResult:
        return PushResult(ok=False)


async def dispatch(
    db: AsyncSession, sender: PushSender, user_id: uuid.UUID, payload: dict[str, Any]
) -> None:
    """Sends `payload` to every one of `user_id`'s push subscriptions,
    deletes any that came back `gone`, and commits. Runs *after* the
    reminder-claim transaction has already committed — push is
    at-most-once/lossy by nature (D7-5), so a send failure here must never
    roll back the in-app `Notification` that was already written."""
    subs = list(
        await db.scalars(select(PushSubscription).where(PushSubscription.user_id == user_id))
    )
    if not subs:
        return

    raw_results = await asyncio.gather(
        *(sender.send(sub, payload) for sub in subs), return_exceptions=True
    )
    results: list[PushResult] = []
    for sub, raw in zip(subs, raw_results, strict=True):
        if isinstance(raw, BaseException):
            # A raising sender must never take down the worker or roll back
            # the in-app `Notification` that's already committed — treat it
            # like any other failed-but-not-gone send.
            logger.warning("push sender raised for %s: %s", sub.endpoint, raw)
            results.append(PushResult(ok=False))
        else:
            results.append(raw)
    gone_ids = [sub.id for sub, result in zip(subs, results, strict=True) if result.gone]
    if gone_ids:
        for sub in subs:
            if sub.id in gone_ids:
                await db.delete(sub)
        await db.commit()
