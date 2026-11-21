# AURA LUXE — Premium Multi-Vendor E-Commerce Marketplace

Aura Luxe is a modular multi-vendor luxury marketplace engineered with **Python**, **Django 5**, and **PostgreSQL**. Inspired by luxury commerce, it unites independent master artisans, fine horology manufactures, and high jewelry boutiques with global collectors and discerning patrons.

---

## 1. Architectural Highlights

- **Modular Monolith**: Separated domain apps (`accounts`, `vendors`, `catalog`, `inventory`, `cart`, `orders`, `payments`, `reviews`, `wishlist`, `dashboard`, `core`).
- **Unified Multi-Vendor Cart & Single Checkout**: Customers acquire items from multiple distinct merchants in a single shopping bag and single transaction.
- **Strict Seller Order Isolation**: The platform automatically partitions checkout items into vendor-specific `SellerFulfillment` records. Sellers only see and fulfill their own order items.
- **Race-Condition Protected Inventory**: Atomic database row-locking (`select_for_update()`) prevents over-selling or negative inventory during concurrent checkouts.
- **Cryptographic Payment Gateway**: Server-side Razorpay test integration verifying HMAC-SHA256 signatures before confirming orders or crediting seller commissions.
- **Automated Marketplace Commission Calculation**: Configurable platform commission automatically computed per line item upon payment confirmation.
- **Minimal Premium Luxury UI/UX**: Original design using an understated aesthetic palette (`#F7F5F0` background, `#20211F` text, `#B69B75` gold accents) with responsive Bootstrap 5 and Bootstrap Icons.

---

## 2. Technology Stack

- **Backend**: Python 3.11+, Django 5.x, Django ORM, Django Authentication, Django Forms
- **Database**: PostgreSQL (production), Psycopg driver, SQLite (dev/test fallback)
- **Frontend**: Django Templates, HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, JavaScript ES6
- **Payment**: Razorpay (Test Mode) with server signature verification & webhooks
- **Image Processing**: Pillow

---

## 3. Directory Layout

```
MULTIVENDOR/
├── manage.py
├── requirements.txt
├── .env.example
├── .env
├── .gitignore
├── README.md
│
├── config/                  # Django project root configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                    # Modular domain applications
│   ├── core/               # Homepage, global context processors, static pages
│   ├── accounts/           # Custom User (email-login), RBAC, Address book
│   ├── vendors/            # Onboarding applications, Store profiles, Approvals
│   ├── catalog/            # Categories, Products, Image galleries
│   ├── inventory/          # Stock tracking, Audit movement ledger
│   ├── cart/               # Session & user carts, AJAX quantity engine
│   ├── orders/             # Multi-vendor orders, SellerFulfillment isolation
│   ├── payments/           # Razorpay client, HMAC verification, Commissions
│   ├── reviews/            # Verified purchaser ratings & appraisals
│   ├── wishlist/           # Curated customer saved items
│   └── dashboard/          # Customer, Vendor, and Administrator cockpits
│
├── templates/               # Minimal Premium luxury template tree
├── static/                  # CSS tokens, components, dashboards, and JS modules
├── media/                   # User and merchant upload storage
├── docs/                    # Architecture, Database Design, Roadmap
└── tests/                   # End-to-end integration and security test suites
```

---

## 4. Quick Start & Installation

### Prerequisites
- Python 3.11 or higher
- Git & GitHub Desktop (optional)
- PostgreSQL 14+ (or use built-in SQLite development fallback)

### Step 1: Clone or Navigate to the Workspace
```powershell
cd c:\Users\Student\Desktop\python_full
```

### Step 2: Configure Environment Variables
Create `.env` from `.env.example`:
```powershell
Copy-Item .env.example .env
```
Inside `.env`, verify your configurations:
```ini
DEBUG=True
SECRET_KEY=django-insecure-aura-luxe-premium-marketplace-key

# Database (PostgreSQL Production)
DB_ENGINE=postgresql
DB_NAME=multivendor_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432

# Or toggle SQLite for local offline testing:
USE_SQLITE=True

# Payment Gateway (Razorpay Test Keys)
RAZORPAY_KEY_ID=rzp_test_YourKey
RAZORPAY_KEY_SECRET=YourSecret
```

### Step 3: Run Database Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Seed Initial Marketplace Data
Run the custom seed command to populate demo categories, vendors, products with stock, customer accounts, and an active multi-vendor order:
```powershell
python manage.py seed_marketplace
```

### Pre-Configured Test Credentials:
- **Marketplace Administrator**:
  - Email: `admin@auraluxe.com`
  - Password: `Admin@12345`
  - URL: `/dashboard/admin-portal/` and `/admin/`
- **Merchant / Vendor 1 (Geneva Horlogerie)**:
  - Email: `horlogerie@auraluxe.com`
  - Password: `Vendor@12345`
  - URL: `/dashboard/vendor/`
- **Merchant / Vendor 2 (Atelier Florentine)**:
  - Email: `florentine@auraluxe.com`
  - Password: `Vendor@12345`
  - URL: `/dashboard/vendor/`
- **Customer / Patron**:
  - Email: `patron@auraluxe.com`
  - Password: `Patron@12345`
  - URL: `/dashboard/customer/`

### Step 5: Start the Development Server
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your web browser.

---

## 5. Running Automated Tests

Aura Luxe includes automated tests covering:
- Customer registration, login, logout
- Vendor application, approval, and store activation
- Product creation, inventory linking, and object-level ownership checks
- Product catalog search, category filtering, and price filters
- Cart addition and quantity updates
- Multi-vendor checkout, parent order creation, and isolated fulfillments
- Payment order generation, HMAC signature verification, and commissions
- Seller fulfillment status updates with tracking codes
- Role-based access control and unauthorized route prevention

To execute all tests:
```powershell
python manage.py test apps tests
```

---

## 6. GitHub Desktop Workflow

1. Open **GitHub Desktop**.
2. Click **File** > **Add Local Repository** (or press `Ctrl+O`).
3. Select this folder: `c:\Users\Student\Desktop\python_full`.
4. GitHub Desktop will read the `.git` repository and `.gitignore` automatically.
5. Create and switch to development branches:
   - `develop`
   - `feature/authentication`
   - `feature/vendors`
   - `feature/catalog`
   - `feature/cart`
   - `feature/orders`
   - `feature/payments`
   - `feature/dashboard`
6. Review changes and commit using descriptive summaries.
7. Push changes to remote origin only when ready.
