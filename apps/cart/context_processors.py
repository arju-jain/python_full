from .services import CartService

def cart_context(request):
    """Exposes cart totals and count globally for headers and quick cart drawers."""
    try:
        cart = CartService.get_or_create_cart(request)
        return {
            'cart': cart,
            'cart_item_count': cart.total_items,
            'cart_subtotal': cart.subtotal,
        }
    except Exception:
        return {
            'cart': None,
            'cart_item_count': 0,
            'cart_subtotal': 0,
        }
