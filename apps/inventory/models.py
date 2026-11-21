from django.db import models
from django.utils.translation import gettext_lazy as _

class Inventory(models.Model):
    """Inventory tracking per product with low stock triggers."""
    product = models.OneToOneField(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    is_in_stock = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Inventory')
        verbose_name_plural = _('Inventories')

    def __str__(self):
        return f"Stock: {self.product.title} - {self.quantity} units"

    def save(self, *args, **kwargs):
        self.is_in_stock = self.quantity > 0
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold


class StockMovement(models.Model):
    """Audit ledger for all inventory adjustments."""
    class MovementType(models.TextChoices):
        PURCHASE_RESTOCK = 'RESTOCK', _('Restock')
        SALE_DEDUCTION = 'SALE', _('Sale Order Deduction')
        REFUND_RESTOCK = 'REFUND', _('Refund Restock')
        ADJUSTMENT = 'ADJUSTMENT', _('Manual Adjustment')

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='movements'
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity_change = models.IntegerField(help_text=_('Positive for addition, negative for deduction'))
    balance_after = models.PositiveIntegerField()
    reference_order = models.CharField(max_length=100, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Stock Movement')
        verbose_name_plural = _('Stock Movements')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.inventory.product.title}: {self.quantity_change:+d} ({self.get_movement_type_display()})"
