"""Main blueprint for home page and SEO routes."""

from datetime import timezone

from flask import Blueprint, Response, abort, current_app, render_template

from app.models import Category, Product, ProductStatus
from app.utils.seo import external_url

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
        canonical_url=external_url("main.index"),
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

Sitemap: {external_url("main.sitemap")}
"""
    return Response(content, mimetype="text/plain")


@main_bp.route("/sitemap.xml")
def sitemap():
    """Generate XML sitemap for SEO."""
    pages = [
        {
            "loc": external_url("main.index"),
            "changefreq": "daily",
            "priority": "1.0",
            "lastmod": None,
        },
        {
            "loc": external_url("products.list_products"),
            "changefreq": "daily",
            "priority": "0.9",
            "lastmod": None,
        },
    ]

    for product in Product.query.filter_by(status=ProductStatus.ACTIVE).order_by(Product.updated_at.desc()):
        pages.append({
            "loc": external_url("products.product_detail", slug=product.slug),
            "changefreq": "weekly",
            "priority": "0.8",
            "lastmod": _format_lastmod(product.updated_at or product.created_at),
        })

    for category in Category.query.filter_by(is_active=True).order_by(Category.name):
        pages.append({
            "loc": external_url("products.category_products", slug=category.slug),
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
