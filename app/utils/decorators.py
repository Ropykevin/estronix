"""Route decorators for access control."""

from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Restrict route to admin users."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated


def verified_required(f):
    """Restrict route to verified users."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_verified:
            flash("Please verify your email address first.", "warning")
            return redirect(url_for("auth.resend_verification"))
        return f(*args, **kwargs)

    return decorated
