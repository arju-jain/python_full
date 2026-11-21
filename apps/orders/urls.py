from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('history/', views.order_history_view, name='history'),
    path('<str:order_number>/', views.order_detail_view, name='detail'),
]
