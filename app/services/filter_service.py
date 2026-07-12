"""Advanced product filtering engine with spec-based facets."""

from sqlalchemy import and_, func, or_

from app.extensions import cache, db
from app.models import Category, Product, ProductSpecification, ProductStatus, Review

# Standard spec keys for electronics filters
FILTER_SPECS = {
    "processor": "Processor",
    "ram": "RAM",
    "storage": "Storage",
    "os": "Operating System",
    "screen_size": "Screen Size",
    "resolution": "Resolution",
    "refresh_rate": "Refresh Rate",
    "graphics": "Graphics Card",
    "battery": "Battery Capacity",
    "battery_life": "Battery Life",
    "charging_speed": "Charging Speed",
    "color": "Color",
    "network": "Network",
    "sim_type": "SIM Type",
    "camera": "Camera Resolution",
    "internal_storage": "Internal Storage",
    "expandable_storage": "Expandable Storage",
    "bluetooth": "Bluetooth Version",
    "wifi": "Wi-Fi Standard",
    "usb": "USB Type",
    "warranty_period": "Warranty Period",
}

SORT_OPTIONS = {
    "newest": Product.created_at.desc(),
    "price_asc": Product.price.asc(),
    "price_desc": Product.price.desc(),
    "name": Product.name.asc(),
    "rating": Product.view_count.desc(),
    "popular": Product.view_count.desc(),
}


class FilterService:
    """Build filtered product queries with URL-param persistence."""

    @classmethod
    def parse_filters(cls, args):
        """Parse request args / dict into filter parameters."""
        return {
            "search": args.get("q", "").strip() or None,
            "category_slug": args.get("category", "").strip() or None,
            "brand": args.get("brand", "").strip() or None,
            "min_price": args.get("min_price", type=float),
            "max_price": args.get("max_price", type=float),
            "sort": args.get("sort", "newest"),
            "in_stock": args.get("in_stock") == "1",
            "on_sale": args.get("on_sale") == "1",
            "min_rating": args.get("min_rating", type=int),
            "specs": {k: args.get(f"spec_{k}", "").strip() for k in FILTER_SPECS if args.get(f"spec_{k}", "").strip()},
        }

    @classmethod
    def build_query(cls, filters):
        query = Product.query.filter(Product.status == ProductStatus.ACTIVE)

        if filters.get("search"):
            term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.brand.ilike(term),
                    Product.sku.ilike(term),
                    Product.model_name.ilike(term),
                )
            )

        if filters.get("category_slug"):
            category = Category.query.filter_by(slug=filters["category_slug"], is_active=True).first()
            if category:
                ids = [c.id for c in category.get_all_children()]
                query = query.filter(Product.category_id.in_(ids))

        if filters.get("brand"):
            query = query.filter(Product.brand.ilike(f"%{filters['brand']}%"))

        if filters.get("min_price") is not None:
            query = query.filter(Product.price >= filters["min_price"])
        if filters.get("max_price") is not None:
            query = query.filter(Product.price <= filters["max_price"])

        if filters.get("in_stock"):
            query = query.filter(Product.stock_quantity > 0, Product.is_preorder.is_(False))

        if filters.get("on_sale"):
            query = query.filter(Product.discount_price.isnot(None), Product.discount_price < Product.price)

        if filters.get("min_rating"):
            subq = (
                db.session.query(Review.product_id, func.avg(Review.rating).label("avg_r"))
                .filter(Review.is_approved.is_(True))
                .group_by(Review.product_id)
                .subquery()
            )
            query = query.outerjoin(subq, Product.id == subq.c.product_id).filter(
                subq.c.avg_r >= filters["min_rating"]
            )

        for spec_param, spec_value in filters.get("specs", {}).items():
            spec_label = FILTER_SPECS.get(spec_param, spec_param)
            query = query.filter(
                Product.id.in_(
                    db.session.query(ProductSpecification.product_id).filter(
                        ProductSpecification.spec_key.ilike(spec_label),
                        ProductSpecification.spec_value.ilike(f"%{spec_value}%"),
                    )
                )
            )

        order = SORT_OPTIONS.get(filters.get("sort"), Product.created_at.desc())
        return query.order_by(order)

    @classmethod
    def get_facets(cls):
        """Available filter options for sidebar."""
        cache_key = "product_filter_facets"
        if cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        brands = (
            db.session.query(Product.brand)
            .filter(Product.status == ProductStatus.ACTIVE)
            .distinct().order_by(Product.brand).all()
        )
        spec_facets = {}
        for param, label in FILTER_SPECS.items():
            values = (
                db.session.query(ProductSpecification.spec_value)
                .join(Product)
                .filter(
                    Product.status == ProductStatus.ACTIVE,
                    ProductSpecification.spec_key.ilike(label),
                )
                .distinct().order_by(ProductSpecification.spec_value).limit(20).all()
            )
            if values:
                spec_facets[param] = {"label": label, "options": [v[0] for v in values]}

        result = {"brands": [b[0] for b in brands], "specs": spec_facets}
        if cache:
            cache.set(cache_key, result, timeout=300)
        return result

    @classmethod
    def filters_to_query_string(cls, filters):
        """Build query string params for URL persistence."""
        params = {}
        for key in ("search", "category_slug", "brand", "sort"):
            if filters.get(key):
                param_key = "q" if key == "search" else ("category" if key == "category_slug" else key)
                params[param_key] = filters[key]
        if filters.get("min_price"):
            params["min_price"] = filters["min_price"]
        if filters.get("max_price"):
            params["max_price"] = filters["max_price"]
        if filters.get("in_stock"):
            params["in_stock"] = "1"
        if filters.get("on_sale"):
            params["on_sale"] = "1"
        if filters.get("min_rating"):
            params["min_rating"] = filters["min_rating"]
        for k, v in filters.get("specs", {}).items():
            params[f"spec_{k}"] = v
        return params
