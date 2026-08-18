"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import auth, dashboard, progress, projects, tags, tasks
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="QuestFlow API",
        description="Gamified productivity hub — tasks, habits, notes, focus timer, XP engine.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(tags.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(progress.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")

    return app


app = create_app()
