"""Timezone-safe "what day is it" helpers.

`date.today()` is banned in domain code (see the ruff banned-api rule in
pyproject.toml) because streaks and daily XP caps must be computed in the
*user's* local timezone, not the server's. Every "what day is it" question
for a given user goes through `user_today()` instead.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.models.user import User


def user_today(user: User) -> date:
    """The current date in `user.timezone`, computed from a real UTC clock
    read (never a cached/mocked one) and converted — never derived from the
    server's local time."""
    return datetime.now(UTC).astimezone(ZoneInfo(user.timezone)).date()
