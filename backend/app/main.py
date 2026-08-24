"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import (
    auth,
    dashboard,
    focus,
    habits,
    notes,
    notifications,
    progress,
    projects,
    push,
    reminders,
    skilltree,
    social,
    tags,
    tasks,
)
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import RequestIDMiddleware


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="QuestFlow API",
        description="Gamified productivity hub — tasks, habits, notes, focus timer, XP engine.",
        version="0.1.0",
    )

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Outermost middleware (added last): every response, including a CORS
    # preflight short-circuit, gets an X-Request-ID header, and the id is
    # established before anything inside — including the exception
    # handlers above — might need to read it.
    app.add_middleware(RequestIDMiddleware)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(tags.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(habits.router, prefix="/api/v1")
    app.include_router(notes.router, prefix="/api/v1")
    app.include_router(focus.router, prefix="/api/v1")
    app.include_router(progress.router, prefix="/api/v1")
    app.include_router(skilltree.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")
    app.include_router(reminders.router, prefix="/api/v1")
    app.include_router(push.router, prefix="/api/v1")
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(social.router, prefix="/api/v1")

    return app


app = create_app()
