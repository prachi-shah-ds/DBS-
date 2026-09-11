"""add dashboard_layout table

Revision ID: 0002_add_dashboard_layout
Revises: <previous>
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_add_dashboard_layout'
down_revision = '<previous>'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'dashboard_layout',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=True),
        sa.Column('role', sa.String(32), nullable=True),
        sa.Column('layout_json', sa.JSON, nullable=False),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

def downgrade():
    op.drop_table('dashboard_layout')
