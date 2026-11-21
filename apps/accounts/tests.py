from django.test import TestCase
from django.urls import reverse
from .models import User, Address

class UserModelTests(TestCase):
    def test_create_customer_user(self):
        user = User.objects.create_user(
            email='customer@example.com',
            password='StrongPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.email, 'customer@example.com')
        self.assertTrue(user.is_active)
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertTrue(user.is_customer)
        self.assertFalse(user.is_vendor)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@auraluxe.com',
            password='AdminPassword123!'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_marketplace_admin)

    def test_address_default_uniqueness(self):
        user = User.objects.create_user(email='test@example.com', password='Password123!')
        addr1 = Address.objects.create(
            user=user,
            address_type=Address.AddressType.SHIPPING,
            full_name='Alice Smith',
            phone_number='1234567890',
            street_address_1='123 Main St',
            city='Mumbai',
            state='Maharashtra',
            postal_code='400001',
            is_default=True
        )
        addr2 = Address.objects.create(
            user=user,
            address_type=Address.AddressType.SHIPPING,
            full_name='Alice Smith',
            phone_number='1234567890',
            street_address_1='456 Park Ave',
            city='Mumbai',
            state='Maharashtra',
            postal_code='400002',
            is_default=True
        )
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)
