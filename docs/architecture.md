# Aura Luxe Architecture Documentation

## 1. System Overview
Aura Luxe is a modular multi-vendor e-commerce marketplace built on Django 5 and PostgreSQL. It delivers a high-end luxury commerce experience for customers, an operational seller cockpit for vendors, and administrative moderation tools for marketplace operators.

## 2. Modular Architecture
The codebase adheres to a modular monolithic pattern:

```
MULTIVENDOR/
├── config/              # Central project configuration, settings, routing
├── apps/
│   ├── core/           # Homepage, global context processors, navigation, static pages
│   ├── accounts/       # Custom user model (email-login), RBAC, customer addresses
│   ├── vendors/        # Vendor store profiles, onboarding, application approvals
│   ├── catalog/        # Categories, multi-image products, slug-based URLs
│   ├── inventory/      # SKU tracking, atomic stock deductions, movement auditing
│   ├── cart/           # Session & database-backed carts, atomic item modifications
│   ├── orders/         # Multi-vendor parent orders, item line prices, seller fulfillment
│   ├── payments/       # Razorpay checkout, signature verification, commissions, payouts
│   ├── reviews/        # Verified purchaser ratings, moderation, feedback loops
│   ├── wishlist/       # Customer wishlists, fast toggle, item moving
│   └── dashboard/      # Role-isolated portals (Customer, Vendor, Admin)
├── templates/          # Responsive Bootstrap 5 + Minimal Premium design
├── static/             # CSS design tokens, JavaScript modules, brand assets
├── media/              # Secure uploads for products, logos, and avatars
└── tests/              # Automated test suites for end-to-end workflows
```

## 3. Role-Based Access Control (RBAC)
- **Customer**: Browses catalog, manages wishlist/cart, places orders, manages addresses, tracks orders, reviews purchased products.
- **Vendor**: Manages store profile, creates/edits products, sets stock levels, fulfills assigned order items, monitors store commissions and sales analytics.
- **Admin**: Moderates catalog, approves/rejects vendor applications, inspects marketplace revenue, sets commissions.

## 4. Multi-Vendor Order & Fulfillment Isolation
When a customer checks out a shopping cart containing products from Vendor A and Vendor B:
1. One single parent `Order` is created to track the customer transaction, shipping address, and total amount.
2. Distinct `OrderItem` records store the exact purchase-time unit price, vendor reference, and quantity.
3. An individual `SellerFulfillment` record is created for each vendor.
4. When Vendor A logs into their dashboard, queries strictly filter by `vendor=request.user.vendor`. Vendor A can update the fulfillment status (Processing, Shipped, Delivered) and tracking information for their own items only, with zero visibility into Vendor B's items.

## 5. Security & Idempotency
- Passwords hashed using PBKDF2 with SHA256.
- Role checks enforced server-side through decorators and mixins (`@vendor_required`, `@admin_required`).
- Cart checkouts and stock deductions execute within `transaction.atomic()` with `select_for_update()` to prevent race conditions and negative inventory.
- Razorpay payments verify cryptographic HMAC-SHA256 signatures before confirming orders and updating database states.
