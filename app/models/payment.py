"""Payment models for M-Pesa and other payment methods."""

import enum
from datetime import datetime, timezone

from app.extensions import db
from app.utils.enums import enum_names


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(enum.Enum):
    MPESA = "mpesa"
    CASH_ON_DELIVERY = "cash_on_delivery"


class Payment(db.Model):
    """Payment transaction record."""

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.Enum(PaymentMethod, values_callable=enum_names), nullable=False)
    status = db.Column(db.Enum(PaymentStatus, values_callable=enum_names), default=PaymentStatus.PENDING, nullable=False)
    transaction_id = db.Column(db.String(100), index=True)
    mpesa_receipt = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    checkout_request_id = db.Column(db.String(100))
    merchant_request_id = db.Column(db.String(100))
    result_code = db.Column(db.String(10))
    result_description = db.Column(db.Text)
    raw_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = db.Column(db.DateTime)

    order = db.relationship("Order", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.id} {self.method.value} {self.status.value}>"
