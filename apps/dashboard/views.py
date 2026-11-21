from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from django.utils import timezone
from apps.accounts.decorators import vendor_required, admin_required, customer_required
from apps.accounts.models import User, Address
from apps.vendors.models import Vendor, VendorApplication
from apps.vendors.forms import VendorStoreProfileForm
from apps.vendors.services import VendorService
from apps.catalog.models import Product, ProductImage, Category
from apps.catalog.forms import ProductForm, ProductImageFormSet
from apps.inventory.models import Inventory
from apps.inventory.services import InventoryService
from apps.orders.models import Order, OrderItem, SellerFulfillment
from apps.orders.forms import FulfillmentUpdateForm
from apps.orders.services import OrderService
from apps.payments.models import Payment, Commission, SellerPayout
from apps.wishlist.models import Wishlist
from apps.reviews.models import Review

# ==============================================================================
# CUSTOMER DASHBOARD
# ==============================================================================

@login_required
def customer_overview_view(request):
    """Customer overview cockpit."""
    recent_orders = Order.objects.filter(customer=request.user).order_by('-created_at')[:5]
    total_orders = Order.objects.filter(customer=request.user).count()
    total_spent = Order.objects.filter(
        customer=request.user,
        payment_status=Order.PaymentStatus.PAID
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    wishlist = Wishlist.objects.filter(user=request.user).first()
    wishlist_count = wishlist.total_items if wishlist else 0
    address_count = Address.objects.filter(user=request.user).count()
    reviews_count = Review.objects.filter(customer=request.user).count()

    return render(request, 'dashboard/customer/overview.html', {
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'wishlist_count': wishlist_count,
        'address_count': address_count,
        'reviews_count': reviews_count,
        'title': 'Customer Account Overview'
    })


# ==============================================================================
# VENDOR DASHBOARD
# ==============================================================================

@vendor_required
def vendor_overview_view(request):
    """Vendor cockpit with revenue, pending orders, and low-stock alerts."""
    vendor = request.user.vendor

    # Revenue Metrics
    commissions = Commission.objects.filter(vendor=vendor, order__payment_status='PAID')
    gross_sales = commissions.aggregate(total=Sum('gross_amount'))['total'] or Decimal('0.00')
    net_earnings = commissions.aggregate(total=Sum('net_seller_amount'))['total'] or Decimal('0.00')
    commission_deducted = commissions.aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00')

    # Fulfillment Metrics
    fulfillments = SellerFulfillment.objects.filter(vendor=vendor)
    total_orders_count = fulfillments.count()
    pending_fulfillment_count = fulfillments.filter(status__in=[SellerFulfillment.Status.PENDING, SellerFulfillment.Status.PROCESSING]).count()

    # Product Metrics
    products = Product.objects.filter(vendor=vendor)
    total_products_count = products.count()
    low_stock_products = products.filter(inventory__quantity__lte=5)

    recent_fulfillments = fulfillments.select_related('order').order_by('-created_at')[:6]

    return render(request, 'dashboard/vendor/overview.html', {
        'vendor': vendor,
        'gross_sales': gross_sales,
        'net_earnings': net_earnings,
        'commission_deducted': commission_deducted,
        'total_orders_count': total_orders_count,
        'pending_fulfillment_count': pending_fulfillment_count,
        'total_products_count': total_products_count,
        'low_stock_count': low_stock_products.count(),
        'recent_fulfillments': recent_fulfillments,
        'title': f'{vendor.store_name} | Seller Cockpit'
    })


@vendor_required
def vendor_products_view(request):
    """List of all products owned by this vendor."""
    vendor = request.user.vendor
    products = Product.objects.filter(vendor=vendor).select_related('category', 'inventory').prefetch_related('images').order_by('-created_at')
    return render(request, 'dashboard/vendor/product_list.html', {
        'vendor': vendor,
        'products': products,
        'title': 'My Products | Seller Catalog'
    })


@vendor_required
def vendor_product_create_view(request):
    """Create a new product with stock and image gallery."""
    vendor = request.user.vendor
    if request.method == 'POST':
        form = ProductForm(request.POST)
        formset = ProductImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor
            product.save()

            # Initialize Inventory
            stock_qty = form.cleaned_data.get('stock_quantity', 10)
            Inventory.objects.create(product=product, quantity=stock_qty)

            # Save Images
            formset.instance = product
            formset.save()

            messages.success(request, f"Product '{product.title}' has been successfully created.")
            return redirect('dashboard:vendor_products')
    else:
        form = ProductForm()
        formset = ProductImageFormSet()

    return render(request, 'dashboard/vendor/product_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Add New Product | Seller Cockpit'
    })


