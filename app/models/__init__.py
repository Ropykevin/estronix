"""Database models for Estronix E-Commerce Platform."""

from app.models.user import Role, User
from app.models.category import Category
from app.models.product import Product, ProductImage, ProductSpecification, ProductStatus
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.address import Address
from app.models.review import Review
from app.models.warehouse import Warehouse, WarehouseInventory, StockTransfer, StockMovement, TransferStatus, MovementType
from app.models.warranty import WarrantyRegistration, WarrantyStatus
from app.models.repair import RepairRequest, RepairImage, RepairStatus
from app.models.tradein import TradeInRequest, TradeInImage, TradeInStatus, DeviceCondition
from app.models.loyalty import LoyaltyAccount, LoyaltyTransaction, LoyaltyTier, TransactionType, Coupon
from app.models.wishlist import WishlistItem, RecentlyViewed, ProductView
from app.models.notification import UserNotification

__all__ = [
    "Role", "User", "Category",
    "Product", "ProductImage", "ProductSpecification", "ProductStatus",
    "Cart", "CartItem", "Order", "OrderItem", "OrderStatus",
    "Payment", "PaymentMethod", "PaymentStatus", "Address", "Review",
    "Warehouse", "WarehouseInventory", "StockTransfer", "StockMovement", "TransferStatus", "MovementType",
    "WarrantyRegistration", "WarrantyStatus",
    "RepairRequest", "RepairImage", "RepairStatus",
    "TradeInRequest", "TradeInImage", "TradeInStatus", "DeviceCondition",
    "LoyaltyAccount", "LoyaltyTransaction", "LoyaltyTier", "TransactionType", "Coupon",
    "WishlistItem", "RecentlyViewed", "ProductView", "UserNotification",
]
