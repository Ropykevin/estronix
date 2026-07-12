"""Repair and service request workflow."""

from app.extensions import db
from app.models import RepairRequest, RepairStatus, UserNotification
from app.utils.helpers import save_upload


class RepairService:
    @classmethod
    def create_request(cls, user, form_data, image_files=None):
        repair = RepairRequest(
            ticket_number=RepairRequest.generate_ticket_number(),
            user_id=user.id,
            product_name=form_data["product_name"],
            brand=form_data.get("brand"),
            serial_number=form_data.get("serial_number"),
            issue_description=form_data["issue_description"],
            status=RepairStatus.RECEIVED,
        )
        db.session.add(repair)
        db.session.flush()

        if image_files:
            from app.models import RepairImage
            for f in image_files:
                url = save_upload(f, "repairs")
                if url:
                    db.session.add(RepairImage(repair_request_id=repair.id, image_url=url))

        cls._notify(user.id, "Repair Request Received", f"Ticket {repair.ticket_number} has been submitted.", f"/account/repairs/{repair.id}")
        db.session.commit()
        return repair

    @classmethod
    def update_status(cls, repair_id, status, admin_notes=None, estimated_cost=None):
        repair = RepairRequest.query.get_or_404(repair_id)
        repair.status = RepairStatus(status)
        if admin_notes:
            repair.admin_notes = admin_notes
        if estimated_cost is not None:
            repair.estimated_cost = estimated_cost
        cls._notify(
            repair.user_id,
            f"Repair Update: {status.replace('_', ' ').title()}",
            f"Your repair ticket {repair.ticket_number} status has been updated.",
            f"/account/repairs/{repair.id}",
        )
        db.session.commit()
        return repair

    @classmethod
    def _notify(cls, user_id, title, message, link):
        db.session.add(UserNotification(user_id=user_id, title=title, message=message, link=link))