@vendor_required
def vendor_product_edit_view(request, pk):
    """Edit an existing product owned by the vendor."""
    vendor = request.user.vendor
    product = get_object_or_404(Product, pk=pk, vendor=vendor)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        if form.is_valid() and formset.is_valid():
            product = form.save()

            # Update Inventory quantity
            new_stock = form.cleaned_data.get('stock_quantity')
            if hasattr(product, 'inventory'):
                inv = product.inventory
                if inv.quantity != new_stock:
                    diff = new_stock - inv.quantity
                    InventoryService.adjust_stock(
                        product=product,
                        quantity_change=diff,
                        movement_type='ADJUSTMENT',
                        notes='Vendor dashboard manual update'
                    )
            else:
                Inventory.objects.create(product=product, quantity=new_stock)

            formset.save()
            messages.success(request, f"Product '{product.title}' updated successfully.")
            return redirect('dashboard:vendor_products')
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)

    return render(request, 'dashboard/vendor/product_form.html', {
        'form': form,
        'formset': formset,
        'product': product,
        'title': f'Edit {product.title}'
    })


@vendor_required
@require_POST
def vendor_product_delete_view(request, pk):
    """Delete vendor's product."""
    vendor = request.user.vendor
    product = get_object_or_404(Product, pk=pk, vendor=vendor)
    title = product.title
    product.delete()
    messages.success(request, f"Product '{title}' removed from catalog.")
    return redirect('dashboard:vendor_products')


@vendor_required
def vendor_orders_view(request):
    """Vendor-isolated orders view. Vendor sees ONLY their fulfillments and items."""
    vendor = request.user.vendor
    status_filter = request.GET.get('status', '')

    fulfillments = SellerFulfillment.objects.filter(vendor=vendor).select_related('order__customer').order_by('-created_at')
    if status_filter:
        fulfillments = fulfillments.filter(status=status_filter)

    return render(request, 'dashboard/vendor/order_list.html', {
        'vendor': vendor,
        'fulfillments': fulfillments,
        'current_status': status_filter,
        'title': 'Seller Orders & Shipments'
    })


@vendor_required
def vendor_order_detail_view(request, pk):
    """Detail view for a seller fulfillment record with dispatch update form."""
    vendor = request.user.vendor
    fulfillment = get_object_or_404(
        SellerFulfillment.objects.select_related('order__customer'),
        pk=pk,
        vendor=vendor
    )

    if request.method == 'POST':
        form = FulfillmentUpdateForm(request.POST, instance=fulfillment)
        if form.is_valid():
            OrderService.update_fulfillment_status(
                fulfillment=fulfillment,
                new_status=form.cleaned_data['status'],
                carrier=form.cleaned_data['shipping_carrier'],
                tracking=form.cleaned_data['tracking_number'],
                notes=form.cleaned_data['notes']
            )
            messages.success(request, "Shipment fulfillment details updated.")
            return redirect('dashboard:vendor_order_detail', pk=fulfillment.pk)
    else:
        form = FulfillmentUpdateForm(instance=fulfillment)

    vendor_items = fulfillment.vendor_items

    return render(request, 'dashboard/vendor/order_detail.html', {
        'vendor': vendor,
        'fulfillment': fulfillment,
        'vendor_items': vendor_items,
        'form': form,
        'title': f'Fulfillment #{fulfillment.pk} - Order #{fulfillment.order.order_number}'
    })


@vendor_required
def vendor_store_settings_view(request):
    """Vendor store profile, branding and banking configuration."""
    vendor = request.user.vendor
    if request.method == 'POST':
        form = VendorStoreProfileForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Store profile and payment details saved.")
            return redirect('dashboard:vendor_settings')
    else:
        form = VendorStoreProfileForm(instance=vendor)

    return render(request, 'dashboard/vendor/store_settings.html', {
        'vendor': vendor,
        'form': form,
        'title': 'Store Settings & Brand Profile'
    })


@vendor_required
def vendor_analytics_view(request):
    """Vendor sales analytics and performance breakdown."""
    vendor = request.user.vendor
    commissions = Commission.objects.filter(vendor=vendor, order__payment_status='PAID').select_related('order_item', 'order')

    total_gross = commissions.aggregate(total=Sum('gross_amount'))['total'] or Decimal('0.00')
    total_commission = commissions.aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00')
    total_net = commissions.aggregate(total=Sum('net_seller_amount'))['total'] or Decimal('0.00')

    # Top selling products
    top_products = OrderItem.objects.filter(vendor=vendor, order__payment_status='PAID').values('product_title').annotate(
        units_sold=Sum('quantity'),
        total_rev=Sum('subtotal')
    ).order_by('-units_sold')[:5]

    return render(request, 'dashboard/vendor/analytics.html', {
        'vendor': vendor,
        'commissions': commissions[:20],
        'total_gross': total_gross,
        'total_commission': total_commission,
        'total_net': total_net,
        'top_products': top_products,
        'title': 'Sales & Financial Analytics'
    })


