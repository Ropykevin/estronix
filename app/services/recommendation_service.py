"""Wishlist, recently viewed, and product recommendations."""

import hashlib

from flask import request, session
from flask_login import current_user

from app.extensions import db
from app.models import Product, ProductStatus, ProductView, RecentlyViewed, WishlistItem


class RecommendationService:
    SESSION_RECENT_KEY = "recently_viewed"

    @classmethod
    def track_view(cls, product_id):
        """Record product view for analytics and recently viewed."""
        product = Product.query.get(product_id)
        if not product:
            return
        product.view_count = (product.view_count or 0) + 1

        ip_hash = None
        if request:
            ip_hash = hashlib.sha256(request.remote_addr.encode()).hexdigest()[:16]

        db.session.add(
            ProductView(
                product_id=product_id,
                user_id=current_user.id if current_user.is_authenticated else None,
                ip_hash=ip_hash,
            )
        )

        if current_user.is_authenticated:
            existing = RecentlyViewed.query.filter_by(user_id=current_user.id, product_id=product_id).first()
            if existing:
                from datetime import datetime, timezone
                existing.viewed_at = datetime.now(timezone.utc)
            else:
                db.session.add(RecentlyViewed(user_id=current_user.id, product_id=product_id))
        else:
            recent = session.get(cls.SESSION_RECENT_KEY, [])
            if product_id in recent:
                recent.remove(product_id)
            recent.insert(0, product_id)
            session[cls.SESSION_RECENT_KEY] = recent[:12]
            session.modified = True

        db.session.commit()

    @classmethod
    def get_recently_viewed(cls, limit=8):
        if current_user.is_authenticated:
            items = (
                RecentlyViewed.query.filter_by(user_id=current_user.id)
                .order_by(RecentlyViewed.viewed_at.desc())
                .limit(limit)
                .all()
            )
            return [i.product for i in items if i.product and i.product.status == ProductStatus.ACTIVE]
        ids = session.get(cls.SESSION_RECENT_KEY, [])[:limit]
        if not ids:
            return []
        products = Product.query.filter(Product.id.in_(ids), Product.status == ProductStatus.ACTIVE).all()
        return sorted(products, key=lambda p: ids.index(p.id))

    @classmethod
    def get_recommended(cls, user=None, limit=8):
        """Recommend featured + popular products in same categories as recent views."""
        recent = cls.get_recently_viewed(3)
        if recent:
            cat_ids = list({p.category_id for p in recent})
            return (
                Product.query.filter(
                    Product.category_id.in_(cat_ids),
                    Product.status == ProductStatus.ACTIVE,
                    Product.id.notin_([p.id for p in recent]),
                )
                .order_by(Product.view_count.desc())
                .limit(limit)
                .all()
            )
        return (
            Product.query.filter_by(status=ProductStatus.ACTIVE, is_featured=True)
            .order_by(Product.view_count.desc())
            .limit(limit)
            .all()
        )


class WishlistService:
    @classmethod
    def toggle(cls, product_id):
        if not current_user.is_authenticated:
            return False, "Please log in to use wishlist."
        existing = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return True, "Removed from wishlist."
        db.session.add(WishlistItem(user_id=current_user.id, product_id=product_id))
        db.session.commit()
        return True, "Added to wishlist."

    @classmethod
    def get_items(cls):
        if not current_user.is_authenticated:
            return []
        return (
            WishlistItem.query.filter_by(user_id=current_user.id)
            .order_by(WishlistItem.created_at.desc())
            .all()
        )

    @classmethod
    def get_count(cls):
        if not current_user.is_authenticated:
            return 0
        return WishlistItem.query.filter_by(user_id=current_user.id).count()
