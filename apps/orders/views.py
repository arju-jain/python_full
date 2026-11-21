from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .services import OrderService
from .models import Order
from .forms import CheckoutForm
from apps.cart.services import CartService
from apps.accounts.models import Address

@login_required
def checkout_view(request):
    """Multi-vendor order checkout."""
    cart = CartService.get_or_create_cart(request)
    if cart.total_items == 0:
        messages.warning(request, "Your shopping bag is empty. Please select products first.")
        return redirect('catalog:product_list')

    addresses = Address.objects.filter(user=request.user, address_type=Address.AddressType.SHIPPING)
    if not addresses.exists():
        messages.info(request, "Please add a delivery address to complete your checkout.")
        return redirect(f"{redirect('accounts:address_add').url}?next={request.path}")

    if request.method == 'POST':
        form = CheckoutForm(request.user, request.POST)
        if form.is_valid():
            address = form.cleaned_data['shipping_address']
            notes = form.cleaned_data['customer_notes']
            try:
                order = OrderService.create_order_from_cart(
                    cart=cart,
                    customer=request.user,
                    address_id=address.id,
                    notes=notes
                )
                # Clear cart items now that order is created
                CartService.clear_cart(cart)
                # Redirect to payment initiation
                return redirect('payments:initiate', order_number=order.order_number)
            except ValidationError as e:
                messages.error(request, str(e.message))
    else:
        initial_data = {}
        default_addr = addresses.filter(is_default=True).first() or addresses.first()
        if default_addr:
            initial_data['shipping_address'] = default_addr.id
        form = CheckoutForm(request.user, initial=initial_data)

    cart_items = cart.items.select_related('product__vendor').all()

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'addresses': addresses,
        'title': 'Secure Checkout | Aura Luxe'
    })


@login_required
def order_detail_view(request, order_number):
    """View detailed order confirmation and tracking status."""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product__images', 'fulfillments__vendor'),
        order_number=order_number,
        customer=request.user
    )
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'title': f"Order #{order.order_number} | Aura Luxe"
    })


@login_required
def order_history_view(request):
    """View customer's order history."""
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {
        'orders': orders,
        'title': 'My Orders | Aura Luxe'
    })
