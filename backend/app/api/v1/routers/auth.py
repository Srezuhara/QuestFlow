"""Auth endpoints: register, login, refresh, logout, me.

Access/refresh tokens travel as httpOnly cookies, never in the response
body — see `_set_auth_cookies` / `_clear_auth_cookies`.
"""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, ProfileUpdate, RegisterRequest, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _set_access_cookie(response: Response, access_token: str) -> None:
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


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    secure = settings.environment != "development"
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    _set_access_cookie(response, access_token)
    _set_refresh_cookie(response, refresh_token)


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


def _failed_refresh_response() -> JSONResponse:
    """A dead/invalid refresh token must not survive the response. Raising
    `HTTPException` here would discard `Set-Cookie` headers set on the
    injected `response` — FastAPI's exception handler builds a fresh
    `JSONResponse` that never sees them, so the dead refresh cookie stays in
    the browser and gets replayed on every subsequent 401. Returning the
    `JSONResponse` directly (with the delete-cookie headers attached first)
    is what actually clears it.
    """
    failed = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid or expired session"},
    )
    _clear_auth_cookies(failed)
    return failed


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> Response:
    if refresh_token is None:
        return _failed_refresh_response()

    try:
        access_token, new_refresh_token = await auth_service.rotate_refresh_token(
            db, refresh_token, request.headers.get("user-agent")
        )
    except auth_service.InvalidRefreshToken:
        return _failed_refresh_response()

    _set_access_cookie(response, access_token)
    if new_refresh_token is not None:
        _set_refresh_cookie(response, new_refresh_token)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


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


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await auth_service.update_profile(db, current_user, data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await auth_service.delete_account(db, current_user)
    _clear_auth_cookies(response)
