"""The Command Center's single aggregated payload."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import DashboardOut, PipelineOut
from app.schemas.progress import LevelProgressOut, XPEventOut
from app.schemas.tasks import TaskOut
from app.services import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
async def get_dashboard(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> DashboardOut:
    dashboard = await dashboard_service.get_dashboard(db, current_user)
    return DashboardOut(
        objectives=[TaskOut.model_validate(t) for t in dashboard.objectives],
        active_count=dashboard.active_count,
        pipeline=PipelineOut(
            due_tomorrow=[TaskOut.model_validate(t) for t in dashboard.pipeline.due_tomorrow],
            due_next_week=[TaskOut.model_validate(t) for t in dashboard.pipeline.due_next_week],
        ),
        progress=LevelProgressOut.model_validate(dashboard.progress),
        recent_activity=[XPEventOut.model_validate(e) for e in dashboard.recent_activity],
    )
