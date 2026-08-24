"""Push-subscription domain service — DB only, no network. Web Push delivery
itself lives in `app/workers/push.py`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import PushSubscription
from app.models.user import User
from app.schemas.push import PushSubscriptionCreate


class PushSubscriptionNotFound(Exception):
    pass


async def upsert_subscription(
    db: AsyncSession, user: User, data: PushSubscriptionCreate
) -> PushSubscription:
    """`endpoint` is globally unique per browser per VAPID key — re-
    subscribing (or a shared device changing accounts) must upsert, never
    insert a duplicate row."""
    # `last_seen_at`'s server_default only fires on INSERT; bump it
    # explicitly on the UPDATE branch too, via a plain SQL `now()` rather
    # than a Python value so it's always the DB's clock.
    stmt = (
        insert(PushSubscription)
        .values(
            user_id=user.id,
            endpoint=data.endpoint,
            p256dh=data.p256dh,
            auth=data.auth,
            user_agent=data.user_agent,
        )
        .on_conflict_do_update(
            index_elements=[PushSubscription.endpoint],
            set_={
                "user_id": user.id,
                "p256dh": data.p256dh,
                "auth": data.auth,
                "user_agent": data.user_agent,
                "last_seen_at": func.now(),
            },
        )
        .returning(PushSubscription)
    )
    result = await db.execute(stmt)
    await db.commit()
    row = result.scalar_one()
    await db.refresh(row)
    return row


async def list_subscriptions(db: AsyncSession, user: User) -> list[PushSubscription]:
    return list(
        await db.scalars(
            select(PushSubscription)
            .where(PushSubscription.user_id == user.id)
            .order_by(PushSubscription.last_seen_at.desc())
        )
    )


async def delete_subscription(db: AsyncSession, user: User, subscription_id: uuid.UUID) -> None:
    sub = await db.get(PushSubscription, subscription_id)
    if sub is None or sub.user_id != user.id:
        raise PushSubscriptionNotFound
    await db.delete(sub)
    await db.commit()


async def delete_by_endpoint(db: AsyncSession, endpoint: str) -> None:
    """Used by the worker to prune subscriptions that turned out `gone`
    (404/410 from the push service)."""
    sub = await db.scalar(select(PushSubscription).where(PushSubscription.endpoint == endpoint))
    if sub is not None:
        await db.delete(sub)
        await db.commit()
