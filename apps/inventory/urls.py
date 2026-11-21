from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.vendor_inventory_list_view, name='inventory_list'),
]
