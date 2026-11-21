from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.accounts.decorators import vendor_required
from .models import Inventory, StockMovement
from .services import InventoryService

@vendor_required
def vendor_inventory_list_view(request):
    """Vendor view of their inventory and stock levels."""
    vendor = request.user.vendor
    inventories = Inventory.objects.filter(product__vendor=vendor).select_related('product')
    return render(request, 'inventory/inventory_list.html', {
        'inventories': inventories,
        'title': 'Inventory Management'
    })
