"""seed achievement catalog

16 achievements per PHASE_5_6_PLAN.md §6.5's table. `downgrade()` deletes by
code (not TRUNCATE) so it composes with future catalog additions.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-20 09:25:00.000000

"""
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

achievements_table = sa.table(
    'achievements',
    sa.column('id', sa.UUID()),
    sa.column('code', sa.String()),
    sa.column('name', sa.String()),
    sa.column('description', sa.String()),
    sa.column(
        'tier',
        postgresql.ENUM(
            'bronze', 'silver', 'gold', 'legendary',
            name='achievement_tier', create_type=False,
        ),
    ),
    sa.column('icon', sa.String()),
    sa.column('xp_reward', sa.Integer()),
    sa.column('criteria', postgresql.JSONB()),
    sa.column('sort_order', sa.Integer()),
)

# (code, tier, name, description, icon, criteria kind, criteria value, xp_reward)
CATALOG: list[tuple[str, str, str, str, str, str, int, int]] = [
    ("first_blood", "bronze", "First Blood", "Complete your first quest.", "swords",
     "tasks_completed_at_least", 1, 100),
    ("task_operative", "silver", "Task Operative", "Complete 50 quests.", "target",
     "tasks_completed_at_least", 50, 500),
    ("task_overlord", "gold", "Task Overlord", "Complete 500 quests.", "crown",
     "tasks_completed_at_least", 500, 2500),
    ("streak_initiate", "bronze", "Streak Initiate", "Hold a 7-day activity streak.", "flame",
     "daily_streak_at_least", 7, 250),
    ("streak_adept", "silver", "Streak Adept", "Hold a 30-day activity streak.", "flame",
     "daily_streak_at_least", 30, 1000),
    ("streak_legend", "legendary", "Streak Legend", "Hold a 100-day activity streak.", "flame",
     "daily_streak_at_least", 100, 5000),
    ("habit_forged", "bronze", "Habit Forged", "Reach a 7-period habit streak.", "link",
     "habit_streak_at_least", 7, 250),
    ("habit_ironclad", "gold", "Habit Ironclad", "Reach a 100-period habit streak.", "anchor",
     "habit_streak_at_least", 100, 3000),
    ("first_focus", "bronze", "First Focus", "Complete 25 focus minutes.", "timer",
     "focus_minutes_at_least", 25, 100),
    ("deep_diver", "silver", "Deep Diver", "Complete 600 focus minutes.", "waves",
     "focus_minutes_at_least", 600, 750),
    ("time_lord", "gold", "Time Lord", "Complete 6000 focus minutes.", "hourglass",
     "focus_minutes_at_least", 6000, 3000),
    ("archivist", "bronze", "Archivist", "Create 10 notes in the Knowledge Vault.", "archive",
     "notes_created_at_least", 10, 200),
    ("level_10", "silver", "Level 10", "Reach level 10.", "star",
     "level_at_least", 10, 500),
    ("level_25", "gold", "Level 25", "Reach level 25.", "star",
     "level_at_least", 25, 2000),
    ("first_unlock", "bronze", "First Unlock", "Unlock your first skill node.", "unlock",
     "skill_nodes_unlocked_at_least", 1, 150),
    ("tree_walker", "legendary", "Tree Walker", "Unlock 15 skill nodes.", "network",
     "skill_nodes_unlocked_at_least", 15, 6000),
]


def _rows() -> list[dict[str, object]]:
    return [
        {
            "id": str(uuid.uuid4()),
            "code": code,
            "name": name,
            "description": description,
            "tier": tier,
            "icon": icon,
            "xp_reward": xp_reward,
            "criteria": {"kind": kind, "value": value},
            "sort_order": i,
        }
        for i, (code, tier, name, description, icon, kind, value, xp_reward) in enumerate(CATALOG)
    ]


def upgrade() -> None:
    op.bulk_insert(achievements_table, _rows())


def downgrade() -> None:
    codes = ", ".join(f"'{code}'" for code, *_ in CATALOG)
    op.execute(f"DELETE FROM user_achievements WHERE achievement_id IN (SELECT id FROM achievements WHERE code IN ({codes}))")
    op.execute(f"DELETE FROM achievements WHERE code IN ({codes})")
