from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import CustomerRegistrationForm, LoginForm, UserProfileForm, AddressForm
from .models import Address, User

def register_view(request):
    """Customer registration view."""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Aura Luxe, {user.first_name or user.email}! Your customer account is ready.")
            return redirect('core:home')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form, 'title': 'Create Customer Account'})


def login_view(request):
    """Customer / Vendor / Admin unified login."""
    if request.user.is_authenticated:
        return redirect('core:home')

    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_short_name()}!")

            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            
            # Role-based landing redirects
            if user.is_marketplace_admin:
                return redirect('dashboard:admin_overview')
            elif user.is_vendor:
                return redirect('dashboard:vendor_overview')
            else:
                return redirect('dashboard:customer_overview')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url, 'title': 'Account Sign In'})


def logout_view(request):
    """Secure logout view."""
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect('core:home')


@login_required
def profile_view(request):
    """Customer profile details and editing."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile information has been updated.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/profile.html', {
        'form': form,
        'addresses': addresses,
        'title': 'My Profile'
    })


@login_required
def address_list_view(request):
    """Customer address book."""
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {'addresses': addresses, 'title': 'Address Book'})


@login_required
def address_create_view(request):
    """Create a new shipping or billing address."""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # If user has no existing addresses, make this default
            if not Address.objects.filter(user=request.user, address_type=address.address_type).exists():
                address.is_default = True
            address.save()
            messages.success(request, "New address successfully saved.")
            next_url = request.GET.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('accounts:address_list')
    else:
        form = AddressForm()

    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add New Address'})


@login_required
def address_edit_view(request, pk):
    """Edit an existing address."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully.")
            return redirect('accounts:address_list')
    else:
        form = AddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {'form': form, 'address': address, 'title': 'Edit Address'})


@login_required
@require_POST
def address_delete_view(request, pk):
    """Delete an address."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, "Address removed.")
    return redirect('accounts:address_list')


@login_required
@require_POST
def address_set_default_view(request, pk):
    """Mark an address as the default."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, f"Default {address.get_address_type_display().lower()} address updated.")
    return redirect('accounts:address_list')
