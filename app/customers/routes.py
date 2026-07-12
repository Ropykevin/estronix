"""Customer account routes — enhanced dashboard."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.customers.forms import AddressForm, ChangePasswordForm, ProfileForm, RepairForm, WarrantyRegisterForm
from app.extensions import db
from app.models import Address, Order, Product, RepairRequest, TradeInRequest, UserNotification
from app.models.loyalty import LoyaltyTransaction
from app.services.invoice_service import InvoiceService
from app.services.loyalty_service import LoyaltyService
from app.services.recommendation_service import RecommendationService, WishlistService
from app.services.repair_service import RepairService
from app.services.warranty_service import WarrantyService
from app.utils.helpers import delete_upload, save_upload
from app.utils.sanitizer import sanitize_html

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/")
@login_required
def dashboard():
    account = LoyaltyService.get_or_create_account(current_user)
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    wishlist = WishlistService.get_items()[:6]
    recent_viewed = RecommendationService.get_recently_viewed(6)
    recommended = RecommendationService.get_recommended(limit=4)
    warranties_active = WarrantyService.get_user_warranties(current_user.id, "active")[:3]
    repairs = RepairRequest.query.filter_by(user_id=current_user.id).order_by(RepairRequest.created_at.desc()).limit(3).all()
    trade_ins = TradeInRequest.query.filter_by(user_id=current_user.id).order_by(TradeInRequest.created_at.desc()).limit(3).all()
    notifications = UserNotification.query.filter_by(user_id=current_user.id, is_read=False).order_by(
        UserNotification.created_at.desc()
    ).limit(5).all()
    reward_history = LoyaltyTransaction.query.filter_by(account_id=account.id).order_by(
        LoyaltyTransaction.created_at.desc()
    ).limit(5).all()

    return render_template(
        "customers/dashboard.html",
        recent_orders=recent_orders,
        wishlist=wishlist,
        recent_viewed=recent_viewed,
        recommended=recommended,
        loyalty=account,
        warranties_active=warranties_active,
        repairs=repairs,
        trade_ins=trade_ins,
        notifications=notifications,
        reward_history=reward_history,
        meta_title="My Account | Estronix",
    )


@customers_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = sanitize_html(form.first_name.data)
        current_user.last_name = sanitize_html(form.last_name.data)
        current_user.phone = form.phone.data

        if form.remove_profile_image.data and current_user.profile_image_url:
            delete_upload(current_user.profile_image_url)
            current_user.profile_image_url = None
        elif form.profile_image.data and form.profile_image.data.filename:
            image_url = save_upload(form.profile_image.data, "profiles")
            if image_url:
                if current_user.profile_image_url:
                    delete_upload(current_user.profile_image_url)
                current_user.profile_image_url = image_url
            else:
                flash("Invalid image file. Use jpg, png, gif, or webp.", "warning")

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("customers.profile"))
    return render_template("customers/profile.html", form=form)


@customers_bp.route("/orders")
@login_required
def orders():
    orders_list = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("customers/orders.html", orders=orders_list)


@customers_bp.route("/orders/<order_number>/invoice-pdf")
@login_required
def download_invoice(order_number):
    from flask import Response
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    pdf = InvoiceService.generate_pdf(order)
    if not pdf:
        flash("PDF generation unavailable. Install reportlab.", "warning")
        return redirect(url_for("orders.invoice", order_number=order_number))
    return Response(pdf, mimetype="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=invoice-{order.invoice_number}.pdf"
    })


@customers_bp.route("/wishlist")
@login_required
def wishlist():
    items = WishlistService.get_items()
    return render_template("customers/wishlist.html", items=items)


@customers_bp.route("/addresses")
@login_required
def addresses():
    user_addresses = current_user.addresses.order_by(Address.is_default.desc()).all()
    return render_template("customers/addresses.html", addresses=user_addresses)


@customers_bp.route("/addresses/add", methods=["GET", "POST"])
@login_required
def add_address():
    form = AddressForm()
    if form.validate_on_submit():
        if form.is_default.data:
            for addr in current_user.addresses:
                addr.is_default = False
        address = Address(
            user_id=current_user.id,
            label=sanitize_html(form.label.data),
            full_name=sanitize_html(form.full_name.data),
            phone=form.phone.data,
            address_line1=sanitize_html(form.address_line1.data),
            address_line2=sanitize_html(form.address_line2.data or ""),
            city=sanitize_html(form.city.data),
            county=sanitize_html(form.county.data or ""),
            postal_code=form.postal_code.data,
            is_default=form.is_default.data,
        )
        db.session.add(address)
        db.session.commit()
        flash("Address added.", "success")
        return redirect(url_for("customers.addresses"))
    return render_template("customers/address_form.html", form=form, title="Add Address")


@customers_bp.route("/warranties")
@login_required
def warranties():
    active = WarrantyService.get_user_warranties(current_user.id, "active")
    expired = WarrantyService.get_user_warranties(current_user.id, "expired")
    return render_template("customers/warranties.html", active=active, expired=expired)


@customers_bp.route("/warranties/register", methods=["GET", "POST"])
@login_required
def register_warranty():
    form = WarrantyRegisterForm()
    form.product_id.choices = [(p.id, p.name) for p in Product.query.filter_by(status="active").limit(100).all()]
    if form.validate_on_submit():
        warranty, error = WarrantyService.register_manual(current_user, form.product_id.data, form.serial_number.data)
        if error:
            flash(error, "danger")
        else:
            flash(f"Warranty registered: {warranty.warranty_number}", "success")
            return redirect(url_for("customers.warranties"))
    return render_template("customers/warranty_register.html", form=form)


@customers_bp.route("/repairs")
@login_required
def repairs():
    items = RepairRequest.query.filter_by(user_id=current_user.id).order_by(RepairRequest.created_at.desc()).all()
    return render_template("customers/repairs.html", repairs=items)


@customers_bp.route("/repairs/submit", methods=["GET", "POST"])
@login_required
def submit_repair():
    form = RepairForm()
    if form.validate_on_submit():
        images = request.files.getlist("images")
        repair = RepairService.create_request(
            current_user,
            {
                "product_name": sanitize_html(form.product_name.data),
                "brand": sanitize_html(form.brand.data or ""),
                "serial_number": form.serial_number.data,
                "issue_description": sanitize_html(form.issue_description.data),
            },
            image_files=images if images else None,
        )
        flash(f"Repair ticket {repair.ticket_number} submitted.", "success")
        return redirect(url_for("customers.repair_detail", repair_id=repair.id))
    return render_template("customers/repair_form.html", form=form)


@customers_bp.route("/repairs/<int:repair_id>")
@login_required
def repair_detail(repair_id):
    repair = RepairRequest.query.filter_by(id=repair_id, user_id=current_user.id).first_or_404()
    return render_template("customers/repair_detail.html", repair=repair)


@customers_bp.route("/loyalty")
@login_required
def loyalty():
    account = LoyaltyService.get_or_create_account(current_user)
    history = LoyaltyTransaction.query.filter_by(account_id=account.id).order_by(LoyaltyTransaction.created_at.desc()).all()
    return render_template("customers/loyalty.html", account=account, history=history)


@customers_bp.route("/notifications")
@login_required
def notifications():
    items = UserNotification.query.filter_by(user_id=current_user.id).order_by(UserNotification.created_at.desc()).all()
    return render_template("customers/notifications.html", notifications=items)


@customers_bp.route("/notifications/<int:nid>/read", methods=["POST"])
@login_required
def mark_notification_read(nid):
    n = UserNotification.query.filter_by(id=nid, user_id=current_user.id).first_or_404()
    n.is_read = True
    db.session.commit()
    return redirect(n.link or url_for("customers.notifications"))


@customers_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for("customers.dashboard"))
    return render_template("customers/change_password.html", form=form)
