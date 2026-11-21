from django.test import TestCase
from decimal import Decimal
from apps.accounts.models import User
from apps.vendors.models import Vendor
from apps.catalog.models import Product
from .models import Wishlist, WishlistItem

class WishlistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='wishuser@example.com', password='Password123!')
        self.vendor = Vendor.objects.create(
            user=User.objects.create_user(email='seller_w@example.com', password='Password123!'),
            store_name='Maison Joaillerie',
            contact_email='contact@joaillerie.com',
            status=Vendor.Status.APPROVED
        )
        self.product = Product.objects.create(
            vendor=self.vendor,
            title='Diamond Solitaire Pendant',
            price=Decimal('85000.00'),
            sku='JW-DIA-001',
            description='18k White Gold diamond solitaire pendant.'
        )

    def test_wishlist_toggle(self):
        wishlist = Wishlist.objects.create(user=self.user)
        # Add to wishlist
        item = WishlistItem.objects.create(wishlist=wishlist, product=self.product)
        self.assertEqual(wishlist.total_items, 1)

        # Remove from wishlist
        item.delete()
        self.assertEqual(wishlist.total_items, 0)
