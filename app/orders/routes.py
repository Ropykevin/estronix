"""Order and checkout routes."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import Order
from app.models.payment import PaymentMethod, PaymentStatus
from app.orders.forms import CheckoutForm
from app.services.cart_service import CartService
from app.services.order_service import OrderService
from app.services.mpesa_service import MpesaService
from app.services.whatsapp_service import WhatsAppService
from app.utils.decorators import verified_required
from app.utils.kenya_data import FREE_DELIVERY_AREA, NAIROBI_COUNTY, is_nairobi_cbd_delivery
from app.utils.sanitizer import sanitize_html

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/checkout", methods=["GET", "POST"])
@login_required
@verified_required
def checkout():
    if CartService.get_cart_item_count() == 0:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart.view_cart"))

    form = CheckoutForm()
    default_address = current_user.addresses.filter_by(is_default=True).first()

    if default_address and request.method == "GET":
        form.full_name.data = default_address.full_name
        form.phone.data = default_address.phone
        form.address_line1.data = default_address.address_line1
        form.address_line2.data = default_address.address_line2
        form.city.data = default_address.city
        if default_address.county:
            form.county.data = default_address.county
        form.postal_code.data = default_address.postal_code

    subtotal = CartService.get_subtotal()
    cart_items = CartService.get_cart_items()
    selected_county = form.county.data if form.county.data else None
    selected_city = form.city.data if form.city.data else None
    shipping = OrderService.calculate_shipping(subtotal, selected_county, selected_city)
    tax = round(float(subtotal) * 0.16, 2)
    total = float(subtotal) + shipping + tax

    if form.validate_on_submit():
        shipping_address = "\n".join(
            filter(
                None,
                [
                    sanitize_html(form.full_name.data),
                    sanitize_html(form.address_line1.data),
                    sanitize_html(form.address_line2.data or ""),
                    f"{sanitize_html(form.city.data)}, {sanitize_html(form.county.data)} {form.postal_code.data or ''}".strip(),
                    "Kenya",
                    f"Phone: {form.phone.data}",
                ],
            )
        )

        order, error = OrderService.create_order(
            user=current_user,
            shipping_address=shipping_address,
            customer_notes=sanitize_html(form.customer_notes.data or ""),
            payment_method=form.payment_method.data,
            county=form.county.data,
            city=form.city.data,
        )

        if error:
            flash(error, "danger")
            return redirect(url_for("cart.view_cart"))

        if form.payment_method.data == "mpesa":
            payment = order.payments.filter_by(status=PaymentStatus.PENDING).first()
            try:
                MpesaService.initiate_stk_push(payment, form.phone.data)
                flash("M-Pesa STK Push sent. Please enter your PIN on your phone.", "info")
            except Exception as e:
                flash(f"Payment initiation failed: {e}. Order created — you can retry payment.", "warning")

        return redirect(url_for("orders.confirmation", order_number=order.order_number))

    return render_template(
        "orders/checkout.html",
        form=form,
        subtotal=subtotal,
        shipping=shipping,
        tax=tax,
        total=total,
        shipping_cost=OrderService.SHIPPING_COST,
        nairobi_county=NAIROBI_COUNTY,
        free_delivery_area=FREE_DELIVERY_AREA,
        qualifies_free_delivery=is_nairobi_cbd_delivery(selected_county, selected_city),
        whatsapp_cart_url=WhatsAppService.cart_order_url(cart_items, subtotal),
        meta_title="Checkout | Estronix",
    )


@orders_bp.route("/confirmation/<order_number>")
@login_required
def confirmation(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    return render_template("orders/confirmation.html", order=order)


@orders_bp.route("/<order_number>")
@login_required
def order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    return render_template("orders/detail.html", order=order)


@orders_bp.route("/<order_number>/invoice")
@login_required
def invoice(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    return render_template("orders/invoice.html", order=order)
