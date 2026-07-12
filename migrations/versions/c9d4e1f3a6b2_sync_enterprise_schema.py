"""Sync enterprise model columns missing from initial migration.

Revision ID: c9d4e1f3a6b2
Revises: b8c3f0d2e5a1
Create Date: 2026-06-28 11:40:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "c9d4e1f3a6b2"
down_revision = "b8c3f0d2e5a1"
branch_labels = None
depends_on = None


def upgrade():
    # repair_requests: invoice_url, completed_at
    with op.batch_alter_table("repair_requests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("invoice_url", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))

    # repair_images: caption
    with op.batch_alter_table("repair_images", schema=None) as batch_op:
        batch_op.add_column(sa.Column("caption", sa.String(length=200), nullable=True))

    # product_views: align with model (ip_hash, viewed_at)
    with op.batch_alter_table("product_views", schema=None) as batch_op:
        batch_op.add_column(sa.Column("ip_hash", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("viewed_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE product_views SET viewed_at = created_at WHERE viewed_at IS NULL AND created_at IS NOT NULL")

    with op.batch_alter_table("product_views", schema=None) as batch_op:
        batch_op.drop_column("session_id")
        batch_op.drop_column("created_at")
        batch_op.create_index(batch_op.f("ix_product_views_viewed_at"), ["viewed_at"], unique=False)

    # recently_viewed: remove session_id, enforce user_id + unique pair
    op.execute("DELETE FROM recently_viewed WHERE user_id IS NULL")

    with op.batch_alter_table("recently_viewed", schema=None) as batch_op:
        batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column("session_id")
        batch_op.create_unique_constraint("uq_user_recent_product", ["user_id", "product_id"])


def downgrade():
    with op.batch_alter_table("recently_viewed", schema=None) as batch_op:
        batch_op.drop_constraint("uq_user_recent_product", type_="unique")
        batch_op.add_column(sa.Column("session_id", sa.String(length=64), nullable=True))
        batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table("product_views", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_product_views_viewed_at"))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("session_id", sa.String(length=64), nullable=True))
        batch_op.drop_column("viewed_at")
        batch_op.drop_column("ip_hash")

    with op.batch_alter_table("repair_images", schema=None) as batch_op:
        batch_op.drop_column("caption")

    with op.batch_alter_table("repair_requests", schema=None) as batch_op:
        batch_op.drop_column("completed_at")
        batch_op.drop_column("invoice_url")
