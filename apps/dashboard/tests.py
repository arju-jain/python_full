from django.test import TestCase
from django.urls import reverse
from decimal import Decimal
from apps.accounts.models import User
from apps.vendors.models import Vendor
from apps.catalog.models import Product

class DashboardAccessTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(email='customer_dash@example.com', password='Password123!')
        
        self.vendor_user = User.objects.create_user(email='vendor_dash@example.com', password='Password123!')
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            store_name='Dashboard Boutique',
            status=Vendor.Status.APPROVED
        )
        self.vendor_user.role = User.Role.VENDOR
        self.vendor_user.save()

        self.admin = User.objects.create_superuser(email='admin_dash@example.com', password='Password123!')

    def test_customer_dashboard_access(self):
        self.client.login(email='customer_dash@example.com', password='Password123!')
        response = self.client.get(reverse('dashboard:customer_overview'))
        self.assertEqual(response.status_code, 200)

    def test_vendor_dashboard_permission_isolation(self):
        # Customer tries to access vendor dashboard -> should be redirected
        self.client.login(email='customer_dash@example.com', password='Password123!')
        res_customer = self.client.get(reverse('dashboard:vendor_overview'))
        self.assertEqual(res_customer.status_code, 302)

        # Approved vendor accesses vendor dashboard -> 200
        self.client.login(email='vendor_dash@example.com', password='Password123!')
        res_vendor = self.client.get(reverse('dashboard:vendor_overview'))
        self.assertEqual(res_vendor.status_code, 200)

    def test_admin_dashboard_permission_isolation(self):
        # Vendor tries to access admin dashboard -> 302 redirected
        self.client.login(email='vendor_dash@example.com', password='Password123!')
        res_vendor = self.client.get(reverse('dashboard:admin_overview'))
        self.assertEqual(res_vendor.status_code, 302)

        # Superuser accesses admin dashboard -> 200
        self.client.login(email='admin_dash@example.com', password='Password123!')
        res_admin = self.client.get(reverse('dashboard:admin_overview'))
        self.assertEqual(res_admin.status_code, 200)
