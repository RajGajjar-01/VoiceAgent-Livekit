"""replace done with status and add duration_minutes to tasks

Revision ID: 3b1e5c8a9f0d
Revises: 0dbd31a546ad
Create Date: 2026-07-13

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b1e5c8a9f0d'
down_revision: str | Sequence[str] | None = '0dbd31a546ad'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('status', sa.String(), nullable=False, server_default='not_started'))
    op.add_column('tasks', sa.Column('duration_minutes', sa.Integer(), nullable=True))
    op.execute("UPDATE tasks SET status = 'completed' WHERE done = TRUE")
    op.alter_column('tasks', 'status', server_default=None)
    op.drop_column('tasks', 'done')


def downgrade() -> None:
    op.add_column('tasks', sa.Column('done', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.execute("UPDATE tasks SET done = TRUE WHERE status = 'completed'")
    op.alter_column('tasks', 'done', server_default=None)
    op.drop_column('tasks', 'duration_minutes')
    op.drop_column('tasks', 'status')
