from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

class Cart(models.Model):
    """Shopping cart supporting authenticated customers and guest sessions."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.email}"
        return f"Guest Cart ({self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def estimated_shipping(self):
        # Complimentary luxury shipping on orders over ₹5,000, else ₹250
        if self.subtotal >= Decimal('5000.00') or self.subtotal == 0:
            return Decimal('0.00')
        return Decimal('250.00')

    @property
    def grand_total(self):
        return self.subtotal + self.estimated_shipping


class CartItem(models.Model):
    """Item record in a cart referencing product and quantity."""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product'], name='unique_cart_product')
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.title}"

    @property
    def unit_price(self):
        return self.product.price

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
