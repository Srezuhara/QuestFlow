"""add refresh_tokens replaced_by_id

Revision ID: 9a33cae20039
Revises: 4d5b624dd0d1
Create Date: 2026-08-20 07:14:44.403623

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a33cae20039'
down_revision: str | None = '4d5b624dd0d1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('refresh_tokens', sa.Column('replaced_by_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_refresh_tokens_replaced_by_id_refresh_tokens',
        'refresh_tokens',
        'refresh_tokens',
        ['replaced_by_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_refresh_tokens_replaced_by_id_refresh_tokens', 'refresh_tokens', type_='foreignkey'
    )
    op.drop_column('refresh_tokens', 'replaced_by_id')
