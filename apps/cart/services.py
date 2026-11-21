from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Cart, CartItem
from apps.catalog.models import Product

class CartService:
    @staticmethod
    def get_or_create_cart(request):
        """Retrieve or initialize the active cart for the session or authenticated user."""
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            # If guest cart existed before login, merge items
            session_key = request.session.session_key
            if session_key:
                guest_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
                if guest_cart:
                    for item in guest_cart.items.all():
                        existing_item = CartItem.objects.filter(cart=cart, product=item.product).first()
                        if existing_item:
                            existing_item.quantity += item.quantity
                            existing_item.save()
                        else:
                            item.cart = cart
                            item.save()
                    guest_cart.delete()
            return cart
        else:
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
            return cart

    @classmethod
    @transaction.atomic
    def add_item(cls, cart: Cart, product: Product, quantity: int = 1):
        """Add product to cart with inventory validation."""
        available_stock = product.stock_quantity
        if available_stock <= 0:
            raise ValidationError(f"'{product.title}' is currently out of stock.")

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            new_qty = cart_item.quantity + quantity
            if new_qty > available_stock:
                cart_item.quantity = available_stock
                cart_item.save()
                raise ValidationError(f"Maximum available stock for '{product.title}' is {available_stock} units. Adjusted to maximum.")
            cart_item.quantity = new_qty
            cart_item.save()
        else:
            if quantity > available_stock:
                cart_item.quantity = available_stock
                cart_item.save()
                raise ValidationError(f"Only {available_stock} units available. Adjusted to maximum.")

        return cart_item

    @classmethod
    def update_quantity(cls, cart_item_id: int, quantity: int, cart: Cart):
        """Update item quantity or remove if quantity <= 0."""
        cart_item = CartItem.objects.filter(id=cart_item_id, cart=cart).first()
        if not cart_item:
            return None

        if quantity <= 0:
            cart_item.delete()
            return None

        available_stock = cart_item.product.stock_quantity
        if quantity > available_stock:
            cart_item.quantity = available_stock
            cart_item.save()
            raise ValidationError(f"Only {available_stock} units available.")
        
        cart_item.quantity = quantity
        cart_item.save()
        return cart_item

    @classmethod
    def remove_item(cls, cart_item_id: int, cart: Cart):
        """Remove product from cart."""
        CartItem.objects.filter(id=cart_item_id, cart=cart).delete()

    @classmethod
    def clear_cart(cls, cart: Cart):
        """Empty cart."""
        cart.items.all().delete()
