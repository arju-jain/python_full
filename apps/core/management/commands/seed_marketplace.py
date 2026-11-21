from decimal import Decimal
from pathlib import Path
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import User, Address
from apps.vendors.models import Vendor
from apps.catalog.models import Category, Product, ProductImage
from apps.inventory.models import Inventory
from apps.orders.models import Order, OrderItem, SellerFulfillment
from apps.payments.models import Payment, Commission

class Command(BaseCommand):
    help = "Seeds initial luxury categories, vendors, products, and administrative accounts."

    def ensure_category_image(self, filename):
        image_dir = Path(settings.MEDIA_ROOT) / 'categories'
        image_dir.mkdir(parents=True, exist_ok=True)
        media_path = image_dir / filename
        source_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'categories' / filename

        if source_path.exists():
            shutil.copy2(source_path, media_path)
        return f"categories/{filename}"

    def ensure_seed_image(self, sku, title, category_name):
        """Create a local premium-looking seed image for a product and return its media path."""
        image_dir = Path(settings.MEDIA_ROOT) / 'products' / 'seed'
        image_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{sku.lower()}-primary.png"
        image_path = image_dir / filename
        source_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'products' / filename

        if source_path.exists():
            shutil.copy2(source_path, image_path)
            return f"products/seed/{filename}"

        if not image_path.exists():
            try:
                from PIL import Image, ImageDraw, ImageFont

                palette = {
                    'Fine Timepieces': ((18, 20, 19), (176, 146, 103)),
                    'Artisanal Leather': ((91, 61, 38), (204, 174, 126)),
                    'High Jewelry': ((32, 35, 43), (205, 181, 125)),
                }
                background, accent = palette.get(category_name, ((40, 40, 40), (182, 155, 117)))

                image = Image.new('RGB', (900, 900), background)
                draw = ImageDraw.Draw(image)
                draw.rounded_rectangle((70, 70, 830, 830), radius=28, outline=accent, width=8)
                draw.ellipse((280, 280, 620, 620), outline=accent, width=18)
                draw.rectangle((440, 210, 460, 690), fill=accent)
                draw.rectangle((210, 440, 690, 460), fill=accent)
                draw.ellipse((400, 400, 500, 500), fill=accent)

                font = ImageFont.load_default()
                title_font = font
                draw.text((450, 760), title[:44], fill=(255, 255, 255), anchor='mm', font=title_font)
                draw.text((450, 800), 'AURA LUXE', fill=accent, anchor='mm', font=title_font)
                image.save(image_path, 'PNG')
            except ImportError:
                self.stdout.write(self.style.WARNING("Pillow is unavailable; seed images could not be generated."))
                return None

        return f"products/seed/{filename}"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Aura Luxe Marketplace with initial data..."))

        # 1. Superuser
        admin, _ = User.objects.get_or_create(
            email='admin@auraluxe.com',
            defaults={
                'first_name': 'Aura',
                'last_name': 'Administrator',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin.set_password('Admin@12345')
        admin.save()
        self.stdout.write(self.style.SUCCESS(f"Administrator initialized: admin@auraluxe.com / Admin@12345"))

        # 2. Customer
        customer, _ = User.objects.get_or_create(
            email='patron@auraluxe.com',
            defaults={
                'first_name': 'Julian',
                'last_name': 'Sinclair',
                'role': User.Role.CUSTOMER,
                'phone_number': '+91 98200 12345'
            }
        )
        customer.set_password('Patron@12345')
        customer.save()

        Address.objects.get_or_create(
            user=customer,
            street_address_1='Flat 14A, Grand Palace Towers, Worli Seaface',
            defaults={
                'address_type': Address.AddressType.SHIPPING,
                'full_name': 'Julian Sinclair',
                'phone_number': '+91 98200 12345',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400018',
                'country': 'India',
                'is_default': True
            }
        )
        self.stdout.write(self.style.SUCCESS("Demo Customer initialized: patron@auraluxe.com / Patron@12345"))

        # 3. Categories
        cat_time, _ = Category.objects.get_or_create(
            name='Fine Timepieces',
            defaults={'slug': 'fine-timepieces', 'description': 'Handcrafted chronometers and perpetual complications.'}
        )
        cat_time.image = self.ensure_category_image('ach-perp-01-primary.png')
        cat_time.is_featured = True
        cat_time.save()
        cat_leather, _ = Category.objects.get_or_create(
            name='Artisanal Leather',
            defaults={'slug': 'artisanal-leather', 'description': 'Full-grain saddle stitched luggage and accessories.'}
        )
        cat_leather.is_featured = True
        cat_leather.save()
        cat_jewelry, _ = Category.objects.get_or_create(
            name='High Jewelry',
            defaults={'slug': 'high-jewelry', 'description': 'Natural gemstones, solitaire diamonds, and platinum creations.'}
        )
        cat_jewelry.image = self.ensure_category_image('vdm-sol-01-primary.png')
        cat_jewelry.is_featured = True
        cat_jewelry.save()
        cat_dress, _ = Category.objects.get_or_create(
            name='Dress & Couture',
            defaults={
                'slug': 'dress-couture',
                'description': 'Elevated ready-to-wear and statement couture.',
                'image': 'categories/dress.jpg',
                'is_featured': True,
            }
        )
        cat_dress.image = self.ensure_category_image('dress.jpg')
        cat_dress.is_featured = True
        cat_dress.save()

        # 4. Vendors
        # Vendor 1: Geneva Horlogerie
        u_v1, _ = User.objects.get_or_create(
            email='horlogerie@auraluxe.com',
            defaults={'first_name': 'Jean-Luc', 'last_name': 'Picard', 'role': User.Role.VENDOR}
        )
        u_v1.set_password('Vendor@12345')
        u_v1.save()

        v1, _ = Vendor.objects.get_or_create(
            user=u_v1,
            defaults={
                'store_name': 'Maison Horlogerie Geneva',
                'slug': 'maison-horlogerie-geneva',
                'contact_email': 'contact@genevahorlogerie.ch',
                'phone_number': '+41 22 819 0000',
                'commission_rate': Decimal('10.00'),
                'status': Vendor.Status.APPROVED,
                'description': 'Master chronometer manufacture based in Geneva since 1888.'
            }
        )

        # Vendor 2: Atelier Florentine
        u_v2, _ = User.objects.get_or_create(
            email='florentine@auraluxe.com',
            defaults={'first_name': 'Matteo', 'last_name': 'Rossi', 'role': User.Role.VENDOR}
        )
        u_v2.set_password('Vendor@12345')
        u_v2.save()

        v2, _ = Vendor.objects.get_or_create(
            user=u_v2,
            defaults={
                'store_name': 'Atelier Florentine',
                'slug': 'atelier-florentine',
                'contact_email': 'info@atelierflorentine.it',
                'phone_number': '+39 055 210 998',
                'commission_rate': Decimal('12.00'),
                'status': Vendor.Status.APPROVED,
                'description': 'Handcrafted Tuscan vegetable-tanned leather trunks and bespoke briefcases.'
            }
        )

        # Vendor 3: L'Orfevre Royal
        u_v3, _ = User.objects.get_or_create(
            email='orfevre@auraluxe.com',
            defaults={'first_name': 'Henri', 'last_name': 'Cartier', 'role': User.Role.VENDOR}
        )
        u_v3.set_password('Vendor@12345')
        u_v3.save()

        v3, _ = Vendor.objects.get_or_create(
            user=u_v3,
            defaults={
                'store_name': "L'Orfevre Royal",
                'slug': 'lorfevre-royal',
                'contact_email': 'salon@lorfevreroyal.fr',
                'phone_number': '+33 1 42 68 0000',
                'commission_rate': Decimal('15.00'),
                'status': Vendor.Status.APPROVED,
                'description': 'Haute joaillerie and ethically sourced natural gemstones from Place Vendôme.'
            }
        )
        self.stdout.write(self.style.SUCCESS("3 Approved Merchant Boutiques initialized."))

        # 5. Products & Inventory
        products_data = [
            (v1, cat_time, 'Aura Chrono Perpetual Calendar', Decimal('185000.00'), Decimal('210000.00'), 'ACH-PERP-01', 12, True,
             'Manufacture calibre with 72-hour power reserve, perpetual calendar and moonphase display.'),
            (v1, cat_time, 'Geneva Skeleton Tourbillon Rose Gold', Decimal('290000.00'), None, 'GVA-SKEL-02', 6, True,
             'Fully skeletonized flying tourbillon in 18k solid rose gold with alligator leather strap.'),
            (v2, cat_leather, 'Florentine Full-Grain Diplomat Briefcase', Decimal('42000.00'), Decimal('48000.00'), 'FLR-DIP-01', 15, True,
             'Hand-burnished bridle leather with solid brass lock and suede interior compartments.'),
            (v2, cat_leather, 'Weekender Tuscan Duffle Trunk', Decimal('58000.00'), None, 'FLR-WKD-02', 8, False,
             'Heritage weekender duffle hand-cut from supple vegetable-tanned bovine hide.'),
            (v3, cat_jewelry, 'Vendôme Solitaire Diamond Ring (2.1ct)', Decimal('450000.00'), None, 'VDM-SOL-01', 4, True,
             'Certified D-color VVS1 round brilliant diamond set in 950 platinum four-prong mount.'),
            (v3, cat_jewelry, 'Royal Emerald & Platinum Tennis Bracelet', Decimal('220000.00'), Decimal('250000.00'), 'RYL-EMR-02', 5, True,
             'Colombian natural vivid green emeralds framed by round brilliant micro-pavé diamonds.')
        ]

        for vendor, category, title, price, compare_at, sku, stock, is_featured, desc in products_data:
            p, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'vendor': vendor,
                    'category': category,
                    'title': title,
                    'price': price,
                    'compare_at_price': compare_at,
                    'description': desc,
                    'short_description': desc[:120],
                    'is_active': True,
                    'is_featured': is_featured
                }
            )
            Inventory.objects.get_or_create(product=p, defaults={'quantity': stock})
            image_name = self.ensure_seed_image(sku, title, category.name)
            if image_name:
                image, _ = ProductImage.objects.get_or_create(
                    product=p,
                    sort_order=0,
                    defaults={
                        'alt_text': title,
                        'is_primary': True,
                    }
                )
                image.image = image_name
                image.alt_text = title
                image.is_primary = True
                image.save()

        self.stdout.write(self.style.SUCCESS("Luxury products and inventories seeded."))

        # 6. Sample Completed Multi-Vendor Order
        prod1 = Product.objects.get(sku='ACH-PERP-01')
        prod2 = Product.objects.get(sku='FLR-DIP-01')

        order_num = 'AL-20261121-DEMO'
        if not Order.objects.filter(order_number=order_num).exists():
            demo_order = Order.objects.create(
                order_number=order_num,
                customer=customer,
                status=Order.Status.CONFIRMED,
                payment_status=Order.PaymentStatus.PAID,
                subtotal_amount=prod1.price + prod2.price,
                shipping_amount=Decimal('0.00'),
                total_amount=prod1.price + prod2.price,
                shipping_full_name=customer.get_full_name(),
                shipping_phone=customer.phone_number,
                shipping_address_line1='Flat 14A, Grand Palace Towers, Worli Seaface',
                shipping_city='Mumbai',
                shipping_state='Maharashtra',
                shipping_postal_code='400018',
                shipping_country='India',
                customer_notes='White-glove weekend delivery requested.'
            )

            item1 = OrderItem.objects.create(
                order=demo_order,
                product=prod1,
                vendor=prod1.vendor,
                product_title=prod1.title,
                sku=prod1.sku,
                unit_price=prod1.price,
                quantity=1,
                subtotal=prod1.price
            )

            item2 = OrderItem.objects.create(
                order=demo_order,
                product=prod2,
                vendor=prod2.vendor,
                product_title=prod2.title,
                sku=prod2.sku,
                unit_price=prod2.price,
                quantity=1,
                subtotal=prod2.price
            )

            # Isolated fulfillments
            f1 = SellerFulfillment.objects.create(
                order=demo_order,
                vendor=prod1.vendor,
                status=SellerFulfillment.Status.SHIPPED,
                shipping_carrier='Ferrari Security Courier',
                tracking_number='FSC-GVA-778899'
            )

            f2 = SellerFulfillment.objects.create(
                order=demo_order,
                vendor=prod2.vendor,
                status=SellerFulfillment.Status.PROCESSING,
                shipping_carrier='DHL Express',
                tracking_number='DHL-FLR-223344'
            )

            # Payment
            payment = Payment.objects.create(
                order=demo_order,
                transaction_id='TXN-DEMO-20261121',
                razorpay_order_id='order_demo_12345678',
                razorpay_payment_id='pay_demo_87654321',
                amount=demo_order.total_amount,
                status=Payment.Status.COMPLETED
            )

            # Commissions
            c1_fee = (item1.subtotal * prod1.vendor.commission_rate) / Decimal('100.00')
            Commission.objects.create(
                order_item=item1,
                vendor=prod1.vendor,
                order=demo_order,
                gross_amount=item1.subtotal,
                commission_rate=prod1.vendor.commission_rate,
                commission_amount=c1_fee,
                net_seller_amount=item1.subtotal - c1_fee
            )

            c2_fee = (item2.subtotal * prod2.vendor.commission_rate) / Decimal('100.00')
            Commission.objects.create(
                order_item=item2,
                vendor=prod2.vendor,
                order=demo_order,
                gross_amount=item2.subtotal,
                commission_rate=prod2.vendor.commission_rate,
                commission_amount=c2_fee,
                net_seller_amount=item2.subtotal - c2_fee
            )
            self.stdout.write(self.style.SUCCESS(f"Multi-vendor demonstration order #{order_num} initialized."))

        self.stdout.write(self.style.SUCCESS("All marketplace seed data successfully generated!"))
