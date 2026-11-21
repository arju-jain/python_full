from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from apps.catalog.models import Category, Product
from apps.vendors.models import Vendor
from .models import NewsletterSubscriber

def home_view(request):
    """
    Homepage featuring luxury hero, featured categories,
    trending products, new arrivals, and featured vendor boutiques.
    """
    featured_categories = Category.objects.filter(is_active=True, is_featured=True)[:6]
    if not featured_categories.exists():
        featured_categories = Category.objects.filter(is_active=True)[:6]

    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True,
        vendor__status=Vendor.Status.APPROVED
    ).select_related('vendor', 'category').prefetch_related('images')[:8]

    new_arrivals = Product.objects.filter(
        is_active=True,
        vendor__status=Vendor.Status.APPROVED
    ).order_by('-created_at').select_related('vendor', 'category').prefetch_related('images')[:8]

    featured_vendors = Vendor.objects.filter(
        status=Vendor.Status.APPROVED
    ).order_by('?')[:4]

    return render(request, 'core/home.html', {
        'featured_categories': featured_categories,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'featured_vendors': featured_vendors,
        'title': 'Aura Luxe | Fine Multi-Vendor Luxury Marketplace'
    })


@require_POST
def newsletter_subscribe_view(request):
    """Handle newsletter subscription form."""
    email = request.POST.get('email', '').strip().lower()
    if email:
        obj, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created:
            messages.success(request, "Thank you for subscribing to Aura Luxe Private Previews.")
        else:
            messages.info(request, "You are already subscribed to our private curations.")
    return redirect('core:home')


def about_view(request):
    """About Aura Luxe."""
    return render(request, 'core/about.html', {'title': 'Our Heritage & Philosophy | Aura Luxe'})


def contact_view(request):
    """Concierge and Support contact page."""
    if request.method == 'POST':
        messages.success(request, "Thank you for your inquiry. A private client concierge will respond within 24 hours.")
        return redirect('core:contact')
    return render(request, 'core/contact.html', {'title': 'Client Concierge | Aura Luxe'})


def terms_view(request):
    """Terms and conditions."""
    return render(request, 'core/terms.html', {'title': 'Terms of Service | Aura Luxe'})


def privacy_view(request):
    """Privacy policy."""
    return render(request, 'core/privacy.html', {'title': 'Privacy Policy | Aura Luxe'})
