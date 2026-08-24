"""add xp_events skill_branch

Revision ID: 5a3a9cdc8aae
Revises: 7597d58aca1a
Create Date: 2026-08-20 09:11:09.485254

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5a3a9cdc8aae'
down_revision: str | None = '7597d58aca1a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # D15 — nullable, stamped at award time. The `skill_branch` Postgres enum
    # type already exists (created by the phase-2 projects migration), so
    # this MUST use create_type=False or `upgrade head` fails — the exact
    # failure mode phase 3 hit (see PHASE_3_4_PLAN.md §3.4).
    op.add_column(
        'xp_events',
        sa.Column(
            'skill_branch',
            postgresql.ENUM(
                'focus', 'health', 'discipline', 'growth', 'wealth',
                name='skill_branch', create_type=False,
            ),
            nullable=True,
        ),
    )

    # Backfill historical XP so branch totals reflect all XP ever earned, not
    # just XP earned after this migration. `streak_bonus` events carry
    # `source_id = habit_id` (same as `habit_log` events) — confirmed against
    # `habit_service.log_habit`, which awards both with `source_id=habit.id`.
    op.execute("""
        UPDATE xp_events e SET skill_branch = p.skill_branch
          FROM tasks t JOIN projects p ON p.id = t.project_id
          WHERE e.source_type = 'task_complete' AND e.source_id = t.id
    """)
    op.execute("""
        UPDATE xp_events e SET skill_branch = h.skill_branch
          FROM habits h
          WHERE e.source_type IN ('habit_log', 'streak_bonus') AND e.source_id = h.id
    """)
    op.execute("""
        UPDATE xp_events e SET skill_branch = 'focus'
          WHERE e.source_type = 'focus_session' AND e.skill_branch IS NULL
    """)


def downgrade() -> None:
    op.drop_column('xp_events', 'skill_branch')
