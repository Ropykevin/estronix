"""Admin product edit tests."""

from decimal import Decimal

from app.extensions import db
from app.models import Category, Product, ProductStatus, Role, User


def _login_admin(client, app):
    with app.app_context():
        admin_role = Role.query.filter_by(name="admin").first()
        if not admin_role:
            admin_role = Role(name="admin", description="admin")
            db.session.add(admin_role)
            db.session.commit()
        if not User.query.filter_by(email="admin@test.com").first():
            admin = User(
                email="admin@test.com",
                username="admin",
                first_name="A",
                last_name="B",
                is_verified=True,
                role_id=admin_role.id,
            )
            admin.set_password("Admin@123")
            db.session.add(admin)
            db.session.commit()

    return client.post(
        "/auth/login",
        data={"email": "admin@test.com", "password": "Admin@123"},
        follow_redirects=True,
    )


def _seed_product(app):
    with app.app_context():
        cat = Category(name="Phones", slug="phones", is_active=True)
        db.session.add(cat)
        db.session.commit()
        product = Product(
            name="Test Phone",
            slug="test-phone",
            sku="TP-001",
            brand="Test",
            price=Decimal("1000"),
            stock_quantity=5,
            category_id=cat.id,
            status=ProductStatus.ACTIVE,
        )
        db.session.add(product)
        db.session.commit()
        return product.id, cat.id


def _csrf_from_html(html):
    import re

    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return match.group(1) if match else None


def test_admin_edit_product_page_loads(client, app):
    _login_admin(client, app)
    product_id, _ = _seed_product(app)
    response = client.get(f"/admin/products/{product_id}/edit")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Test Phone" in html
    assert "Edit Product" in html


def test_admin_edit_product_updates(client, app):
    _login_admin(client, app)
    product_id, category_id = _seed_product(app)

    response = client.get(f"/admin/products/{product_id}/edit")
    csrf_token = _csrf_from_html(response.get_data(as_text=True))

    response = client.post(
        f"/admin/products/{product_id}/edit",
        data={
            "csrf_token": csrf_token,
            "name": "Test Phone Updated",
            "sku": "TP-001",
            "brand": "TestBrand",
            "description": "Updated desc",
            "price": "1500",
            "discount_price": "",
            "stock_quantity": "10",
            "warranty_info": "1 year",
            "category_id": str(category_id),
            "status": "active",
            "submit": "Save Product",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Product updated." in response.data

    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.name == "Test Phone Updated"
        assert float(product.price) == 1500
        assert product.stock_quantity == 10
