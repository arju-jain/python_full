from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Wishlist, WishlistItem
from apps.catalog.models import Product

@login_required
def wishlist_detail_view(request):
    """View items saved to wishlist."""
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    items = wishlist.items.select_related('product__vendor', 'product__inventory').prefetch_related('product__images')
    return render(request, 'wishlist/wishlist_detail.html', {
        'wishlist': wishlist,
        'items': items,
        'title': 'My Wishlist | Aura Luxe'
    })


@login_required
@require_POST
def wishlist_toggle_view(request, product_id):
    """Toggle product in user's wishlist (AJAX or standard POST)."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    
    item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'

    if item:
        item.delete()
        added = False
        message = f"Removed '{product.title}' from your wishlist."
    else:
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        added = True
        message = f"Saved '{product.title}' to your wishlist."

    if is_ajax:
        return JsonResponse({
            'success': True,
            'added': added,
            'message': message,
            'wishlist_item_count': wishlist.total_items
        })

    messages.info(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'wishlist:wishlist_detail'))


@login_required
@require_POST
def wishlist_remove_view(request, item_id):
    """Remove item directly from wishlist."""
    item = get_object_or_404(WishlistItem, pk=item_id, wishlist__user=request.user)
    item.delete()
    messages.info(request, "Item removed from your wishlist.")
    return redirect('wishlist:wishlist_detail')
