"""Multi-warehouse inventory management."""

import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.models import Product, ProductStatus, Warehouse, WarehouseInventory, StockTransfer, StockMovement
from app.models.warehouse import MovementType, TransferStatus


class WarehouseService:
    @classmethod
    def get_stock_for_region(cls, product_id, region):
        """Available quantity in warehouses serving a region."""
        items = (
            WarehouseInventory.query.join(Warehouse)
            .filter(
                WarehouseInventory.product_id == product_id,
                Warehouse.is_active.is_(True),
                Warehouse.region.ilike(f"%{region}%"),
            )
            .all()
        )
        return sum(i.available for i in items)

    @classmethod
    def assign_stock(cls, warehouse_id, product_id, quantity, user_id=None, notes=None):
        inv = WarehouseInventory.query.filter_by(warehouse_id=warehouse_id, product_id=product_id).first()
        if not inv:
            inv = WarehouseInventory(warehouse_id=warehouse_id, product_id=product_id, quantity=0)
            db.session.add(inv)
        inv.quantity = quantity
        cls._log_movement(warehouse_id, product_id, MovementType.ADJUSTMENT, quantity - (inv.quantity - quantity), quantity, user_id, notes)
        cls._sync_product_total(product_id)
        db.session.commit()
        return inv

    @classmethod
    def add_stock(cls, warehouse_id, product_id, quantity, user_id=None, reference=None):
        inv = WarehouseInventory.query.filter_by(warehouse_id=warehouse_id, product_id=product_id).first()
        if not inv:
            inv = WarehouseInventory(warehouse_id=warehouse_id, product_id=product_id, quantity=0)
            db.session.add(inv)
        inv.quantity += quantity
        cls._log_movement(warehouse_id, product_id, MovementType.INBOUND, quantity, inv.quantity, user_id, reference)
        cls._sync_product_total(product_id)
        db.session.commit()
        return inv

    @classmethod
    def deduct_stock(cls, warehouse_id, product_id, quantity, user_id=None, reference=None):
        inv = WarehouseInventory.query.filter_by(warehouse_id=warehouse_id, product_id=product_id).first()
        if not inv or inv.available < quantity:
            return False
        inv.quantity -= quantity
        cls._log_movement(warehouse_id, product_id, MovementType.SALE, -quantity, inv.quantity, user_id, reference)
        cls._sync_product_total(product_id)
        db.session.commit()
        return True

    @classmethod
    def create_transfer(cls, from_id, to_id, product_id, quantity, user_id=None, notes=None):
        from_inv = WarehouseInventory.query.filter_by(warehouse_id=from_id, product_id=product_id).first()
        if not from_inv or from_inv.available < quantity:
            return None, "Insufficient stock at source warehouse."
        transfer = StockTransfer(
            transfer_number=f"TRF-{uuid.uuid4().hex[:10].upper()}",
            from_warehouse_id=from_id,
            to_warehouse_id=to_id,
            product_id=product_id,
            quantity=quantity,
            status=TransferStatus.PENDING,
            notes=notes,
            created_by_id=user_id,
        )
        db.session.add(transfer)
        db.session.commit()
        return transfer, None

    @classmethod
    def complete_transfer(cls, transfer_id, user_id=None):
        transfer = StockTransfer.query.get_or_404(transfer_id)
        if transfer.status != TransferStatus.PENDING:
            return False, "Transfer is not pending."
        from_inv = WarehouseInventory.query.filter_by(
            warehouse_id=transfer.from_warehouse_id, product_id=transfer.product_id
        ).first()
        if not from_inv or from_inv.available < transfer.quantity:
            return False, "Insufficient stock."
        from_inv.quantity -= transfer.quantity
        to_inv = WarehouseInventory.query.filter_by(
            warehouse_id=transfer.to_warehouse_id, product_id=transfer.product_id
        ).first()
        if not to_inv:
            to_inv = WarehouseInventory(
                warehouse_id=transfer.to_warehouse_id, product_id=transfer.product_id, quantity=0
            )
            db.session.add(to_inv)
        to_inv.quantity += transfer.quantity
        transfer.status = TransferStatus.COMPLETED
        transfer.completed_at = datetime.now(timezone.utc)
        cls._log_movement(transfer.from_warehouse_id, transfer.product_id, MovementType.TRANSFER, -transfer.quantity, from_inv.quantity, user_id, transfer.transfer_number)
        cls._log_movement(transfer.to_warehouse_id, transfer.product_id, MovementType.TRANSFER, transfer.quantity, to_inv.quantity, user_id, transfer.transfer_number)
        cls._sync_product_total(transfer.product_id)
        db.session.commit()
        return True, None

    @classmethod
    def _log_movement(cls, warehouse_id, product_id, mtype, change, after, user_id, ref=None):
        db.session.add(
            StockMovement(
                warehouse_id=warehouse_id,
                product_id=product_id,
                movement_type=mtype,
                quantity_change=change,
                quantity_after=after,
                reference=ref,
                created_by_id=user_id,
            )
        )

    @classmethod
    def _sync_product_total(cls, product_id):
        total = db.session.query(db.func.coalesce(db.func.sum(WarehouseInventory.quantity), 0)).filter_by(
            product_id=product_id
        ).scalar()
        product = Product.query.get(product_id)
        if product:
            product.stock_quantity = int(total)
            if product.stock_quantity == 0 and not product.is_preorder:
                product.status = ProductStatus.OUT_OF_STOCK
            elif product.status == ProductStatus.OUT_OF_STOCK and product.stock_quantity > 0:
                product.status = ProductStatus.ACTIVE

    @classmethod
    def get_inventory_report(cls):
        warehouses = Warehouse.query.filter_by(is_active=True).order_by(Warehouse.name).all()
        return {"warehouses": warehouses, "total_skus": WarehouseInventory.query.count()}
