"""Common helper functions."""

import os
import secrets
import uuid
from datetime import datetime, timezone

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.utils import secure_filename


def format_currency(amount, currency="KES"):
    """Format a numeric amount as currency string."""
    return f"{currency} {float(amount):,.2f}"


def allowed_file(filename):
    """Check if uploaded file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


def save_upload(file, subfolder="products"):
    """Save an uploaded file and return its relative URL path."""
    if not file or not allowed_file(file.filename):
        return None

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, secure_filename(filename))
    file.save(filepath)
    return f"/static/uploads/{subfolder}/{filename}"


def delete_upload(relative_url):
    """Remove a previously uploaded file from disk."""
    if not relative_url or not relative_url.startswith("/static/uploads/"):
        return

    filepath = os.path.join(current_app.root_path, relative_url.lstrip("/"))
    if os.path.isfile(filepath):
        os.remove(filepath)


def generate_token(data, salt="estronix-token"):
    """Generate a signed timed token."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(data, salt=salt)


def verify_token(token, salt="estronix-token", max_age=3600):
    """Verify a signed timed token and return payload or None."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return serializer.loads(token, salt=salt, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


def utcnow():
    return datetime.now(timezone.utc)
