import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Order(models.Model):
    """Parent multi-vendor order representing a single customer transaction."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Payment')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    class PaymentStatus(models.TextChoices):
        UNPAID = 'UNPAID', _('Unpaid')
        PAID = 'PAID', _('Paid')
        FAILED = 'FAILED', _('Payment Failed')
        REFUNDED = 'REFUNDED', _('Refunded')

    order_number = models.CharField(max_length=64, unique=True, db_index=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True
    )
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Shipping Address Snapshot
    shipping_full_name = models.CharField(max_length=150)
    shipping_phone = models.CharField(max_length=20)
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='India')

    customer_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} - {self.customer.email} (₹{self.total_amount})"

    @classmethod
    def generate_order_number(cls):
        date_str = timezone.now().strftime('%Y%m%d')
        unique_token = uuid.uuid4().hex[:6].upper()
        return f"AL-{date_str}-{unique_token}"


class OrderItem(models.Model):
    """Specific product line item preserving snapshot price and vendor assignment."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    vendor = models.ForeignKey(
        'vendors.Vendor',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    product_title = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')

    def __str__(self):
        return f"{self.quantity}x {self.product_title} from {self.vendor.store_name}"


class SellerFulfillment(models.Model):
    """Vendor-isolated fulfillment record allowing each seller to manage their own shipments."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('In Production / Packaging')
        SHIPPED = 'SHIPPED', _('Dispatched / In Transit')
        DELIVERED = 'DELIVERED', _('Delivered')
        CANCELLED = 'CANCELLED', _('Cancelled')

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='fulfillments'
    )
    vendor = models.ForeignKey(
        'vendors.Vendor',
        on_delete=models.CASCADE,
        related_name='fulfillments'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    tracking_number = models.CharField(max_length=120, blank=True)
    shipping_carrier = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Seller Fulfillment')
        verbose_name_plural = _('Seller Fulfillments')
        constraints = [
            models.UniqueConstraint(fields=['order', 'vendor'], name='unique_order_vendor_fulfillment')
        ]

    def __str__(self):
        return f"Fulfillment for Order #{self.order.order_number} by {self.vendor.store_name} ({self.get_status_display()})"

    @property
    def vendor_items(self):
        """Returns OrderItems strictly belonging to this vendor."""
        return self.order.items.filter(vendor=self.vendor)

    @property
    def vendor_subtotal(self):
        """Total gross revenue for this vendor on this order."""
        return sum(item.subtotal for item in self.vendor_items)
