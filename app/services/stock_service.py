"""Real-time stock display and regional availability."""

from flask import current_app

from app.models import Product, ProductStatus, Warehouse, WarehouseInventory


class StockService:
    LOW_THRESHOLD = 3

    @classmethod
    def get_display_status(cls, product):
        """Return stock label, CSS class, and delivery estimate."""
        if product.is_preorder:
            return {
                "label": "Available for Preorder",
                "css_class": "stock-preorder",
                "code": "preorder",
                "delivery": f"Ships in {product.delivery_estimate_days or 14} days",
            }
        qty = cls.get_available_quantity(product)
        if qty <= 0 or product.status == ProductStatus.OUT_OF_STOCK:
            return {
                "label": "Out of Stock",
                "css_class": "stock-out",
                "code": "out_of_stock",
                "delivery": None,
            }
        threshold = current_app.config.get("LOW_STOCK_THRESHOLD", 10) if current_app else 10
        if qty <= cls.LOW_THRESHOLD:
            return {
                "label": f"Only {qty} Left",
                "css_class": "stock-low",
                "code": "low_stock",
                "delivery": cls._delivery_estimate(product),
            }
        if qty <= threshold:
            return {
                "label": "In Stock — Limited",
                "css_class": "stock-limited",
                "code": "in_stock",
                "delivery": cls._delivery_estimate(product),
            }
        return {
            "label": "In Stock",
            "css_class": "stock-in",
            "code": "in_stock",
            "delivery": cls._delivery_estimate(product),
        }

    @classmethod
    def get_available_quantity(cls, product, region=None):
        """Total available stock, optionally filtered by customer region."""
        if region:
            regional = (
                WarehouseInventory.query.join(Warehouse)
                .filter(
                    WarehouseInventory.product_id == product.id,
                    Warehouse.is_active.is_(True),
                    Warehouse.region.ilike(f"%{region}%"),
                )
                .all()
            )
            if regional:
                return sum(wi.available for wi in regional)
        return product.stock_quantity

    @classmethod
    def _delivery_estimate(cls, product):
        days = product.delivery_estimate_days or 3
        if days <= 2:
            return "Delivery in 1–2 business days"
        return f"Delivery in {days}–{days + 2} business days"

    @classmethod
    def sync_product_stock(cls, product_id):
        """Sync Product.stock_quantity from sum of warehouse inventory."""
        total = (
            WarehouseInventory.query.filter_by(product_id=product_id)
            .with_entities(WarehouseInventory.quantity)
            .all()
        )
        product = Product.query.get(product_id)
        if product and total:
            product.stock_quantity = sum(t[0] for t in total)
            from app.extensions import db
            if product.stock_quantity == 0:
                product.status = ProductStatus.OUT_OF_STOCK
            elif product.status == ProductStatus.OUT_OF_STOCK:
                product.status = ProductStatus.ACTIVE
            db.session.commit()
