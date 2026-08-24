"""Demo data seeding — `make seed`.

Idempotent by **fixed-identity upsert**, never delete-then-recreate, never
blind insert (D9-8, PHASE_8_9_PLAN.md §9.4.1). This runs against the **dev**
database, which holds data the developer cares about — a destructive seed
would be how a morning of manual testing gets lost, and a blind-insert seed
would silently double every row on a second run and corrupt the very
`EXPLAIN ANALYZE` numbers this exists to produce (see §9.4.2).

Every row here is created through the **real service functions** —
`task_service`, `habit_service`, `focus_service`, `project_service`,
`auth_service` — never by hand-writing `XPEvent`/`Task`/etc rows directly.
`xp_events` has exactly one legitimate writer (`gamification.xp.award`), so
anything else would not match what the app actually produces, which makes
every number this data is used to tune a fiction.

**Two real constraints in the current service layer, discovered while
writing this — not worked around, because doing so would mean bypassing the
service functions this script is required to go through:**

1. `task_service.complete_task` and `focus_service.complete_session` both
   stamp `occurred_on`/`started_at` from `datetime.now(UTC)` with **no
   backdating parameter** — unlike `habit_service.log_habit`, which takes an
   explicit `logged_for`. So task-completion and focus-session XP events in
   this seed all land on **today**, not spread across the historical window.
   Habits carry the ~90-day historical spread instead, and that is what
   actually exercises `/me/xp-summary`'s date-range grouping — the query
   §9.4.2 cares about tuning.
2. `TaskUpdate` has no `status` field and there is no task-archive endpoint,
   so only `TODO` and `DONE` are reachable through the real API. Tasks here
   are seeded as one or the other; `IN_PROGRESS`/`ARCHIVED` are not used
   because there is no real path to them to seed through.
"""

from __future__ import annotations

import asyncio
import random
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.enums import FocusMode, HabitCadence, TaskPriority
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.schemas.habits import HabitCreate
from app.schemas.projects import ProjectCreate
from app.schemas.tasks import TaskCreate
from app.services import auth_service, focus_service, habit_service, project_service, task_service

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo-password-do-not-ship"
FILLER_COUNT = 10
PROJECT_COUNT = 5
TASK_COUNT = 200
HABIT_DAYS = 90
FOCUS_SESSION_COUNT = 50

PROJECT_NAMES = [
    ("Mainframe Ops", "mainframe-ops"),
    ("Signal Corps", "signal-corps"),
    ("Deep Archive", "deep-archive"),
    ("Wetware Upkeep", "wetware-upkeep"),
    ("Black Budget", "black-budget"),
]

HABIT_SPECS = [
    ("Morning Uplink", HabitCadence.DAILY),
    ("Hydrate", HabitCadence.DAILY),
    ("Read The Feed", HabitCadence.DAILY),
    ("Weekly Retro", HabitCadence.WEEKLY),
    ("Backup Rotation", HabitCadence.WEEKLY),
    ("Deep Work Block", HabitCadence.DAILY),
]


async def _find_user(db: AsyncSession, email: str) -> User | None:
    result = await db.scalar(select(User).where(User.email == email))
    return result


