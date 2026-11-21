from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(5, '5 Stars - Exceptional'), (4, '4 Stars - Very Good'), (3, '3 Stars - Average'), (2, '2 Stars - Fair'), (1, '1 Star - Poor')],
                attrs={'class': 'form-select'}
            ),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Summary of your experience'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detail the craftsmanship, fit, packaging and luxury experience...'}),
        }
