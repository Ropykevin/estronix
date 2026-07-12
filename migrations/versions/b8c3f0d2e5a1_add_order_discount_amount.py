"""Add missing orders.discount_amount column.

Revision ID: b8c3f0d2e5a1
Revises: a7f2e9c1b4d0
Create Date: 2026-06-28 11:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "b8c3f0d2e5a1"
down_revision = "a7f2e9c1b4d0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("discount_amount", sa.Numeric(precision=10, scale=2), nullable=True, server_default="0")
        )


def downgrade():
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_column("discount_amount")
