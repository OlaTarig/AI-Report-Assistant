"""add reports and report_versions

Revision ID: 87f58c8cace9
Revises: e49aa4614fc2
Create Date: 2026-09-12 23:08:39.698156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '87f58c8cace9'
down_revision: Union[str, None] = 'e49aa4614fc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('reports',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('current_version_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('conversation_id')
    )
    op.create_table('report_versions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('report_id', sa.UUID(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # Added as a separate operation (not inline in create_table above)
    # because 'reports' and 'report_versions' reference each other —
    # both tables must exist before this constraint can be satisfied.
    op.create_foreign_key(
        'fk_reports_current_version_id',
        'reports', 'report_versions',
        ['current_version_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_reports_current_version_id', 'reports', type_='foreignkey')
    op.drop_table('report_versions')
    op.drop_table('reports')
