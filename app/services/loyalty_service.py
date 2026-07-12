"""Loyalty points, referrals, and coupon redemption."""

from flask import current_app

from app.extensions import db
from app.models import Coupon, LoyaltyAccount, LoyaltyTransaction, LoyaltyTier, TransactionType, UserNotification

POINTS_PER_KES = 1  # 1 point per KES spent
REDEMPTION_RATE = 100  # 100 points = KES 1 discount


class LoyaltyService:
    @classmethod
    def get_or_create_account(cls, user):
        account = user.loyalty_account
        if not account:
            account = LoyaltyAccount(
                user_id=user.id,
                referral_code=LoyaltyAccount.generate_referral_code(),
            )
            db.session.add(account)
            db.session.commit()
        return account

    @classmethod
    def earn_from_order(cls, user, order):
        account = cls.get_or_create_account(user)
        points = int(float(order.total_amount) * POINTS_PER_KES)
        if points <= 0:
            return
        account.points_balance += points
        account.lifetime_points += points
        account.update_tier()
        db.session.add(
            LoyaltyTransaction(
                account_id=account.id,
                transaction_type=TransactionType.EARN,
                points=points,
                balance_after=account.points_balance,
                description=f"Purchase {order.order_number}",
                order_id=order.id,
            )
        )
        db.session.commit()

    @classmethod
    def redeem_points(cls, user, points):
        account = cls.get_or_create_account(user)
        if points > account.points_balance:
            return None, "Insufficient points."
        discount = round(points / REDEMPTION_RATE, 2)
        account.points_balance -= points
        db.session.add(
            LoyaltyTransaction(
                account_id=account.id,
                transaction_type=TransactionType.REDEEM,
                points=-points,
                balance_after=account.points_balance,
                description=f"Redeemed for KES {discount:,.2f} discount",
            )
        )
        db.session.commit()
        return discount, None

    @classmethod
    def apply_referral(cls, new_user, referral_code):
        referrer_account = LoyaltyAccount.query.filter_by(referral_code=referral_code.upper()).first()
        if not referrer_account or referrer_account.user_id == new_user.id:
            return False
        new_account = cls.get_or_create_account(new_user)
        new_account.referred_by_id = referrer_account.user_id
        bonus = 500
        referrer_account.points_balance += bonus
        referrer_account.lifetime_points += bonus
        new_account.points_balance += 200
        new_account.lifetime_points += 200
        db.session.add(
            LoyaltyTransaction(
                account_id=referrer_account.id,
                transaction_type=TransactionType.REFERRAL,
                points=bonus,
                balance_after=referrer_account.points_balance,
                description=f"Referral: {new_user.username}",
            )
        )
        db.session.commit()
        return True

    @classmethod
    def validate_coupon(cls, code, order_total):
        coupon = Coupon.query.filter_by(code=code.upper()).first()
        if not coupon or not coupon.is_valid():
            return None, "Invalid or expired coupon."
        if order_total < float(coupon.min_order_amount or 0):
            return None, f"Minimum order KES {coupon.min_order_amount:,.0f} required."
        if coupon.discount_percent:
            discount = round(float(order_total) * float(coupon.discount_percent) / 100, 2)
        else:
            discount = float(coupon.discount_amount or 0)
        return {"coupon": coupon, "discount": discount}, None

    @classmethod
    def use_coupon(cls, coupon):
        coupon.uses_count += 1
        db.session.commit()
