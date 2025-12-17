"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-12-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(512), nullable=False),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('1')),
        sa.Column('is_admin', sa.Boolean, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'products',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('price', sa.Float, server_default='0'),
        sa.Column('category', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'messages',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('role', sa.String(32), nullable=False),
        sa.Column('content', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('request_id', sa.String(128)),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('ip', sa.String(64)),
        sa.Column('action', sa.String(255)),
        sa.Column('payload', sa.Text),
        sa.Column('result', sa.Text),
        sa.Column('pii_flag', sa.Boolean, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'reindex_checkpoints',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('collection', sa.String(255), nullable=False),
        sa.Column('last_processed_id', sa.Integer, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('reindex_checkpoints')
    op.drop_table('audit_logs')
    op.drop_table('messages')
    op.drop_table('products')
    op.drop_table('users')
