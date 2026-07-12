"""Device trade-in routes."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import TradeInRequest, TradeInStatus
from app.services.tradein_service import TradeInService
from app.tradein.forms import TradeInForm
from app.utils.sanitizer import sanitize_html

tradein_bp = Blueprint("tradein", __name__)


@tradein_bp.route("/")
def index():
    return render_template("tradein/index.html", meta_title="Trade-In Program | Estronix")


@tradein_bp.route("/submit", methods=["GET", "POST"])
@login_required
def submit():
    form = TradeInForm()
    if form.validate_on_submit():
        images = request.files.getlist("images")
        trade_in = TradeInService.create_request(
            current_user,
            {
                "device_brand": sanitize_html(form.device_brand.data),
                "device_model": sanitize_html(form.device_model.data),
                "device_type": form.device_type.data,
                "condition": form.condition.data,
                "condition_notes": sanitize_html(form.condition_notes.data or ""),
            },
            image_files=images if images else None,
        )
        flash(f"Trade-in submitted! Reference: {trade_in.reference_number}", "success")
        return redirect(url_for("tradein.detail", trade_in_id=trade_in.id))
    return render_template("tradein/submit.html", form=form)


@tradein_bp.route("/<int:trade_in_id>")
@login_required
def detail(trade_in_id):
    trade_in = TradeInRequest.query.filter_by(id=trade_in_id, user_id=current_user.id).first_or_404()
    return render_template("tradein/detail.html", trade_in=trade_in)


@tradein_bp.route("/<int:trade_in_id>/accept", methods=["POST"])
@login_required
def accept_offer(trade_in_id):
    trade_in, error = TradeInService.accept_offer(trade_in_id, current_user.id)
    if error:
        flash(error, "danger")
    else:
        flash("Offer accepted! We will contact you with next steps.", "success")
    return redirect(url_for("tradein.detail", trade_in_id=trade_in_id))
