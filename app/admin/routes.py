"""Admin dashboard and management routes."""

import os
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.admin.forms import CategoryForm, OrderStatusForm, ProductForm, StockUpdateForm
from app.extensions import db
from app.models import Category, Order, OrderStatus, Product, User
from app.models.product import ProductImage, ProductStatus
from app.services.analytics_service import AnalyticsService
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.utils.decorators import admin_required
from app.utils.helpers import save_upload
from app.utils.sanitizer import sanitize_html
from flask_login import logout_user

admin_bp = Blueprint("admin", __name__)


def _normalize_sku(sku):
    return sku.upper().strip()


def _product_category_choices(selected_category_id=None):
    """Active categories plus the product's current category if inactive."""
    query = Category.query
    if selected_category_id:
        query = query.filter(
            db.or_(Category.is_active.is_(True), Category.id == selected_category_id)
        )
    else:
        query = query.filter_by(is_active=True)
    return [(c.id, c.name) for c in query.order_by(Category.name).all()]


def _populate_product_form(form, product):
    form.status.data = product.status.value
    form.is_featured.data = product.is_featured


MAX_PRODUCT_IMAGES = 10


def _upload_file_size(file_storage):
    """Return uploaded file size in bytes."""
    if getattr(file_storage, "content_length", None):
        return file_storage.content_length

    stream = file_storage.stream
    position = stream.tell()
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(position)
    return size


def _add_product_images(product, files):
    """Save uploaded files and attach them to a product."""
    if not files:
        return 0

    max_file_size = current_app.config.get("MAX_UPLOAD_FILE_SIZE", 8 * 1024 * 1024)
    current_count = len(product.images)
    if current_count >= MAX_PRODUCT_IMAGES:
        flash(f"This product already has the maximum of {MAX_PRODUCT_IMAGES} images.", "warning")
        return 0

    has_primary = any(img.is_primary for img in product.images)
    max_sort = (
        db.session.query(func.coalesce(func.max(ProductImage.sort_order), -1))
        .filter_by(product_id=product.id)
        .scalar()
    )
    added = 0
    skipped_large = 0

    for file_storage in files:
        if current_count + added >= MAX_PRODUCT_IMAGES:
            break
        if not file_storage or not getattr(file_storage, "filename", ""):
            continue

        if _upload_file_size(file_storage) > max_file_size:
            skipped_large += 1
            continue

        image_url = save_upload(file_storage)
        if not image_url:
            continue

        is_primary = not has_primary and added == 0
        max_sort += 1
        db.session.add(
            ProductImage(
                product_id=product.id,
                image_url=image_url,
                is_primary=is_primary,
                sort_order=max_sort,
                alt_text=product.name,
            )
        )
        added += 1
        if is_primary:
            has_primary = True

    if skipped_large:
        max_mb = max_file_size // (1024 * 1024)
        flash(
            f"Skipped {skipped_large} image(s) over {max_mb} MB each. Compress them and try again.",
            "warning",
        )

    return added


def _ensure_product_primary_image(product):
    """Ensure one image is marked primary when images exist."""
    if any(img.is_primary for img in product.images):
        return

    first_image = sorted(product.images, key=lambda img: (img.sort_order, img.id))[0] if product.images else None
    if first_image:
        first_image.is_primary = True


def _sku_taken(sku, exclude_product_id=None):
    query = Product.query.filter_by(sku=sku)
    if exclude_product_id:
        query = query.filter(Product.id != exclude_product_id)
    return query.first()


def _slug_taken(slug, exclude_product_id=None):
    query = Product.query.filter_by(slug=slug)
    if exclude_product_id:
        query = query.filter(Product.id != exclude_product_id)
    return query.first()


def _flash_integrity_error(exc):
    detail = str(getattr(exc, "orig", exc)).lower()
    if "sku" in detail:
        flash("A product with this SKU already exists.", "danger")
    elif "slug" in detail:
        flash(
            "A product with this URL slug already exists — usually because another product "
            "has the same (or very similar) name. Use a more distinct name or edit the existing product.",
            "danger",
        )
    else:
        flash("Could not save product: a duplicate value was detected.", "danger")


