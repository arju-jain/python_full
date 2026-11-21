from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.accounts.models import User
from apps.vendors.models import Vendor
from apps.catalog.models import Product
from .models import Inventory, StockMovement
from .services import InventoryService

class InventoryServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='vendor_inv@example.com', password='Password123!')
        self.vendor = Vendor.objects.create(
            user=self.user,
            store_name='Cashmere Atelier',
            contact_email='info@cashmere.com',
            status=Vendor.Status.APPROVED
        )
        self.product = Product.objects.create(
            vendor=self.vendor,
            title='Pure Cashmere Wrap',
            price=Decimal('22000.00'),
            sku='CSH-WRAP-001',
            description='100% Himalayan Mongolian Cashmere wrap.'
        )

    def test_stock_adjustment_and_negative_prevention(self):
        # Restock 10 units
        InventoryService.adjust_stock(
            product=self.product,
            quantity_change=10,
            movement_type=StockMovement.MovementType.PURCHASE_RESTOCK,
            notes='Initial intake'
        )
        inv = Inventory.objects.get(product=self.product)
        self.assertEqual(inv.quantity, 10)
        self.assertTrue(inv.is_in_stock)

        # Deduct 4 units for order
        InventoryService.deduct_stock_for_order(self.product, quantity=4, order_number='ORD-1001')
        inv.refresh_from_db()
        self.assertEqual(inv.quantity, 6)

        # Attempt to over-deduct 10 units (should fail with ValidationError)
        with self.assertRaises(ValidationError):
            InventoryService.deduct_stock_for_order(self.product, quantity=10, order_number='ORD-1002')

        # Verify stock remained at 6
        inv.refresh_from_db()
        self.assertEqual(inv.quantity, 6)
