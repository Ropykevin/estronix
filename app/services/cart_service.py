"""Shopping cart business logic."""

from flask import session
from flask_login import current_user

from app.extensions import db
from app.models import Cart, CartItem, Product


class CartService:
    """Manage cart operations for authenticated and guest users."""

    SESSION_KEY = "guest_cart"

    @classmethod
    def get_or_create_cart(cls):
        if current_user.is_authenticated:
            cart = current_user.cart
            if not cart:
                cart = Cart(user_id=current_user.id)
                db.session.add(cart)
                db.session.commit()
            cls._merge_guest_cart(cart)
            return cart
        return None

    @classmethod
    def _merge_guest_cart(cls, cart):
        guest_items = session.get(cls.SESSION_KEY, {})
        if not guest_items:
            return

        for product_id_str, qty in guest_items.items():
            product_id = int(product_id_str)
            product = Product.query.get(product_id)
            if not product:
                continue
            existing = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
            if existing:
                existing.quantity = min(existing.quantity + qty, product.stock_quantity)
            else:
                db.session.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=min(qty, product.stock_quantity)))

        session.pop(cls.SESSION_KEY, None)
        db.session.commit()

    @classmethod
    def get_cart_item_count(cls):
        if current_user.is_authenticated:
            cart = current_user.cart
            return cart.total_items if cart else 0
        return sum(session.get(cls.SESSION_KEY, {}).values())

    @classmethod
    def add_item(cls, product_id, quantity=1):
        product = Product.query.get_or_404(product_id)
        if not product.is_in_stock:
            return False, "Product is out of stock."

        quantity = max(1, min(quantity, product.stock_quantity))

        if current_user.is_authenticated:
            cart = cls.get_or_create_cart()
            item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
            if item:
                new_qty = min(item.quantity + quantity, product.stock_quantity)
                item.quantity = new_qty
            else:
                db.session.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity))
            db.session.commit()
        else:
            guest_cart = session.get(cls.SESSION_KEY, {})
            current_qty = guest_cart.get(str(product_id), 0)
            guest_cart[str(product_id)] = min(current_qty + quantity, product.stock_quantity)
            session[cls.SESSION_KEY] = guest_cart
            session.modified = True

        return True, "Added to cart."

    @classmethod
    def update_item(cls, product_id, quantity):
        product = Product.query.get_or_404(product_id)
        quantity = max(0, min(quantity, product.stock_quantity))

        if current_user.is_authenticated:
            cart = cls.get_or_create_cart()
            item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
            if not item:
                return False, "Item not in cart."
            if quantity == 0:
                db.session.delete(item)
            else:
                item.quantity = quantity
            db.session.commit()
        else:
            guest_cart = session.get(cls.SESSION_KEY, {})
            if quantity == 0:
                guest_cart.pop(str(product_id), None)
            else:
                guest_cart[str(product_id)] = quantity
            session[cls.SESSION_KEY] = guest_cart
            session.modified = True

        return True, "Cart updated."

    @classmethod
    def remove_item(cls, product_id):
        return cls.update_item(product_id, 0)

    @classmethod
    def get_cart_items(cls):
        if current_user.is_authenticated:
            cart = cls.get_or_create_cart()
            return cart.items.all() if cart else []

        guest_cart = session.get(cls.SESSION_KEY, {})
        items = []
        for product_id_str, qty in guest_cart.items():
            product = Product.query.get(int(product_id_str))
            if product:
                items.append({"product": product, "quantity": qty, "line_total": float(product.effective_price) * qty})
        return items

    @classmethod
    def get_subtotal(cls):
        if current_user.is_authenticated:
            cart = cls.get_or_create_cart()
            return cart.subtotal if cart else 0

        return sum(item["line_total"] for item in cls.get_cart_items())

    @classmethod
    def clear_cart(cls):
        if current_user.is_authenticated:
            cart = current_user.cart
            if cart:
                CartItem.query.filter_by(cart_id=cart.id).delete()
                db.session.commit()
        session.pop(cls.SESSION_KEY, None)
