from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Order, OrderItem, SellerFulfillment
from apps.inventory.services import InventoryService
from apps.accounts.models import Address

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(cart, customer, address_id: int, notes: str = ""):
        """
        Executes atomic multi-vendor checkout:
        1. Validates cart non-empty.
        2. Validates shipping address.
        3. Locks and validates stock for all items.
        4. Generates unique parent Order.
        5. Creates immutable snapshot OrderItem records.
        6. Creates individual SellerFulfillment records per vendor.
        7. Deducts inventory atomically.
        """
        cart_items = list(cart.items.select_related('product__vendor', 'product__inventory').all())
        if not cart_items:
            raise ValidationError("Your shopping bag is empty.")

        try:
            address = Address.objects.get(id=address_id, user=customer)
        except Address.DoesNotExist:
            raise ValidationError("Invalid shipping address selected.")

        # Validate stock availability for all items before any creation
        for item in cart_items:
            product = item.product
            if product.stock_quantity < item.quantity:
                raise ValidationError(
                    f"Insufficient stock for '{product.title}'. Requested {item.quantity}, but only {product.stock_quantity} available."
                )

        subtotal = cart.subtotal
        shipping = cart.estimated_shipping
        total = subtotal + shipping

        # Create parent order
        order = Order.objects.create(
            order_number=Order.generate_order_number(),
            customer=customer,
            status=Order.Status.PENDING,
            payment_status=Order.PaymentStatus.UNPAID,
            subtotal_amount=subtotal,
            shipping_amount=shipping,
            total_amount=total,
            shipping_full_name=address.full_name,
            shipping_phone=address.phone_number,
            shipping_address_line1=address.street_address_1,
            shipping_address_line2=address.street_address_2,
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_postal_code=address.postal_code,
            shipping_country=address.country,
            customer_notes=notes
        )

        # Collect distinct vendors to create SellerFulfillment records
        vendors = set()

        for item in cart_items:
            product = item.product
            vendor = product.vendor
            vendors.add(vendor)

            # Snapshots of exact item title, sku, unit price
            OrderItem.objects.create(
                order=order,
                product=product,
                vendor=vendor,
                product_title=product.title,
                sku=product.sku,
                unit_price=product.price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )

            # Atomically deduct inventory
            InventoryService.deduct_stock_for_order(
                product=product,
                quantity=item.quantity,
                order_number=order.order_number
            )

        # Create isolated SellerFulfillment for each vendor
        for vendor in vendors:
            SellerFulfillment.objects.create(
                order=order,
                vendor=vendor,
                status=SellerFulfillment.Status.PENDING
            )

        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order, reason: str = ""):
        """Cancels an order and restocks inventory."""
        if order.status in [Order.Status.COMPLETED, Order.Status.CANCELLED]:
            raise ValidationError("This order cannot be cancelled.")

        order.status = Order.Status.CANCELLED
        order.save()

        # Restock products
        for item in order.items.all():
            InventoryService.restock_for_refund(
                product=item.product,
                quantity=item.quantity,
                order_number=order.order_number
            )

        # Update fulfillments
        order.fulfillments.all().update(status=SellerFulfillment.Status.CANCELLED)
        return order

    @staticmethod
    def update_fulfillment_status(fulfillment: SellerFulfillment, new_status: str, carrier: str = "", tracking: str = "", notes: str = ""):
        """Allows seller to update their own shipment status."""
        fulfillment.status = new_status
        if carrier:
            fulfillment.shipping_carrier = carrier
        if tracking:
            fulfillment.tracking_number = tracking
        if notes:
            fulfillment.notes = notes

        if new_status == SellerFulfillment.Status.SHIPPED and not fulfillment.dispatched_at:
            fulfillment.dispatched_at = timezone.now()
        elif new_status == SellerFulfillment.Status.DELIVERED and not fulfillment.delivered_at:
            fulfillment.delivered_at = timezone.now()

        fulfillment.save()

        # Check if all fulfillments for the order are delivered
        order = fulfillment.order
        all_statuses = order.fulfillments.values_list('status', flat=True)
        if all(s == SellerFulfillment.Status.DELIVERED for s in all_statuses):
            order.status = Order.Status.COMPLETED
            order.save(update_fields=['status'])
        elif any(s in [SellerFulfillment.Status.PROCESSING, SellerFulfillment.Status.SHIPPED] for s in all_statuses):
            if order.status == Order.Status.CONFIRMED:
                order.status = Order.Status.PROCESSING
                order.save(update_fields=['status'])

        return fulfillment
