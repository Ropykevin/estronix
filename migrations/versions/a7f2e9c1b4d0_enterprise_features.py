"""Enterprise features migration — warehouses, warranties, loyalty, etc.

Revision ID: a7f2e9c1b4d0
Revises: 143b86e3a6b7
Create Date: 2026-06-23 22:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "a7f2e9c1b4d0"
down_revision = "143b86e3a6b7"
branch_labels = None
depends_on = None


def upgrade():
    # Product extensions
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("model_name", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("color", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("warranty_months", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("is_preorder", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("delivery_estimate_days", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("video_url", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("youtube_url", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("manual_url", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("brochure_url", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("viewer_360_url", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("view_count", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_products_model_name"), ["model_name"], unique=False)
        batch_op.create_index(batch_op.f("ix_products_price"), ["price"], unique=False)
        batch_op.create_index(batch_op.f("ix_products_stock_quantity"), ["stock_quantity"], unique=False)

    # User extensions
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("date_of_birth", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("delivery_region", sa.String(length=100), nullable=True))

    # Order extensions
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("invoice_number", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("discount_amount", sa.Numeric(precision=10, scale=2), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("loyalty_points_redeemed", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("loyalty_discount", sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column("coupon_code", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("shipping_region", sa.String(length=100), nullable=True))
        batch_op.create_index(batch_op.f("ix_orders_invoice_number"), ["invoice_number"], unique=True)

    # Warehouses
    op.create_table(
        "warehouses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_warehouses_code"), "warehouses", ["code"], unique=True)
    op.create_index(op.f("ix_warehouses_region"), "warehouses", ["region"], unique=False)

    op.create_table(
        "warehouse_inventory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reserved", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("warehouse_id", "product_id", name="uq_warehouse_product"),
    )

    op.create_table(
        "stock_transfers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transfer_number", sa.String(length=36), nullable=False),
        sa.Column("from_warehouse_id", sa.Integer(), nullable=False),
        sa.Column("to_warehouse_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("pending", "in_transit", "completed", "cancelled", name="transferstatus"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["from_warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["to_warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stock_transfers_transfer_number"), "stock_transfers", ["transfer_number"], unique=True)

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.Enum("inbound", "outbound", "transfer", "adjustment", "sale", name="movementtype"), nullable=False),
        sa.Column("quantity_change", sa.Integer(), nullable=False),
        sa.Column("quantity_after", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Warranties
    op.create_table(
        "warranty_registrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("warranty_number", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("order_item_id", sa.Integer(), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("status", sa.Enum("active", "expired", "void", "claimed", name="warrantystatus"), nullable=False),
        sa.Column("certificate_url", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_warranty_registrations_serial_number"), "warranty_registrations", ["serial_number"], unique=False)
    op.create_index(op.f("ix_warranty_registrations_warranty_number"), "warranty_registrations", ["warranty_number"], unique=True)

    # Repairs
    op.create_table(
        "repair_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("issue_description", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("received", "diagnosing", "waiting_for_parts", "repairing", "ready_for_pickup", "completed", "cancelled", name="repairstatus"), nullable=False),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("invoice_url", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_repair_requests_ticket_number"), "repair_requests", ["ticket_number"], unique=True)

    op.create_table(
        "repair_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repair_request_id", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=255), nullable=False),
        sa.Column("caption", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["repair_request_id"], ["repair_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Trade-ins
    op.create_table(
        "trade_in_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference_number", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_brand", sa.String(length=100), nullable=False),
        sa.Column("device_model", sa.String(length=200), nullable=False),
        sa.Column("condition", sa.Enum("excellent", "good", "fair", "poor", name="devicecondition"), nullable=False),
        sa.Column("condition_notes", sa.Text(), nullable=True),
        sa.Column("estimated_value", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("final_offer", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("status", sa.Enum("submitted", "under_review", "offer_sent", "accepted", "rejected", "completed", "cancelled", name="tradeinstatus"), nullable=False),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("linked_order_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["linked_order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trade_in_requests_reference_number"), "trade_in_requests", ["reference_number"], unique=True)

    op.create_table(
        "trade_in_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trade_in_id", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["trade_in_id"], ["trade_in_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Loyalty
    op.create_table(
        "loyalty_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("points_balance", sa.Integer(), nullable=False),
        sa.Column("lifetime_points", sa.Integer(), nullable=False),
        sa.Column("tier", sa.Enum("bronze", "silver", "gold", "platinum", name="loyaltytier"), nullable=False),
        sa.Column("referral_code", sa.String(length=20), nullable=False),
        sa.Column("referred_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["referred_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_loyalty_accounts_referral_code"), "loyalty_accounts", ["referral_code"], unique=True)

    op.create_table(
        "loyalty_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.Enum("earn", "redeem", "bonus", "referral", "birthday", "first_order", "adjustment", name="transactiontype"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["loyalty_accounts.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("discount_percent", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("discount_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("min_order_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("uses_count", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("valid_from", sa.DateTime(), nullable=True),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_coupons_code"), "coupons", ["code"], unique=True)

    # Wishlist & views
    op.create_table(
        "wishlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )

    op.create_table(
        "recently_viewed",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("viewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_user_recent_product"),
    )

    op.create_table(
        "product_views",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("viewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_views_viewed_at"), "product_views", ["viewed_at"], unique=False)

    op.create_table(
        "user_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link", sa.String(length=255), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("user_notifications")
    op.drop_table("product_views")
    op.drop_table("recently_viewed")
    op.drop_table("wishlist_items")
    op.drop_table("coupons")
    op.drop_table("loyalty_transactions")
    op.drop_table("loyalty_accounts")
    op.drop_table("trade_in_images")
    op.drop_table("trade_in_requests")
    op.drop_table("repair_images")
    op.drop_table("repair_requests")
    op.drop_table("warranty_registrations")
    op.drop_table("stock_movements")
    op.drop_table("stock_transfers")
    op.drop_table("warehouse_inventory")
    op.drop_table("warehouses")

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_orders_invoice_number"))
        batch_op.drop_column("shipping_region")
        batch_op.drop_column("coupon_code")
        batch_op.drop_column("loyalty_discount")
        batch_op.drop_column("loyalty_points_redeemed")
        batch_op.drop_column("discount_amount")
        batch_op.drop_column("invoice_number")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("delivery_region")
        batch_op.drop_column("date_of_birth")

    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_products_stock_quantity"))
        batch_op.drop_index(batch_op.f("ix_products_price"))
        batch_op.drop_index(batch_op.f("ix_products_model_name"))
        batch_op.drop_column("view_count")
        batch_op.drop_column("viewer_360_url")
        batch_op.drop_column("brochure_url")
        batch_op.drop_column("manual_url")
        batch_op.drop_column("youtube_url")
        batch_op.drop_column("video_url")
        batch_op.drop_column("delivery_estimate_days")
        batch_op.drop_column("is_preorder")
        batch_op.drop_column("warranty_months")
        batch_op.drop_column("color")
        batch_op.drop_column("model_name")
