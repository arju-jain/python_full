from django.test import TestCase
from decimal import Decimal
from apps.accounts.models import User
from apps.vendors.models import Vendor
from apps.inventory.models import Inventory
from .models import Category, Product

class CatalogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='vendor_cat@example.com', password='Password123!')
        self.vendor = Vendor.objects.create(
            user=self.user,
            store_name='Haute Couture Boutique',
            contact_email='contact@haute.com',
            status=Vendor.Status.APPROVED
        )
        self.category = Category.objects.create(name='Leather Bags', slug='leather-bags')

    def test_product_creation_and_inventory_link(self):
        product = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            title='Artisan Tote Bag',
            price=Decimal('14999.00'),
            compare_at_price=Decimal('18999.00'),
            sku='BAG-ARTISAN-01',
            description='Hand-stitched full grain Italian leather tote bag.'
        )
        Inventory.objects.create(product=product, quantity=15)

        self.assertEqual(product.stock_quantity, 15)
        self.assertTrue(product.is_in_stock)
        self.assertEqual(product.discount_percent, 21)
        self.assertTrue(product.slug.startswith('artisan-tote-bag'))
