"""PDF invoice generation and email delivery."""

import io
import os
import uuid

from flask import current_app, render_template, url_for

from app.extensions import db
from app.models import Order


class InvoiceService:
    @classmethod
    def ensure_invoice_number(cls, order):
        if not order.invoice_number:
            order.invoice_number = Order.generate_invoice_number()
            db.session.commit()
        return order.invoice_number

    @classmethod
    def generate_pdf(cls, order):
        """Generate PDF invoice bytes using ReportLab."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ImportError:
            return None

        cls.ensure_invoice_number(order)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=20 * mm, bottomMargin=20 * mm)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"<b>{current_app.config['APP_NAME']}</b>", styles["Title"]))
        elements.append(Paragraph("Tax Invoice", styles["Heading2"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Invoice: <b>{order.invoice_number}</b>", styles["Normal"]))
        elements.append(Paragraph(f"Order: {order.order_number}", styles["Normal"]))
        elements.append(Paragraph(f"Date: {order.created_at.strftime('%Y-%m-%d')}", styles["Normal"]))
        elements.append(Paragraph(f"Customer: {order.user.full_name}", styles["Normal"]))
        elements.append(Spacer(1, 16))

        data = [["Product", "SKU", "Qty", "Unit Price", "Total"]]
        for item in order.items:
            data.append([
                item.product_name,
                item.product_sku,
                str(item.quantity),
                f"KES {float(item.unit_price):,.2f}",
                f"KES {float(item.total_price):,.2f}",
            ])
        data.append(["", "", "", "Subtotal", f"KES {float(order.subtotal):,.2f}"])
        data.append(["", "", "", "Shipping", f"KES {float(order.shipping_cost):,.2f}"])
        data.append(["", "", "", "VAT (16%)", f"KES {float(order.tax_amount):,.2f}"])
        if order.loyalty_discount:
            data.append(["", "", "", "Loyalty Discount", f"-KES {float(order.loyalty_discount):,.2f}"])
        data.append(["", "", "", "TOTAL", f"KES {float(order.total_amount):,.2f}"])

        table = Table(data, colWidths=[180, 70, 40, 80, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -4), 0.5, colors.grey),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Thank you for shopping with Estronix.", styles["Normal"]))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    def email_invoice(cls, order):
        from app.services.email_service import EmailService
        pdf_bytes = cls.generate_pdf(order)
        if pdf_bytes:
            # Email with PDF attachment would extend EmailService
            pass
        html = render_template("emails/invoice.html", order=order)
        EmailService.send_email(
            f"Invoice {order.invoice_number}",
            [order.user.email],
            f"Your invoice for order {order.order_number}",
            html,
        )
