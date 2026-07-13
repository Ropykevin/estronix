"""Bootstrap admin account from environment configuration."""

import secrets

from flask import current_app

from app.extensions import db
from app.models import Role, User


def _unique_username(base):
    username = (base[:80] or "admin")
    suffix = 1
    while User.query.filter_by(username=username).first():
        username = f"{base[:75]}{suffix}"[:80]
        suffix += 1
    return username


def _username_from_email(email):
    return email.split("@")[0].replace(".", "_")


def ensure_admin(*, reset_password=False):
    """Create, migrate, or update the configured admin user.

    Returns a short status string describing what happened.
    """
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        return "error: admin role missing — run flask init-db first"

    admin_email = current_app.config["ADMIN_EMAIL"]
    admin_password = current_app.config.get("ADMIN_INITIAL_PASSWORD") or ""

    admin_user = User.query.filter_by(email=admin_email).first()
    legacy_admin = User.query.filter_by(email="admin@estronix.com").first()
    role_admin = User.query.filter_by(role_id=admin_role.id).first()

    if admin_user and admin_user.is_admin:
        if reset_password:
            if not admin_password:
                return f"error: set ADMIN_INITIAL_PASSWORD to reset password for {admin_email}"
            admin_user.set_password(admin_password)
            admin_user.is_verified = True
            admin_user.is_active = True
            db.session.commit()
            return f"password reset for {admin_email}"
        return f"admin already exists: {admin_email}"

    if admin_user and not admin_user.is_admin:
        if not reset_password:
            return (
                f"error: {admin_email} is a customer account — "
                "run: flask ensure-admin --force"
            )
        if not admin_password:
            return f"error: set ADMIN_INITIAL_PASSWORD to promote {admin_email} to admin"
        admin_user.role_id = admin_role.id
        admin_user.set_password(admin_password)
        admin_user.is_verified = True
        admin_user.is_active = True
        db.session.commit()
        return f"promoted {admin_email} to admin and reset password"

    if legacy_admin and legacy_admin.is_admin:
        legacy_admin.email = admin_email
        legacy_admin.username = _unique_username(_username_from_email(admin_email))
        legacy_admin.is_verified = True
        legacy_admin.is_active = True
        if admin_password:
            legacy_admin.set_password(admin_password)
        db.session.commit()
        if admin_password:
            return f"migrated admin to {admin_email} and set password from ADMIN_INITIAL_PASSWORD"
        return f"migrated admin email to {admin_email}"

    if role_admin:
        role_admin.email = admin_email
        role_admin.username = _unique_username(_username_from_email(admin_email))
        role_admin.is_verified = True
        role_admin.is_active = True
        if admin_password:
            role_admin.set_password(admin_password)
        db.session.commit()
        if admin_password:
            return f"updated admin email to {admin_email} and set password from ADMIN_INITIAL_PASSWORD"
        return f"updated admin email to {admin_email}"

    if not admin_password:
        if current_app.config.get("TESTING"):
            admin_password = "Admin@123"
        else:
            admin_password = secrets.token_urlsafe(16)
            print(f"Generated admin password (save now): {admin_password}")

    admin = User(
        email=admin_email,
        username=_unique_username(_username_from_email(admin_email)),
        first_name="System",
        last_name="Admin",
        is_verified=True,
        is_active=True,
        role_id=admin_role.id,
    )
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()

    if current_app.config.get("ADMIN_INITIAL_PASSWORD"):
        return f"created admin: {admin_email} (password from ADMIN_INITIAL_PASSWORD)"
    return f"created admin: {admin_email}"
