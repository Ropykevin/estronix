"""Sync enterprise model columns missing from initial migration.

Revision ID: c9d4e1f3a6b2
Revises: b8c3f0d2e5a1
Create Date: 2026-06-28 11:40:00.000000

Most columns here are already created in a7f2e9c1b4d0. Operations are
guarded so this revision can run safely on fresh and partially-migrated DBs.
"""
from alembic import op
import sqlalchemy as sa


revision = "c9d4e1f3a6b2"
down_revision = "b8c3f0d2e5a1"
branch_labels = None
depends_on = None


def _table_columns(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_indexes(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _table_constraints(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {constraint["name"] for constraint in inspector.get_unique_constraints(table_name)}


def upgrade():
    repair_columns = _table_columns("repair_requests")
    with op.batch_alter_table("repair_requests", schema=None) as batch_op:
        if "invoice_url" not in repair_columns:
            batch_op.add_column(sa.Column("invoice_url", sa.String(length=255), nullable=True))
        if "completed_at" not in repair_columns:
            batch_op.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))

    repair_image_columns = _table_columns("repair_images")
    with op.batch_alter_table("repair_images", schema=None) as batch_op:
        if "caption" not in repair_image_columns:
            batch_op.add_column(sa.Column("caption", sa.String(length=200), nullable=True))

    product_view_columns = _table_columns("product_views")
    with op.batch_alter_table("product_views", schema=None) as batch_op:
        if "ip_hash" not in product_view_columns:
            batch_op.add_column(sa.Column("ip_hash", sa.String(length=64), nullable=True))
        if "viewed_at" not in product_view_columns:
            batch_op.add_column(sa.Column("viewed_at", sa.DateTime(), nullable=True))

    if "created_at" in product_view_columns:
        op.execute(
            "UPDATE product_views SET viewed_at = created_at "
            "WHERE viewed_at IS NULL AND created_at IS NOT NULL"
        )

    product_view_columns = _table_columns("product_views")
    product_view_indexes = _table_indexes("product_views")
    with op.batch_alter_table("product_views", schema=None) as batch_op:
        if "session_id" in product_view_columns:
            batch_op.drop_column("session_id")
        if "created_at" in product_view_columns:
            batch_op.drop_column("created_at")
        if "ix_product_views_viewed_at" not in product_view_indexes:
            batch_op.create_index(batch_op.f("ix_product_views_viewed_at"), ["viewed_at"], unique=False)

    recently_viewed_columns = _table_columns("recently_viewed")
    recently_viewed_constraints = _table_constraints("recently_viewed")
    if "user_id" in recently_viewed_columns:
        op.execute("DELETE FROM recently_viewed WHERE user_id IS NULL")

    with op.batch_alter_table("recently_viewed", schema=None) as batch_op:
        if "user_id" in recently_viewed_columns:
            batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
        if "session_id" in recently_viewed_columns:
            batch_op.drop_column("session_id")
        if "uq_user_recent_product" not in recently_viewed_constraints:
            batch_op.create_unique_constraint("uq_user_recent_product", ["user_id", "product_id"])


def downgrade():
    recently_viewed_constraints = _table_constraints("recently_viewed")
    recently_viewed_columns = _table_columns("recently_viewed")

    with op.batch_alter_table("recently_viewed", schema=None) as batch_op:
        if "uq_user_recent_product" in recently_viewed_constraints:
            batch_op.drop_constraint("uq_user_recent_product", type_="unique")
        if "session_id" not in recently_viewed_columns:
            batch_op.add_column(sa.Column("session_id", sa.String(length=64), nullable=True))
        if "user_id" in recently_viewed_columns:
            batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=True)

    product_view_indexes = _table_indexes("product_views")
    product_view_columns = _table_columns("product_views")
    with op.batch_alter_table("product_views", schema=None) as batch_op:
        if "ix_product_views_viewed_at" in product_view_indexes:
            batch_op.drop_index(batch_op.f("ix_product_views_viewed_at"))
        if "created_at" not in product_view_columns:
            batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        if "session_id" not in product_view_columns:
            batch_op.add_column(sa.Column("session_id", sa.String(length=64), nullable=True))
        if "viewed_at" in product_view_columns:
            batch_op.drop_column("viewed_at")
        if "ip_hash" in product_view_columns:
            batch_op.drop_column("ip_hash")

    repair_image_columns = _table_columns("repair_images")
    with op.batch_alter_table("repair_images", schema=None) as batch_op:
        if "caption" in repair_image_columns:
            batch_op.drop_column("caption")

    repair_columns = _table_columns("repair_requests")
    with op.batch_alter_table("repair_requests", schema=None) as batch_op:
        if "completed_at" in repair_columns:
            batch_op.drop_column("completed_at")
        if "invoice_url" in repair_columns:
            batch_op.drop_column("invoice_url")
