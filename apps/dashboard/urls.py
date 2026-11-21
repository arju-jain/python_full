from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Customer Dashboard
    path('customer/', views.customer_overview_view, name='customer_overview'),

    # Vendor Dashboard
    path('vendor/', views.vendor_overview_view, name='vendor_overview'),
    path('vendor/products/', views.vendor_products_view, name='vendor_products'),
    path('vendor/products/add/', views.vendor_product_create_view, name='vendor_product_add'),
    path('vendor/products/<int:pk>/edit/', views.vendor_product_edit_view, name='vendor_product_edit'),
    path('vendor/products/<int:pk>/delete/', views.vendor_product_delete_view, name='vendor_product_delete'),
    path('vendor/orders/', views.vendor_orders_view, name='vendor_orders'),
    path('vendor/orders/<int:pk>/', views.vendor_order_detail_view, name='vendor_order_detail'),
    path('vendor/settings/', views.vendor_store_settings_view, name='vendor_settings'),
    path('vendor/analytics/', views.vendor_analytics_view, name='vendor_analytics'),

    # Admin Dashboard
    path('admin-portal/', views.admin_overview_view, name='admin_overview'),
    path('admin-portal/vendors/', views.admin_vendors_view, name='admin_vendors'),
    path('admin-portal/vendors/<int:app_id>/approve/', views.admin_vendor_approve_view, name='admin_vendor_approve'),
    path('admin-portal/vendors/<int:app_id>/reject/', views.admin_vendor_reject_view, name='admin_vendor_reject'),
    path('admin-portal/vendors/<int:vendor_id>/toggle-status/', views.admin_vendor_toggle_status_view, name='admin_vendor_toggle_status'),
    path('admin-portal/products/', views.admin_products_view, name='admin_products'),
    path('admin-portal/products/<int:pk>/toggle/', views.admin_product_toggle_view, name='admin_product_toggle'),
    path('admin-portal/orders/', views.admin_orders_view, name='admin_orders'),
    path('admin-portal/transactions/', views.admin_transactions_view, name='admin_transactions'),
]
