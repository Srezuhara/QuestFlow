import uuid
from datetime import UTC, datetime

from app.db.session import AsyncSessionLocal
from app.models.enums import XPSourceType
from app.schemas.auth import RegisterRequest
from app.services import auth_service
from app.services.gamification import xp
from app.services.gamification.leveling import level_for_xp, xp_floor_for_level, xp_progress


def test_level_for_xp_starts_at_one() -> None:
    assert level_for_xp(0) == 1
    assert level_for_xp(-100) == 1


def test_level_for_xp_is_monotonic_nondecreasing() -> None:
    prev = level_for_xp(0)
    for total in range(0, 200_000, 137):
        level = level_for_xp(total)
        assert level >= prev
        prev = level


def test_xp_progress_is_internally_consistent() -> None:
    for total in (0, 1, 99, 100, 5_000, 250_000):
        progress = xp_progress(total)
        assert 0.0 <= progress.percent <= 100.0
        assert progress.level == level_for_xp(total)
        assert xp_floor_for_level(progress.level) <= total


async def test_recompute_progress_matches_incrementally_maintained_progress() -> None:
    """The ledger is its own oracle: `recompute_progress()` rebuilds
    `user_progress` from `xp_events` alone, and must always agree with the
    version `award()` maintains incrementally on every call."""
    async with AsyncSessionLocal() as db:
        user = await auth_service.register_user(
            db,
            RegisterRequest(
                email="ledger@example.com",
                password="correct-horse-battery-staple",
                handle="ledgeruser",
                display_name="Ledger User",
                timezone="UTC",
            ),
        )

        for i, amount in enumerate([500, -500, 250, 150, -150, 75]):
            await xp.award(
                db,
                user=user,
                source_type=XPSourceType.TASK_COMPLETE,
                source_id=uuid.uuid4(),
                amount=amount,
                idempotency_key=f"test-ledger:{i}:{datetime.now(UTC).isoformat()}",
            )
        await db.commit()

        live = await xp.get_progress(db, user)
        assert live.total_xp == 325

        recomputed = await xp.recompute_progress(db, user.id)
        await db.commit()

        assert recomputed.total_xp == live.total_xp
        assert recomputed.level == live.level
        assert recomputed.last_active_on == live.last_active_on
