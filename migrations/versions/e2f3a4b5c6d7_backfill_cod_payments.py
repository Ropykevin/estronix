"""Backfill completed COD payments for sales reporting.

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-07-04 07:45:00.000000
"""
from alembic import op


revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE payments
        SET status = 'COMPLETED',
            completed_at = COALESCE(completed_at, created_at, NOW())
        WHERE method = 'CASH_ON_DELIVERY'
          AND status = 'PENDING'
        """
    )
    op.execute(
        """
        UPDATE orders
        SET status = 'PROCESSING'
        WHERE status = 'PENDING'
          AND id IN (
              SELECT order_id
              FROM payments
              WHERE method = 'CASH_ON_DELIVERY'
                AND status = 'COMPLETED'
          )
        """
    )


def downgrade():
    pass
