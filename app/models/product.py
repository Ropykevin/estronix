"""Product models including images and specifications."""

import enum
from datetime import datetime, timezone

from slugify import slugify

from app.extensions import db
from app.utils.enums import enum_names


class ProductStatus(enum.Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


class Product(db.Model):
    """Electronic product listing."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=False, index=True)
    model_name = db.Column(db.String(120), index=True)
    color = db.Column(db.String(50))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False, index=True)
    discount_price = db.Column(db.Numeric(10, 2))
    stock_quantity = db.Column(db.Integer, default=0, nullable=False, index=True)
    warranty_info = db.Column(db.String(255))
    warranty_months = db.Column(db.Integer, default=12)
    is_preorder = db.Column(db.Boolean, default=False)
    delivery_estimate_days = db.Column(db.Integer, default=3)
    video_url = db.Column(db.String(255))
    youtube_url = db.Column(db.String(255))
    manual_url = db.Column(db.String(255))
    brochure_url = db.Column(db.String(255))
    viewer_360_url = db.Column(db.String(255))
    view_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum(ProductStatus, values_callable=enum_names), default=ProductStatus.ACTIVE, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(320))
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    category = db.relationship("Category", back_populates="products")
    images = db.relationship(
        "ProductImage",
        back_populates="product",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
    )
    specifications = db.relationship(
        "ProductSpecification",
        back_populates="product",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    reviews = db.relationship("Review", back_populates="product", lazy="dynamic")
    warehouse_stock = db.relationship("WarehouseInventory", back_populates="product", lazy="dynamic")
    views = db.relationship("ProductView", back_populates="product", lazy="dynamic")

    def get_spec(self, key):
        """Return specification value by key (case-insensitive)."""
        for spec in self.specifications:
            if spec.spec_key.lower() == key.lower():
                return spec.spec_value
        return None

    def get_specs_dict(self):
        return {s.spec_key: s.spec_value for s in self.specifications.all()}

    @property
    def stock_display(self):
        """Human-readable stock status for storefront."""
        from app.services.stock_service import StockService
        return StockService.get_display_status(self)

    @staticmethod
    def generate_slug(name):
        return slugify(name, max_length=220)

    @property
    def effective_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def is_on_sale(self):
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def discount_percentage(self):
        if self.is_on_sale and self.price > 0:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0 and self.status == ProductStatus.ACTIVE

    @property
    def is_low_stock(self):
        from flask import current_app
        threshold = current_app.config.get("LOW_STOCK_THRESHOLD", 10)
        return 0 < self.stock_quantity <= threshold

    @property
    def primary_image(self):
        primary = next((img for img in self.images if img.is_primary), None)
        return primary or (self.images[0] if self.images else None)

    @property
    def average_rating(self):
        reviews = self.reviews.filter_by(is_approved=True).all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def __repr__(self):
        return f"<Product {self.name}>"


class ProductImage(db.Model):
    """Product image gallery entry."""

    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(200))
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product", back_populates="images")

    def __repr__(self):
        return f"<ProductImage {self.id} for Product {self.product_id}>"


class ProductSpecification(db.Model):
    """Key-value product specification (e.g., RAM: 16GB)."""

    __tablename__ = "product_specifications"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    spec_key = db.Column(db.String(100), nullable=False, index=True)
    spec_value = db.Column(db.String(255), nullable=False, index=True)
    sort_order = db.Column(db.Integer, default=0)

    product = db.relationship("Product", back_populates="specifications")

    def __repr__(self):
        return f"<ProductSpec {self.spec_key}: {self.spec_value}>"
