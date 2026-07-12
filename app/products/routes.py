"""Product listing and detail routes."""

from flask import Blueprint, abort, current_app, jsonify, render_template, request, url_for

from sqlalchemy import desc

from app.models import Category, Product, ProductStatus, Review
from app.services.filter_service import FilterService
from app.services.product_service import ProductService
from app.services.recommendation_service import RecommendationService, WishlistService
from app.services.whatsapp_service import WhatsAppService

products_bp = Blueprint("products", __name__)


@products_bp.route("/")
def list_products():
    """Product listing with advanced filters."""
    filters = FilterService.parse_filters(request.args)
    page = request.args.get("page", 1, type=int)
    query = FilterService.build_query(filters)
    per_page = current_app.config["ITEMS_PER_PAGE"]
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    facets = FilterService.get_facets()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()

    context = {
        "products": pagination.items,
        "pagination": pagination,
        "filters": filters,
        "facets": facets,
        "categories": categories,
        "search": filters.get("search") or "",
        "category_slug": filters.get("category_slug") or "",
        "brand": filters.get("brand") or "",
        "min_price": filters.get("min_price"),
        "max_price": filters.get("max_price"),
        "sort": filters.get("sort", "newest"),
        "meta_title": f"Shop Electronics{' - ' + filters['search'] if filters.get('search') else ''} | Estronix",
        "meta_description": "Browse electronics with advanced filters at Estronix Kenya.",
        "canonical_url": url_for("products.list_products", **FilterService.filters_to_query_string(filters), _external=True),
    }

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_template("products/_product_grid.html", **context)
        return jsonify({"html": html, "total": pagination.total, "pages": pagination.pages})

    return render_template("products/list.html", **context)


@products_bp.route("/category/<slug>")
def category_products(slug):
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    args = request.args.to_dict()
    args["category"] = slug
    filters = FilterService.parse_filters(args)
    page = request.args.get("page", 1, type=int)
    query = FilterService.build_query(filters)
    pagination = query.paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False)

    return render_template(
        "products/category.html",
        category=category,
        products=pagination.items,
        pagination=pagination,
        filters=filters,
        sort=filters.get("sort", "newest"),
        breadcrumb=category.get_breadcrumb(),
        meta_title=f"{category.name} - Shop Online | Estronix",
        meta_description=category.description or f"Shop {category.name} at Estronix.",
        canonical_url=url_for("products.category_products", slug=slug, _external=True),
    )


@products_bp.route("/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first()
    if not product or product.status == ProductStatus.DISCONTINUED:
        abort(404)

    RecommendationService.track_view(product.id)
    related = ProductService.get_related_products(product)
    recommended = RecommendationService.get_recommended(limit=4)
    specs = product.specifications.order_by("sort_order").all()
    images = list(product.images)
    reviews = product.reviews.filter_by(is_approved=True).order_by(desc(Review.created_at)).limit(10).all()
    stock_info = product.stock_display

    return render_template(
        "products/detail.html",
        product=product,
        related_products=related,
        recommended_products=recommended,
        specifications=specs,
        images=images,
        reviews=reviews,
        stock_info=stock_info,
        meta_title=product.meta_title or f"{product.name} | Estronix",
        meta_description=product.meta_description or (product.description[:320] if product.description else ""),
        canonical_url=url_for("products.product_detail", slug=product.slug, _external=True),
        whatsapp_product_url=WhatsAppService.product_order_url(product, 1),
    )


@products_bp.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
def toggle_wishlist(product_id):
    success, message = WishlistService.toggle(product_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": success, "message": message})
    from flask import flash, redirect
    flash(message, "success" if success else "info")
    return redirect(request.referrer or url_for("products.list_products"))
