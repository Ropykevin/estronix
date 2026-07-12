# Docker VPS Deployment — Estronix

Deploy using **host PostgreSQL + Docker app + Nginx** on Ubuntu.

```
Internet → Nginx (:80/:443) → 127.0.0.1:APP_PORT → Docker (Gunicorn)
                                      ↓
                              PostgreSQL (host)
```

## Prerequisites

| Item | Requirement |
|------|-------------|
| VPS | Ubuntu 22.04+, 2 GB RAM recommended |
| Domain | DNS A record → VPS IP (`estronix.co.ke`) |
| Ports | 22, 80, 443 open |
| Software | Docker, Docker Compose, Git, Python 3 |

## One-time server packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin nginx postgresql postgresql-contrib \
  certbot python3-certbot-nginx git curl redis-server ufw

sudo usermod -aG docker $USER
# Log out and back in so docker group applies
```

## Step 1 — Clone the project on the VPS

```bash
cd ~
git clone <your-repo-url> ecommerce
cd ecommerce
```

## Step 2 — Configure `.env`

```bash
cp .env.example .env
nano .env
```

Required production values:

```env
FLASK_ENV=production
SECRET_KEY=<64-char-random>
JWT_SECRET_KEY=<different-64-char-random>

POSTGRES_USER=estronix
POSTGRES_PASSWORD=<strong-db-password>
POSTGRES_DB=estronix
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DOMAIN=estronix.co.ke
APP_PORT=5060
PORT=5060
APP_URL=https://estronix.co.ke

BREVO_API_KEY=<your-brevo-api-key>
MAIL_DEFAULT_SENDER=info@estronix.co.ke
MAIL_CONSOLE=False

MPESA_ENV=production
MPESA_CONSUMER_KEY=...
MPESA_CONSUMER_SECRET=...
MPESA_SHORTCODE=...
MPESA_PASSKEY=...
MPESA_CALLBACK_TOKEN=<long-random-token>
MPESA_CALLBACK_URL=https://estronix.co.ke/payments/mpesa/callback?token=<same-token>

RATELIMIT_STORAGE_URI=redis://127.0.0.1:6379/0
SESSION_COOKIE_SECURE=True
ADMIN_INITIAL_PASSWORD=<strong-admin-password>
```

Generate secrets:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Important:** `APP_PORT` in `.env` must match what Nginx proxies to and what Docker uses.

Register `MPESA_CALLBACK_URL` in the Safaricom Daraja portal.

## Step 3 — One-time infrastructure setup

```bash
sudo bash mypostgresql.sh
```

This installs/configures:

- PostgreSQL database and user from `.env`
- Nginx reverse proxy: `http://DOMAIN` → `http://127.0.0.1:APP_PORT`
- Security headers on Nginx

Optional SSL in the same run:

```bash
sudo INSTALL_SSL=true bash mypostgresql.sh
```

Copy the printed `DATABASE_URL` into `.env` if you set it manually, or let Step 4 sync it.

## Step 4 — First app deploy

```bash
bash deployment.sh
```

This will:

1. Verify PostgreSQL login
2. Pull latest Git code
3. Write `.env.docker-runtime` with `DATABASE_URL`
4. Build and start the `claid` Docker container
5. Run `flask db upgrade` inside the container (via entrypoint)
6. Wait until the app responds on `APP_PORT`

## Step 5 — Initialize admin and sample data (first time only)

```bash
docker compose exec web flask init-db
docker compose exec web flask seed-data   # optional demo catalog
```

`init-db` uses `ADMIN_INITIAL_PASSWORD` from `.env`. Change the admin password after first login.

## Step 6 — Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

Do **not** expose `APP_PORT` or `5432` publicly — only Nginx should be reachable.

## Verify

```bash
curl -I http://127.0.0.1:${APP_PORT:-5060}/
curl -I https://estronix.co.ke
docker compose ps
docker compose logs -f web
```

- Storefront: `https://estronix.co.ke`
- Admin: `https://estronix.co.ke/admin`

## Updating after code changes

```bash
cd ~/ecommerce
git pull
bash deployment.sh
```

## Troubleshooting

| Problem | Command / fix |
|---------|----------------|
| Postgres login failed | `sudo bash scripts/reset_claid_db_user.sh` then `bash deployment.sh` |
| Container crash-loop | `docker compose logs --tail=100 web` |
| Port mismatch | Align `APP_PORT` in `.env`, `docker-compose.yml`, and Nginx |
| Redis rate limits | `sudo systemctl enable redis-server && sudo systemctl start redis-server` |
| Weak startup error | Ensure `SECRET_KEY` ≥ 32 chars and `MPESA_CALLBACK_TOKEN` is set |

## Architecture notes

- **Container name:** `claid`
- **Network:** `host` (container shares VPS network; DB at `127.0.0.1`)
- **Uploads:** Docker volume `uploads_data`
- **Do not use** `python run.py` in production — Docker runs Gunicorn via `wsgi.py`
