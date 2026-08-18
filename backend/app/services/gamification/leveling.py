"""Pure XP <-> level curve. Defined once, here — the frontend never
re-derives it; it only ever renders whatever `xp_progress()` returns.

Curve: `level = floor((total_xp / 100) ** (1/1.6)) + 1`, per the plan. This
module also provides the inverse (`xp_floor_for_level`) so the sidebar's
"XP: N% TO NEXT LEVEL" bar can be computed without a lookup table.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

LEVEL_XP_SCALE = 100
LEVEL_XP_EXPONENT = 1.6


def level_for_xp(total_xp: int) -> int:
    if total_xp <= 0:
        return 1
    root: float = (total_xp / LEVEL_XP_SCALE) ** (1 / LEVEL_XP_EXPONENT)
    return math.floor(root) + 1


def xp_floor_for_level(level: int) -> int:
    """Minimum total XP required to be *at* `level`."""
    if level <= 1:
        return 0
    powered: float = (level - 1) ** LEVEL_XP_EXPONENT
    return math.ceil(LEVEL_XP_SCALE * powered)


@dataclass(frozen=True)
class LevelProgress:
    level: int
    total_xp: int
    xp_into_level: int
    xp_for_next_level: int
    percent: float


def xp_progress(total_xp: int) -> LevelProgress:
    total_xp = max(0, total_xp)
    level = level_for_xp(total_xp)
    floor_xp = xp_floor_for_level(level)
    next_floor_xp = xp_floor_for_level(level + 1)
    into_level = total_xp - floor_xp
    span = next_floor_xp - floor_xp
    percent = 0.0 if span <= 0 else min(100.0, round((into_level / span) * 100, 1))
    return LevelProgress(
        level=level,
        total_xp=total_xp,
        xp_into_level=into_level,
        xp_for_next_level=span,
        percent=percent,
    )
