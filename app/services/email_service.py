"""Email service for verification, password reset, and order emails via SMTP."""

from flask import current_app, render_template, url_for
from flask_mail import Message

from app.extensions import mail
from app.utils.helpers import generate_token


class EmailService:
    """Handles transactional email delivery through SMTP (Flask-Mail)."""

    @staticmethod
    def _sender():
        name = current_app.config.get("MAIL_DEFAULT_SENDER_NAME", current_app.config["APP_NAME"])
        email = current_app.config["MAIL_DEFAULT_SENDER"]
        return (name, email)

    @classmethod
    def check_smtp_configuration(cls):
        password = current_app.config.get("MAIL_PASSWORD")
        return {
            "mail_server": current_app.config.get("MAIL_SERVER"),
            "mail_port": current_app.config.get("MAIL_PORT"),
            "mail_use_tls": current_app.config.get("MAIL_USE_TLS"),
            "mail_username": current_app.config.get("MAIL_USERNAME"),
            "mail_password_set": bool(password and str(password).strip()),
            "mail_default_sender": current_app.config.get("MAIL_DEFAULT_SENDER"),
            "mail_default_sender_name": current_app.config.get("MAIL_DEFAULT_SENDER_NAME"),
        }

    @classmethod
    def _send_via_smtp(cls, subject, recipients, text_body, html_body):
        password = (current_app.config.get("MAIL_PASSWORD") or "").strip()
        if not password:
            raise ValueError(
                "MAIL_PASSWORD is not configured. "
                "Create an SMTP key in Brevo → SMTP & API → SMTP keys."
            )

        message = Message(
            subject=subject,
            recipients=recipients,
            body=text_body,
            html=html_body,
            sender=cls._sender(),
        )
        mail.send(message)
        return {"status": "sent", "recipients": recipients}

    @classmethod
    def send_test_email(cls, recipient, subject=None, message=None):
        """Send a test email via SMTP; raises on failure."""
        recipient = recipient.strip().lower()
        app_name = current_app.config["APP_NAME"]
        subject = subject or f"Test email from {app_name}"
        message = message or f"If you received this, SMTP email is working for {app_name}."
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

        result = cls._send_via_smtp(subject, [recipient], message, html_body)
        current_app.logger.info("SMTP test email sent to %s", recipient)
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
            EmailService._send_via_smtp(subject, recipients, text_body, html_body)
        except Exception as e:
            current_app.logger.error("SMTP email send failed: %s", e)
            if current_app.debug:
                current_app.logger.warning(
                    "\n%s\nSMTP failed — use this link in dev:\n%s\n%s",
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
