from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from .models import Vendor, VendorApplication

class VendorService:
    @staticmethod
    @transaction.atomic
    def approve_application(application: VendorApplication, reviewer: User, commission_rate: float = 10.00):
        """Approves a vendor application, elevates user role to VENDOR, and creates or updates Vendor record."""
        application.status = VendorApplication.Status.APPROVED
        application.reviewed_by = reviewer
        application.reviewed_at = timezone.now()
        application.save()

        # Update User role
        user = application.user
        user.role = User.Role.VENDOR
        user.save(update_fields=['role'])

        # Create or update Vendor record
        vendor, created = Vendor.objects.get_or_create(
            user=user,
            defaults={
                'store_name': application.store_name,
                'contact_email': application.contact_email or user.email,
                'phone_number': application.phone_number,
                'tax_id': application.tax_id,
                'commission_rate': commission_rate,
                'status': Vendor.Status.APPROVED,
            }
        )
        if not created:
            vendor.status = Vendor.Status.APPROVED
            vendor.store_name = application.store_name
            vendor.commission_rate = commission_rate
            vendor.save()

        return vendor

    @staticmethod
    @transaction.atomic
    def reject_application(application: VendorApplication, reviewer: User, notes: str = ""):
        """Rejects a vendor application."""
        application.status = VendorApplication.Status.REJECTED
        application.reviewed_by = reviewer
        application.review_notes = notes
        application.reviewed_at = timezone.now()
        application.save()

        if hasattr(application.user, 'vendor'):
            application.user.vendor.status = Vendor.Status.REJECTED
            application.user.vendor.save()

        return application

    @staticmethod
    def suspend_vendor(vendor: Vendor, notes: str = ""):
        """Suspends an active vendor store."""
        vendor.status = Vendor.Status.SUSPENDED
        vendor.save()
        return vendor
