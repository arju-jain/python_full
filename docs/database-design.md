# Aura Luxe Database Design & Schema Specification

## Database Engine
- **Production**: PostgreSQL 15+ via `psycopg`
- **Development/Testing Fallback**: SQLite

## Entity Relationship Overview

### 1. Accounts
- **`accounts_user`**:
  - `id`: BigAutoField (PK)
  - `email`: EmailField (unique, indexed, primary login username)
  - `first_name`, `last_name`: CharField
  - `role`: CharField (`CUSTOMER`, `VENDOR`, `ADMIN`)
  - `phone_number`: CharField
  - `is_active`, `is_staff`, `is_superuser`: BooleanField
  - `date_joined`, `updated_at`: DateTimeField
- **`accounts_address`**:
  - `id`: BigAutoField (PK)
  - `user`: ForeignKey(`accounts_user`, on_delete=CASCADE)
  - `address_type`: CharField (`SHIPPING`, `BILLING`)
  - `full_name`, `phone_number`: CharField
  - `street_address_1`, `street_address_2`: CharField
  - `city`, `state`, `postal_code`, `country`: CharField
  - `is_default`: BooleanField

### 2. Vendors
- **`vendors_vendor`**:
  - `id`: BigAutoField (PK)
  - `user`: OneToOneField(`accounts_user`, on_delete=CASCADE)
  - `store_name`: CharField (unique)
  - `slug`: SlugField (unique)
  - `description`: TextField
  - `logo`: ImageField
  - `banner`: ImageField
  - `contact_email`, `phone_number`: CharField
  - `commission_rate`: DecimalField (default 10.00%)
  - `status`: CharField (`PENDING`, `APPROVED`, `REJECTED`, `SUSPENDED`)
  - `created_at`, `updated_at`: DateTimeField
- **`vendors_vendorapplication`**:
  - `id`: BigAutoField (PK)
  - `user`: OneToOneField(`accounts_user`, on_delete=CASCADE)
  - `store_name`: CharField
  - `business_details`, `tax_id`: CharField / TextField
  - `status`: CharField (`PENDING`, `APPROVED`, `REJECTED`)
  - `reviewed_by`: ForeignKey(`accounts_user`, null=True)
  - `review_notes`: TextField
  - `created_at`, `reviewed_at`: DateTimeField

### 3. Catalog
- **`catalog_category`**:
  - `id`: BigAutoField (PK)
  - `name`: CharField
  - `slug`: SlugField (unique)
  - `description`: TextField
  - `image`: ImageField
  - `parent`: ForeignKey('self', null=True, blank=True)
  - `is_active`: BooleanField
- **`catalog_product`**:
  - `id`: BigAutoField (PK)
  - `vendor`: ForeignKey(`vendors_vendor`, on_delete=CASCADE)
  - `category`: ForeignKey(`catalog_category`, on_delete=SET_NULL)
  - `title`: CharField
  - `slug`: SlugField (unique)
  - `description`: TextField
  - `price`: DecimalField(max_digits=12, decimal_places=2)
  - `compare_at_price`: DecimalField(null=True, blank=True)
  - `sku`: CharField (unique)
  - `is_active`: BooleanField
  - `is_featured`: BooleanField
  - `created_at`, `updated_at`: DateTimeField
- **`catalog_productimage`**:
  - `id`: BigAutoField (PK)
  - `product`: ForeignKey(`catalog_product`, on_delete=CASCADE, related_name='images')
  - `image`: ImageField
  - `alt_text`: CharField
  - `is_primary`: BooleanField
  - `sort_order`: PositiveIntegerField

### 4. Inventory
- **`inventory_inventory`**:
  - `id`: BigAutoField (PK)
  - `product`: OneToOneField(`catalog_product`, on_delete=CASCADE, related_name='inventory')
  - `quantity`: PositiveIntegerField(default=0)
  - `low_stock_threshold`: PositiveIntegerField(default=5)
  - `is_in_stock`: BooleanField
  - `updated_at`: DateTimeField
