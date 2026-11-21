from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg
from .models import Category, Product, ProductImage
from apps.reviews.models import Review

def product_list_view(request, category_slug=None):
    """Product catalog with searching, faceted filters, sorting and pagination."""
    products = Product.objects.filter(is_active=True, vendor__status='APPROVED').select_related('vendor', 'category', 'inventory').prefetch_related('images')
    
    current_category = None
    categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children')

    # Category Filter
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        # Include products in subcategories
        cat_ids = [current_category.id] + list(current_category.children.values_list('id', flat=True))
        products = products.filter(category_id__in=cat_ids)
    elif request.GET.get('category'):
        cat_param = request.GET.get('category')
        current_category = Category.objects.filter(slug=cat_param, is_active=True).first()
        if current_category:
            cat_ids = [current_category.id] + list(current_category.children.values_list('id', flat=True))
            products = products.filter(category_id__in=cat_ids)

    # Search Query
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(vendor__store_name__icontains=query)
        )

    # Price Filtering
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Availability Filter
    in_stock = request.GET.get('in_stock')
    if in_stock == '1':
        products = products.filter(inventory__quantity__gt=0)

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'title_asc':
        products = products.order_by('title')
    else:  # newest
        products = products.order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    return render(request, 'catalog/product_list.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'current_category': current_category,
        'query': query,
        'sort': sort,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'in_stock': in_stock or '',
        'total_count': paginator.count,
        'title': f"{current_category.name} | Aura Luxe Collection" if current_category else "Luxury Catalog | Aura Luxe"
    })


def product_detail_view(request, slug):
    """Detailed product view with gallery, stock, seller details and verified reviews."""
    product = get_object_or_404(
        Product.objects.select_related('vendor', 'category', 'inventory').prefetch_related('images'),
        slug=slug,
        is_active=True,
        vendor__status='APPROVED'
    )

    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(pk=product.pk).select_related('vendor').prefetch_related('images')[:4]

    reviews = product.reviews.filter(is_approved=True).select_related('customer')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0

    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'title': f"{product.title} | Aura Luxe"
    })
