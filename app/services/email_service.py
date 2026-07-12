"""Email service for verification and password reset via Brevo API."""

import requests
from flask import current_app, render_template, url_for

from app.utils.helpers import generate_token

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailService:
    """Handles transactional email delivery through Brevo."""

    @staticmethod
    def _sender():
        return {
            "name": current_app.config.get("MAIL_DEFAULT_SENDER_NAME", current_app.config["APP_NAME"]),
            "email": current_app.config["MAIL_DEFAULT_SENDER"],
        }

    @classmethod
    def _send_via_brevo(cls, subject, recipients, text_body, html_body):
        api_key = current_app.config.get("BREVO_API_KEY")
        if not api_key:
            raise ValueError("BREVO_API_KEY is not configured")

        response = requests.post(
            BREVO_API_URL,
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
                "accept": "application/json",
            },
            json={
                "sender": cls._sender(),
                "to": [{"email": email} for email in recipients],
                "subject": subject,
                "htmlContent": html_body,
                "textContent": text_body,
            },
            timeout=30,
        )
        response.raise_for_status()

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
        except Exception as e:
            current_app.logger.error("Brevo email send failed: %s", e)
            if current_app.debug:
                current_app.logger.warning(
                    "\n%s\nBrevo failed — use this link in dev:\n%s\n%s",
                    "=" * 60,
                    text_body,
                    "=" * 60,
                )

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