- **`inventory_stockmovement`**:
  - `id`: BigAutoField (PK)
  - `inventory`: ForeignKey(`inventory_inventory`, on_delete=CASCADE)
  - `movement_type`: CharField (`PURCHASE_RESTOCK`, `SALE_DEDUCTION`, `REFUND_RESTOCK`, `ADJUSTMENT`)
  - `quantity_change`: IntegerField
  - `balance_after`: PositiveIntegerField
  - `reference`: CharField
  - `created_at`: DateTimeField

### 5. Cart & Wishlist
- **`cart_cart`**:
  - `id`: BigAutoField (PK)
  - `user`: ForeignKey(`accounts_user`, null=True, blank=True)
  - `session_key`: CharField (null=True, blank=True)
  - `created_at`, `updated_at`: DateTimeField
- **`cart_cartitem`**:
  - `cart`: ForeignKey(`cart_cart`, on_delete=CASCADE, related_name='items')
  - `product`: ForeignKey(`catalog_product`, on_delete=CASCADE)
  - `quantity`: PositiveIntegerField(default=1)
  - UniqueConstraint(`cart`, `product`)
- **`wishlist_wishlist`** & **`wishlist_wishlistitem`**:
  - Customer saved product references.

### 6. Orders & Seller Fulfillment
- **`orders_order`**:
  - `id`: BigAutoField (PK)
  - `order_number`: CharField(unique=True)
  - `customer`: ForeignKey(`accounts_user`, on_delete=CASCADE)
  - `status`: CharField (`PENDING`, `CONFIRMED`, `PROCESSING`, `COMPLETED`, `CANCELLED`)
  - `total_amount`: DecimalField
  - `shipping_fee`: DecimalField
  - `shipping_full_name`, `shipping_phone`, `shipping_address`, `shipping_city`, `shipping_postal_code`: CharField
  - `created_at`, `updated_at`: DateTimeField
- **`orders_orderitem`**:
  - `id`: BigAutoField (PK)
  - `order`: ForeignKey(`orders_order`, on_delete=CASCADE, related_name='items')
  - `product`: ForeignKey(`catalog_product`, on_delete=PROTECT)
  - `vendor`: ForeignKey(`vendors_vendor`, on_delete=PROTECT)
  - `quantity`: PositiveIntegerField
  - `unit_price`: DecimalField (snapshot price)
  - `subtotal`: DecimalField
- **`orders_sellerfulfillment`**:
  - `id`: BigAutoField (PK)
  - `order`: ForeignKey(`orders_order`, on_delete=CASCADE)
  - `vendor`: ForeignKey(`vendors_vendor`, on_delete=CASCADE)
  - `status`: CharField (`PENDING`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`)
  - `tracking_number`: CharField
  - `shipping_carrier`: CharField
  - `dispatched_at`, `delivered_at`: DateTimeField
  - UniqueConstraint(`order`, `vendor`)

### 7. Payments, Commissions & Payouts
- **`payments_payment`**:
  - `order`: OneToOneField(`orders_order`)
  - `transaction_id`: CharField
  - `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`: CharField
  - `amount`: DecimalField
  - `status`: CharField (`PENDING`, `COMPLETED`, `FAILED`, `REFUNDED`)
- **`payments_commission`**:
  - `order_item`: OneToOneField(`orders_orderitem`)
  - `vendor`: ForeignKey(`vendors_vendor`)
  - `order`: ForeignKey(`orders_order`)
  - `gross_amount`: DecimalField
  - `commission_rate`: DecimalField
  - `commission_amount`: DecimalField
  - `net_seller_amount`: DecimalField
- **`payments_sellerpayout`**:
  - `vendor`: ForeignKey(`vendors_vendor`)
  - `amount`: DecimalField
  - `status`: CharField (`PENDING`, `PAID`, `CANCELLED`)
  - `reference_id`: CharField
  - `payout_date`: DateTimeField

### 8. Reviews
- **`reviews_review`**:
  - `product`: ForeignKey(`catalog_product`, related_name='reviews')
  - `customer`: ForeignKey(`accounts_user`)
  - `rating`: PositiveSmallIntegerField (1 to 5)
  - `title`: CharField
  - `comment`: TextField
  - `is_verified_purchase`: BooleanField
  - `is_approved`: BooleanField
  - UniqueConstraint(`product`, `customer`)
