from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def customer_required(view_func):
    """Requires authenticated user with CUSTOMER role."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access this page.")
            return redirect('accounts:login')
        if not request.user.is_customer and not request.user.is_superuser:
            messages.error(request, "Access restricted to customers.")
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def vendor_required(view_func):
    """Requires authenticated user with VENDOR role and an approved vendor profile."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to your vendor account.")
            return redirect('accounts:login')
        if not request.user.is_vendor and not request.user.is_superuser:
            messages.error(request, "Access restricted to vendors.")
            return redirect('core:home')
        
        # Check vendor profile approval
        if not request.user.is_superuser:
            if not hasattr(request.user, 'vendor'):
                messages.warning(request, "Please complete your vendor onboarding application.")
                return redirect('vendors:apply')
            if request.user.vendor.status != 'APPROVED':
                messages.warning(request, f"Your store is currently {request.user.vendor.get_status_display().lower()}. Waiting for administrator approval.")
                return redirect('vendors:status')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """Requires authenticated user with ADMIN role or superuser status."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Administrator login required.")
            return redirect('accounts:login')
        if not request.user.is_marketplace_admin:
            messages.error(request, "Access denied. Administrator privileges required.")
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
