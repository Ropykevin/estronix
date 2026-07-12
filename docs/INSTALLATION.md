# Installation Guide

## System Requirements

| Component | Minimum Version |
|-----------|----------------|
| Python | 3.12 |
| PostgreSQL | 14 |
| pip | 23+ |

## Step-by-Step Setup

### 1. Clone and Enter Project

```bash
cd ecommerce
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
SECRET_KEY=<generate-a-64-char-random-string>
DATABASE_URL=postgresql://estronix_user:estronix_pass@localhost:5432/estronix_db
BREVO_API_KEY=your-brevo-api-key
MAIL_DEFAULT_SENDER=info@estronix.co.ke
MAIL_DEFAULT_SENDER_NAME=Estronix
MPESA_CONSUMER_KEY=your-key
MPESA_CONSUMER_SECRET=your-secret
MPESA_PASSKEY=your-passkey
MPESA_CALLBACK_URL=https://yourdomain.com/payments/mpesa/callback
```

Generate a secret key:

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. PostgreSQL Database

```sql
CREATE USER estronix_user WITH PASSWORD 'estronix_pass';
CREATE DATABASE estronix_db OWNER estronix_user;
GRANT ALL PRIVILEGES ON DATABASE estronix_db TO estronix_user;
```

### 6. Run Migrations

```bash
export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
flask init-db
flask seed-data
```

### 7. Start Application

```bash
python run.py
```

### 8. Verify Installation

- Home: http://localhost:5000
- Admin: http://localhost:5000/admin (login as admin)
- Products: http://localhost:5000/products/
- Sitemap: http://localhost:5000/sitemap.xml

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `psycopg2` install fails | Install PostgreSQL dev headers or use `psycopg2-binary` |
| Migration errors | Ensure `DATABASE_URL` is correct and DB exists |
| Email not sending | Configure Gmail App Password or SMTP provider |
| M-Pesa sandbox fails | Use Safaricom Daraja sandbox credentials |
