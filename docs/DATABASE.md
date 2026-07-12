# Database Documentation

## Entity Relationship Overview

```
roles ──1:N── users ──1:N── addresses
                │
                ├──1:1── carts ──1:N── cart_items ──N:1── products
                │
                └──1:N── orders ──1:N── order_items ──N:1── products
                          │
                          └──1:N── payments

categories ──1:N── products ──1:N── product_images
     │                  │
     │ (self-ref)       ├──1:N── product_specifications
     └── parent_id      └──1:N── reviews ──N:1── users
```

## Tables

### roles
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| name | VARCHAR(50) UNIQUE | `admin` or `customer` |
| description | VARCHAR(255) | Role description |

### users
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| email | VARCHAR(120) UNIQUE | Login email |
| username | VARCHAR(80) UNIQUE | Display username |
| password_hash | VARCHAR(256) | Werkzeug hashed password |
| role_id | INTEGER FK → roles | RBAC role |
| is_verified | BOOLEAN | Email verification status |

### categories
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| name | VARCHAR(100) | Category name |
| slug | VARCHAR(120) UNIQUE | SEO-friendly URL slug |
| parent_id | INTEGER FK → categories | Parent for nesting |

### products
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| name, slug, sku, brand | VARCHAR | Product identifiers |
| price, discount_price | NUMERIC(10,2) | Pricing |
| stock_quantity | INTEGER | Inventory count |
| status | ENUM | active, draft, out_of_stock, discontinued |
| category_id | INTEGER FK → categories | Product category |
| meta_title, meta_description | VARCHAR | SEO fields |

### orders
| Column | Type | Description |
|--------|------|-------------|
| order_number | VARCHAR(36) UNIQUE | e.g. EST-A1B2C3D4E5F6 |
| status | ENUM | pending → paid → processing → shipped → delivered / cancelled |
| subtotal, shipping_cost, tax_amount, total_amount | NUMERIC | Order totals |

### payments
| Column | Type | Description |
|--------|------|-------------|
| method | ENUM | mpesa, cash_on_delivery |
| status | ENUM | pending, completed, failed, refunded |
| checkout_request_id | VARCHAR | M-Pesa STK reference |
| mpesa_receipt | VARCHAR | M-Pesa receipt number |

## Indexes

- `users.email`, `users.username` — login lookups
- `products.slug`, `products.sku`, `products.brand` — search and URL routing
- `categories.slug` — category pages
- `orders.order_number` — order tracking
- `payments.transaction_id`, `payments.checkout_request_id` — payment reconciliation

## Migration Commands

```bash
flask db migrate -m "Description of change"
flask db upgrade
flask db downgrade  # Rollback one revision
```
