"""Repair & service request models."""

import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.utils.enums import enum_values


class RepairStatus(enum.Enum):
    RECEIVED = "received"
    DIAGNOSING = "diagnosing"
    WAITING_FOR_PARTS = "waiting_for_parts"
    REPAIRING = "repairing"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RepairRequest(db.Model):
    """Customer repair / service ticket."""

    __tablename__ = "repair_requests"

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(36), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    issue_description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(RepairStatus, values_callable=enum_values), default=RepairStatus.RECEIVED, nullable=False)
    admin_notes = db.Column(db.Text)
    estimated_cost = db.Column(db.Numeric(10, 2))
    invoice_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="repair_requests")
    images = db.relationship("RepairImage", back_populates="repair_request", lazy="dynamic", cascade="all, delete-orphan")

    @staticmethod
    def generate_ticket_number():
        return f"REP-{uuid.uuid4().hex[:10].upper()}"

    def __repr__(self):
        return f"<RepairRequest {self.ticket_number}>"


class RepairImage(db.Model):
    """Uploaded images for a repair request."""

    __tablename__ = "repair_images"

    id = db.Column(db.Integer, primary_key=True)
    repair_request_id = db.Column(db.Integer, db.ForeignKey("repair_requests.id"), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    repair_request = db.relationship("RepairRequest", back_populates="images")
