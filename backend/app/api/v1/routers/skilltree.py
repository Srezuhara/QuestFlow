"""Skill-node unlock endpoint. `GET /me/skill-tree` lives in `progress.py`
(which already owns `/me`) per the plan's preferred placement — only
`/skill-nodes/*` lives here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.enums import SkillNodeState
from app.models.user import User
from app.schemas.achievements import AchievementOut
from app.schemas.progress import LevelProgressOut
from app.schemas.skilltree import SkillNodeOut, UnlockResponse
from app.services.gamification import skilltree
from app.services.gamification.achievements import EarnedAchievement

router = APIRouter(prefix="/skill-nodes", tags=["skilltree"])


def _to_achievement_out(earned: EarnedAchievement) -> AchievementOut:
    a = earned.achievement
    return AchievementOut(
        id=a.id,
        code=a.code,
        name=a.name,
        description=a.description,
        tier=a.tier,
        icon=a.icon,
        xp_reward=a.xp_reward,
        earned_at=earned.earned_at,
        progress_percent=100.0,
    )


@router.post("/{code}/unlock", response_model=UnlockResponse)
async def unlock_node(
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UnlockResponse:
    try:
        result = await skilltree.unlock_node(db, current_user, code)
    except skilltree.SkillNodeNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Skill node not found"
        ) from exc
    except skilltree.NodeAlreadyUnlocked as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Skill node already unlocked"
        ) from exc
    except skilltree.NodeNotAvailable as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.reason) from exc

    node = result.node
    return UnlockResponse(
        node=SkillNodeOut(
            id=node.id,
            code=node.code,
            branch=node.branch,
            name=node.name,
            description=node.description,
            tier=node.tier,
            xp_cost=node.xp_cost,
            prerequisite_codes=node.prerequisite_codes,
            icon=node.icon,
            layout_x=node.layout_x,
            layout_y=node.layout_y,
            state=SkillNodeState.UNLOCKED,
            unlocked_at=None,
        ),
        newly_available=result.newly_available_codes,
        xp_delta=result.xp_delta,
        progress=LevelProgressOut.model_validate(result.progress),
        newly_earned_achievements=[
            _to_achievement_out(a) for a in result.newly_earned_achievements
        ],
    )
