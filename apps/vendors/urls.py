from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('apply/', views.vendor_apply_view, name='apply'),
    path('status/', views.vendor_status_view, name='status'),
    path('store/<slug:slug>/', views.vendor_store_public_view, name='store_detail'),
]