def _flush_product_session():
    try:
        db.session.flush()
        return True
    except IntegrityError as exc:
        db.session.rollback()
        _flash_integrity_error(exc)
        return False


def _commit_product_form():
    """Commit product changes or flash on duplicate SKU/slug."""
    try:
        db.session.commit()
        return True
    except IntegrityError as exc:
        db.session.rollback()
        _flash_integrity_error(exc)
        return False


@admin_bp.before_request
@login_required
@admin_required
def require_admin():
    pass


@admin_bp.route("/")
def dashboard():
    """Admin dashboard with key metrics."""
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    total_sales = AnalyticsService.total_paid_sales()
    monthly_sales = AnalyticsService.paid_sales_since(thirty_days_ago)
    total_orders = Order.query.count()
    total_products = Product.query.count()
    total_customers = User.query.join(User.role).filter_by(name="customer").count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    low_stock = InventoryService.get_low_stock_products()

    return render_template(
        "admin/dashboard.html",
        total_sales=total_sales,
        monthly_sales=monthly_sales,
        total_orders=total_orders,
        total_products=total_products,
        total_customers=total_customers,
        recent_orders=recent_orders,
        low_stock=low_stock,
    )


# --- Products ---

@admin_bp.route("/products")
def products():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "")
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%"))
    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/products/list.html", pagination=pagination, search=search)


@admin_bp.route("/products/create", methods=["GET", "POST"])
def create_product():
    form = ProductForm()
    form.category_id.choices = _product_category_choices()
    form.status.data = ProductStatus.ACTIVE.value

    if form.validate_on_submit():
        sku = _normalize_sku(form.sku.data)
        slug = Product.generate_slug(form.name.data)

        if _sku_taken(sku):
            flash(f"A product with SKU '{sku}' already exists. Use a different SKU or edit the existing product.", "danger")
            return render_template("admin/products/form.html", form=form, title="Create Product")

        if _slug_taken(slug):
            flash(
                f"A product with the URL slug '{slug}' already exists. Use a more distinct product name "
                f"or edit the existing product.",
                "danger",
            )
            return render_template("admin/products/form.html", form=form, title="Create Product")

        product = Product(
            name=sanitize_html(form.name.data),
            slug=slug,
            sku=sku,
            brand=sanitize_html(form.brand.data),
            description=sanitize_html(form.description.data or ""),
            price=form.price.data,
            discount_price=form.discount_price.data,
            stock_quantity=form.stock_quantity.data,
            warranty_info=form.warranty_info.data,
            category_id=form.category_id.data,
            status=ProductStatus(form.status.data),
            is_featured=form.is_featured.data,
            meta_title=form.meta_title.data,
            meta_description=form.meta_description.data,
        )
        db.session.add(product)
        if not _flush_product_session():
            return render_template("admin/products/form.html", form=form, title="Create Product")

        added = _add_product_images(product, form.images.data)
        if added:
            _ensure_product_primary_image(product)

        if _commit_product_form():
            flash("Product created.", "success")
            return redirect(url_for("admin.products"))
        return render_template("admin/products/form.html", form=form, title="Create Product")

    return render_template("admin/products/form.html", form=form, title="Create Product")


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product, product_id=product.id)
    form.category_id.choices = _product_category_choices(product.category_id)
    if request.method == "GET":
        _populate_product_form(form, product)

    if form.validate_on_submit():
        sku = _normalize_sku(form.sku.data)
        slug = Product.generate_slug(form.name.data)

        if _sku_taken(sku, exclude_product_id=product.id):
            flash(f"SKU '{sku}' is already used by another product.", "danger")
            return render_template("admin/products/form.html", form=form, product=product, title="Edit Product")

        if _slug_taken(slug, exclude_product_id=product.id):
            flash(
                f"URL slug '{slug}' is already used by another product. Use a more distinct product name.",
                "danger",
            )
            return render_template("admin/products/form.html", form=form, product=product, title="Edit Product")

        product.name = sanitize_html(form.name.data)
        product.slug = slug
        product.sku = sku
        product.brand = sanitize_html(form.brand.data)
        product.description = sanitize_html(form.description.data or "")
        product.price = form.price.data
        product.discount_price = form.discount_price.data
        product.stock_quantity = form.stock_quantity.data
        product.warranty_info = form.warranty_info.data
        product.category_id = form.category_id.data
        product.status = ProductStatus(form.status.data)
        product.is_featured = form.is_featured.data
        product.meta_title = form.meta_title.data
        product.meta_description = form.meta_description.data

        added = _add_product_images(product, form.images.data)
        if added:
            _ensure_product_primary_image(product)

        if _commit_product_form():
            flash("Product updated.", "success")
            return redirect(url_for("admin.edit_product", product_id=product.id))
        return render_template("admin/products/form.html", form=form, product=product, title="Edit Product")

    return render_template("admin/products/form.html", form=form, product=product, title="Edit Product")


