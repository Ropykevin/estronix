"""Authentication routes."""
from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth.forms import ForgotPasswordForm, LoginForm, RegistrationForm, ResetPasswordForm
from app.extensions import db, limiter
from app.models import Role, User
from app.services.email_service import EmailService
from app.utils.helpers import generate_token, verify_token
from app.utils.security import is_safe_redirect_url
from app.utils.sanitizer import sanitize_html

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        customer_role = Role.query.filter_by(name="customer").first()
        if not customer_role:
            flash("System not configured. Please contact support.", "danger")
            return redirect(url_for("auth.register"))

        user = User(
            email=form.email.data.lower().strip(),
            username=form.username.data.lower().strip(),
            first_name=sanitize_html(form.first_name.data.strip()),
            last_name=sanitize_html(form.last_name.data.strip()),
            phone=form.phone.data.strip(),
            role_id=customer_role.id,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        EmailService.send_verification_email(user)
        flash("Account created! Please check your email to verify your account.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("auth.login"))

            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=form.remember.data)

            next_page = request.args.get("next")
            if next_page and not is_safe_redirect_url(next_page):
                next_page = None

            if user.is_admin:
                return redirect(next_page or url_for("admin.dashboard"))
            return redirect(next_page or url_for("main.index"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/verify/<token>")
def verify_email(token):
    email = verify_token(token, salt="email-verify", max_age=86400)
    if not email:
        flash("Verification link is invalid or expired.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    if user.is_verified:
        flash("Email already verified.", "info")
    else:
        user.is_verified = True
        db.session.commit()
        flash("Email verified successfully! You can now log in.", "success")

    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
@login_required
def resend_verification():
    if current_user.is_verified:
        return redirect(url_for("main.index"))

    EmailService.send_verification_email(current_user)
    flash("Verification email sent.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            EmailService.send_password_reset_email(user)
        flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_token(token, salt="password-reset", max_age=3600)
    if not email:
        flash("Reset link is invalid or expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)
