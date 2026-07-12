"""Loyalty, referral, and coupon models."""

import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.utils.enums import enum_values


class LoyaltyTier(enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class TransactionType(enum.Enum):
    EARN = "earn"
    REDEEM = "redeem"
    BONUS = "bonus"
    REFERRAL = "referral"
    BIRTHDAY = "birthday"
    FIRST_ORDER = "first_order"
    ADJUSTMENT = "adjustment"


class LoyaltyAccount(db.Model):
    """Customer loyalty points account."""

    __tablename__ = "loyalty_accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    points_balance = db.Column(db.Integer, default=0, nullable=False)
    lifetime_points = db.Column(db.Integer, default=0, nullable=False)
    tier = db.Column(db.Enum(LoyaltyTier, values_callable=enum_values), default=LoyaltyTier.BRONZE, nullable=False)
    referral_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    referred_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", foreign_keys=[user_id], back_populates="loyalty_account")
    referred_by = db.relationship("User", foreign_keys=[referred_by_id])
    transactions = db.relationship("LoyaltyTransaction", back_populates="account", lazy="dynamic")

    @staticmethod
    def generate_referral_code():
        return uuid.uuid4().hex[:8].upper()

    def update_tier(self):
        if self.lifetime_points >= 10000:
            self.tier = LoyaltyTier.PLATINUM
        elif self.lifetime_points >= 5000:
            self.tier = LoyaltyTier.GOLD
        elif self.lifetime_points >= 2000:
            self.tier = LoyaltyTier.SILVER
        else:
            self.tier = LoyaltyTier.BRONZE


class LoyaltyTransaction(db.Model):
    """Points earn/redeem history."""

    __tablename__ = "loyalty_transactions"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("loyalty_accounts.id"), nullable=False)
    transaction_type = db.Column(db.Enum(TransactionType, values_callable=enum_values), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    account = db.relationship("LoyaltyAccount", back_populates="transactions")
    order = db.relationship("Order")


class Coupon(db.Model):
    """Discount coupon / promo code."""

    __tablename__ = "coupons"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    discount_percent = db.Column(db.Numeric(5, 2))
    discount_amount = db.Column(db.Numeric(10, 2))
    min_order_amount = db.Column(db.Numeric(10, 2), default=0)
    max_uses = db.Column(db.Integer)
    uses_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    valid_from = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def is_valid(self):
        now = datetime.now(timezone.utc)
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses and self.uses_count >= self.max_uses:
            return False
        return True
