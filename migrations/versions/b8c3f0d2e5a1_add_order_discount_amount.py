"""Add missing orders.discount_amount column.

Revision ID: b8c3f0d2e5a1
Revises: a7f2e9c1b4d0
Create Date: 2026-06-28 11:30:00.000000

Note: discount_amount is already created in a7f2e9c1b4d0. This revision
remains in the chain for compatibility with databases that were stamped
before that column was consolidated.
"""
from alembic import op
import sqlalchemy as sa


revision = "b8c3f0d2e5a1"
down_revision = "a7f2e9c1b4d0"
branch_labels = None
depends_on = None


def _orders_has_column(name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return name in {column["name"] for column in inspector.get_columns("orders")}


def upgrade():
    if _orders_has_column("discount_amount"):
        return

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("discount_amount", sa.Numeric(precision=10, scale=2), nullable=True, server_default="0")
        )


def downgrade():
    if not _orders_has_column("discount_amount"):
        return

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_column("discount_amount")
