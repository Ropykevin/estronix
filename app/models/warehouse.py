"""Multi-warehouse inventory models."""

import enum
from datetime import datetime, timezone

from app.extensions import db
from app.utils.enums import enum_values


class TransferStatus(enum.Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MovementType(enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    SALE = "sale"


class Warehouse(db.Model):
    """Physical warehouse / fulfillment center."""

    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    region = db.Column(db.String(100), nullable=False, index=True)
    city = db.Column(db.String(100))
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    inventory = db.relationship("WarehouseInventory", back_populates="warehouse", lazy="dynamic")
    transfers_from = db.relationship(
        "StockTransfer", foreign_keys="StockTransfer.from_warehouse_id", back_populates="from_warehouse", lazy="dynamic"
    )
    transfers_to = db.relationship(
        "StockTransfer", foreign_keys="StockTransfer.to_warehouse_id", back_populates="to_warehouse", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Warehouse {self.code}>"


class WarehouseInventory(db.Model):
    """Stock level per product per warehouse."""

    __tablename__ = "warehouse_inventory"

    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    reserved = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    warehouse = db.relationship("Warehouse", back_populates="inventory")
    product = db.relationship("Product", back_populates="warehouse_stock")

    __table_args__ = (db.UniqueConstraint("warehouse_id", "product_id", name="uq_warehouse_product"),)

    @property
    def available(self):
        return max(0, self.quantity - self.reserved)


class StockTransfer(db.Model):
    """Inter-warehouse stock transfer."""

    __tablename__ = "stock_transfers"

    id = db.Column(db.Integer, primary_key=True)
    transfer_number = db.Column(db.String(36), unique=True, nullable=False, index=True)
    from_warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    to_warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(TransferStatus, values_callable=enum_values), default=TransferStatus.PENDING, nullable=False)
    notes = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)

    from_warehouse = db.relationship("Warehouse", foreign_keys=[from_warehouse_id], back_populates="transfers_from")
    to_warehouse = db.relationship("Warehouse", foreign_keys=[to_warehouse_id], back_populates="transfers_to")
    product = db.relationship("Product")
    created_by = db.relationship("User")


class StockMovement(db.Model):
    """Audit log of inventory changes."""

    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    movement_type = db.Column(db.Enum(MovementType, values_callable=enum_values), nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)
    quantity_after = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    warehouse = db.relationship("Warehouse")
    product = db.relationship("Product")
    created_by = db.relationship("User")
