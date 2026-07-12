# Estronix — Electronics E-Commerce Platform

Production-ready Flask e-commerce platform for selling electronic products online, with M-Pesa payments, admin dashboard, and PostgreSQL.

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Browser   │────▶│  Nginx/Gunicorn│────▶│  Flask App      │
│  Bootstrap  │     │  (Production)  │     │  (Blueprints)   │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────┐
                    ▼                              ▼                  ▼
             ┌────────────┐               ┌─────────────┐    ┌──────────────┐
             │ PostgreSQL │               │ M-Pesa API  │    │ SMTP (Mail)  │
             └────────────┘               └─────────────┘    └──────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Application Factory** | Enables multiple configs (dev/test/prod) and clean testing |
| **Blueprint Modules** | Separates auth, products, cart, orders, payments, admin concerns |
| **Service Layer** | Business logic isolated from routes (CartService, OrderService, MpesaService) |
| **PostgreSQL + SQLAlchemy** | Relational integrity, enums, and production scalability |
| **Flask-Login + RBAC** | Session auth with role-based admin/customer access |
| **JWT Extension** | Pre-configured for future REST API expansion |
| **Guest + Auth Carts** | Session cart for guests, DB cart for logged-in users with merge on login |

## Project Structure

```
ecommerce/
├── app/
│   ├── auth/           # Registration, login, password reset, email verification
│   ├── admin/          # Dashboard, product/category/order management
│   ├── products/       # Catalog, search, filters, product detail
│   ├── cart/           # Add/update/remove cart items
│   ├── orders/         # Checkout, order history, invoices
│   ├── payments/       # M-Pesa STK Push & callback
│   ├── customers/      # Profile, addresses, order tracking
│   ├── models/         # SQLAlchemy ORM models
│   ├── services/       # Business logic layer
│   ├── templates/      # Jinja2 HTML templates
│   ├── static/         # CSS, JS, images
│   └── utils/          # Helpers, decorators, sanitization
├── config/             # Environment configurations
├── migrations/         # Flask-Migrate database migrations
├── tests/              # Pytest test suite
├── docs/               # Extended documentation
├── requirements.txt
├── .env.example
└── run.py
```

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- pip / virtualenv

### Installation

```bash
cd ecommerce
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database and M-Pesa credentials
```

### Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE USER estronix_user WITH PASSWORD 'estronix_pass';"
psql -U postgres -c "CREATE DATABASE estronix_db OWNER estronix_user;"

# Initialize Flask-Migrate
set FLASK_APP=run.py          # Windows
export FLASK_APP=run.py       # Linux

flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Seed roles, admin user, and sample data
flask init-db
flask seed-data
```

**Default admin credentials:** `admin@estronix.com` / `Admin@123` (change immediately in production)

### Run Development Server

```bash
python run.py
```

Visit http://localhost:5000

### Run Tests

```bash
pytest -v
```

## Features

- **Authentication** — Register, login, email verification, password reset, RBAC
- **Products** — CRUD, categories (nested), search, filters, pagination, SEO slugs
- **Cart** — Guest session cart + persistent user cart with merge
- **Checkout** — Shipping details, VAT, M-Pesa STK Push, cash on delivery
- **Orders** — Status tracking (Pending → Paid → Processing → Shipped → Delivered)
- **Admin Dashboard** — Sales metrics, low stock alerts, reports with charts
- **M-Pesa** — Safaricom Daraja STK Push, callback verification, payment logging
- **SEO** — Dynamic meta tags, Open Graph, XML sitemap, robots.txt
- **Security** — CSRF, password hashing, rate limiting, input sanitization, env-based secrets

## Documentation

| Document | Description |
|----------|-------------|
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Detailed installation guide |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Ubuntu + Nginx + Gunicorn + SSL |
| [docs/DATABASE.md](docs/DATABASE.md) | Schema and ER diagram |
| [docs/API.md](docs/API.md) | API endpoints (current + future JWT) |

## Environment Variables

See `.env.example` for all configuration options. **Never commit `.env` or hardcode secrets.**

## License

Proprietary — Estronix Platform
