import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from .models import Payment, Commission, SellerPayout
from .services import RazorpayService
from apps.orders.models import Order

@login_required
def payment_initiate_view(request, order_number):
    """Initializes payment order and prepares Razorpay test checkout."""
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)

    if order.payment_status == Order.PaymentStatus.PAID:
        messages.info(request, "This order has already been paid.")
        return redirect('orders:detail', order_number=order.order_number)

    payment = RazorpayService.create_payment_order(order)
    amount_in_paise = int(order.total_amount * 100)

    return render(request, 'payments/checkout_payment.html', {
        'order': order,
        'payment': payment,
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
        'amount_in_paise': amount_in_paise,
        'currency': payment.currency,
        'title': f"Complete Payment - Order #{order.order_number}"
    })


@require_POST
@login_required
def payment_verify_view(request, order_number):
    """
    Verifies Razorpay payment signature and confirms order.
    Never marks order paid without signature verification.
    """
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)

    razorpay_order_id = request.POST.get('razorpay_order_id', '').strip()
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '').strip()
    razorpay_signature = request.POST.get('razorpay_signature', '').strip()

    is_valid = RazorpayService.verify_signature(
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature
    )

    if is_valid:
        RazorpayService.process_successful_payment(
            order=order,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature
        )
        messages.success(request, f"Payment verified successfully! Your order #{order.order_number} is confirmed.")
        return redirect('orders:detail', order_number=order.order_number)
    else:
        RazorpayService.process_failed_payment(
            order=order,
            error_msg="Cryptographic payment signature verification failed."
        )
        messages.error(request, "Payment verification failed. Please try again or use another payment method.")
        return redirect('payments:failed', order_number=order.order_number)


@login_required
def payment_failed_view(request, order_number):
    """Payment failure notification with retry button."""
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    return render(request, 'payments/payment_failed.html', {
        'order': order,
        'title': f"Payment Failed - Order #{order.order_number}"
    })


@csrf_exempt
@require_POST
def payment_webhook_view(request):
    """Processes server-to-server Razorpay webhooks with signature check."""
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
    webhook_signature = request.headers.get('X-Razorpay-Signature', '')

    payload = request.body.decode('utf-8')
    client = RazorpayService.get_client()

    if client and webhook_secret and not webhook_secret.startswith('sample_'):
        try:
            client.utility.verify_webhook_signature(payload, webhook_signature, webhook_secret)
        except Exception:
            return HttpResponseBadRequest("Invalid Webhook Signature")

    try:
        data = json.loads(payload)
        event = data.get('event')
        if event == 'order.paid':
            payload_entity = data.get('payload', {}).get('order', {}).get('entity', {})
            receipt = payload_entity.get('receipt')
            if receipt:
                order = Order.objects.filter(order_number=receipt).first()
                if order and order.payment_status != Order.PaymentStatus.PAID:
                    payments = data.get('payload', {}).get('payment', {}).get('entity', {})
                    pid = payments.get('id', 'webhook_paid')
                    RazorpayService.process_successful_payment(order, pid, "webhook_verified")
    except Exception:
        pass

    return HttpResponse(status=200)
