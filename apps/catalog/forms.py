from django import forms
from django.forms import inlineformset_factory
from .models import Product, ProductImage, Category

class ProductForm(forms.ModelForm):
    stock_quantity = forms.IntegerField(
        min_value=0,
        initial=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Available Stock Quantity'}),
        help_text="Units available for sale in inventory."
    )

    class Meta:
        model = Product
        fields = [
            'title', 'category', 'price', 'compare_at_price',
            'sku', 'short_description', 'description', 'is_active', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Italian Silk Cashmere Scarf'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'compare_at_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00 (Optional)'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. AUR-LUX-001'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief 1-2 sentence highlight'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Full product provenance, material composition, specifications and care details'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        if self.instance and self.instance.pk and hasattr(self.instance, 'inventory'):
            self.fields['stock_quantity'].initial = self.instance.inventory.quantity

    def clean_sku(self):
        sku = self.cleaned_data.get('sku').upper().strip()
        query = Product.objects.filter(sku=sku)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError("This SKU is already in use by another product.")
        return sku


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'sort_order']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descriptive alt text'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'max-width: 80px;'}),
        }

ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=3,
    can_delete=True
)
