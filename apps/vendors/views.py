from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import vendor_required
from .models import Vendor, VendorApplication
from .forms import VendorApplicationForm, VendorStoreProfileForm

@login_required
def vendor_apply_view(request):
    """Vendor onboarding application page."""
    # Check if user already has an application
    existing_application = VendorApplication.objects.filter(user=request.user).first()
    if existing_application:
        return redirect('vendors:status')

    if request.method == 'POST':
        form = VendorApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            messages.success(request, "Your vendor application has been submitted! Our curatorial team will review it shortly.")
            return redirect('vendors:status')
    else:
        initial = {
            'contact_email': request.user.email,
            'phone_number': request.user.phone_number,
        }
        form = VendorApplicationForm(initial=initial)

    return render(request, 'vendors/apply.html', {'form': form, 'title': 'Become an Aura Luxe Vendor'})


@login_required
def vendor_status_view(request):
    """View application or store status."""
    application = VendorApplication.objects.filter(user=request.user).first()
    vendor = getattr(request.user, 'vendor', None)
    return render(request, 'vendors/status.html', {
        'application': application,
        'vendor': vendor,
        'title': 'Vendor Account Status'
    })


def vendor_store_public_view(request, slug):
    """Public vendor storefront."""
    vendor = get_object_or_404(Vendor, slug=slug, status=Vendor.Status.APPROVED)
    products = vendor.products.filter(is_active=True).select_related('category').prefetch_related('images')
    return render(request, 'vendors/store_detail.html', {
        'vendor': vendor,
        'products': products,
        'title': f"{vendor.store_name} | Aura Luxe Boutique"
    })
