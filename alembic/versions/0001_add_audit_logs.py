"""create audit_logs

Revision ID: 0001_add_audit_logs
Revises: <previous>
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_add_audit_logs'
down_revision = '<previous>'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=True,
        sa.Column('action', sa.String(128), nullable=False),
        sa.Column('target', sa.String(256), nullable=True),
        sa.Column('details', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('audit_logs')
