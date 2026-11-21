from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist_detail_view, name='wishlist_detail'),
    path('toggle/<int:product_id>/', views.wishlist_toggle_view, name='wishlist_toggle'),
    path('remove/<int:item_id>/', views.wishlist_remove_view, name='wishlist_remove'),
]
