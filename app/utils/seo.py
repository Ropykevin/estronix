"""SEO helpers for canonical URLs and sitemap generation."""

from urllib.parse import urlparse

from flask import current_app, request, url_for


def _normalize_base_url(url):
    url = (url or "").strip().rstrip("/")
    if url and "://" not in url:
        url = f"http://{url}"
    return url


def _is_local_host(netloc):
    if not netloc:
        return True
    host = netloc.split(":")[0].lower()
    return host in {"localhost", "127.0.0.1", "0.0.0.0"}


def site_base_url():
    """Public site root for SEO URLs."""
    configured = _normalize_base_url(current_app.config.get("APP_URL"))
    parsed = urlparse(configured) if configured else None

    if configured and parsed and parsed.netloc and not _is_local_host(parsed.netloc):
        return configured

    domain = (current_app.config.get("DOMAIN") or "").strip()
    if domain:
        scheme = "https" if current_app.config.get("PREFERRED_URL_SCHEME") == "https" else "http"
        return f"{scheme}://{domain}".rstrip("/")

    if request:
        scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
        host = request.headers.get("X-Forwarded-Host", request.host)
        if host and not _is_local_host(host):
            return f"{scheme}://{host}".rstrip("/")

    return configured or "http://localhost:5000"


def external_url(endpoint, **values):
    """Build an absolute public URL for sitemaps, robots, and canonical tags."""
    path = url_for(endpoint, _external=False, **values)
    return f"{site_base_url()}{path}"
