"""Shopping cart models."""

from datetime import datetime, timezone

from app.extensions import db


class Cart(db.Model):
    """Persistent shopping cart for authenticated users."""

    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    session_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", back_populates="cart")
    items = db.relationship("CartItem", back_populates="cart", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items)

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items)

    def __repr__(self):
        return f"<Cart {self.id} user={self.user_id}>"


class CartItem(db.Model):
    """Individual line item in a shopping cart."""

    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product")

    __table_args__ = (db.UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),)

    @property
    def line_total(self):
        return float(self.product.effective_price) * self.quantity

    def __repr__(self):
        return f"<CartItem cart={self.cart_id} product={self.product_id} qty={self.quantity}>"
