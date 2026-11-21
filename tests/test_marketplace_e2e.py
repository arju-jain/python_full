from decimal import Decimal
import hmac
import hashlib
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from apps.accounts.models import User, Address
from apps.vendors.models import Vendor, VendorApplication
from apps.vendors.services import VendorService
from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.inventory.services import InventoryService
from apps.cart.models import Cart, CartItem
from apps.cart.services import CartService
from apps.orders.models import Order, OrderItem, SellerFulfillment
from apps.orders.services import OrderService
from apps.payments.models import Payment, Commission
from apps.payments.services import RazorpayService
from apps.reviews.models import Review

class MarketplaceEndToEndTests(TestCase):
    def setUp(self):
        # 1. Administrator
        self.admin = User.objects.create_superuser(
            email='director@auraluxe.com',
            password='AdminPassword2026!'
        )

        # 2. Customer
        self.customer = User.objects.create_user(
            email='lady.genevieve@example.com',
            password='CustomerSecurePass123!',
            first_name='Genevieve',
            last_name='Sinclair'
        )
        self.address = Address.objects.create(
            user=self.customer,
            address_type=Address.AddressType.SHIPPING,
            full_name='Lady Genevieve Sinclair',
            phone_number='+919876543210',
            street_address_1='42 Mayfair Crescent',
            city='Mumbai',
            state='Maharashtra',
            postal_code='400001',
            country='India',
            is_default=True
        )

        # 3. Category
        self.category = Category.objects.create(name='Haute Horlogerie', slug='haute-horlogerie')

        # 4. Vendor 1
        self.user_v1 = User.objects.create_user(email='geneva.watches@example.com', password='Password123!')
        self.vendor1 = Vendor.objects.create(
            user=self.user_v1,
            store_name='Geneva Timepieces',
            contact_email='contact@geneva.ch',
            commission_rate=Decimal('10.00'),
            status=Vendor.Status.APPROVED
        )
        self.user_v1.role = User.Role.VENDOR
        self.user_v1.save()

        self.product1 = Product.objects.create(
            vendor=self.vendor1,
            category=self.category,
            title='Geneva Perpetual Tourbillon',
            price=Decimal('150000.00'),
            compare_at_price=Decimal('175000.00'),
            sku='GVA-TOURB-01',
            description='Swiss hand-wound tourbillon mechanism in 18k rose gold.'
        )
        Inventory.objects.create(product=self.product1, quantity=8)

        # 5. Vendor 2
        self.user_v2 = User.objects.create_user(email='florence.leather@example.com', password='Password123!')
        self.vendor2 = Vendor.objects.create(
            user=self.user_v2,
            store_name='Atelier Firenze',
            contact_email='contact@firenze.it',
            commission_rate=Decimal('12.50'),
            status=Vendor.Status.APPROVED
        )
        self.user_v2.role = User.Role.VENDOR
        self.user_v2.save()

        self.product2 = Product.objects.create(
            vendor=self.vendor2,
            title='Hand-Stitched Bridle Leather Portfolio',
            price=Decimal('35000.00'),
            sku='AF-PORT-01',
            description='Full-grain vegetable-tanned bridle leather.'
        )
        Inventory.objects.create(product=self.product2, quantity=12)

    def test_01_customer_registration_and_authentication(self):
        """Tests customer registration, login verification, and logout."""
        c = Client()
        # Register new patron
        reg_response = c.post(reverse('accounts:register'), {
            'first_name': 'Julian',
            'last_name': 'Vance',
            'email': 'julian.vance@example.com',
            'phone_number': '9876500000',
            'password': 'StrongPassword2026!',
            'confirm_password': 'StrongPassword2026!'
        })
        self.assertEqual(reg_response.status_code, 302)
        new_user = User.objects.get(email='julian.vance@example.com')
        self.assertEqual(new_user.role, User.Role.CUSTOMER)

        # Logout
        c.get(reverse('accounts:logout'))

        # Login
        login_res = c.post(reverse('accounts:login'), {
            'email': 'julian.vance@example.com',
            'password': 'StrongPassword2026!'
        })
        self.assertEqual(login_res.status_code, 302)

    def test_02_vendor_application_and_approval_workflow(self):
        """Tests vendor application, admin approval, and store initialization."""
        applicant = User.objects.create_user(email='applicant@craft.com', password='Password123!')
        c = Client()
        c.login(email='applicant@craft.com', password='Password123!')

        # Submit vendor application
        app_res = c.post(reverse('vendors:apply'), {
            'store_name': 'Kyoto Lacquerware',
            'contact_email': 'info@kyotolacquer.jp',
            'phone_number': '9871122334',
            'tax_id': 'TAX-KYO-9988',
            'business_details': 'Generational Urushi lacquer artisan workshop.'
        })
        self.assertEqual(app_res.status_code, 302)
        application = VendorApplication.objects.get(user=applicant)
        self.assertEqual(application.status, VendorApplication.Status.PENDING)

        # Admin approves application
        c_admin = Client()
        c_admin.login(email='director@auraluxe.com', password='AdminPassword2026!')
        approve_res = c_admin.post(reverse('dashboard:admin_vendor_approve', kwargs={'app_id': application.id}))
        self.assertEqual(approve_res.status_code, 302)

        application.refresh_from_db()
        applicant.refresh_from_db()
        self.assertEqual(application.status, VendorApplication.Status.APPROVED)
        self.assertEqual(applicant.role, User.Role.VENDOR)
        self.assertTrue(hasattr(applicant, 'vendor'))
        self.assertEqual(applicant.vendor.status, Vendor.Status.APPROVED)

    def test_03_vendor_product_creation_and_ownership_security(self):
        """Tests that Vendor A cannot modify or delete Vendor B's products."""
        c_v1 = Client()
        c_v1.login(email='geneva.watches@example.com', password='Password123!')

        # Vendor 1 attempts to edit Vendor 2's product -> 404 forbidden
        unauth_edit = c_v1.get(reverse('dashboard:vendor_product_edit', kwargs={'pk': self.product2.pk}))
        self.assertEqual(unauth_edit.status_code, 404)

        # Vendor 1 attempts to delete Vendor 2's product -> 404 forbidden
        unauth_delete = c_v1.post(reverse('dashboard:vendor_product_delete', kwargs={'pk': self.product2.pk}))
        self.assertEqual(unauth_delete.status_code, 404)

        # Vendor 1 successfully edits own product
        auth_edit = c_v1.post(reverse('dashboard:vendor_product_edit', kwargs={'pk': self.product1.pk}), {
            'title': 'Geneva Perpetual Tourbillon Platinum Edition',
            'category': self.category.id,
            'price': '160000.00',
            'sku': 'GVA-TOURB-01',
            'description': 'Updated platinum edition.',
            'stock_quantity': 10,
            'is_active': True,
            'images-TOTAL_FORMS': '0',
            'images-INITIAL_FORMS': '0',
        })
        self.assertEqual(auth_edit.status_code, 302)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.title, 'Geneva Perpetual Tourbillon Platinum Edition')
        self.assertEqual(self.product1.price, Decimal('160000.00'))
        self.assertEqual(self.product1.stock_quantity, 10)

    def test_04_product_catalog_search_and_filters(self):
        """Tests product listing with text search, category filters, and price ranges."""
        c = Client()
        # Search by keyword
        res_search = c.get(reverse('catalog:product_list') + '?q=Tourbillon')
        self.assertEqual(res_search.status_code, 200)
        self.assertContains(res_search, 'Geneva Perpetual Tourbillon')

        # Filter by Category
        res_cat = c.get(reverse('catalog:product_list_by_category', kwargs={'category_slug': 'haute-horlogerie'}))
        self.assertEqual(res_cat.status_code, 200)
        self.assertContains(res_cat, 'Geneva Perpetual Tourbillon')

        # Filter by price range
        res_price = c.get(reverse('catalog:product_list') + '?min_price=100000')
        self.assertEqual(res_price.status_code, 200)
        self.assertContains(res_price, 'Geneva Perpetual Tourbillon')
        self.assertNotContains(res_price, 'Bridle Leather Portfolio')

    def test_05_multi_vendor_atomic_checkout_workflow(self):
        """
        Tests the core multi-vendor workflow:
        - Customer adds items from Vendor 1 and Vendor 2 to cart.
        - Checks out with shipping address.
        - Single parent Order created.
        - Isolated OrderItems and SellerFulfillments created.
        - Inventory deducted atomically.
        """
        cart = Cart.objects.create(user=self.customer)
        CartService.add_item(cart, self.product1, quantity=1)
        CartService.add_item(cart, self.product2, quantity=2)

        self.assertEqual(cart.total_items, 3)
        expected_subtotal = Decimal('150000.00') + (Decimal('35000.00') * 2)  # 220,000.00
        self.assertEqual(cart.subtotal, expected_subtotal)

        # Checkout
        order = OrderService.create_order_from_cart(
            cart=cart,
            customer=self.customer,
            address_id=self.address.id,
            notes='Leave at concierge reception.'
        )

        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.UNPAID)
        self.assertEqual(order.total_amount, expected_subtotal)

        # Check fulfillments
        self.assertEqual(order.fulfillments.count(), 2)
        f_v1 = order.fulfillments.get(vendor=self.vendor1)
        f_v2 = order.fulfillments.get(vendor=self.vendor2)
        self.assertEqual(f_v1.vendor_items.count(), 1)
        self.assertEqual(f_v2.vendor_items.count(), 1)
        self.assertEqual(f_v1.vendor_subtotal, Decimal('150000.00'))
        self.assertEqual(f_v2.vendor_subtotal, Decimal('70000.00'))

        # Check inventory deductions
        self.product1.inventory.refresh_from_db()
        self.product2.inventory.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 7)  # 8 - 1 = 7
        self.assertEqual(self.product2.stock_quantity, 10) # 12 - 2 = 10

    def test_06_payment_verification_and_commission_calculation(self):
        """
        Tests Razorpay payment order generation, cryptographic signature verification,
        and automated commission splitting per vendor.
        """
        cart = Cart.objects.create(user=self.customer)
        CartService.add_item(cart, self.product1, quantity=1) # 150,000 (10% comm = 15,000, net = 135,000)
        CartService.add_item(cart, self.product2, quantity=1) # 35,000 (12.5% comm = 4,375, net = 30,625)

        order = OrderService.create_order_from_cart(cart, self.customer, self.address.id)
        payment = RazorpayService.create_payment_order(order)

        # Cryptographic Signature Verification
        secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        r_order_id = payment.razorpay_order_id
        r_payment_id = 'pay_rzp_mock_live_12345'
        valid_signature = hmac.new(
            secret.encode('utf-8'),
            f"{r_order_id}|{r_payment_id}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Execute confirmation
        confirmed_payment = RazorpayService.process_successful_payment(order, r_payment_id, valid_signature)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(confirmed_payment.status, Payment.Status.COMPLETED)

        # Verify commissions
        comm_v1 = Commission.objects.get(order_item__product=self.product1)
        self.assertEqual(comm_v1.gross_amount, Decimal('150000.00'))
        self.assertEqual(comm_v1.commission_rate, Decimal('10.00'))
        self.assertEqual(comm_v1.commission_amount, Decimal('15000.00'))
        self.assertEqual(comm_v1.net_seller_amount, Decimal('135000.00'))

        comm_v2 = Commission.objects.get(order_item__product=self.product2)
        self.assertEqual(comm_v2.gross_amount, Decimal('35000.00'))
        self.assertEqual(comm_v2.commission_rate, Decimal('12.50'))
        self.assertEqual(comm_v2.commission_amount, Decimal('4375.00'))
        self.assertEqual(comm_v2.net_seller_amount, Decimal('30625.00'))

        # Verify fulfillments moved to PROCESSING
        for f in order.fulfillments.all():
            self.assertEqual(f.status, SellerFulfillment.Status.PROCESSING)

    def test_07_seller_fulfillment_isolation_and_dispatch(self):
        """Tests that Vendor 1 updates only their own dispatch, without affecting Vendor 2."""
        cart = Cart.objects.create(user=self.customer)
        CartService.add_item(cart, self.product1, quantity=1)
        CartService.add_item(cart, self.product2, quantity=1)
        order = OrderService.create_order_from_cart(cart, self.customer, self.address.id)

        f_v1 = order.fulfillments.get(vendor=self.vendor1)
        f_v2 = order.fulfillments.get(vendor=self.vendor2)

        # Vendor 1 logs in and updates their dispatch
        c_v1 = Client()
        c_v1.login(email='geneva.watches@example.com', password='Password123!')
        res = c_v1.post(reverse('dashboard:vendor_order_detail', kwargs={'pk': f_v1.pk}), {
            'status': SellerFulfillment.Status.SHIPPED,
            'shipping_carrier': 'Ferrari Armed Express',
            'tracking_number': 'FAE-CH-998877',
            'notes': 'Dispatched in reinforced tamper-proof security box.'
        })
        self.assertEqual(res.status_code, 302)

        f_v1.refresh_from_db()
        f_v2.refresh_from_db()
        self.assertEqual(f_v1.status, SellerFulfillment.Status.SHIPPED)
        self.assertEqual(f_v1.tracking_number, 'FAE-CH-998877')
        self.assertEqual(f_v1.shipping_carrier, 'Ferrari Armed Express')

        # Vendor 2 remains PENDING (strictly isolated)
        self.assertEqual(f_v2.status, SellerFulfillment.Status.PENDING)
        self.assertEqual(f_v2.tracking_number, '')

    def test_08_rbac_and_unauthorized_access_prevention(self):
        """Verifies server-side authorization blocks illegal role access."""
        c = Client()
        # 1. Anonymous visitor cannot access customer, vendor, or admin dashboard
        self.assertEqual(c.get(reverse('dashboard:customer_overview')).status_code, 302)
        self.assertEqual(c.get(reverse('dashboard:vendor_overview')).status_code, 302)
        self.assertEqual(c.get(reverse('dashboard:admin_overview')).status_code, 302)

        # 2. Customer cannot access vendor dashboard or admin dashboard
        c.login(email='lady.genevieve@example.com', password='CustomerSecurePass123!')
        self.assertEqual(c.get(reverse('dashboard:vendor_overview')).status_code, 302)
        self.assertEqual(c.get(reverse('dashboard:admin_overview')).status_code, 302)

        # 3. Vendor cannot access admin dashboard
        c.login(email='geneva.watches@example.com', password='Password123!')
        self.assertEqual(c.get(reverse('dashboard:admin_overview')).status_code, 302)

        # 4. Superadmin has access to admin dashboard
        c.login(email='director@auraluxe.com', password='AdminPassword2026!')
        self.assertEqual(c.get(reverse('dashboard:admin_overview')).status_code, 200)
