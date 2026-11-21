from django.test import TestCase
from apps.accounts.models import User
from .models import Vendor, VendorApplication
from .services import VendorService

class VendorWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='vendor_applicant@example.com', password='Password123!')
        self.admin = User.objects.create_superuser(email='superadmin@auraluxe.com', password='AdminPassword123!')

    def test_vendor_application_and_approval(self):
        # 1. User submits application
        application = VendorApplication.objects.create(
            user=self.user,
            store_name='Maison Artisan',
            business_details='Handcrafted luxury leather goods',
            tax_id='GSTIN99887766',
            contact_email='contact@maisonartisan.com',
            phone_number='9876543210'
        )
        self.assertEqual(application.status, VendorApplication.Status.PENDING)
        self.assertEqual(self.user.role, User.Role.CUSTOMER)

        # 2. Administrator approves application via VendorService
        vendor = VendorService.approve_application(application, self.admin, commission_rate=12.50)
        
        # Verify application status
        application.refresh_from_db()
        self.assertEqual(application.status, VendorApplication.Status.APPROVED)
        self.assertEqual(application.reviewed_by, self.admin)

        # Verify User role elevated to VENDOR
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.VENDOR)
        self.assertTrue(self.user.is_vendor)

        # Verify Vendor record
        self.assertEqual(vendor.store_name, 'Maison Artisan')
        self.assertEqual(vendor.status, Vendor.Status.APPROVED)
        self.assertEqual(float(vendor.commission_rate), 12.50)
        self.assertTrue(vendor.slug.startswith('maison-artisan'))
