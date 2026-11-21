# Aura Luxe Development Roadmap & Execution Stages

## Stage 1: Environment & Architecture Foundations (COMPLETED)
- Directory layout: apps, templates, static, media, tests, docs
- Settings, WSGI, ASGI, requirements.txt, .gitignore, .env configuration
- PostgreSQL readiness and connection handlers

## Stage 2: Custom User Authentication & Roles (PHASE 2)
- Custom User model (`accounts.User`) with email primary identity
- User roles: CUSTOMER, VENDOR, ADMIN
- Customer Address model for shipping and billing
- Registration, login, logout, password change, address management
- Permission decorators: `@vendor_required`, `@admin_required`, `@customer_required`

## Stage 3: Vendor Onboarding & Store Engine (PHASE 3)
- Vendor Application submission workflow
- Administrator approval / rejection / suspension workflows
- Vendor Store model with custom slug, logo, banner, commission overrides
- Storefront public views: `/vendors/<slug>/`

## Stage 4: Product Catalog, Multi-Images & Inventory (PHASE 4)
- Category model with hierarchical parents and slugs
- Product model with vendor relationship, pricing, compare-at pricing, and SKU
- Multi-image upload and feature image designation
- Inventory model with low-stock alerts
- StockMovement audit ledger tracking restocks and sale deductions

## Stage 5: Premium Minimal Luxury Frontend (PHASE 5)
- Color Palette: #F7F5F0 background, #20211F text, #B69B75 gold accent
- Base template, reusable navbar, mega-menu, footer, toast alerts, pagination
- Modern Homepage with hero slider, featured collections, new arrivals, vendor spotlights
- Product listing with multi-faceted filtering (category, price range, stock status, sorting)
- Product detail page with image gallery, seller badge, reviews, add-to-cart/wishlist

## Stage 6: Shopping Cart, Wishlist & Addresses (PHASE 6)
- Database & session synchronized shopping cart
- AJAX and standard quantity increment/decrement/removal
- Stock availability pre-check
- Wishlist save/toggle and move-to-cart workflows
- Delivery address selection and creation

## Stage 7: Multi-Vendor Orders & Seller Fulfillment (PHASE 7)
- Multi-vendor checkout with atomic database transactions (`select_for_update`)
- Parent Order creation with unique human-readable tracking number
- OrderItem records preserving exact purchase-time unit prices and seller assignments
- Isolated SellerFulfillment records for seller-specific dispatch and tracking updates

## Stage 8: Payments, Commissions & Payouts (PHASE 8)
- Razorpay test-mode client integration
- Secure server-side order generation and signature verification (HMAC-SHA256)
- Webhook endpoints and payment failure/cancellation handlers
- Automated commission calculation per seller item
- Seller payout ledger records

## Stage 9: Role Dashboards (PHASE 9)
- Customer Dashboard: Profile, addresses, order history, track order, wishlist, reviews
- Vendor Dashboard: Sales KPIs, revenue, order fulfillment, product catalog manager, store settings
- Admin Dashboard: Platform GMV, total commissions, vendor moderation, catalog controls

## Stage 10: Reviews, Automated Tests & Verification (PHASE 10)
- Verified purchaser reviews with rating averages
- Comprehensive Django automated test suite covering all critical workflows
- GitHub Desktop documentation and final delivery report