@admin_bp.route("/products/<int:product_id>/images/<int:image_id>/primary", methods=["POST"])
def set_primary_product_image(product_id, image_id):
    product = Product.query.get_or_404(product_id)
    image = ProductImage.query.filter_by(id=image_id, product_id=product.id).first_or_404()

    for existing in product.images:
        existing.is_primary = existing.id == image.id

    db.session.commit()
    flash("Primary image updated.", "success")
    return redirect(url_for("admin.edit_product", product_id=product.id))


@admin_bp.route("/products/<int:product_id>/images/<int:image_id>/delete", methods=["POST"])
def delete_product_image(product_id, image_id):
    product = Product.query.get_or_404(product_id)
    image = ProductImage.query.filter_by(id=image_id, product_id=product.id).first_or_404()
    was_primary = image.is_primary

    delete_upload(image.image_url)
    db.session.delete(image)
    db.session.flush()

    if was_primary:
        _ensure_product_primary_image(product)

    db.session.commit()
    flash("Image removed.", "success")
    return redirect(url_for("admin.edit_product", product_id=product.id))


@admin_bp.route("/products/<int:product_id>/stock", methods=["GET", "POST"])
def update_stock(product_id):
    product = Product.query.get_or_404(product_id)
    form = StockUpdateForm()
    if form.validate_on_submit():
        InventoryService.update_stock(product_id, form.quantity.data, form.operation.data)
        flash("Stock updated.", "success")
        return redirect(url_for("admin.products"))
    return render_template("admin/products/stock.html", product=product, form=form)


# --- Categories ---

@admin_bp.route("/categories")
def categories():
    all_categories = Category.query.order_by(Category.sort_order, Category.name).all()
    return render_template("admin/categories/list.html", categories=all_categories)


@admin_bp.route("/categories/create", methods=["GET", "POST"])
def create_category():
    form = CategoryForm()
    form.parent_id.choices = [(0, "None (Top Level)")] + [
        (c.id, c.name) for c in Category.query.filter_by(parent_id=None).order_by(Category.name)
    ]

    if form.validate_on_submit():
        parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        category = Category(
            name=sanitize_html(form.name.data),
            slug=Category.generate_slug(form.name.data),
            description=sanitize_html(form.description.data or ""),
            parent_id=parent_id,
            sort_order=form.sort_order.data or 0,
            is_active=form.is_active.data,
        )
        if form.image.data:
            category.image_url = save_upload(form.image.data, "categories")
        db.session.add(category)
        db.session.commit()
        flash("Category created.", "success")
        return redirect(url_for("admin.categories"))

    return render_template("admin/categories/form.html", form=form, title="Create Category")


# --- Orders ---

@admin_bp.route("/orders")
def orders():
    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status", "")
    query = Order.query
    if status_filter:
        query = query.filter_by(status=OrderStatus(status_filter))
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/orders/list.html", pagination=pagination, status_filter=status_filter, OrderStatus=OrderStatus)


