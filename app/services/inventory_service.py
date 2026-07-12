"""Inventory management service."""

from flask import current_app

from app.extensions import db
from app.models import Product, ProductStatus


class InventoryService:
    """Stock management and reporting."""

    @classmethod
    def update_stock(cls, product_id, quantity, operation="set"):
        product = Product.query.get_or_404(product_id)

        if operation == "add":
            product.stock_quantity += quantity
        elif operation == "subtract":
            product.stock_quantity = max(0, product.stock_quantity - quantity)
        else:
            product.stock_quantity = max(0, quantity)

        if product.stock_quantity == 0:
            product.status = ProductStatus.OUT_OF_STOCK
        elif product.status == ProductStatus.OUT_OF_STOCK:
            product.status = ProductStatus.ACTIVE

        db.session.commit()
        return product

    @classmethod
    def get_low_stock_products(cls):
        threshold = current_app.config.get("LOW_STOCK_THRESHOLD", 10)
        return (
            Product.query.filter(
                Product.stock_quantity > 0,
                Product.stock_quantity <= threshold,
                Product.status != ProductStatus.DISCONTINUED,
            )
            .order_by(Product.stock_quantity.asc())
            .all()
        )

    @classmethod
    def get_inventory_report(cls):
        products = Product.query.order_by(Product.name).all()
        threshold = current_app.config.get("LOW_STOCK_THRESHOLD", 10)
        return {
            "total_products": len(products),
            "in_stock": sum(1 for p in products if p.stock_quantity > threshold),
            "low_stock": sum(1 for p in products if 0 < p.stock_quantity <= threshold),
            "out_of_stock": sum(1 for p in products if p.stock_quantity == 0),
            "total_units": sum(p.stock_quantity for p in products),
            "products": products,
        }
