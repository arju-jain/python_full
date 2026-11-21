from django.contrib import admin
from .models import Inventory, StockMovement

class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ('movement_type', 'quantity_change', 'balance_after', 'reference_order', 'notes', 'created_at')
    can_delete = False


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'low_stock_threshold', 'is_in_stock', 'updated_at')
    list_filter = ('is_in_stock',)
    search_fields = ('product__title', 'product__sku')
    inlines = [StockMovementInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'movement_type', 'quantity_change', 'balance_after', 'reference_order', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('inventory__product__title', 'reference_order')
