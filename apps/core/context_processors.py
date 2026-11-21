from django.conf import settings
from apps.catalog.models import Category

def marketplace_context(request):
    """Global marketplace information available across all templates."""
    try:
        nav_categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children')[:8]
    except Exception:
        nav_categories = []

    return {
        'marketplace_name': getattr(settings, 'MARKETPLACE_NAME', 'AURA LUXE'),
        'currency_symbol': getattr(settings, 'CURRENCY_SYMBOL', '₹'),
        'nav_categories': nav_categories,
    }
