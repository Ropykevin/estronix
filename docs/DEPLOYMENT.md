# VPS Deployment — Ubuntu + Nginx + Gunicorn + PostgreSQL

Deploy Estronix to a Linux VPS using the files in `deploy/vps/`.

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| VPS | Ubuntu 22.04 or 24.04, 1 GB RAM minimum (2 GB recommended) |
| Domain | DNS A record pointing to the VPS public IP |
| Git repo | Code pushed to GitHub/GitLab/Bitbucket |
| Ports | 22 (SSH), 80 and 443 open |

## Files

```
deploy/vps/
├── setup-vps.sh           # One-time server setup (run as root)
├── deploy.sh              # Pull updates and restart (run as estronix)
├── backup-db.sh           # PostgreSQL backup script
├── estronix.service       # systemd unit for Gunicorn
├── gunicorn.conf.py       # Gunicorn workers, socket, timeouts
├── nginx-estronix.conf    # Nginx reverse proxy + static files
└── env.production.example # Production .env template
```

## Quick deploy (automated)

SSH into your VPS as root, then run:

```bash
# Clone the repo first (or upload files), then:
cd /path/to/ecommerce

export DOMAIN=yourdomain.com
export REPO_URL=https://github.com/your-org/ecommerce.git
export DB_PASSWORD='your-strong-db-password'

sudo bash deploy/vps/setup-vps.sh
```

The script will:

1. Install Python, Nginx, PostgreSQL, Certbot, Git
2. Create the `estronix` system user
3. Clone the repo to `/home/estronix/ecommerce`
4. Create a Python virtualenv and install dependencies
5. Create `.env` from the production template
6. Run `flask db upgrade` and `flask init-db`
7. Enable the Gunicorn systemd service
8. Configure Nginx and request an SSL certificate
9. Enable the firewall (SSH + HTTP/HTTPS)

## Manual step-by-step

### 1. System packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip nginx postgresql postgresql-contrib certbot python3-certbot-nginx git ufw
```

### 2. PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE USER estronix_user WITH PASSWORD 'strong_password_here';
CREATE DATABASE estronix_db OWNER estronix_user;
\q
```

### 3. Application user and code

```bash
sudo adduser --disabled-password estronix
sudo usermod -aG www-data estronix
sudo su - estronix

git clone <your-repo-url> ~/ecommerce
cd ~/ecommerce
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Environment file

```bash
cp deploy/vps/env.production.example .env
nano .env
```

Required changes:

- `SECRET_KEY` and `JWT_SECRET_KEY` — long random strings
- `DATABASE_URL` — match your PostgreSQL password
- `APP_URL` — `https://yourdomain.com`
- `BREVO_API_KEY` — Brevo API key for order/verification emails
- `MPESA_*` — production Daraja credentials
- `MPESA_CALLBACK_URL` — `https://yourdomain.com/payments/mpesa/callback`

Generate a secret key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Uploads directory

```bash
mkdir -p app/static/uploads
chmod 775 app/static/uploads
```

### 6. Database migration

```bash
export FLASK_APP=run.py
flask db upgrade
flask init-db
# Optional sample catalog:
flask seed-data
```

Default admin: `admin@estronix.com` / `Admin@123` — change immediately after first login.

### 7. Gunicorn (systemd)

```bash
exit   # back to root/sudo user
sudo cp /home/estronix/ecommerce/deploy/vps/estronix.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable estronix
sudo systemctl start estronix
sudo systemctl status estronix
```

### 8. Nginx

Replace `YOUR_DOMAIN` in the config, then install:

```bash
sudo cp /home/estronix/ecommerce/deploy/vps/nginx-estronix.conf /etc/nginx/sites-available/estronix
sudo sed -i 's/YOUR_DOMAIN/yourdomain.com/g' /etc/nginx/sites-available/estronix
sudo ln -sf /etc/nginx/sites-available/estronix /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 10. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Updating the live site

On the VPS, as the `estronix` user:

```bash
cd ~/ecommerce
bash deploy/vps/deploy.sh
```

Or manually:

```bash
cd ~/ecommerce
git pull
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart estronix
```

## Database backups

```bash
# One-off backup
bash deploy/vps/backup-db.sh

# Daily at 2 AM (add to root crontab: sudo crontab -e)
0 2 * * * /home/estronix/ecommerce/deploy/vps/backup-db.sh
```

## Useful commands

```bash
# App logs
sudo journalctl -u estronix -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Restart app
sudo systemctl restart estronix

# Check socket permissions
ls -la /home/estronix/ecommerce/estronix.sock
```

## Post-deployment checklist

- [ ] Change default admin password
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Set `SESSION_COOKIE_SECURE=True` in `.env`
- [ ] Set `MAIL_CONSOLE=False` in production
- [ ] Configure production M-Pesa credentials
- [ ] Confirm M-Pesa callback URL is publicly reachable
- [ ] Point domain DNS to the VPS IP
- [ ] Set up daily database backups
- [ ] Test checkout, email, and WhatsApp order links

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 502 Bad Gateway | `sudo systemctl status estronix` — check Gunicorn is running and socket exists |
| Permission denied on uploads | `sudo chown -R estronix:www-data app/static/uploads && chmod -R 775 app/static/uploads` |
| CSRF or session issues behind HTTPS | Ensure Nginx sends `X-Forwarded-Proto` (included in `nginx-estronix.conf`) |
| Upload too large | Nginx `client_max_body_size 64M` is set; match `MAX_CONTENT_LENGTH_MB=64` in `.env` |
| Certbot fails | DNS must point to the server before running certbot |