@admin_bp.route("/orders/<int:order_id>", methods=["GET", "POST"])
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    form = OrderStatusForm()
    form.status.choices = [(s.value, s.value.title()) for s in OrderStatus]

    if request.method == "GET":
        form.status.data = order.status.value
        form.tracking_number.data = order.tracking_number
        form.admin_notes.data = order.admin_notes

    if form.validate_on_submit():
        order.status = OrderStatus(form.status.data)
        order.tracking_number = form.tracking_number.data
        order.admin_notes = sanitize_html(form.admin_notes.data or "")

        now = datetime.now(timezone.utc)
        if order.status == OrderStatus.PAID:
            OrderService.mark_order_paid(order, paid_at=now)
        if order.status == OrderStatus.SHIPPED and not order.shipped_at:
            order.shipped_at = now
        if order.status == OrderStatus.DELIVERED and not order.delivered_at:
            order.delivered_at = now

        db.session.commit()
        flash("Order updated.", "success")
        return redirect(url_for("admin.order_detail", order_id=order.id))

    return render_template("admin/orders/detail.html", order=order, form=form)


# --- Customers ---

@admin_bp.route("/customers")
def customers():
    page = request.args.get("page", 1, type=int)
    pagination = (
        User.query.join(User.role)
        .filter_by(name="customer")
        .order_by(User.created_at.desc())
        .paginate(page=page, per_page=20, error_out=False)
    )
    return render_template("admin/customers/list.html", pagination=pagination)


# --- Inventory & Reports ---

@admin_bp.route("/inventory")
def inventory():
    report = InventoryService.get_inventory_report()
    return render_template("admin/inventory.html", report=report)


