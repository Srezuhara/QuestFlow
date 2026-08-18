"""Auth endpoints: register, login, refresh, logout, me.

Access/refresh tokens travel as httpOnly cookies, never in the response
body — see `_set_auth_cookies` / `_clear_auth_cookies`.
"""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    secure = settings.environment != "development"
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> User:
    try:
        user = await auth_service.register_user(db, data)
    except auth_service.EmailAlreadyRegistered as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from exc
    except auth_service.HandleAlreadyTaken as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Handle already taken"
        ) from exc

    access_token, refresh_token = await auth_service.issue_token_pair(
        db, user, request.headers.get("user-agent")
    )
    _set_auth_cookies(response, access_token, refresh_token)
    return user


@router.post("/login", response_model=UserOut)
async def login(
    data: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> User:
    try:
        user = await auth_service.authenticate_user(db, data.email, data.password)
    except auth_service.InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        ) from exc

    access_token, refresh_token = await auth_service.issue_token_pair(
        db, user, request.headers.get("user-agent")
    )
    _set_auth_cookies(response, access_token, refresh_token)
    return user


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> None:
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        access_token, new_refresh_token = await auth_service.rotate_refresh_token(
            db, refresh_token, request.headers.get("user-agent")
        )
    except auth_service.InvalidRefreshToken as exc:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session"
        ) from exc

    _set_auth_cookies(response, access_token, new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> None:
    if refresh_token is not None:
        await auth_service.revoke_refresh_token(db, refresh_token)
    _clear_auth_cookies(response)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
