import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from .services import CartService
from .models import CartItem
from apps.catalog.models import Product

def cart_detail_view(request):
    """View customer's shopping cart."""
    cart = CartService.get_or_create_cart(request)
    cart_items = cart.items.select_related('product__vendor', 'product__inventory').prefetch_related('product__images')
    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'cart_items': cart_items,
        'title': 'Shopping Bag | Aura Luxe'
    })


@require_POST
def cart_add_view(request, product_id):
    """Add product to shopping cart via standard POST or AJAX."""
    cart = CartService.get_or_create_cart(request)
    product = get_object_or_404(Product, pk=product_id, is_active=True)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
    
    quantity = 1
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1
    else:
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

    try:
        CartService.add_item(cart, product, quantity=max(1, quantity))
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': f"Added '{product.title}' to your shopping bag.",
                'cart_item_count': cart.total_items,
                'cart_subtotal': str(cart.subtotal)
            })
        messages.success(request, f"'{product.title}' added to your shopping bag.")
    except ValidationError as e:
        if is_ajax:
            return JsonResponse({'success': False, 'message': str(e.message)}, status=400)
        messages.warning(request, str(e.message))

    return redirect('cart:cart_detail')


@require_POST
def cart_update_view(request, item_id):
    """Update item quantity in cart."""
    cart = CartService.get_or_create_cart(request)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'

    quantity = 1
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1
    else:
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

    try:
        updated_item = CartService.update_quantity(item_id, quantity, cart)
        if is_ajax:
            return JsonResponse({
                'success': True,
                'item_subtotal': str(updated_item.subtotal) if updated_item else '0.00',
                'cart_subtotal': str(cart.subtotal),
                'cart_total': str(cart.grand_total),
                'cart_item_count': cart.total_items
            })
        messages.success(request, "Bag updated.")
    except ValidationError as e:
        if is_ajax:
            return JsonResponse({'success': False, 'message': str(e.message)}, status=400)
        messages.warning(request, str(e.message))

    return redirect('cart:cart_detail')


@require_POST
def cart_remove_view(request, item_id):
    """Remove item from cart."""
    cart = CartService.get_or_create_cart(request)
    CartService.remove_item(item_id, cart)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': "Item removed from bag.",
            'cart_subtotal': str(cart.subtotal),
            'cart_total': str(cart.grand_total),
            'cart_item_count': cart.total_items
        })
    messages.info(request, "Item removed from your shopping bag.")
    return redirect('cart:cart_detail')
