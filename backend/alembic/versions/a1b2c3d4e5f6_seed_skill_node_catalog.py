"""seed skill node catalog

D16 — the skill-node catalog is global reference data, seeded here (not by
`make seed`, which is for demo *user* data). D20 — layout is radial, computed
in this migration: `core_nexus` at (0, 0); branch *i* (declaration order —
focus, health, discipline, growth, wealth) at angle `i * 72deg` measured from
straight up; a tier-*t* node at
`(round(sin(angle) * t * 120), round(-cos(angle) * t * 120))`.

Revision ID: a1b2c3d4e5f6
Revises: f11cc752ae9a
Create Date: 2026-08-20 09:20:00.000000

"""
import math
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = 'f11cc752ae9a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

skill_nodes_table = sa.table(
    'skill_nodes',
    sa.column('id', sa.UUID()),
    sa.column('code', sa.String()),
    sa.column(
        'branch',
        postgresql.ENUM(
            'focus', 'health', 'discipline', 'growth', 'wealth',
            name='skill_branch', create_type=False,
        ),
    ),
    sa.column('name', sa.String()),
    sa.column('description', sa.String()),
    sa.column('tier', sa.Integer()),
    sa.column('xp_cost', sa.Integer()),
    sa.column('prerequisite_codes', sa.ARRAY(sa.String())),
    sa.column('icon', sa.String()),
    sa.column('layout_x', sa.Integer()),
    sa.column('layout_y', sa.Integer()),
)

# Branch declaration order — see app/models/enums.py::SkillBranch.
BRANCHES = ["focus", "health", "discipline", "growth", "wealth"]

XP_COST_BY_TIER = {1: 500, 2: 2000, 3: 6000, 4: 15000, 5: 40000}

BRANCH_CODES: dict[str, list[str]] = {
    "focus": ["deep_work", "time_block", "flow_state", "single_thread", "monk_mode"],
    "health": ["hydration", "cold_shower", "nutrition", "fitness_core", "peak_vitality"],
    "discipline": ["early_rise", "no_snooze", "sleep_cycle", "iron_will", "unbreakable"],
    "growth": ["daily_reading", "note_taking", "skill_drill", "teach_back", "polymath"],
    "wealth": ["expense_log", "budget_lock", "invest_habit", "side_income", "compound_engine"],
}

DESCRIPTIONS: dict[str, str] = {
    "deep_work": "Silence the noise floor and hold a single thread of execution.",
    "time_block": "Carve the day into armored blocks the calendar can't breach.",
    "flow_state": "Slip past the friction layer into pure signal.",
    "single_thread": "One objective, zero context-switch tax.",
    "monk_mode": "Full lockdown — every cycle routed to the mission.",
    "hydration": "Keep the wetware running at spec.",
    "cold_shower": "Shock the system online before the grid does.",
    "nutrition": "Fuel the chassis on a real supply chain, not vending-machine scraps.",
    "fitness_core": "Load-bearing structure — reinforce it daily.",
    "peak_vitality": "Redline sustained without a system fault.",
    "early_rise": "Beat the sun to the terminal.",
    "no_snooze": "First alarm, first move — no negotiating with the old self.",
    "sleep_cycle": "Reboot on a fixed schedule the body can trust.",
    "iron_will": "The plan survives contact with resistance.",
    "unbreakable": "No override, no excuse — the discipline holds.",
    "daily_reading": "Feed the archive one page at a time.",
    "note_taking": "Compress the signal before it decays.",
    "skill_drill": "Repetition until the motion is muscle memory.",
    "teach_back": "If you can explain it, you actually own it.",
    "polymath": "Cross-wire the disciplines until new paths light up.",
    "expense_log": "Every credit tracked — no leaks in the ledger.",
    "budget_lock": "Hard limits, hard-coded.",
    "invest_habit": "Compound interest doesn't care about your excuses.",
    "side_income": "A second income stream, running in parallel.",
    "compound_engine": "The money now works the night shift too.",
}

ICONS: dict[str, str] = {
    "deep_work": "brain-circuit",
    "time_block": "calendar-clock",
    "flow_state": "waves",
    "single_thread": "git-commit-horizontal",
    "monk_mode": "shield",
    "hydration": "droplet",
    "cold_shower": "snowflake",
    "nutrition": "apple",
    "fitness_core": "dumbbell",
    "peak_vitality": "heart-pulse",
    "early_rise": "sunrise",
    "no_snooze": "alarm-clock",
    "sleep_cycle": "moon",
    "iron_will": "shield-check",
    "unbreakable": "gem",
    "daily_reading": "book-open",
    "note_taking": "notebook-pen",
    "skill_drill": "target",
    "teach_back": "presentation",
    "polymath": "sparkles",
    "expense_log": "receipt",
    "budget_lock": "lock",
    "invest_habit": "trending-up",
    "side_income": "banknote",
    "compound_engine": "infinity",
}

ALL_CODES = ["core_nexus"] + [code for codes in BRANCH_CODES.values() for code in codes]


def _node_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "id": str(uuid.uuid4()),
            "code": "core_nexus",
            "branch": None,
            "name": "Core Nexus",
            "description": "The origin node — every discipline branches from here.",
            "tier": 0,
            "xp_cost": 0,
            "prerequisite_codes": [],
            "icon": "circuit-board",
            "layout_x": 0,
            "layout_y": 0,
        }
    ]
    for i, branch in enumerate(BRANCHES):
        angle = math.radians(i * 72)
        codes = BRANCH_CODES[branch]
        for tier, code in enumerate(codes, start=1):
            prereq = "core_nexus" if tier == 1 else codes[tier - 2]
            rows.append(
                {
                    "id": str(uuid.uuid4()),
                    "code": code,
                    "branch": branch,
                    "name": code.replace("_", " ").title(),
                    "description": DESCRIPTIONS[code],
                    "tier": tier,
                    "xp_cost": XP_COST_BY_TIER[tier],
                    "prerequisite_codes": [prereq],
                    "icon": ICONS[code],
                    "layout_x": round(math.sin(angle) * tier * 120),
                    "layout_y": round(-math.cos(angle) * tier * 120),
                }
            )
    return rows


def upgrade() -> None:
    op.bulk_insert(skill_nodes_table, _node_rows())


def downgrade() -> None:
    op.execute(
        "DELETE FROM skill_nodes WHERE code IN ("
        + ", ".join(f"'{code}'" for code in ALL_CODES)
        + ")"
    )
