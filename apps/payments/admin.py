from django.contrib import admin
from .models import Payment, Commission, SellerPayout, Refund

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'amount', 'currency', 'status', 'razorpay_payment_id', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('transaction_id', 'order__order_number', 'razorpay_payment_id', 'razorpay_order_id')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('order_item', 'vendor', 'gross_amount', 'commission_rate', 'commission_amount', 'net_seller_amount', 'created_at')
    list_filter = ('vendor', 'created_at')
    search_fields = ('order_item__product_title', 'vendor__store_name', 'order__order_number')


@admin.register(SellerPayout)
class SellerPayoutAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'amount', 'status', 'reference_id', 'payout_date', 'created_at')
    list_filter = ('status', 'vendor', 'created_at')
    search_fields = ('vendor__store_name', 'reference_id')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('payment', 'amount', 'status', 'razorpay_refund_id', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment__transaction_id', 'razorpay_refund_id')
