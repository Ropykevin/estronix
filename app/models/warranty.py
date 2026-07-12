"""Warranty registration models."""

import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.utils.enums import enum_values


class WarrantyStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    VOID = "void"
    CLAIMED = "claimed"


class WarrantyRegistration(db.Model):
    """Registered product warranty for a customer."""

    __tablename__ = "warranty_registrations"

    id = db.Column(db.Integer, primary_key=True)
    warranty_number = db.Column(db.String(36), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey("order_items.id"), nullable=True)
    serial_number = db.Column(db.String(100), nullable=False, index=True)
    product_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(WarrantyStatus, values_callable=enum_values), default=WarrantyStatus.ACTIVE, nullable=False)
    certificate_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="warranties")
    product = db.relationship("Product")
    order = db.relationship("Order")

    @staticmethod
    def generate_warranty_number():
        return f"WRN-{uuid.uuid4().hex[:10].upper()}"

    @property
    def is_active(self):
        return self.status == WarrantyStatus.ACTIVE and self.expiry_date >= datetime.now(timezone.utc).date()

    def __repr__(self):
        return f"<Warranty {self.warranty_number}>"
