from django.test import TestCase
from decimal import Decimal
from apps.accounts.models import User
from apps.vendors.models import Vendor
from apps.catalog.models import Product
from apps.inventory.models import Inventory
from .models import Cart, CartItem
from .services import CartService

class CartServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='buyer@example.com', password='Password123!')
        self.vendor = Vendor.objects.create(
            user=User.objects.create_user(email='seller1@example.com', password='Password123!'),
            store_name='Atelier Royale',
            contact_email='contact@royale.com',
            status=Vendor.Status.APPROVED
        )
        self.product = Product.objects.create(
            vendor=self.vendor,
            title='Velvet Loafers',
            price=Decimal('12000.00'),
            sku='LOAF-VEL-01',
            description='Handmade Italian velvet loafers.'
        )
        Inventory.objects.create(product=self.product, quantity=5)

    def test_cart_addition_and_totals(self):
        cart = Cart.objects.create(user=self.user)
        CartService.add_item(cart, self.product, quantity=2)

        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.subtotal, Decimal('24000.00'))
        self.assertEqual(cart.grand_total, Decimal('24000.00'))  # Free shipping over 5000

        item = cart.items.first()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.subtotal, Decimal('24000.00'))
