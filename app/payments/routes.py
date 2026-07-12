"""Payment routes including M-Pesa callback."""

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from app.extensions import csrf, limiter
from app.services.mpesa_service import MpesaCallbackError, MpesaService
from app.utils.security import verify_mpesa_callback_token

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/mpesa/callback", methods=["POST"])
@csrf.exempt
@limiter.limit("120 per minute")
def mpesa_callback():
    """Handle M-Pesa STK Push callback (CSRF exempt for external webhook)."""
    if not verify_mpesa_callback_token():
        abort(403)

    data = request.get_json(silent=True) or {}
    try:
        payment = MpesaService.handle_callback(data)
    except MpesaCallbackError as exc:
        return jsonify({"ResultCode": 1, "ResultDesc": str(exc)}), 200

    if payment:
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200
    return jsonify({"ResultCode": 1, "ResultDesc": "Payment not found"}), 200


@payments_bp.route("/mpesa/status/<checkout_request_id>")
@login_required
@limiter.limit("30 per minute")
def mpesa_status(checkout_request_id):
    """Query M-Pesa payment status for the current user's order."""
    payment = MpesaService.get_payment_for_user(checkout_request_id, current_user.id)
    if not payment:
        abort(404)

    try:
        result = MpesaService.query_stk_status(checkout_request_id)
        return jsonify(result)
    except Exception:
        return jsonify({"error": "Unable to query payment status."}), 500
