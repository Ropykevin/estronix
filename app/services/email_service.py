"""Email service for verification and password reset via Brevo API."""

import json

import requests
from flask import current_app, render_template, url_for

from app.utils.helpers import generate_token

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_SENDERS_URL = "https://api.brevo.com/v3/senders"


class EmailService:
    """Handles transactional email delivery through Brevo."""

    @staticmethod
    def _api_headers():
        api_key = current_app.config.get("BREVO_API_KEY")
        if not api_key:
            raise ValueError("BREVO_API_KEY is not configured")
        return {
            "api-key": api_key,
            "Content-Type": "application/json",
            "accept": "application/json",
        }

    @staticmethod
    def _format_brevo_error(response):
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError):
            return response.text or f"HTTP {response.status_code}"

        message = data.get("message") or data.get("error") or response.text
        code = data.get("code")
        if code:
            return f"{message} (code: {code})"
        return message

    @staticmethod
    def _sender():
        return {
            "name": current_app.config.get("MAIL_DEFAULT_SENDER_NAME", current_app.config["APP_NAME"]),
            "email": current_app.config["MAIL_DEFAULT_SENDER"],
        }

    @classmethod
    def list_senders(cls):
        response = requests.get(BREVO_SENDERS_URL, headers=cls._api_headers(), timeout=30)
        response.raise_for_status()
        return response.json().get("senders", [])

    @classmethod
    def check_sender_configuration(cls):
        configured = current_app.config["MAIL_DEFAULT_SENDER"].strip().lower()
        senders = cls.list_senders()
        verified = [
            s for s in senders
            if str(s.get("email", "")).lower() == configured and s.get("active")
        ]
        return {
            "configured_sender": configured,
            "configured_sender_name": current_app.config.get("MAIL_DEFAULT_SENDER_NAME"),
            "verified_match": bool(verified),
            "senders": senders,
        }

    @classmethod
    def _send_via_brevo(cls, subject, recipients, text_body, html_body):
        sender = cls._sender()
        response = requests.post(
            BREVO_API_URL,
            headers=cls._api_headers(),
            json={
                "sender": sender,
                "to": [{"email": email} for email in recipients],
                "subject": subject,
                "htmlContent": html_body,
                "textContent": text_body,
            },
            timeout=30,
        )
        if not response.ok:
            detail = cls._format_brevo_error(response)
            hint = (
                f"Brevo rejected sender '{sender['email']}'. "
                "Add and verify this address under Brevo → Settings → Senders. "
                "If you see 'SMTP account is not yet activated', contact Brevo support."
            )
            if response.status_code in (400, 403):
                raise RuntimeError(f"{detail}. {hint}")
            raise RuntimeError(detail)
        return response.json() if response.content else {}

    @classmethod
    def send_test_email(cls, recipient, subject=None, message=None):
        """Send a test email via Brevo; raises on failure."""
        recipient = recipient.strip().lower()
        app_name = current_app.config["APP_NAME"]
        subject = subject or f"Test email from {app_name}"
        message = message or f"If you received this, Brevo email is working for {app_name}."
        html_body = f"<p>{message}</p>"

        if current_app.config.get("MAIL_SUPPRESS_SEND"):
            return {"status": "suppressed", "to": recipient}

        if current_app.config.get("MAIL_CONSOLE"):
            current_app.logger.info(
                "\n%s\nDEV EMAIL (console mode)\nTo: %s\nSubject: %s\n%s\n%s",
                "=" * 60,
                recipient,
                subject,
                message,
                "=" * 60,
            )
            return {"status": "console", "to": recipient}

        result = cls._send_via_brevo(subject, [recipient], message, html_body)
        current_app.logger.info("Brevo test email sent to %s", recipient)
        return {"status": "sent", "to": recipient, "response": result}

    @staticmethod
    def send_email(subject, recipients, text_body, html_body):
        if current_app.config.get("MAIL_SUPPRESS_SEND"):
            return

        if current_app.config.get("MAIL_CONSOLE"):
            current_app.logger.info(
                "\n%s\nDEV EMAIL (console mode)\nTo: %s\nSubject: %s\n%s\n%s",
                "=" * 60,
                ", ".join(recipients),
                subject,
                text_body,
                "=" * 60,
            )
            return

        try:
            EmailService._send_via_brevo(subject, recipients, text_body, html_body)
        except requests.HTTPError as e:
            detail = e.response.text if e.response is not None else str(e)
            current_app.logger.error("Brevo email send failed: %s", detail)
            if current_app.debug:
                current_app.logger.warning(
                    "\n%s\nBrevo failed — use this link in dev:\n%s\n%s",
                    "=" * 60,
                    text_body,
                    "=" * 60,
                )
        except Exception as e:
            current_app.logger.error("Brevo email send failed: %s", e)

    @classmethod
    def send_verification_email(cls, user):
        token = generate_token(user.email, salt="email-verify")
        verify_url = url_for("auth.verify_email", token=token, _external=True)
        subject = f"Verify your {current_app.config['APP_NAME']} account"
        html = render_template("emails/verify_email.html", user=user, verify_url=verify_url)
        text = f"Verify your account: {verify_url}"
        cls.send_email(subject, [user.email], text, html)

    @classmethod
    def send_password_reset_email(cls, user):
        token = generate_token(user.email, salt="password-reset")
        reset_url = url_for("auth.reset_password", token=token, _external=True)
        subject = f"Reset your {current_app.config['APP_NAME']} password"
        html = render_template("emails/reset_password.html", user=user, reset_url=reset_url)
        text = f"Reset your password: {reset_url}"
        cls.send_email(subject, [user.email], text, html)

    @classmethod
    def send_order_confirmation(cls, order):
        subject = f"Order Confirmation - {order.order_number}"
        html = render_template("emails/order_confirmation.html", order=order)
        text = f"Your order {order.order_number} has been placed."
        cls.send_email(subject, [order.user.email], text, html)
