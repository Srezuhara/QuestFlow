"""Skill-tree domain service. Pure-ish domain logic; no HTTP concerns — the
router translates the exceptions here into responses.

State derivation is the core rule (D13): a node is `UNLOCKED` if the user has
a `user_skill_nodes` row for it; else `AVAILABLE` if every prerequisite is
`UNLOCKED` **and** the relevant branch XP meets `xp_cost`; else `LOCKED`.
`core_nexus` (tier 0, no branch, no prerequisites) is `AVAILABLE` for every
user from the start. States are never stored — storing them would go stale
the moment XP changes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SkillBranch, SkillNodeState, XPSourceType
from app.models.gamification import XPEvent
from app.models.skilltree import SkillNode, UserSkillNode
from app.models.user import User
from app.services.gamification import achievements, xp
from app.services.gamification.leveling import LevelProgress, xp_progress


class SkillNodeNotFound(Exception):
    pass


class NodeAlreadyUnlocked(Exception):
    pass


class NodeNotAvailable(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class SkillNodeView:
    node: SkillNode
    state: SkillNodeState
    unlocked_at: datetime | None


@dataclass(frozen=True)
class SkillTreeView:
    nodes: list[SkillNodeView]
    branch_xp: dict[SkillBranch, int]


@dataclass(frozen=True)
class UnlockResult:
    node: SkillNode
    newly_available_codes: list[str]
    xp_delta: int
    progress: LevelProgress
    newly_earned_achievements: list[achievements.EarnedAchievement]


async def branch_xp(db: AsyncSession, user_id: uuid.UUID) -> dict[SkillBranch, int]:
    """Every `SkillBranch` key is always present (missing -> 0) so callers
    never `KeyError`."""
    rows = (
        await db.execute(
            select(XPEvent.skill_branch, func.coalesce(func.sum(XPEvent.awarded_xp), 0))
            .where(XPEvent.user_id == user_id, XPEvent.skill_branch.is_not(None))
            .group_by(XPEvent.skill_branch)
        )
    ).all()
    totals: dict[SkillBranch, int] = dict.fromkeys(SkillBranch, 0)
    for branch, total in rows:
        totals[branch] = int(total)
    return totals


def _derive_state(
    node: SkillNode, unlocked_codes: set[str], totals: dict[SkillBranch, int]
) -> SkillNodeState:
    if node.code in unlocked_codes:
        return SkillNodeState.UNLOCKED
    if node.tier == 0:
        return SkillNodeState.AVAILABLE
    prereqs_met = all(code in unlocked_codes for code in node.prerequisite_codes)
    xp_met = node.branch is not None and totals.get(node.branch, 0) >= node.xp_cost
    if prereqs_met and xp_met:
        return SkillNodeState.AVAILABLE
    return SkillNodeState.LOCKED


async def get_tree(db: AsyncSession, user: User) -> SkillTreeView:
    """One query for nodes, one for the user's unlocks, one for branch XP —
    three total, regardless of node count."""
    nodes = list(await db.scalars(select(SkillNode).order_by(SkillNode.tier, SkillNode.code)))
    user_nodes = list(
        await db.scalars(select(UserSkillNode).where(UserSkillNode.user_id == user.id))
    )
    totals = await branch_xp(db, user.id)

    unlocked_at_by_node_id = {un.node_id: un.unlocked_at for un in user_nodes}
    unlocked_codes = {n.code for n in nodes if n.id in unlocked_at_by_node_id}

    views = [
        SkillNodeView(
            node=node,
            state=_derive_state(node, unlocked_codes, totals),
            unlocked_at=unlocked_at_by_node_id.get(node.id),
        )
        for node in nodes
    ]
    return SkillTreeView(nodes=views, branch_xp=totals)


async def unlock_node(db: AsyncSession, user: User, code: str) -> UnlockResult:
    node = await db.scalar(select(SkillNode).where(SkillNode.code == code))
    if node is None:
        raise SkillNodeNotFound

    before = await get_tree(db, user)
    before_states = {v.node.code: v.state for v in before.nodes}
    view = next((v for v in before.nodes if v.node.code == code), None)
    if view is None:
        raise SkillNodeNotFound

    if view.state == SkillNodeState.UNLOCKED:
        raise NodeAlreadyUnlocked
    if view.state != SkillNodeState.AVAILABLE:
        # Client never decides eligibility — re-derive server-side and
        # explain the shortfall so the UI can show it verbatim.
        unlocked_codes = {v.node.code for v in before.nodes if v.state == SkillNodeState.UNLOCKED}
        missing = [c for c in node.prerequisite_codes if c not in unlocked_codes]
        if missing:
            raise NodeNotAvailable(f"Missing prerequisite(s): {', '.join(missing)}")
        branch_label = node.branch.value if node.branch is not None else "any"
        raise NodeNotAvailable(f"Requires {node.xp_cost} {branch_label} XP")

    db.add(UserSkillNode(user_id=user.id, node_id=node.id))
    await db.flush()

    xp_delta = 0
    event = await xp.award(
        db,
        user=user,
        source_type=XPSourceType.ACHIEVEMENT,
        source_id=node.id,
        amount=node.xp_cost // 10,
        idempotency_key=f"skill_unlock:{node.id}:{user.id}",
        skill_branch=node.branch,
    )
    if event is not None:
        xp_delta = event.awarded_xp

    newly_earned = await achievements.evaluate(db, user)

    await db.commit()
    await db.refresh(node)

    after = await get_tree(db, user)
    after_states = {v.node.code: v.state for v in after.nodes}
    newly_available = [
        c
        for c, state in after_states.items()
        if state == SkillNodeState.AVAILABLE and before_states.get(c) == SkillNodeState.LOCKED
    ]

    progress = await xp.get_progress(db, user)
    return UnlockResult(
        node=node,
        newly_available_codes=newly_available,
        xp_delta=xp_delta,
        progress=xp_progress(progress.total_xp),
        newly_earned_achievements=newly_earned,
    )
