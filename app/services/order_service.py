"""Order creation and management service."""

from datetime import datetime, timezone

from app.extensions import db
from app.models import Order, OrderItem, OrderStatus, Product
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.services.cart_service import CartService
from app.services.email_service import EmailService
from app.utils.kenya_data import is_nairobi_cbd_delivery


class OrderService:
    """Handle order lifecycle operations."""

    SHIPPING_COST = 500  # KES flat rate outside Nairobi CBD

    @classmethod
    def calculate_shipping(cls, subtotal, county=None, city=None):
        """Free within Nairobi CBD; flat rate elsewhere."""
        if is_nairobi_cbd_delivery(county, city):
            return 0
        if not county or not str(county).strip():
            return 0
        return cls.SHIPPING_COST

    @classmethod
    def create_order(cls, user, shipping_address, billing_address=None, customer_notes=None, payment_method="mpesa", county=None, city=None):
        cart_items = CartService.get_cart_items()
        if not cart_items:
            return None, "Your cart is empty."

        if cart_items and hasattr(cart_items[0], "product"):
            items_data = [(item.product, item.quantity) for item in cart_items]
        else:
            items_data = [(item["product"], item["quantity"]) for item in cart_items]

        for product, qty in items_data:
            if product.stock_quantity < qty:
                return None, f"Insufficient stock for {product.name}."

        subtotal = CartService.get_subtotal()
        shipping = cls.calculate_shipping(subtotal, county, city)
        tax = round(float(subtotal) * 0.16, 2)
        total = float(subtotal) + shipping + tax

        order = Order(
            order_number=Order.generate_order_number(),
            invoice_number=Order.generate_invoice_number(),
            user_id=user.id,
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            shipping_cost=shipping,
            tax_amount=tax,
            total_amount=total,
            shipping_address=shipping_address,
            billing_address=billing_address or shipping_address,
            customer_notes=customer_notes,
            shipping_region=county or getattr(user, "delivery_region", None),
        )
        db.session.add(order)
        db.session.flush()

        for product, qty in items_data:
            unit_price = product.effective_price
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name=product.name,
                    product_sku=product.sku,
                    quantity=qty,
                    unit_price=unit_price,
                    total_price=float(unit_price) * qty,
                )
            )
            product.stock_quantity -= qty

        method = PaymentMethod.MPESA if payment_method == "mpesa" else PaymentMethod.CASH_ON_DELIVERY
        payment = Payment(order_id=order.id, amount=total, method=method, status=PaymentStatus.PENDING)
        db.session.add(payment)
        db.session.commit()

        CartService.clear_cart()
        EmailService.send_order_confirmation(order)

        return order, None

    @classmethod
    def mark_order_paid(cls, order, paid_at=None):
        """Mark an order as paid and complete its payment record."""
        now = paid_at or datetime.now(timezone.utc)
        already_paid = order.status == OrderStatus.PAID and order.paid_at is not None

        order.status = OrderStatus.PAID
        if not order.paid_at:
            order.paid_at = now

        for payment in order.payments:
            if payment.status != PaymentStatus.COMPLETED:
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = order.paid_at

        if not already_paid:
            db.session.flush()
            cls.on_order_paid(order)

    @classmethod
    def on_order_paid(cls, order):
        """Post-payment hooks after M-Pesa confirmation."""
        if order.status != OrderStatus.PAID:
            return
        cls._run_post_order_hooks(order)

    @classmethod
    def _run_post_order_hooks(cls, order):
        """Warranties, loyalty points, and invoice email."""
        from app.services.warranty_service import WarrantyService
        from app.services.loyalty_service import LoyaltyService
        from app.services.invoice_service import InvoiceService

        try:
            WarrantyService.register_from_order(order)
        except Exception:
            db.session.rollback()
        try:
            LoyaltyService.earn_from_order(order.user, order)
        except Exception:
            db.session.rollback()
        try:
            InvoiceService.email_invoice(order)
        except Exception:
            pass
