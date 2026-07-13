"""Application configuration classes."""

import os
from datetime import timedelta
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def _app_url_settings():
    app_url = os.environ.get("APP_URL", "").strip()
    domain = os.environ.get("DOMAIN", "").strip()

    if not app_url and domain:
        app_url = f"http://{domain}"
    if not app_url:
        app_url = "http://localhost:5000"
    if "://" not in app_url:
        app_url = f"http://{app_url}"

    parsed = urlparse(app_url)
    netloc = parsed.netloc or None
    if netloc and (netloc.split(":")[0].lower() in {"localhost", "127.0.0.1", "0.0.0.0"}):
        netloc = None

    return {
        "APP_URL": app_url.rstrip("/"),
        "DOMAIN": domain or None,
        "PREFERRED_URL_SCHEME": parsed.scheme or "http",
        "SERVER_NAME": netloc,
    }


_APP_URL = _app_url_settings()


def _env_bool(key, default="False"):
    """Parse boolean env vars; tolerates trailing whitespace."""
    return os.environ.get(key, default).strip().lower() in ("true", "1", "yes")


class Config:
    """Base configuration shared across all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://estronix_user:estronix_pass@localhost:5432/estronix_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True

    # Session security
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = int(os.environ.get("WTF_CSRF_TIME_LIMIT", 3600))

    # Brevo transactional email (REST API — not SMTP)
    # Create an API key at: Brevo → SMTP & API → API Keys (starts with xkeysib-)
    BREVO_API_KEY = (os.environ.get("BREVO_API_KEY") or "").strip() or None
    MAIL_DEFAULT_SENDER = (
        os.environ.get("MAIL_DEFAULT_SENDER")
        or os.environ.get("CONTACT_EMAIL")
        or "estronix82@gmail.com"
    ).strip()
    MAIL_DEFAULT_SENDER_NAME = os.environ.get("MAIL_DEFAULT_SENDER_NAME", os.environ.get("APP_NAME", "Estronix"))
    MAIL_SUPPRESS_SEND = _env_bool("MAIL_SUPPRESS_SEND")
    MAIL_CONSOLE = _env_bool("MAIL_CONSOLE")

    # JWT (for future API expansion)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Application settings
    APP_NAME = os.environ.get("APP_NAME", "Estronix")
    APP_URL = _APP_URL["APP_URL"]
    DOMAIN = _APP_URL["DOMAIN"]
    PREFERRED_URL_SCHEME = _APP_URL["PREFERRED_URL_SCHEME"]
    SERVER_NAME = _APP_URL["SERVER_NAME"]
    GOOGLE_SITE_VERIFICATION = (os.environ.get("GOOGLE_SITE_VERIFICATION") or "").strip() or None
    GOOGLE_SITE_VERIFICATION_HTML = (os.environ.get("GOOGLE_SITE_VERIFICATION_HTML") or "").strip() or None
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "estronix82@gmail.com").strip().lower()
    ADMIN_INITIAL_PASSWORD = (
        os.environ.get("ADMIN_INITIAL_PASSWORD") or os.environ.get("ADMIN_PASSWORD") or ""
    ).strip() or None
    CONTACT_PHONE = os.environ.get("CONTACT_PHONE", "0757840780")
    CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "estronix82@gmail.com")
    WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", os.environ.get("CONTACT_PHONE", "0757840780"))
    ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE", 12))
    LOW_STOCK_THRESHOLD = int(os.environ.get("LOW_STOCK_THRESHOLD", 10))
    UPLOAD_FOLDER = os.path.join("app", "static", "uploads")
    MAX_UPLOAD_FILE_SIZE = int(os.environ.get("MAX_UPLOAD_FILE_SIZE_MB", 8)) * 1024 * 1024
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 64)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # M-Pesa Daraja API
    MPESA_ENV = os.environ.get("MPESA_ENV", "sandbox")
    MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY")
    MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET")
    MPESA_SHORTCODE = os.environ.get("MPESA_SHORTCODE", "174379")
    MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY")
    MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL")
    MPESA_CALLBACK_TOKEN = (os.environ.get("MPESA_CALLBACK_TOKEN") or "").strip() or None
    MPESA_VERIFY_CALLBACK = _env_bool("MPESA_VERIFY_CALLBACK", "True")

    # Rate limiting (use Redis in production: redis://127.0.0.1:6379/0)
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_HEADERS_ENABLED = True

    # Caching (SimpleCache for dev; Redis in production)
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))
    CACHE_REDIS_URL = os.environ.get("CACHE_REDIS_URL")


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False
    # Log emails to terminal instead of SMTP when True (default in dev)
    MAIL_CONSOLE = _env_bool("MAIL_CONSOLE", "True")


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    MAIL_CONSOLE = False
    RATELIMIT_STORAGE_URI = os.environ.get(
        "RATELIMIT_STORAGE_URI",
        "redis://127.0.0.1:6379/0",
    )


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SERVER_NAME = "localhost"
    APP_URL = "http://localhost"
    GOOGLE_SITE_VERIFICATION = None
    GOOGLE_SITE_VERIFICATION_HTML = None
