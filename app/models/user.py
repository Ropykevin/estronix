"""User and Role models."""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Role(db.Model):
    """User role for RBAC (Role-Based Access Control)."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    users = db.relationship("User", back_populates="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    """Customer and admin user account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login = db.Column(db.DateTime)
    date_of_birth = db.Column(db.Date)
    delivery_region = db.Column(db.String(100), default="Nairobi")
    profile_image_url = db.Column(db.String(255))

    role = db.relationship("Role", back_populates="users")
    addresses = db.relationship("Address", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    cart = db.relationship("Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="user", lazy="dynamic")
    reviews = db.relationship("Review", back_populates="user", lazy="dynamic")
    wishlist_items = db.relationship("WishlistItem", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    recently_viewed = db.relationship("RecentlyViewed", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    loyalty_account = db.relationship("LoyaltyAccount", foreign_keys="LoyaltyAccount.user_id", back_populates="user", uselist=False)
    warranties = db.relationship("WarrantyRegistration", back_populates="user", lazy="dynamic")
    repair_requests = db.relationship("RepairRequest", back_populates="user", lazy="dynamic")
    trade_in_requests = db.relationship("TradeInRequest", back_populates="user", lazy="dynamic")
    notifications = db.relationship("UserNotification", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.username

    @property
    def is_admin(self):
        return self.role and self.role.name == "admin"

    @property
    def is_customer(self):
        return self.role and self.role.name == "customer"

    def __repr__(self):
        return f"<User {self.username}>"
