from django import forms
from .models import SellerFulfillment
from apps.accounts.models import Address

class CheckoutForm(forms.Form):
    shipping_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        empty_label=None,
        required=True
    )
    customer_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Special delivery instructions or gate access notes (optional)'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shipping_address'].queryset = Address.objects.filter(
            user=user,
            address_type=Address.AddressType.SHIPPING
        )


class FulfillmentUpdateForm(forms.ModelForm):
    class Meta:
        model = SellerFulfillment
        fields = ['status', 'shipping_carrier', 'tracking_number', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'shipping_carrier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. DHL Express, Blue Dart, FedEx'}),
            'tracking_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Airway Bill (AWB) or Tracking code'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal handling remarks or customer dispatch note'}),
        }
