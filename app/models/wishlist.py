"""Wishlist and recently viewed products."""

from datetime import datetime, timezone

from app.extensions import db


class WishlistItem(db.Model):
    """Customer saved / wishlist product."""

    __tablename__ = "wishlist_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="wishlist_items")
    product = db.relationship("Product")

    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_user_wishlist_product"),)


class RecentlyViewed(db.Model):
    """Persisted recently viewed products for logged-in users."""

    __tablename__ = "recently_viewed"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    viewed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="recently_viewed")
    product = db.relationship("Product")

    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_user_recent_product"),)


class ProductView(db.Model):
    """Analytics: product page views."""

    __tablename__ = "product_views"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    ip_hash = db.Column(db.String(64))
    viewed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    product = db.relationship("Product", back_populates="views")
    user = db.relationship("User")
