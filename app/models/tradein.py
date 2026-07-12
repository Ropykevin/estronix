"""Device trade-in program models."""

import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.utils.enums import enum_values


class TradeInStatus(enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    OFFER_SENT = "offer_sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DeviceCondition(enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class TradeInRequest(db.Model):
    """Customer device trade-in submission."""

    __tablename__ = "trade_in_requests"

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(36), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    device_brand = db.Column(db.String(100), nullable=False)
    device_model = db.Column(db.String(200), nullable=False)
    condition = db.Column(db.Enum(DeviceCondition, values_callable=enum_values), nullable=False)
    condition_notes = db.Column(db.Text)
    estimated_value = db.Column(db.Numeric(10, 2))
    final_offer = db.Column(db.Numeric(10, 2))
    status = db.Column(db.Enum(TradeInStatus, values_callable=enum_values), default=TradeInStatus.SUBMITTED, nullable=False)
    linked_order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", back_populates="trade_in_requests")
    images = db.relationship("TradeInImage", back_populates="trade_in", lazy="dynamic", cascade="all, delete-orphan")
    linked_order = db.relationship("Order")

    @staticmethod
    def generate_reference():
        return f"TIN-{uuid.uuid4().hex[:10].upper()}"

    def __repr__(self):
        return f"<TradeIn {self.reference_number}>"


class TradeInImage(db.Model):
    """Device photos for trade-in assessment."""

    __tablename__ = "trade_in_images"

    id = db.Column(db.Integer, primary_key=True)
    trade_in_id = db.Column(db.Integer, db.ForeignKey("trade_in_requests.id"), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    trade_in = db.relationship("TradeInRequest", back_populates="images")
