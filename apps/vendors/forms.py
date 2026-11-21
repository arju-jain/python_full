from django import forms
from .models import Vendor, VendorApplication

class VendorApplicationForm(forms.ModelForm):
    class Meta:
        model = VendorApplication
        fields = ['store_name', 'contact_email', 'phone_number', 'tax_id', 'business_details']
        widgets = {
            'store_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand or Store Name'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'business@domain.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'GSTIN / VAT / Business ID'}),
            'business_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your product categories, origins, manufacturing, or artisan craftsmanship'}),
        }


class VendorStoreProfileForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'store_name', 'description', 'contact_email', 'phone_number',
            'logo', 'banner', 'bank_account_holder', 'bank_account_number',
            'bank_ifsc_code', 'bank_name'
        ]
        widgets = {
            'store_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'banner': forms.FileInput(attrs={'class': 'form-control'}),
            'bank_account_holder': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
