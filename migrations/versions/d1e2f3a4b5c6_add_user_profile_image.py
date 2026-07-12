"""Add optional profile image URL to users.

Revision ID: d1e2f3a4b5c6
Revises: c9d4e1f3a6b2
Create Date: 2026-07-04 07:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "d1e2f3a4b5c6"
down_revision = "c9d4e1f3a6b2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("profile_image_url", sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("profile_image_url")