@admin_bp.route("/reports")
def reports():
    from sqlalchemy import extract

    monthly_data = (
        db.session.query(
            extract("month", Order.paid_at).label("month"),
            func.sum(Order.total_amount).label("total"),
        )
        .filter(Order.status == OrderStatus.PAID, Order.paid_at.isnot(None))
        .group_by("month")
        .all()
    )
    status_counts = (
        db.session.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    return render_template("admin/reports.html", monthly_data=monthly_data, status_counts=status_counts)


# --- Warehouses ---

@admin_bp.route("/warehouses")
def warehouses():
    from app.models import Warehouse
    items = Warehouse.query.order_by(Warehouse.name).all()
    return render_template("admin/warehouses/list.html", warehouses=items)


@admin_bp.route("/warehouses/create", methods=["GET", "POST"])
def create_warehouse():
    from app.models import Warehouse
    if request.method == "POST":
        wh = Warehouse(
            name=sanitize_html(request.form.get("name", "")),
            code=request.form.get("code", "").upper().strip(),
            region=sanitize_html(request.form.get("region", "")),
            address=sanitize_html(request.form.get("address", "")),
            is_active=request.form.get("is_active") == "on",
        )
        db.session.add(wh)
        db.session.commit()
        flash("Warehouse created.", "success")
        return redirect(url_for("admin.warehouses"))
    return render_template("admin/warehouses/form.html", title="Create Warehouse")


@admin_bp.route("/warehouses/<int:warehouse_id>/stock")
def warehouse_stock(warehouse_id):
    from app.models import Warehouse, WarehouseInventory
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    stock = WarehouseInventory.query.filter_by(warehouse_id=warehouse_id).all()
    products = Product.query.filter_by(status=ProductStatus.ACTIVE).order_by(Product.name).all()
    return render_template("admin/warehouses/stock.html", warehouse=warehouse, stock=stock, products=products)


@admin_bp.route("/warehouses/<int:warehouse_id>/assign", methods=["POST"])
def assign_warehouse_stock(warehouse_id):
    from app.services.warehouse_service import WarehouseService
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", type=int)
    if product_id and quantity is not None:
        WarehouseService.assign_stock(warehouse_id, product_id, quantity, user_id=current_user.id)
        flash("Stock assigned.", "success")
    return redirect(url_for("admin.warehouse_stock", warehouse_id=warehouse_id))


@admin_bp.route("/transfers", methods=["GET", "POST"])
def transfers():
    from app.models import Warehouse, StockTransfer
    from app.services.warehouse_service import WarehouseService
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(status=ProductStatus.ACTIVE).order_by(Product.name).all()
    if request.method == "POST":
        transfer, error = WarehouseService.create_transfer(
            request.form.get("from_id", type=int),
            request.form.get("to_id", type=int),
            request.form.get("product_id", type=int),
            request.form.get("quantity", type=int),
            user_id=current_user.id,
            notes=request.form.get("notes"),
        )
        if error:
            flash(error, "danger")
        else:
            flash(f"Transfer {transfer.transfer_number} created.", "success")
            return redirect(url_for("admin.transfers"))
    recent = StockTransfer.query.order_by(StockTransfer.created_at.desc()).limit(20).all()
    return render_template("admin/warehouses/transfers.html", warehouses=warehouses, products=products, transfers=recent)


@admin_bp.route("/transfers/<int:transfer_id>/complete", methods=["POST"])
def complete_transfer(transfer_id):
    from app.services.warehouse_service import WarehouseService
    ok, msg = WarehouseService.complete_transfer(transfer_id, current_user.id)
    flash(msg or "Transfer completed.", "success" if ok else "danger")
    return redirect(url_for("admin.transfers"))


# --- Repairs ---

@admin_bp.route("/repairs")
def repairs():
    from app.models import RepairRequest
    items = RepairRequest.query.order_by(RepairRequest.created_at.desc()).all()
    return render_template("admin/repairs/list.html", repairs=items)


@admin_bp.route("/repairs/<int:repair_id>", methods=["GET", "POST"])
def repair_detail(repair_id):
    from app.models import RepairRequest, RepairStatus
    from app.services.repair_service import RepairService
    repair = RepairRequest.query.get_or_404(repair_id)
    if request.method == "POST":
        RepairService.update_status(
            repair_id,
            request.form.get("status"),
            admin_notes=request.form.get("admin_notes"),
            estimated_cost=request.form.get("estimated_cost", type=float),
        )
        flash("Repair updated.", "success")
        return redirect(url_for("admin.repair_detail", repair_id=repair_id))
    return render_template("admin/repairs/detail.html", repair=repair, RepairStatus=RepairStatus)


# --- Trade-Ins ---

@admin_bp.route("/trade-ins")
def trade_ins():
    from app.models import TradeInRequest
    items = TradeInRequest.query.order_by(TradeInRequest.created_at.desc()).all()
    return render_template("admin/tradeins/list.html", trade_ins=items)


@admin_bp.route("/trade-ins/<int:trade_in_id>", methods=["GET", "POST"])
def trade_in_detail(trade_in_id):
    from app.models import TradeInRequest, TradeInStatus
    from app.services.tradein_service import TradeInService
    trade_in = TradeInRequest.query.get_or_404(trade_in_id)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "offer":
            TradeInService.send_offer(trade_in_id, request.form.get("offer_amount", type=float), request.form.get("admin_notes"))
            flash("Offer sent to customer.", "success")
        elif action == "reject":
            trade_in.status = TradeInStatus.REJECTED
            db.session.commit()
            flash("Trade-in rejected.", "info")
        return redirect(url_for("admin.trade_in_detail", trade_in_id=trade_in_id))
    return render_template("admin/tradeins/detail.html", trade_in=trade_in, TradeInStatus=TradeInStatus)


# --- Analytics ---

@admin_bp.route("/analytics")
def analytics():
    from app.services.analytics_service import AnalyticsService
    metrics = AnalyticsService.get_dashboard_metrics()
    return render_template("admin/analytics.html", metrics=metrics)


@admin_bp.route("/analytics/export/<fmt>")
def analytics_export(fmt):
    from flask import Response
    from app.services.analytics_service import AnalyticsService
    if fmt == "csv":
        data = AnalyticsService.export_csv()
        return Response(data, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=analytics.csv"})
    flash("Export format not supported.", "warning")
    return redirect(url_for("admin.analytics"))

# logout route
@admin_bp.route("/logout")
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("admin.login"))