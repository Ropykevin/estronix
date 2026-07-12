"""M-Pesa Daraja API integration service."""

import base64
import json
from datetime import datetime, timezone
from decimal import Decimal

import requests
from flask import current_app

from app.extensions import db
from app.models import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus


class MpesaCallbackError(Exception):
    """Raised when a callback fails validation."""


class MpesaService:
    """Safaricom M-Pesa STK Push integration."""

    SANDBOX_BASE = "https://sandbox.safaricom.co.ke"
    PRODUCTION_BASE = "https://api.safaricom.co.ke"

    @classmethod
    def _base_url(cls):
        env = current_app.config.get("MPESA_ENV", "sandbox")
        return cls.PRODUCTION_BASE if env == "production" else cls.SANDBOX_BASE

    @classmethod
    def _is_production(cls):
        return current_app.config.get("MPESA_ENV") == "production"

    @classmethod
    def _get_access_token(cls):
        key = current_app.config["MPESA_CONSUMER_KEY"]
        secret = current_app.config["MPESA_CONSUMER_SECRET"]
        if not key or not secret:
            raise ValueError("M-Pesa credentials not configured.")

        credentials = base64.b64encode(f"{key}:{secret}".encode()).decode()
        response = requests.get(
            f"{cls._base_url()}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {credentials}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    @classmethod
    def _generate_password(cls):
        shortcode = current_app.config["MPESA_SHORTCODE"]
        passkey = current_app.config["MPESA_PASSKEY"]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        password_str = f"{shortcode}{passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        return password, timestamp

    @classmethod
    def format_phone(cls, phone):
        """Normalize Kenyan phone to 254XXXXXXXXX format."""
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("+"):
            phone = phone[1:]
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif phone.startswith("7") or phone.startswith("1"):
            phone = "254" + phone
        return phone

    @classmethod
    def initiate_stk_push(cls, payment, phone_number):
        """Initiate M-Pesa STK Push for a payment."""
        token = cls._get_access_token()
        password, timestamp = cls._generate_password()

        payload = {
            "BusinessShortCode": current_app.config["MPESA_SHORTCODE"],
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(float(payment.amount)),
            "PartyA": cls.format_phone(phone_number),
            "PartyB": current_app.config["MPESA_SHORTCODE"],
            "PhoneNumber": cls.format_phone(phone_number),
            "CallBackURL": current_app.config["MPESA_CALLBACK_URL"],
            "AccountReference": payment.order.order_number,
            "TransactionDesc": f"Payment for order {payment.order.order_number}",
        }

        response = requests.post(
            f"{cls._base_url()}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=30,
        )

        data = response.json()
        payment.raw_response = json.dumps(data)
        payment.phone_number = cls.format_phone(phone_number)

        if response.status_code == 200 and data.get("ResponseCode") == "0":
            payment.checkout_request_id = data.get("CheckoutRequestID")
            payment.merchant_request_id = data.get("MerchantRequestID")
            payment.status = PaymentStatus.PENDING
        else:
            payment.status = PaymentStatus.FAILED
            payment.result_description = data.get("errorMessage") or data.get("ResponseDescription")

        db.session.commit()
        return data

    @classmethod
    def _extract_callback_metadata(cls, body):
        metadata = {}
        for item in body.get("CallbackMetadata", {}).get("Item", []):
            metadata[item.get("Name")] = item.get("Value")
        return metadata

    @classmethod
    def _verify_stk_with_daraja(cls, checkout_request_id):
        """Confirm payment status with Safaricom before marking an order paid."""
        if not current_app.config.get("MPESA_VERIFY_CALLBACK", True):
            return True

        try:
            result = cls.query_stk_status(checkout_request_id)
        except Exception as exc:
            current_app.logger.error("STK verification failed for %s: %s", checkout_request_id, exc)
            return False

        return str(result.get("ResultCode", "")) == "0"

    @classmethod
    def handle_callback(cls, callback_data):
        """Process M-Pesa STK callback payload."""
        body = callback_data.get("Body", {}).get("stkCallback", {})
        checkout_request_id = body.get("CheckoutRequestID")
        result_code = str(body.get("ResultCode", ""))

        if not checkout_request_id:
            raise MpesaCallbackError("Missing CheckoutRequestID")

        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()
        if not payment:
            return None

        payment.result_code = result_code
        payment.result_description = body.get("ResultDesc")
        payment.raw_response = json.dumps(callback_data)

        if payment.status == PaymentStatus.COMPLETED:
            current_app.logger.info(
                "Ignoring duplicate M-Pesa callback for payment %s", payment.id
            )
            db.session.commit()
            return payment

        if result_code != "0":
            payment.status = PaymentStatus.FAILED
            db.session.commit()
            return payment

        metadata = cls._extract_callback_metadata(body)
        receipt = str(metadata.get("MpesaReceiptNumber", "") or "")
        callback_amount = metadata.get("Amount")

        if not receipt:
            payment.status = PaymentStatus.FAILED
            payment.result_description = "Missing MpesaReceiptNumber in callback"
            db.session.commit()
            raise MpesaCallbackError("Missing MpesaReceiptNumber")

        expected_amount = Decimal(str(payment.order.total_amount))
        try:
            received_amount = Decimal(str(callback_amount))
        except Exception as exc:
            raise MpesaCallbackError("Invalid callback amount") from exc

        if received_amount != expected_amount:
            payment.status = PaymentStatus.FAILED
            payment.result_description = (
                f"Amount mismatch: expected {expected_amount}, received {received_amount}"
            )
            db.session.commit()
            current_app.logger.warning(
                "M-Pesa amount mismatch for payment %s: expected %s got %s",
                payment.id,
                expected_amount,
                received_amount,
            )
            raise MpesaCallbackError("Payment amount does not match order total")

        duplicate_receipt = Payment.query.filter(
            Payment.mpesa_receipt == receipt,
            Payment.id != payment.id,
            Payment.status == PaymentStatus.COMPLETED,
        ).first()
        if duplicate_receipt:
            payment.status = PaymentStatus.FAILED
            payment.result_description = "Duplicate M-Pesa receipt"
            db.session.commit()
            raise MpesaCallbackError("Duplicate M-Pesa receipt")

        if cls._is_production() and not cls._verify_stk_with_daraja(checkout_request_id):
            payment.status = PaymentStatus.FAILED
            payment.result_description = "STK verification with Safaricom failed"
            db.session.commit()
            raise MpesaCallbackError("STK verification failed")

        payment.mpesa_receipt = receipt
        payment.amount = received_amount
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.now(timezone.utc)
        payment.transaction_id = receipt

        order = payment.order
        order.status = OrderStatus.PAID
        order.paid_at = datetime.now(timezone.utc)

        db.session.commit()

        from app.services.order_service import OrderService
        OrderService.on_order_paid(order)

        return payment

    @classmethod
    def query_stk_status(cls, checkout_request_id):
        """Query STK push transaction status."""
        token = cls._get_access_token()
        password, timestamp = cls._generate_password()

        payload = {
            "BusinessShortCode": current_app.config["MPESA_SHORTCODE"],
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        response = requests.post(
            f"{cls._base_url()}/mpesa/stkpush/v1/query",
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=30,
        )
        return response.json()

    @classmethod
    def get_payment_for_user(cls, checkout_request_id, user_id):
        """Return a payment only if it belongs to the given user."""
        return (
            Payment.query.filter_by(checkout_request_id=checkout_request_id)
            .join(Order, Payment.order_id == Order.id)
            .filter(Order.user_id == user_id)
            .first()
        )
