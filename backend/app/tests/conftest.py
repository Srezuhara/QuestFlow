from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db.session import AsyncSessionLocal, engine
from app.main import app
from app.models.user import RefreshToken, User


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """A `client` already logged in as a fresh user — most task/project/tag/
    dashboard tests need an authenticated session and don't care who it is."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "player1@example.com",
            "password": "correct-horse-battery-staple",
            "handle": "player1",
            "display_name": "Player One",
            "timezone": "UTC",
        },
    )
    return client


@pytest.fixture(autouse=True)
async def _clean_users_and_dispose_engine() -> AsyncGenerator[None, None]:
    """Two teardown steps that must run in this exact order — combined into
    one fixture so that order is a plain code sequence rather than something
    relying on pytest's same-scope autouse ordering (which isn't reliably
    "declaration order" across fixtures with no dependency relationship):

    1. Clean up every user a test created. Every user-owned table (projects,
       tasks, xp_events, ...) has an `ON DELETE CASCADE` FK to `users`, so
       deleting the users is enough to clean up everything that test touched.
    2. *Then* dispose the engine's connection pool. pytest-asyncio gives each
       test function its own event loop, but the pool is created lazily and
       bound to whichever loop first used it — without disposing it between
       tests, a later test's new loop can hand a query to a connection that
       belongs to an already-closed loop (surfaces as asyncpg InterfaceErrors
       or AttributeErrors deep in the Windows proactor transport). This must
       run *after* step 1, since step 1 still needs a live engine.
    """
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(delete(RefreshToken))
        await session.execute(delete(User))
        await session.commit()
    await engine.dispose()
