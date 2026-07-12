"""Order models."""

import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.utils.enums import enum_names


class OrderStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(db.Model):
    """Customer order."""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(36), unique=True, nullable=False, index=True)
    invoice_number = db.Column(db.String(36), unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.Enum(OrderStatus, values_callable=enum_names), default=OrderStatus.PENDING, nullable=False, index=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_cost = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    loyalty_points_redeemed = db.Column(db.Integer, default=0)
    loyalty_discount = db.Column(db.Numeric(10, 2), default=0)
    coupon_code = db.Column(db.String(50))
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_region = db.Column(db.String(100))
    shipping_address = db.Column(db.Text)
    billing_address = db.Column(db.Text)
    customer_notes = db.Column(db.Text)
    admin_notes = db.Column(db.Text)
    tracking_number = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    paid_at = db.Column(db.DateTime)
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", lazy="dynamic", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="order", lazy="dynamic")

    @staticmethod
    def generate_order_number():
        return f"EST-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def generate_invoice_number():
        return f"INV-{uuid.uuid4().hex[:12].upper()}"

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(db.Model):
    """Line item within an order (price snapshot at time of purchase)."""

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_sku = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"
