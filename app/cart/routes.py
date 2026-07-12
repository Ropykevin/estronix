"""Shopping cart routes."""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import Product
from app.services.cart_service import CartService
from app.services.whatsapp_service import WhatsAppService

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/")
def view_cart():
    items = CartService.get_cart_items()
    subtotal = CartService.get_subtotal()

    if items and hasattr(items[0], "product"):
        cart_items = items
    else:
        cart_items = items

    return render_template(
        "cart/view.html",
        cart_items=cart_items,
        subtotal=subtotal,
        whatsapp_cart_url=WhatsAppService.cart_order_url(cart_items, subtotal),
        meta_title="Shopping Cart | Estronix",
    )


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    quantity = request.form.get("quantity", 1, type=int)
    product = Product.query.get_or_404(product_id)
    success, message = CartService.add_item(product_id, quantity)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "success": success,
                "message": message,
                "cart_count": CartService.get_cart_item_count(),
                "product_name": product.name if success else None,
            }
        )

    flash(message, "success" if success else "danger")
    return redirect(request.referrer or url_for("products.list_products"))


def _cart_ajax_payload(success, message, product_id=None, removed=False):
    items = CartService.get_cart_items()
    subtotal = CartService.get_subtotal()
    payload = {
        "success": success,
        "message": message,
        "cart_count": CartService.get_cart_item_count(),
        "subtotal": float(subtotal),
        "removed": removed,
    }

    if success and product_id and not removed:
        product = Product.query.get(product_id)
        if product:
            qty = request.form.get("quantity", 1, type=int)
            payload["line_total"] = float(product.effective_price) * qty

    if success and (removed or not items):
        payload["html"] = render_template(
            "cart/_content.html",
            cart_items=items,
            subtotal=subtotal,
            whatsapp_cart_url=WhatsAppService.cart_order_url(items, subtotal),
        )

    return payload


@cart_bp.route("/update/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    quantity = request.form.get("quantity", 1, type=int)
    success, message = CartService.update_item(product_id, quantity)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        removed = quantity == 0
        return jsonify(_cart_ajax_payload(success, message, product_id=product_id, removed=removed))

    flash(message, "success" if success else "danger")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    success, message = CartService.remove_item(product_id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(_cart_ajax_payload(success, message, product_id=product_id, removed=True))

    flash("Item removed from cart.", "info")
    return redirect(url_for("cart.view_cart"))
