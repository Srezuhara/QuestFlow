"""Web Push subscription endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.push import PublicKeyOut, PushSubscriptionCreate, PushSubscriptionOut
from app.services import push_service

router = APIRouter(prefix="/push", tags=["push"])


def _to_out(sub: object) -> PushSubscriptionOut:
    return PushSubscriptionOut.model_validate(sub, from_attributes=True)


@router.get("/public-key", response_model=PublicKeyOut)
async def get_public_key() -> PublicKeyOut:
    """Diagnostic endpoint — lets the frontend confirm `VITE_VAPID_PUBLIC_KEY`
    matches what the API is actually configured with."""
    return PublicKeyOut(
        public_key=settings.vapid_public_key if settings.push_enabled else None,
        push_enabled=settings.push_enabled,
    )


@router.post(
    "/subscriptions",
    response_model=PushSubscriptionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    data: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PushSubscriptionOut:
    if not settings.push_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push is not configured on this server (placeholder VAPID keys)",
        )
    sub = await push_service.upsert_subscription(db, current_user, data)
    return _to_out(sub)


@router.get("/subscriptions", response_model=list[PushSubscriptionOut])
async def list_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PushSubscriptionOut]:
    subs = await push_service.list_subscriptions(db, current_user)
    return [_to_out(s) for s in subs]


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await push_service.delete_subscription(db, current_user, subscription_id)
    except push_service.PushSubscriptionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        ) from exc
