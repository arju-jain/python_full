from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from .forms import ReviewForm
from apps.catalog.models import Product
from apps.orders.models import OrderItem

@login_required
def add_review_view(request, product_id):
    """Submit a review for a product."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)

    # Check if user already reviewed
    existing = Review.objects.filter(product=product, customer=request.user).first()
    if existing:
        messages.info(request, "You have already reviewed this product.")
        return redirect('catalog:product_detail', slug=product.slug)

    # Check verified purchase
    is_verified = OrderItem.objects.filter(
        order__customer=request.user,
        order__payment_status='PAID',
        product=product
    ).exists()

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.customer = request.user
            review.is_verified_purchase = is_verified
            review.save()
            messages.success(request, "Thank you! Your review has been published.")
            return redirect('catalog:product_detail', slug=product.slug)
    else:
        form = ReviewForm()

    return render(request, 'reviews/add_review.html', {
        'form': form,
        'product': product,
        'is_verified': is_verified,
        'title': f"Review {product.title}"
    })
