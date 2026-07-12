"""Main blueprint for home page and SEO routes."""

from flask import Blueprint, Response, render_template, url_for

from app.models import Category, Product, ProductStatus

main_bp = Blueprint("main", __name__)


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

Sitemap: {url_for('main.sitemap', _external=True)}
"""
    return Response(content, mimetype="text/plain")


@main_bp.route("/sitemap.xml")
def sitemap():
    """Generate XML sitemap for SEO."""
    from flask import request

    pages = []
    base = request.url_root.rstrip("/")

    static_pages = [
        ("", "daily", "1.0"),
        ("/products/", "daily", "0.9"),
    ]
    for path, freq, priority in static_pages:
        pages.append({"loc": f"{base}{path}", "changefreq": freq, "priority": priority})

    for product in Product.query.filter_by(status=ProductStatus.ACTIVE).all():
        pages.append({
            "loc": f"{base}/products/{product.slug}",
            "changefreq": "weekly",
            "priority": "0.8",
        })

    for category in Category.query.filter_by(is_active=True).all():
        pages.append({
            "loc": f"{base}/products/category/{category.slug}",
            "changefreq": "weekly",
            "priority": "0.7",
        })

    xml = render_template("main/sitemap.xml", pages=pages)
    return Response(xml, mimetype="application/xml")