async def _seed_demo_user(db: AsyncSession) -> None:
    existing = await _find_user(db, DEMO_EMAIL)
    if existing is not None:
        # D9-8: the unit of idempotency is the whole user subtree — never
        # top up child rows on a user that already exists.
        print(f"seed: demo user already exists ({DEMO_EMAIL}) — skipping subtree")
        return

    user = await auth_service.register_user(
        db,
        RegisterRequest(
            email=DEMO_EMAIL,
            password=DEMO_PASSWORD,
            handle="demo",
            display_name="Demo Architect",
            # Non-UTC on purpose (PHASE_3_4_PLAN.md §1.1): anything touching
            # dates needs at least one non-UTC case, and a UTC-only seed
            # would hide exactly the off-by-one-day bugs this project has
            # hit before.
            timezone="Asia/Kolkata",
        ),
    )

    projects = []
    for i, (name, slug) in enumerate(PROJECT_NAMES):
        project = await project_service.create_project(
            db, user, ProjectCreate(name=name, slug=slug, position=i)
        )
        projects.append(project)

    for i in range(TASK_COUNT):
        priority = random.choice(list(TaskPriority))
        due_offset = random.randint(-30, 30)
        task = await task_service.create_task(
            db,
            user,
            TaskCreate(
                title=f"Seed Quest {i:03d}",
                priority=priority,
                project_id=random.choice(projects).id if projects else None,
                due_at=datetime.now(UTC) + timedelta(days=due_offset),
            ),
        )
        if random.random() < 0.5:
            await task_service.complete_task(db, user, task.id)

    habit_ids = []
    for name, cadence in HABIT_SPECS:
        view = await habit_service.create_habit(
            db, user, HabitCreate(name=name, cadence=cadence, xp_value=50)
        )
        habit_ids.append((view.habit.id, cadence))

    today = date.today()
    for habit_id, cadence in habit_ids:
        if cadence == HabitCadence.DAILY:
            for day_offset in range(HABIT_DAYS):
                # Deliberately gapped — an unbroken streak would hide
                # streak-break bugs and isn't representative.
                if random.random() < 0.7:
                    logged_for = today - timedelta(days=day_offset)
                    await habit_service.log_habit(db, user, habit_id, logged_for=logged_for)
        else:
            for week_offset in range(HABIT_DAYS // 7):
                if random.random() < 0.75:
                    logged_for = today - timedelta(weeks=week_offset)
                    await habit_service.log_habit(db, user, habit_id, logged_for=logged_for)

    for _ in range(FOCUS_SESSION_COUNT):
        session = await focus_service.start_session(
            db, user, mode=FocusMode.FOCUS, planned_seconds=25 * 60
        )
        await focus_service.complete_session(db, user, session.id)

    print(
        f"seed: created demo user + {len(projects)} projects + {TASK_COUNT} tasks + "
        f"{len(habit_ids)} habits + {FOCUS_SESSION_COUNT} focus sessions"
    )


async def _seed_filler_users(db: AsyncSession) -> None:
    created = 0
    for i in range(1, FILLER_COUNT + 1):
        email = f"seed_user{i:02d}@example.com"
        existing = await _find_user(db, email)
        if existing is not None:
            continue

        user = await auth_service.register_user(
            db,
            RegisterRequest(
                email=email,
                password=DEMO_PASSWORD,
                handle=f"seeduser{i:02d}",
                display_name=f"Seed Filler {i:02d}",
                timezone="UTC",
            ),
        )
        # A deliberate tie: users 1 and 2 both get exactly the same XP, so
        # the leaderboard's RANK() (1, 1, 3 — not 1, 2, 3) has something
        # real to rank rather than only being exercised by tests.
        xp_value = 300 if i in (1, 2) else 100 + i * 37
        task = await task_service.create_task(
            db, user, TaskCreate(title="Seed Filler Quest", priority="later", xp_value=xp_value)
        )
        await task_service.complete_task(db, user, task.id)
        created += 1

    if created:
        print(f"seed: created {created} leaderboard filler users")
    else:
        print("seed: filler users already exist — skipping")


async def _seed() -> None:
    async with AsyncSessionLocal() as db:
        total_before = await db.scalar(select(func.count()).select_from(User))
        await _seed_demo_user(db)
        await _seed_filler_users(db)
        total_after = await db.scalar(select(func.count()).select_from(User))

        if total_before == total_after:
            print(f"seed: already applied ({total_after} users present) — nothing to do")
        else:
            print(f"seed: done ({total_before} -> {total_after} users)")


def run() -> None:
    asyncio.run(_seed())


if __name__ == "__main__":
    run()
