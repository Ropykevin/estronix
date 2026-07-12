"""Reset COD payments that were counted before order was marked paid.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-07-04 07:50:00.000000
"""
from alembic import op


revision = "f3a4b5c6d7e8"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE payments
        SET status = 'PENDING',
            completed_at = NULL
        WHERE status = 'COMPLETED'
          AND order_id IN (
              SELECT id FROM orders WHERE status != 'PAID'
          )
        """
    )


def downgrade():
    pass