# ==============================================================================
# ADMINISTRATOR DASHBOARD
# ==============================================================================

@admin_required
def admin_overview_view(request):
    """Marketplace administrator control center."""
    total_customers = User.objects.filter(role=User.Role.CUSTOMER).count()
    total_vendors = Vendor.objects.count()
    pending_applications_count = VendorApplication.objects.filter(status=VendorApplication.Status.PENDING).count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()

    paid_orders = Order.objects.filter(payment_status=Order.PaymentStatus.PAID)
    platform_gmv = paid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_commissions = Commission.objects.aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00')

    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:8]
    pending_applications = VendorApplication.objects.filter(status=VendorApplication.Status.PENDING).select_related('user')[:5]

    return render(request, 'dashboard/admin/overview.html', {
        'total_customers': total_customers,
        'total_vendors': total_vendors,
        'pending_applications_count': pending_applications_count,
        'total_products': total_products,
        'total_orders': total_orders,
        'platform_gmv': platform_gmv,
        'total_commissions': total_commissions,
        'recent_orders': recent_orders,
        'pending_applications': pending_applications,
        'title': 'Marketplace Administrative Cockpit'
    })


@admin_required
def admin_vendors_view(request):
    """Manage all vendors and pending applications."""
    applications = VendorApplication.objects.select_related('user').order_by('-created_at')
    vendors = Vendor.objects.select_related('user').order_by('store_name')

    return render(request, 'dashboard/admin/vendors_manage.html', {
        'applications': applications,
        'vendors': vendors,
        'title': 'Vendor Store Operations'
    })


@admin_required
@require_POST
def admin_vendor_approve_view(request, app_id):
    """Approve a vendor application."""
    application = get_object_or_404(VendorApplication, pk=app_id)
    VendorService.approve_application(application, request.user)
    messages.success(request, f"Application for '{application.store_name}' approved. Store is now active.")
    return redirect('dashboard:admin_vendors')


@admin_required
@require_POST
def admin_vendor_reject_view(request, app_id):
    """Reject a vendor application."""
    application = get_object_or_404(VendorApplication, pk=app_id)
    notes = request.POST.get('notes', 'Application rejected by administration.')
    VendorService.reject_application(application, request.user, notes=notes)
    messages.info(request, f"Application for '{application.store_name}' rejected.")
    return redirect('dashboard:admin_vendors')


@admin_required
@require_POST
def admin_vendor_toggle_status_view(request, vendor_id):
    """Toggle vendor status between APPROVED and SUSPENDED."""
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    if vendor.status == Vendor.Status.APPROVED:
        vendor.status = Vendor.Status.SUSPENDED
        messages.warning(request, f"Vendor '{vendor.store_name}' has been suspended.")
    else:
        vendor.status = Vendor.Status.APPROVED
        messages.success(request, f"Vendor '{vendor.store_name}' has been reactivated.")
    vendor.save()
    return redirect('dashboard:admin_vendors')


@admin_required
def admin_products_view(request):
    """Moderate products across the marketplace."""
    products = Product.objects.select_related('vendor', 'category', 'inventory').order_by('-created_at')
    return render(request, 'dashboard/admin/products_manage.html', {
        'products': products,
        'title': 'Catalog Moderation'
    })


@admin_required
@require_POST
def admin_product_toggle_view(request, pk):
    """Toggle product active status."""
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    status_str = "activated" if product.is_active else "deactivated"
    messages.info(request, f"Product '{product.title}' has been {status_str}.")
    return redirect('dashboard:admin_products')


@admin_required
def admin_orders_view(request):
    """View all marketplace orders and fulfillment states."""
    orders = Order.objects.select_related('customer').prefetch_related('fulfillments__vendor').order_by('-created_at')
    return render(request, 'dashboard/admin/orders_manage.html', {
        'orders': orders,
        'title': 'Marketplace Orders Monitor'
    })


@admin_required
def admin_transactions_view(request):
    """Platform transactions, commissions, and seller payout ledger."""
    payments = Payment.objects.select_related('order__customer').order_by('-created_at')
    commissions = Commission.objects.select_related('vendor', 'order').order_by('-created_at')
    payouts = SellerPayout.objects.select_related('vendor').order_by('-created_at')

    return render(request, 'dashboard/admin/transactions_manage.html', {
        'payments': payments,
        'commissions': commissions,
        'payouts': payouts,
        'title': 'Financial Transactions & Ledgers'
    })
