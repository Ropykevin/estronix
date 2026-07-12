"""Pytest configuration and fixtures."""

import pytest

from app import create_app
from app.extensions import db
from app.models import Role, User


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        for role_name in ("admin", "customer"):
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name, description=f"{role_name} role"))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def customer_user(app):
    role = Role.query.filter_by(name="customer").first()
    user = User(
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        phone="0712345678",
        is_verified=True,
        role_id=role.id,
    )
    user.set_password("TestPass1")
    db.session.add(user)
    db.session.commit()
    return user
