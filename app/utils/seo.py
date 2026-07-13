"""SEO helpers for canonical URLs and sitemap generation."""

from urllib.parse import urlparse

from flask import current_app, request


def site_base_url():
    """Public site root from APP_URL, falling back to the current request."""
    configured = (current_app.config.get("APP_URL") or "").strip().rstrip("/")
    if configured:
        if "://" not in configured:
            configured = f"https://{configured}"
        return configured
    return request.url_root.rstrip("/")


def configure_url_generation(app):
    """Align Flask external URL generation with APP_URL."""
    app_url = (app.config.get("APP_URL") or "").strip()
    if not app_url:
        return

    if "://" not in app_url:
        app_url = f"https://{app_url}"

    parsed = urlparse(app_url)
    if parsed.scheme:
        app.config["PREFERRED_URL_SCHEME"] = parsed.scheme
    if parsed.netloc:
        app.config["SERVER_NAME"] = parsed.netloc
