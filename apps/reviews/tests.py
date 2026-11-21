from django.test import TestCase
from decimal import Decimal
from apps.accounts.models import User
from apps.vendors.models import Vendor
from apps.catalog.models import Product
from .models import Review

class ReviewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(email='buyer_rev@example.com', password='Password123!')
        self.vendor = Vendor.objects.create(
            user=User.objects.create_user(email='seller_rev@example.com', password='Password123!'),
            store_name='Silk House',
            status=Vendor.Status.APPROVED
        )
        self.product = Product.objects.create(
            vendor=self.vendor,
            title='Mulberry Silk Scarf',
            price=Decimal('5000.00'),
            sku='SILK-001',
            description='Fine mulberry silk.'
        )

    def test_review_creation_and_rating_calculation(self):
        review = Review.objects.create(
            product=self.product,
            customer=self.customer,
            rating=5,
            title='Exquisite Quality',
            comment='The texture and sheen are beyond expectations.'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(self.product.average_rating, 5.0)
        self.assertEqual(self.product.review_count, 1)
