from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/<str:order_number>/', views.payment_initiate_view, name='initiate'),
    path('verify/<str:order_number>/', views.payment_verify_view, name='verify'),
    path('failed/<str:order_number>/', views.payment_failed_view, name='failed'),
    path('webhook/', views.payment_webhook_view, name='webhook'),
]
