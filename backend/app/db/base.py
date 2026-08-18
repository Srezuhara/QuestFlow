"""SQLAlchemy 2.0 declarative base.

All ORM models (phase 2+) inherit from `Base`. Alembic's `env.py` imports
this module's metadata as the autogenerate target.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all QuestFlow ORM models."""
