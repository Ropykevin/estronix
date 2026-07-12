"""Device trade-in program service."""

from decimal import Decimal

from app.extensions import db
from app.models import TradeInRequest, TradeInStatus, UserNotification
from app.models.tradein import DeviceCondition
from app.utils.helpers import save_upload

# Base trade-in values by condition multiplier
CONDITION_MULTIPLIERS = {
    "excellent": Decimal("0.85"),
    "good": Decimal("0.70"),
    "fair": Decimal("0.50"),
    "poor": Decimal("0.30"),
}

BASE_VALUES = {
    "smartphone": Decimal("25000"),
    "laptop": Decimal("45000"),
    "tablet": Decimal("15000"),
    "default": Decimal("10000"),
}


class TradeInService:
    @classmethod
    def estimate_value(cls, device_type, condition):
        base = BASE_VALUES.get(device_type, BASE_VALUES["default"])
        multiplier = CONDITION_MULTIPLIERS.get(condition, Decimal("0.50"))
        return round(base * multiplier, 2)

    @classmethod
    def create_request(cls, user, form_data, image_files=None):
        condition = form_data["condition"]
        if isinstance(condition, str):
            condition = DeviceCondition(condition)
        estimated = cls.estimate_value(form_data.get("device_type", "default"), condition.value if isinstance(condition, DeviceCondition) else condition)
        trade_in = TradeInRequest(
            reference_number=TradeInRequest.generate_reference(),
            user_id=user.id,
            device_brand=form_data["device_brand"],
            device_model=form_data["device_model"],
            condition=condition,
            condition_notes=form_data.get("condition_notes"),
            estimated_value=estimated,
            status=TradeInStatus.SUBMITTED,
        )
        db.session.add(trade_in)
        db.session.flush()

        if image_files:
            from app.models import TradeInImage
            for f in image_files:
                url = save_upload(f, "tradeins")
                if url:
                    db.session.add(TradeInImage(trade_in_id=trade_in.id, image_url=url))

        db.session.add(
            UserNotification(
                user_id=user.id,
                title="Trade-In Submitted",
                message=f"Reference {trade_in.reference_number}. Estimated value: KES {estimated:,.0f}",
                link=f"/trade-in/{trade_in.id}",
            )
        )
        db.session.commit()
        return trade_in

    @classmethod
    def send_offer(cls, trade_in_id, offer_amount, admin_notes=None):
        trade_in = TradeInRequest.query.get_or_404(trade_in_id)
        trade_in.final_offer = offer_amount
        trade_in.status = TradeInStatus.OFFER_SENT
        trade_in.admin_notes = admin_notes
        db.session.add(
            UserNotification(
                user_id=trade_in.user_id,
                title="Trade-In Offer Ready",
                message=f"Offer: KES {float(offer_amount):,.0f} for your {trade_in.device_model}",
                link=f"/trade-in/{trade_in.id}",
            )
        )
        db.session.commit()
        return trade_in

    @classmethod
    def accept_offer(cls, trade_in_id, user_id):
        trade_in = TradeInRequest.query.filter_by(id=trade_in_id, user_id=user_id).first_or_404()
        if trade_in.status != TradeInStatus.OFFER_SENT:
            return None, "No pending offer."
        trade_in.status = TradeInStatus.ACCEPTED
        db.session.commit()
        return trade_in, None
