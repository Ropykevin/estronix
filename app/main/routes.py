"""Main blueprint for home page and SEO routes."""

from datetime import timezone

from flask import Blueprint, Response, abort, current_app, render_template, url_for

from app.models import Category, Product, ProductStatus

main_bp = Blueprint("main", __name__)


def _format_lastmod(value):
    if not value:
        return None
    dt = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date().isoformat()


@main_bp.route("/")
def index():
    """Home page with featured products and categories."""
    featured_products = (
        Product.query.filter_by(status=ProductStatus.ACTIVE, is_featured=True)
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    latest_products = (
        Product.query.filter_by(status=ProductStatus.ACTIVE)
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    categories = (
        Category.query.filter_by(is_active=True, parent_id=None)
        .order_by(Category.sort_order)
        .limit(6)
        .all()
    )

    return render_template(
        "main/index.html",
        featured_products=featured_products,
        latest_products=latest_products,
        categories=categories,
        meta_title="Estronix — Premium Electronics Store in Kenya | M-Pesa & Free Nairobi CBD Delivery",
        meta_description="Shop smartphones, laptops, headphones & home appliances at Estronix Kenya. Genuine products, M-Pesa checkout, warranty included & free delivery within Nairobi CBD.",
        canonical_url=url_for("main.index", _external=True),
    )


@main_bp.route("/robots.txt")
def robots_txt():
    """Serve robots.txt for search engine crawlers."""
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /auth/
Disallow: /account/
Disallow: /cart/
Disallow: /checkout/
Disallow: /orders/
Disallow: /payments/

Sitemap: {url_for('main.sitemap', _external=True)}
"""
    return Response(content, mimetype="text/plain")


@main_bp.route("/sitemap.xml")
def sitemap():
    """Generate XML sitemap for SEO."""
    pages = [
        {
            "loc": url_for("main.index", _external=True),
            "changefreq": "daily",
            "priority": "1.0",
            "lastmod": None,
        },
        {
            "loc": url_for("products.list_products", _external=True),
            "changefreq": "daily",
            "priority": "0.9",
            "lastmod": None,
        },
    ]

    for product in Product.query.filter_by(status=ProductStatus.ACTIVE).order_by(Product.updated_at.desc()):
        pages.append({
            "loc": url_for("products.product_detail", slug=product.slug, _external=True),
            "changefreq": "weekly",
            "priority": "0.8",
            "lastmod": _format_lastmod(product.updated_at or product.created_at),
        })

    for category in Category.query.filter_by(is_active=True).order_by(Category.name):
        pages.append({
            "loc": url_for("products.category_products", slug=category.slug, _external=True),
            "changefreq": "weekly",
            "priority": "0.7",
            "lastmod": _format_lastmod(category.updated_at or category.created_at),
        })

    xml = render_template("main/sitemap.xml", pages=pages)
    return Response(xml, mimetype="application/xml")


@main_bp.route("/google<token>.html")
def google_site_verification(token):
    """Serve Google Search Console HTML verification file."""
    configured = (current_app.config.get("GOOGLE_SITE_VERIFICATION_HTML") or "").strip()
    filename = f"google{token}.html"
    if configured != filename:
        abort(404)
    return Response(f"google-site-verification: {filename}", mimetype="text/html")
