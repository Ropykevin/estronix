"""Warranty registration and certificate management."""

from datetime import date, timedelta

from app.extensions import db
from app.models import Order, OrderItem, Product, WarrantyRegistration, WarrantyStatus


class WarrantyService:
    @classmethod
    def register_from_order(cls, order):
        """Auto-register warranties for all order items."""
        warranties = []
        for item in order.items:
            product = Product.query.get(item.product_id)
            months = product.warranty_months if product and product.warranty_months else 12
            start = date.today()
            warranty = WarrantyRegistration(
                warranty_number=WarrantyRegistration.generate_warranty_number(),
                user_id=order.user_id,
                product_id=item.product_id,
                order_id=order.id,
                order_item_id=item.id,
                serial_number=f"SN-{order.order_number}-{item.id}",
                product_name=item.product_name,
                start_date=start,
                expiry_date=start + timedelta(days=months * 30),
                status=WarrantyStatus.ACTIVE,
            )
            db.session.add(warranty)
            warranties.append(warranty)
        db.session.commit()
        return warranties

    @classmethod
    def register_manual(cls, user, product_id, serial_number):
        """Customer self-registration by serial number."""
        existing = WarrantyRegistration.query.filter_by(serial_number=serial_number).first()
        if existing:
            return None, "Serial number already registered."

        product = Product.query.get_or_404(product_id)
        months = product.warranty_months or 12
        start = date.today()
        warranty = WarrantyRegistration(
            warranty_number=WarrantyRegistration.generate_warranty_number(),
            user_id=user.id,
            product_id=product_id,
            serial_number=serial_number.upper(),
            product_name=product.name,
            start_date=start,
            expiry_date=start + timedelta(days=months * 30),
            status=WarrantyStatus.ACTIVE,
        )
        db.session.add(warranty)
        db.session.commit()
        return warranty, None

    @classmethod
    def get_user_warranties(cls, user_id, status=None):
        query = WarrantyRegistration.query.filter_by(user_id=user_id)
        if status == "active":
            query = query.filter(WarrantyRegistration.status == WarrantyStatus.ACTIVE)
        elif status == "expired":
            query = query.filter(WarrantyRegistration.status == WarrantyStatus.EXPIRED)
        return query.order_by(WarrantyRegistration.expiry_date.desc()).all()

    @classmethod
    def refresh_statuses(cls):
        """Mark expired warranties."""
        today = date.today()
        expired = WarrantyRegistration.query.filter(
            WarrantyRegistration.expiry_date < today,
            WarrantyRegistration.status == WarrantyStatus.ACTIVE,
        ).all()
        for w in expired:
            w.status = WarrantyStatus.EXPIRED
        db.session.commit()
