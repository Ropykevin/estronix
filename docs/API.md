# API Documentation

## Current Web Routes

The platform currently serves HTML via Flask blueprints. Key URL patterns:

### Public

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page |
| GET | `/products/` | Product listing with search/filters |
| GET | `/products/<slug>` | Product detail |
| GET | `/products/category/<slug>` | Category products |
| GET | `/cart/` | View cart |
| POST | `/cart/add/<product_id>` | Add to cart |
| GET | `/robots.txt` | SEO robots file |
| GET | `/sitemap.xml` | XML sitemap |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/auth/register` | Customer registration |
| GET/POST | `/auth/login` | Login |
| GET | `/auth/logout` | Logout |
| GET | `/auth/verify/<token>` | Email verification |
| GET/POST | `/auth/forgot-password` | Password reset request |
| GET/POST | `/auth/reset-password/<token>` | Set new password |

### Customer (Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/account/` | Customer dashboard |
| GET | `/account/orders` | Order history |
| GET/POST | `/orders/checkout` | Checkout |
| GET | `/orders/<order_number>` | Order detail |
| GET | `/orders/<order_number>/invoice` | Printable invoice |

### Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payments/mpesa/callback` | M-Pesa STK webhook (CSRF exempt) |
| GET | `/payments/mpesa/status/<checkout_request_id>` | Query payment status |

### Admin (Admin Role Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/` | Dashboard |
| GET/POST | `/admin/products/create` | Create product |
| GET/POST | `/admin/products/<id>/edit` | Edit product |
| GET/POST | `/admin/orders/<id>` | Manage order |
| GET | `/admin/inventory` | Inventory report |
| GET | `/admin/reports` | Sales analytics |

## Future REST API (JWT)

JWT is pre-configured via `Flask-JWT-Extended`. Planned endpoints:

```
POST /api/v1/auth/login          → { access_token, refresh_token }
POST /api/v1/auth/refresh        → { access_token }
GET  /api/v1/products            → JSON product list
GET  /api/v1/products/<slug>     → JSON product detail
GET  /api/v1/cart                → Cart JSON
POST /api/v1/orders              → Create order
GET  /api/v1/orders/<number>     → Order detail
```

### JWT Configuration

```python
# config/settings.py
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
```

### Example Future Usage

```python
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    # Validate credentials...
    token = create_access_token(identity=user.id)
    return jsonify(access_token=token)

@api_bp.route("/products", methods=["GET"])
@jwt_required()
def api_products():
    # Return JSON product list
    pass
```

## M-Pesa Callback Payload

Safaricom sends POST JSON to `/payments/mpesa/callback`:

```json
{
  "Body": {
    "stkCallback": {
      "CheckoutRequestID": "...",
      "ResultCode": 0,
      "ResultDesc": "Success",
      "CallbackMetadata": {
        "Item": [
          {"Name": "Amount", "Value": 1500},
          {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"}
        ]
      }
    }
  }
}
```

## Rate Limits

| Route | Limit |
|-------|-------|
| Global default | 200/day, 50/hour |
| `/auth/register` | 10/hour |
| `/auth/login` | 20/hour |
| `/auth/forgot-password` | 5/hour |
