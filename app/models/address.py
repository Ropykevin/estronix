"""Customer address model."""

from datetime import datetime, timezone

from app.extensions import db


class Address(db.Model):
    """Shipping or billing address for a customer."""

    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    label = db.Column(db.String(50), default="Home")
    full_name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    county = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default="Kenya", nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", back_populates="addresses")

    def formatted(self):
        parts = [
            self.full_name,
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.county or ''} {self.postal_code or ''}".strip(),
            self.country,
            f"Phone: {self.phone}",
        ]
        return "\n".join(p for p in parts if p)

    def __repr__(self):
        return f"<Address {self.label} for User {self.user_id}>"
