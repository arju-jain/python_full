from django.contrib import admin
from .models import Vendor, VendorApplication
from .services import VendorService

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'status', 'commission_rate', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('store_name', 'user__email', 'contact_email', 'tax_id')
    prepopulated_fields = {'slug': ('store_name',)}
    actions = ['approve_selected_vendors', 'suspend_selected_vendors']

    @admin.action(description="Approve selected vendors")
    def approve_selected_vendors(self, request, queryset):
        for vendor in queryset:
            vendor.status = Vendor.Status.APPROVED
            vendor.save()
        self.message_user(request, f"{queryset.count()} vendors approved.")

    @admin.action(description="Suspend selected vendors")
    def suspend_selected_vendors(self, request, queryset):
        for vendor in queryset:
            VendorService.suspend_vendor(vendor)
        self.message_user(request, f"{queryset.count()} vendors suspended.")


@admin.register(VendorApplication)
class VendorApplicationAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'contact_email', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('store_name', 'user__email', 'contact_email')
    actions = ['approve_applications', 'reject_applications']

    @admin.action(description="Approve selected vendor applications")
    def approve_applications(self, request, queryset):
        for app in queryset.filter(status=VendorApplication.Status.PENDING):
            VendorService.approve_application(app, request.user)
        self.message_user(request, "Selected vendor applications approved and stores initialized.")

    @admin.action(description="Reject selected vendor applications")
    def reject_applications(self, request, queryset):
        for app in queryset.filter(status=VendorApplication.Status.PENDING):
            VendorService.reject_application(app, request.user, notes="Rejected via administration action.")
        self.message_user(request, "Selected applications rejected.")
