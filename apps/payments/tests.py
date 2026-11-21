import hmac
import hashlib
from decimal import Decimal
from django.test import TestCase
from django.conf import settings
from apps.accounts.models import User
from apps.vendors.models import Vendor
from apps.catalog.models import Product
from apps.orders.models import Order, OrderItem, SellerFulfillment
from .models import Payment, Commission
from .services import RazorpayService

class PaymentAndCommissionTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(email='customer_pay@example.com', password='Password123!')
        self.seller_user = User.objects.create_user(email='seller_pay@example.com', password='Password123!')
        self.vendor = Vendor.objects.create(
            user=self.seller_user,
            store_name='Milan Timepieces',
            commission_rate=Decimal('15.00'),
            status=Vendor.Status.APPROVED
        )
        self.product = Product.objects.create(
            vendor=self.vendor,
            title='Classic Chrono',
            price=Decimal('10000.00'),
            sku='MLN-CHR-01',
            description='Swiss movement chronograph.'
        )
        self.order = Order.objects.create(
            order_number='AL-20261121-PAY1',
            customer=self.customer,
            subtotal_amount=Decimal('10000.00'),
            shipping_amount=Decimal('0.00'),
            total_amount=Decimal('10000.00'),
            shipping_full_name='Test Buyer',
            shipping_phone='9999999999',
            shipping_address_line1='Test St',
            shipping_city='Delhi',
            shipping_state='Delhi',
            shipping_postal_code='110001'
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            vendor=self.vendor,
            product_title=self.product.title,
            sku=self.product.sku,
            unit_price=self.product.price,
            quantity=1,
            subtotal=Decimal('10000.00')
        )
        self.fulfillment = SellerFulfillment.objects.create(
            order=self.order,
            vendor=self.vendor,
            status=SellerFulfillment.Status.PENDING
        )

    def test_payment_initiation_and_commission_calculation(self):
        # 1. Create payment order
        payment = RazorpayService.create_payment_order(self.order)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.amount, Decimal('10000.00'))
        self.assertTrue(payment.razorpay_order_id)

        # 2. Verify signature test
        secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        r_order_id = payment.razorpay_order_id
        r_payment_id = 'pay_test_998877'
        valid_sig = hmac.new(secret.encode(), f"{r_order_id}|{r_payment_id}".encode(), hashlib.sha256).hexdigest()
        self.assertTrue(RazorpayService.verify_signature(r_order_id, r_payment_id, valid_sig))
        self.assertFalse(RazorpayService.verify_signature(r_order_id, r_payment_id, "invalid_sig_abc"))

        # 3. Process payment confirmation
        RazorpayService.process_successful_payment(self.order, r_payment_id, valid_sig)

        # Verify Order & Payment Status
        self.order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(payment.status, Payment.Status.COMPLETED)

        # 4. Verify Commission Record
        commission = Commission.objects.get(order_item=self.item)
        self.assertEqual(commission.gross_amount, Decimal('10000.00'))
        self.assertEqual(commission.commission_rate, Decimal('15.00'))
        self.assertEqual(commission.commission_amount, Decimal('1500.00'))
        self.assertEqual(commission.net_seller_amount, Decimal('8500.00'))

        # 5. Verify SellerFulfillment moved to PROCESSING
        self.fulfillment.refresh_from_db()
        self.assertEqual(self.fulfillment.status, SellerFulfillment.Status.PROCESSING)
