from collections.abc import AsyncGenerator, Awaitable, Callable, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.deps import get_db
from app.main import app
from app.models.user import RefreshToken, User

if settings.test_database_url == settings.database_url:
    pytest.exit(
        "Refusing to run: TEST_DATABASE_URL equals DATABASE_URL — "
        "the suite would wipe dev data."
    )

test_engine = create_async_engine(settings.test_database_url, echo=False, future=True)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def _override_db_dependency() -> Generator[None, None, None]:
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def make_client() -> AsyncGenerator[Callable[..., Awaitable[AsyncClient]], None]:
    """Factory for additional authenticated users. Each call registers
    `{handle}@example.com` and returns a **separate** `AsyncClient` with its
    own cookie jar — httpx cookies are per-client, so two users genuinely
    need two clients. All of them are closed at teardown; the autouse
    `DELETE FROM users` fixture then cascades away everything they created.
    """
    created: list[AsyncClient] = []

    async def _make(handle: str, *, display_name: str | None = None) -> AsyncClient:
        transport = ASGITransport(app=app)
        ac = AsyncClient(transport=transport, base_url="http://test")
        created.append(ac)
        response = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": f"{handle}@example.com",
                "password": "correct-horse-battery-staple",
                "handle": handle,
                "display_name": display_name or handle.title(),
                "timezone": "UTC",
            },
        )
        assert response.status_code == 201, response.text
        return ac

    yield _make
    for ac in created:
        await ac.aclose()


@pytest.fixture
async def auth_client(make_client: Callable[..., Awaitable[AsyncClient]]) -> AsyncClient:
    """A client already logged in as a fresh user — most task/project/tag/
    dashboard tests need an authenticated session and don't care who it is."""
    return await make_client("player1", display_name="Player One")


@pytest.fixture(autouse=True)
async def _clean_users_and_dispose_engine() -> AsyncGenerator[None, None]:
    """Two teardown steps that must run in this exact order — combined into
    one fixture so that order is a plain code sequence rather than something
    relying on pytest's same-scope autouse ordering (which isn't reliably
    "declaration order" across fixtures with no dependency relationship):

    1. Clean up every user a test created. Every user-owned table (projects,
       tasks, xp_events, ...) has an `ON DELETE CASCADE` FK to `users`, so
       deleting the users is enough to clean up everything that test touched.
       This runs against the dedicated `questflow_test` database, never the
       dev database `api`/`web` serve.
    2. *Then* dispose the engine's connection pool. pytest-asyncio gives each
       test function its own event loop, but the pool is created lazily and
       bound to whichever loop first used it — without disposing it between
       tests, a later test's new loop can hand a query to a connection that
       belongs to an already-closed loop (surfaces as asyncpg InterfaceErrors
       or AttributeErrors deep in the Windows proactor transport). This must
       run *after* step 1, since step 1 still needs a live engine.
    """
    yield
    async with TestSessionLocal() as session:
        await session.execute(delete(RefreshToken))
        await session.execute(delete(User))
        await session.commit()
    await test_engine.dispose()
