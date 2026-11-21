from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Inventory, StockMovement

class InventoryService:
    @staticmethod
    @transaction.atomic
    def adjust_stock(product, quantity_change: int, movement_type: str, reference: str = "", notes: str = ""):
        """
        Adjust stock atomically with row-locking (select_for_update).
        Prevents negative stock and logs every movement.
        """
        # Lock inventory row
        inventory, created = Inventory.objects.select_for_update().get_or_create(
            product=product,
            defaults={'quantity': 0}
        )

        new_quantity = inventory.quantity + quantity_change
        if new_quantity < 0:
            raise ValidationError(
                f"Insufficient stock for '{product.title}'. Requested deduction {abs(quantity_change)}, but only {inventory.quantity} available."
            )

        inventory.quantity = new_quantity
        inventory.is_in_stock = new_quantity > 0
        inventory.save()

        # Record movement
        StockMovement.objects.create(
            inventory=inventory,
            movement_type=movement_type,
            quantity_change=quantity_change,
            balance_after=new_quantity,
            reference_order=reference,
            notes=notes
        )

        return inventory

    @classmethod
    def deduct_stock_for_order(cls, product, quantity: int, order_number: str):
        return cls.adjust_stock(
            product=product,
            quantity_change=-quantity,
            movement_type=StockMovement.MovementType.SALE_DEDUCTION,
            reference=order_number,
            notes=f"Order #{order_number} checkout deduction"
        )

    @classmethod
    def restock_for_refund(cls, product, quantity: int, order_number: str):
        return cls.adjust_stock(
            product=product,
            quantity_change=quantity,
            movement_type=StockMovement.MovementType.REFUND_RESTOCK,
            reference=order_number,
            notes=f"Order #{order_number} refund restock"
        )
