from django.contrib import admin
from .models import Order, OrderItem, SellerFulfillment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'vendor', 'product_title', 'sku', 'unit_price', 'quantity', 'subtotal', 'created_at')
    can_delete = False


class SellerFulfillmentInline(admin.TabularInline):
    model = SellerFulfillment
    extra = 0
    readonly_fields = ('vendor', 'status', 'shipping_carrier', 'tracking_number', 'dispatched_at', 'delivered_at')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'customer__email', 'shipping_full_name', 'shipping_phone')
    inlines = [OrderItemInline, SellerFulfillmentInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_title', 'vendor', 'quantity', 'unit_price', 'subtotal', 'created_at')
    list_filter = ('vendor', 'created_at')
    search_fields = ('order__order_number', 'product_title', 'sku')


@admin.register(SellerFulfillment)
class SellerFulfillmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'vendor', 'status', 'shipping_carrier', 'tracking_number', 'dispatched_at', 'delivered_at')
    list_filter = ('status', 'vendor', 'created_at')
    search_fields = ('order__order_number', 'vendor__store_name', 'tracking_number')
