"""WhatsApp order link and message helpers."""

from urllib.parse import quote

from flask import current_app, url_for

from app.utils.kenya_data import whatsapp_link


class WhatsAppService:
    """Build wa.me order links with pre-filled messages."""

    @classmethod
    def _phone(cls):
        return current_app.config.get("WHATSAPP_NUMBER", "0757840780")

    @classmethod
    def _app_name(cls):
        return current_app.config.get("APP_NAME", "Estronix")

    @classmethod
    def order_url(cls, message, phone=None):
        phone = phone or cls._phone()
        return f"{whatsapp_link(phone)}?text={quote(message)}"

    @classmethod
    def product_message(cls, product, quantity=1):
        quantity = max(1, int(quantity))
        unit_price = float(product.effective_price)
        line_total = unit_price * quantity
        product_url = url_for("products.product_detail", slug=product.slug, _external=True)

        return (
            f"Hi {cls._app_name()}, I'd like to place an order:\n\n"
            f"*{product.name}*\n"
            f"Brand: {product.brand}\n"
            f"SKU: {product.sku}\n"
            f"Quantity: {quantity}\n"
            f"Unit price: KES {unit_price:,.0f}\n"
            f"Line total: KES {line_total:,.0f}\n"
            f"Link: {product_url}\n\n"
            f"Please confirm availability, delivery area, and payment options."
        )

    @classmethod
    def product_order_url(cls, product, quantity=1):
        return cls.order_url(cls.product_message(product, quantity))

    @classmethod
    def cart_message(cls, cart_items, subtotal):
        if not cart_items:
            return (
                f"Hi {cls._app_name()}, I'd like to place an order.\n\n"
                f"Please share your current catalogue and delivery details."
            )

        lines = [f"Hi {cls._app_name()}, I'd like to place an order:\n"]
        for index, item in enumerate(cart_items, start=1):
            product = item.product if hasattr(item, "product") else item["product"]
            qty = item.quantity if hasattr(item, "quantity") else item["quantity"]
            unit_price = float(product.effective_price)
            line_total = unit_price * qty
            lines.append(
                f"{index}. *{product.name}* ({product.sku})\n"
                f"   Qty: {qty} × KES {unit_price:,.0f} = KES {line_total:,.0f}"
            )

        lines.append(f"\n*Subtotal: KES {float(subtotal):,.0f}*")
        lines.append("\nPlease confirm availability, delivery address, and payment options.")
        return "\n".join(lines)

    @classmethod
    def cart_order_url(cls, cart_items, subtotal):
        return cls.order_url(cls.cart_message(cart_items, subtotal))
