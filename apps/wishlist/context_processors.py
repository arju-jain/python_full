from .models import Wishlist

def wishlist_context(request):
    """Exposes customer's wishlist item count globally."""
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.filter(user=request.user).first()
            count = wishlist.total_items if wishlist else 0
            user_wishlist_product_ids = list(wishlist.items.values_list('product_id', flat=True)) if wishlist else []
            return {
                'wishlist_item_count': count,
                'user_wishlist_product_ids': user_wishlist_product_ids,
            }
        except Exception:
            return {'wishlist_item_count': 0, 'user_wishlist_product_ids': []}
    return {'wishlist_item_count': 0, 'user_wishlist_product_ids': []}
