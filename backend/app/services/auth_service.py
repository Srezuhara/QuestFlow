"""Auth domain service — registration, login, refresh-token rotation with
reuse detection, and logout. Routers stay thin and translate the exceptions
here into HTTP responses.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.schemas.auth import ProfileUpdate, RegisterRequest


class EmailAlreadyRegistered(Exception):
    pass


class HandleAlreadyTaken(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class InvalidRefreshToken(Exception):
    pass


# Two racing tabs (or a React StrictMode double-mount) whose access cookies
# both expired will each present the *same* raw refresh token. The loser
# would normally trip reuse-detection and get every session revoked — this
# grace window lets a rotation that already happened moments ago be treated
# as "another tab beat you to it", not theft.
REFRESH_REUSE_GRACE_SECONDS = 15


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    if await db.scalar(select(User).where(User.email == data.email)) is not None:
        raise EmailAlreadyRegistered
    if await db.scalar(select(User).where(User.handle == data.handle)) is not None:
        raise HandleAlreadyTaken

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        handle=data.handle,
        display_name=data.display_name,
        timezone=data.timezone,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise EmailAlreadyRegistered from exc
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise InvalidCredentials
    return user


async def issue_token_pair(db: AsyncSession, user: User, user_agent: str | None) -> tuple[str, str]:
    access_token = create_access_token(user.id)
    raw_refresh = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=refresh_token_expiry(),
            user_agent=user_agent,
        )
    )
    await db.commit()
    return access_token, raw_refresh


async def rotate_refresh_token(
    db: AsyncSession, raw_refresh_token: str, user_agent: str | None
) -> tuple[str, str | None]:
    """Validate + rotate a refresh token. Raises `InvalidRefreshToken` on any
    failure — including reuse of an already-rotated token outside the grace
    window, in which case every unrevoked token for that user is revoked
    (chain kill) before the exception is raised, since reuse means the token
    was likely stolen.

    Returns `(access_token, new_refresh_token)` on a normal rotation, or
    `(access_token, None)` on the grace path — a racing tab presented a token
    that *this same request cycle* already rotated moments ago. The
    successor's raw value is never stored (only its hash), so the grace path
    cannot re-emit a refresh cookie; the caller must leave the existing
    refresh cookie untouched (it already holds the successor's value, since
    both tabs share the browser cookie jar).
    """
    token_hash = hash_refresh_token(raw_refresh_token)
    token = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if token is None:
        raise InvalidRefreshToken

    now = datetime.now(UTC)

    if token.revoked_at is not None:
        grace_elapsed = now - token.revoked_at
        if token.replaced_by_id is not None and grace_elapsed <= timedelta(
            seconds=REFRESH_REUSE_GRACE_SECONDS
        ):
            user = await db.get(User, token.user_id)
            if user is None or not user.is_active:
                raise InvalidRefreshToken
            return create_access_token(user.id), None

        chain = await db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == token.user_id, RefreshToken.revoked_at.is_(None)
            )
        )
        for rt in chain:
            rt.revoked_at = now
        await db.commit()
        raise InvalidRefreshToken

    if token.expires_at < now:
        raise InvalidRefreshToken

    user = await db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise InvalidRefreshToken

    access_token = create_access_token(user.id)
    raw_new_refresh = generate_refresh_token()
    new_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_new_refresh),
        expires_at=refresh_token_expiry(),
        user_agent=user_agent,
    )
    db.add(new_token)
    await db.flush()
    token.revoked_at = now
    token.replaced_by_id = new_token.id
    await db.commit()
    return access_token, raw_new_refresh


async def revoke_refresh_token(db: AsyncSession, raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)
    token = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        await db.commit()


async def update_profile(db: AsyncSession, user: User, data: ProfileUpdate) -> User:
    """`avatar_url` is already validated against the preset allowlist by the
    schema (D9-3) — this is a plain field update, same `exclude_unset`
    pattern as `preferences_service.update_preferences` so an explicit
    `avatar_url: null` clears it while an omitted field leaves it alone."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_account(db: AsyncSession, user: User) -> None:
    """Hard delete. Every user-owned table (projects, tasks, xp_events,
    habits, notes, focus_sessions, reminders, push_subscriptions,
    notifications, user_progress, user_preferences, user_skill_nodes,
    user_achievements, refresh_tokens) has ON DELETE CASCADE to `users`, so
    this one statement is the whole implementation. If a future table does
    not cascade, this raises rather than silently orphaning rows — which is
    the correct failure mode."""
    await db.delete(user)
    await db.commit()
