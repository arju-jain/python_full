from django.test import TestCase
from decimal import Decimal
from apps.accounts.models import User, Address
from apps.vendors.models import Vendor
from apps.catalog.models import Product
from apps.inventory.models import Inventory
from apps.cart.models import Cart
from apps.cart.services import CartService
from .models import Order, OrderItem, SellerFulfillment
from .services import OrderService

class MultiVendorOrderTests(TestCase):
    def setUp(self):
        # Customer
        self.customer = User.objects.create_user(email='customer_ord@example.com', password='Password123!')
        self.address = Address.objects.create(
            user=self.customer,
            address_type=Address.AddressType.SHIPPING,
            full_name='Lady Eleanor',
            phone_number='9876543210',
            street_address_1='10 Kensington Mansions',
            city='Bangalore',
            state='Karnataka',
            postal_code='560001',
            is_default=True
        )

        # Vendor 1
        user_v1 = User.objects.create_user(email='v1@example.com', password='Password123!')
        self.vendor1 = Vendor.objects.create(user=user_v1, store_name='Aura Leather Goods', status=Vendor.Status.APPROVED)
        self.product1 = Product.objects.create(
            vendor=self.vendor1, title='Leather Briefcase', price=Decimal('25000.00'), sku='V1-BRF-01', description='Fine leather.'
        )
        Inventory.objects.create(product=self.product1, quantity=10)

        # Vendor 2
        user_v2 = User.objects.create_user(email='v2@example.com', password='Password123!')
        self.vendor2 = Vendor.objects.create(user=user_v2, store_name='Luxe Timepieces', status=Vendor.Status.APPROVED)
        self.product2 = Product.objects.create(
            vendor=self.vendor2, title='Chronograph Gold Watch', price=Decimal('90000.00'), sku='V2-WAT-01', description='Fine watch.'
        )
        Inventory.objects.create(product=self.product2, quantity=5)

    def test_multi_vendor_checkout_and_fulfillments(self):
        # 1. Customer adds items from Vendor 1 and Vendor 2 into same cart
        cart = Cart.objects.create(user=self.customer)
        CartService.add_item(cart, self.product1, quantity=1)
        CartService.add_item(cart, self.product2, quantity=1)

        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.subtotal, Decimal('115000.00'))

        # 2. Execute multi-vendor checkout
        order = OrderService.create_order_from_cart(
            cart=cart,
            customer=self.customer,
            address_id=self.address.id
        )

        # 3. Verify single parent order
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.total_amount, Decimal('115000.00'))
        self.assertEqual(order.status, Order.Status.PENDING)

        # 4. Verify Order Items
        self.assertEqual(order.items.count(), 2)
        item1 = order.items.get(product=self.product1)
        item2 = order.items.get(product=self.product2)
        self.assertEqual(item1.vendor, self.vendor1)
        self.assertEqual(item2.vendor, self.vendor2)
        self.assertEqual(item1.unit_price, Decimal('25000.00'))
        self.assertEqual(item2.unit_price, Decimal('90000.00'))

        # 5. Verify isolated SellerFulfillments (one for each vendor)
        self.assertEqual(order.fulfillments.count(), 2)
        f1 = order.fulfillments.get(vendor=self.vendor1)
        f2 = order.fulfillments.get(vendor=self.vendor2)
        self.assertEqual(f1.status, SellerFulfillment.Status.PENDING)
        self.assertEqual(f2.status, SellerFulfillment.Status.PENDING)

        # Verify vendor items isolation
        self.assertEqual(list(f1.vendor_items), [item1])
        self.assertEqual(list(f2.vendor_items), [item2])

        # 6. Verify inventory deducted
        self.product1.inventory.refresh_from_db()
        self.product2.inventory.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 9)
        self.assertEqual(self.product2.stock_quantity, 4)
