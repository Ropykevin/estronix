"""Product search and listing service."""

from sqlalchemy import or_

from app.extensions import db
from app.models import Category, Product, ProductStatus


class ProductService:
    """Business logic for product queries."""

    SORT_OPTIONS = {
        "newest": Product.created_at.desc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "name": Product.name.asc(),
    }

    @classmethod
    def build_query(cls, search=None, category_slug=None, brand=None, min_price=None, max_price=None, sort="newest"):
        query = Product.query.filter(Product.status == ProductStatus.ACTIVE)

        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.brand.ilike(term),
                    Product.sku.ilike(term),
                    Product.description.ilike(term),
                )
            )

        if category_slug:
            category = Category.query.filter_by(slug=category_slug, is_active=True).first()
            if category:
                category_ids = [c.id for c in category.get_all_children()]
                query = query.filter(Product.category_id.in_(category_ids))

        if brand:
            query = query.filter(Product.brand.ilike(f"%{brand.strip()}%"))

        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        order = cls.SORT_OPTIONS.get(sort, Product.created_at.desc())
        return query.order_by(order)

    @classmethod
    def get_brands(cls):
        return (
            db.session.query(Product.brand)
            .filter(Product.status == ProductStatus.ACTIVE)
            .distinct()
            .order_by(Product.brand)
            .all()
        )

    @classmethod
    def get_related_products(cls, product, limit=4):
        return (
            Product.query.filter(
                Product.category_id == product.category_id,
                Product.id != product.id,
                Product.status == ProductStatus.ACTIVE,
            )
            .order_by(Product.created_at.desc())
            .limit(limit)
            .all()
        )
