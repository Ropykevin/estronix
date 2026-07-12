"""Admin analytics and reporting service."""

import csv
import io
from datetime import datetime, timedelta, timezone

from sqlalchemy import extract, func

from app.extensions import db
from app.models import Order, OrderStatus, Payment, PaymentStatus, Product, ProductView, User
from app.models.payment import PaymentMethod


class AnalyticsService:
    @classmethod
    def _paid_orders_filter(cls):
        return Order.status == OrderStatus.PAID

    @classmethod
    def total_paid_sales(cls):
        return float(
            db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
            .filter(cls._paid_orders_filter())
            .scalar() or 0
        )

    @classmethod
    def paid_sales_since(cls, since):
        return float(
            db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
            .filter(cls._paid_orders_filter(), Order.paid_at.isnot(None), Order.paid_at >= since)
            .scalar() or 0
        )

    @classmethod
    def get_dashboard_metrics(cls):
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        def revenue_since(since):
            return cls.paid_sales_since(since)

        total_orders = Order.query.count()
        avg_order = float(
            db.session.query(func.coalesce(func.avg(Order.total_amount), 0)).scalar() or 0
        )
        repeat_customers = (
            db.session.query(Order.user_id)
            .group_by(Order.user_id)
            .having(func.count(Order.id) > 1)
            .count()
        )

        return {
            "daily_revenue": revenue_since(today_start),
            "monthly_revenue": revenue_since(month_start),
            "yearly_revenue": revenue_since(year_start),
            "total_orders": total_orders,
            "avg_order_value": avg_order,
            "repeat_customers": repeat_customers,
            "customer_growth": User.query.join(User.role).filter_by(name="customer").count(),
            "top_products": cls.get_top_products_safe(10),
            "top_categories": cls.get_top_categories(5),
            "order_status_distribution": cls.get_order_status_counts(),
            "payment_stats": cls.get_payment_stats(),
            "most_viewed": cls.get_most_viewed(10),
            "monthly_trend": cls.get_monthly_revenue(12),
        }

    @classmethod
    def get_top_products(cls, limit=10):
        return (
            db.session.query(
                Product.name,
                func.sum(db.text("order_items.quantity")).label("sold"),
                func.sum(db.text("order_items.total_price")).label("revenue"),
            )
            .join(db.text("order_items ON order_items.product_id = products.id"))
            .group_by(Product.id, Product.name)
            .order_by(func.sum(db.text("order_items.quantity")).desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_top_products_safe(cls, limit=10):
        from app.models import OrderItem
        return (
            db.session.query(
                Product.name,
                func.sum(OrderItem.quantity).label("sold"),
                func.sum(OrderItem.total_price).label("revenue"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .group_by(Product.id, Product.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_top_categories(cls, limit=5):
        from app.models import Category, OrderItem
        return (
            db.session.query(Category.name, func.count(OrderItem.id).label("orders"))
            .join(Product, Product.category_id == Category.id)
            .join(OrderItem, OrderItem.product_id == Product.id)
            .group_by(Category.id, Category.name)
            .order_by(func.count(OrderItem.id).desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_order_status_counts(cls):
        return db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()

    @classmethod
    def get_payment_stats(cls):
        return (
            db.session.query(Payment.method, Payment.status, func.count(Payment.id), func.sum(Payment.amount))
            .group_by(Payment.method, Payment.status)
            .all()
        )

    @classmethod
    def get_most_viewed(cls, limit=10):
        return (
            db.session.query(Product.name, Product.view_count, Product.slug)
            .filter(Product.view_count > 0)
            .order_by(Product.view_count.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_monthly_revenue(cls, months=12):
        return (
            db.session.query(
                extract("year", Order.paid_at).label("year"),
                extract("month", Order.paid_at).label("month"),
                func.sum(Order.total_amount).label("total"),
            )
            .filter(cls._paid_orders_filter(), Order.paid_at.isnot(None))
            .group_by("year", "month")
            .order_by("year", "month")
            .limit(months)
            .all()
        )

    @classmethod
    def export_orders_csv(cls):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Order", "Customer", "Status", "Total", "Date"])
        for order in Order.query.order_by(Order.created_at.desc()).limit(1000):
            writer.writerow([
                order.order_number,
                order.user.email,
                order.status.value,
                float(order.total_amount),
                order.created_at.isoformat(),
            ])
        return output.getvalue()

    @classmethod
    def export_csv(cls):
        """Export analytics summary as CSV."""
        metrics = cls.get_dashboard_metrics()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Daily Revenue", metrics["daily_revenue"]])
        writer.writerow(["Monthly Revenue", metrics["monthly_revenue"]])
        writer.writerow(["Yearly Revenue", metrics["yearly_revenue"]])
        writer.writerow(["Total Orders", metrics["total_orders"]])
        writer.writerow(["Average Order Value", metrics["avg_order_value"]])
        writer.writerow(["Repeat Customers", metrics["repeat_customers"]])
        writer.writerow(["Customer Growth", metrics["customer_growth"]])
        writer.writerow([])
        writer.writerow(["Top Products", "Sold", "Revenue"])
        for row in metrics["top_products"]:
            writer.writerow([row.name, row.sold, float(row.revenue or 0)])
        return output.getvalue()
