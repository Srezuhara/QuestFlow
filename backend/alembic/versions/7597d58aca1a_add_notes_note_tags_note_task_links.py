"""add notes note_tags note_task_links

Revision ID: 7597d58aca1a
Revises: 9a33cae20039
Create Date: 2026-08-20 08:00:44.834983

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7597d58aca1a'
down_revision: str | None = '9a33cae20039'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('notes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('body_md', sa.Text(), server_default='', nullable=False),
    sa.Column('is_pinned', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('archived_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notes_user_id'), 'notes', ['user_id'], unique=False)
    op.create_table('note_tags',
    sa.Column('note_id', sa.UUID(), nullable=False),
    sa.Column('tag_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('note_id', 'tag_id')
    )
    op.create_table('note_task_links',
    sa.Column('note_id', sa.UUID(), nullable=False),
    sa.Column('task_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('note_id', 'task_id')
    )

    # `search_vector` is a DB-maintained generated column — Alembic
    # autogenerate cannot emit `GENERATED ALWAYS AS ... STORED`, so it's
    # written by hand here. `env.py`'s `include_object` filter keeps future
    # autogenerate runs from trying to ALTER/DROP it.
    op.execute("""
        ALTER TABLE notes ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(body_md, '')), 'B')
        ) STORED
    """)
    op.execute("CREATE INDEX ix_notes_search_vector ON notes USING GIN (search_vector)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_notes_search_vector")
    op.execute("ALTER TABLE notes DROP COLUMN IF EXISTS search_vector")
    op.drop_table('note_task_links')
    op.drop_table('note_tags')
    op.drop_index(op.f('ix_notes_user_id'), table_name='notes')
    op.drop_table('notes')
