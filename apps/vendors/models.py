from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

class Vendor(models.Model):
    """Store profile for an approved marketplace merchant."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        SUSPENDED = 'SUSPENDED', _('Suspended')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor'
    )
    store_name = models.CharField(_('store name'), max_length=200, unique=True)
    slug = models.SlugField(_('store slug'), max_length=220, unique=True, blank=True)
    description = models.TextField(_('store description'), blank=True)
    logo = models.ImageField(upload_to='vendors/logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='vendors/banners/', blank=True, null=True)
    contact_email = models.EmailField(_('business contact email'))
    phone_number = models.CharField(_('business phone'), max_length=20, blank=True)
    business_registration_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(_('GSTIN / Tax ID'), max_length=100, blank=True)
    commission_rate = models.DecimalField(
        _('marketplace commission %'),
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text=_('Percentage deducted by marketplace on sales')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    
    # Banking details for payouts
    bank_account_holder = models.CharField(max_length=150, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc_code = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Vendor Store')
        verbose_name_plural = _('Vendor Stores')
        ordering = ['store_name']

    def __str__(self):
        return f"{self.store_name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.store_name)
            slug = base_slug
            counter = 1
            while Vendor.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED


class VendorApplication(models.Model):
    """Vendor onboarding request submitted by users."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_application'
    )
    store_name = models.CharField(max_length=200)
    business_details = models.TextField(help_text=_('Describe your products, business experience, and supply capacity.'))
    tax_id = models.CharField(max_length=100, blank=True, help_text=_('GSTIN or Business Tax ID'))
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_vendor_applications'
    )
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Vendor Application')
        verbose_name_plural = _('Vendor Applications')
        ordering = ['-created_at']

    def __str__(self):
        return f"Application: {self.store_name} by {self.user.email} ({self.get_status_display()})"
