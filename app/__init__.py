"""Application factory for Estronix E-Commerce Platform."""

import os

import click
from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from app.extensions import csrf, db, jwt, limiter, login_manager, mail, migrate, cache
from app.utils.security import validate_production_config
from config import config


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    validate_production_config(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_security_headers(app)
    _register_context_processors(app)
    _register_cli_commands(app)

    return app


def _init_extensions(app):
    """Initialize Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    if cache:
        cache.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        user = User.query.get(int(user_id))
        if user and user.is_active:
            return user
        return None


def _register_blueprints(app):
    """Register all application blueprints."""
    from app.auth.routes import auth_bp
    from app.products.routes import products_bp
    from app.cart.routes import cart_bp
    from app.orders.routes import orders_bp
    from app.payments.routes import payments_bp
    from app.customers.routes import customers_bp
    from app.admin.routes import admin_bp
    from app.main.routes import main_bp

    from app.tradein.routes import tradein_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(payments_bp, url_prefix="/payments")
    app.register_blueprint(customers_bp, url_prefix="/account")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(tradein_bp, url_prefix="/trade-in")


def _register_error_handlers(app):
    """Register HTTP error handlers."""

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template("errors/429.html", description=e.description), 429

    @app.errorhandler(RequestEntityTooLarge)
    @app.errorhandler(413)
    def request_entity_too_large(e):
        max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        flash(
            f"Upload too large. Keep the total upload under {max_mb} MB "
            "(use fewer images or compress them before uploading).",
            "danger",
        )
        return redirect(request.referrer or url_for("admin.products")), 413


def _register_security_headers(app):
    """Add security headers on every response in non-debug environments."""

    @app.after_request
    def set_security_headers(response):
        if app.debug or app.config.get("TESTING"):
            return response

        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        if request.is_secure or app.config.get("SESSION_COOKIE_SECURE"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' cdn.jsdelivr.net fonts.googleapis.com 'unsafe-inline'; "
            "font-src 'self' fonts.gstatic.com cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-src https://www.youtube.com https://www.youtube-nocookie.com;"
        )
        return response


def _register_context_processors(app):
    """Inject global template variables."""

    @app.context_processor
    def inject_globals():
        from app.services.cart_service import CartService
        from app.models import Category

        cart_count = 0
        if hasattr(CartService, "get_cart_item_count"):
            try:
                cart_count = CartService.get_cart_item_count()
            except Exception:
                cart_count = 0

        nav_categories = Category.query.filter_by(is_active=True, parent_id=None).order_by(
            Category.sort_order, Category.name
        ).limit(8).all()

        from app.utils.kenya_data import FREE_DELIVERY_AREA, phone_tel_link, whatsapp_link
        from app.services.whatsapp_service import WhatsAppService

        whatsapp_number = app.config.get("WHATSAPP_NUMBER", "0757840780")
        contact_phone = app.config.get("CONTACT_PHONE", "0757840780")
        contact_email = app.config.get("CONTACT_EMAIL", "estronix82@gmail.com")

        return {
            "app_name": app.config["APP_NAME"],
            "app_url": app.config.get("APP_URL", "http://localhost:5000").rstrip("/"),
            "cart_count": cart_count,
            "nav_categories": nav_categories,
            "canonical_url": None,
            "whatsapp_number": whatsapp_number,
            "whatsapp_url": whatsapp_link(whatsapp_number),
            "whatsapp_order_url": WhatsAppService.order_url,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "contact_phone_tel": phone_tel_link(contact_phone),
            "free_delivery_area": FREE_DELIVERY_AREA,
        }


def _register_cli_commands(app):
    """Register Flask CLI commands."""

    @app.cli.command("init-db")
    def init_db():
        """Initialize database with default roles and admin user."""
        from app.models import Role
        from app.services.admin_setup import ensure_admin

        db.create_all()

        for role_name in ("admin", "customer"):
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name, description=f"{role_name.title()} role"))

        db.session.commit()
        print(ensure_admin())
        print("Database initialized successfully.")

    @app.cli.command("ensure-admin")
    @click.option(
        "--force",
        is_flag=True,
        help="Reset password from ADMIN_INITIAL_PASSWORD and promote the configured email to admin.",
    )
    def ensure_admin_cmd(force):
        """Create or update the admin account from ADMIN_EMAIL / ADMIN_INITIAL_PASSWORD."""
        from app.services.admin_setup import ensure_admin

        print(ensure_admin(reset_password=force))

    @app.cli.command("test-email")
    @click.option(
        "--to",
        default=None,
        help="Recipient email. Defaults to ADMIN_EMAIL or CONTACT_EMAIL.",
    )
    @click.option("--subject", default=None, help="Email subject line.")
    @click.option("--message", default=None, help="Plain-text email body.")
    def test_email(to, subject, message):
        """Send a test email via Brevo."""
        from app.services.email_service import EmailService

        recipient = (
            to
            or app.config.get("ADMIN_EMAIL")
            or app.config.get("CONTACT_EMAIL")
            or app.config.get("MAIL_DEFAULT_SENDER")
        )
        if not recipient:
            raise click.ClickException("Pass --to or set ADMIN_EMAIL / CONTACT_EMAIL in .env")

        try:
            result = EmailService.send_test_email(recipient, subject=subject, message=message)
        except Exception as e:
            raise click.ClickException(str(e)) from e

        click.echo(f"Email result: {result}")

    @app.cli.command("seed-data")
    def seed_data():
        """Seed sample categories and products."""
        from app.services.seed_service import SeedService
        SeedService.seed_all()
        print("Sample data seeded successfully.")
