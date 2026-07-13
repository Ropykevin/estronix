"""Security helpers for redirects, callbacks, and production validation."""

import os
import secrets
from urllib.parse import urlsplit

from flask import request

WEAK_SECRET_KEYS = frozenset({
    "dev-secret-change-in-production",
    "change-this-to-a-long-random-secret-key",
})


def is_safe_redirect_url(target):
    """Allow only same-site relative paths (blocks open redirects)."""
    if not target:
        return False

    test_parts = urlsplit(target)

    return (
        test_parts.scheme in ("", "http", "https")
        and not test_parts.netloc
        and test_parts.scheme != "javascript"
        and target.startswith("/")
        and not target.startswith("//")
    )


def verify_mpesa_callback_token():
    """Validate shared secret on M-Pesa webhook (query param or header)."""
    from flask import current_app

    expected = (current_app.config.get("MPESA_CALLBACK_TOKEN") or "").strip()
    if not expected:
        return not _is_production_app()

    provided = (
        request.args.get("token")
        or request.headers.get("X-Mpesa-Callback-Token")
        or ""
    ).strip()
    return secrets.compare_digest(provided, expected)


def _is_production_app():
    from flask import current_app

    return (
        current_app.config.get("ENV") == "production"
        or os.environ.get("FLASK_ENV") == "production"
    )


def validate_production_config(app):
    """Fail fast when production is misconfigured."""
    if app.config.get("DEBUG") or app.config.get("TESTING"):
        return

    if os.environ.get("FLASK_ENV") != "production":
        return

    secret_key = app.config.get("SECRET_KEY") or ""
    if secret_key in WEAK_SECRET_KEYS or len(secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY must be a unique random string of at least 32 characters in production."
        )

    jwt_key = app.config.get("JWT_SECRET_KEY") or ""
    if jwt_key in WEAK_SECRET_KEYS or jwt_key == secret_key:
        app.logger.warning("JWT_SECRET_KEY should be independent from SECRET_KEY in production.")

    if not app.config.get("MPESA_CALLBACK_TOKEN"):
        raise RuntimeError(
            "MPESA_CALLBACK_TOKEN is required in production. "
            "Append ?token=<secret> to MPESA_CALLBACK_URL."
        )

    if not app.config.get("BREVO_API_KEY") and not app.config.get("MAIL_CONSOLE"):
        raise RuntimeError("BREVO_API_KEY is required in production when MAIL_CONSOLE is false.")

    app_url = (app.config.get("APP_URL") or "").lower()
    if "localhost" in app_url or "127.0.0.1" in app_url:
        domain = app.config.get("DOMAIN")
        if not domain:
            app.logger.warning(
                "APP_URL points to localhost in production. Set APP_URL=http://estronix.co.ke "
                "or at least DOMAIN=estronix.co.ke for correct sitemap and SEO URLs."
            )

    rate_limit_uri = app.config.get("RATELIMIT_STORAGE_URI", "memory://")
    if rate_limit_uri.startswith("memory://"):
        app.logger.warning(
            "RATELIMIT_STORAGE_URI uses in-memory storage; "
            "use Redis in production for effective rate limits across workers."
        )
