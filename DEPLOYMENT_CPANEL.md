# cPanel Deployment Guide (Django + Passenger)

This project is ready for cPanel deployment with Python App (Passenger/WSGI).

## 1) Prerequisites in cPanel

- Create a subdomain, for example: `hr.yourdomain.com`.
- In cPanel, create a Python App (Setup Python App):
  - Python version: 3.10+ (or the latest available compatible with Django 4.2)
  - Application root: folder containing `manage.py`
  - Application URL: your subdomain
  - Application startup file: `passenger_wsgi.py`
  - Application entry point: `application`

## 2) Upload code

Use either:
- cPanel Git Version Control (recommended), or
- File Manager upload/extract.

Ensure these are present in app root:
- `manage.py`
- `passenger_wsgi.py`
- `hrms/`
- `requirements.txt`

## 3) Install Python dependencies

From cPanel Terminal (inside app root), activate the app virtualenv and install:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This base requirements file is optimized for PostgreSQL deployments on cPanel.
If you deploy with MySQL, install `mysqlclient` only on servers that already have MySQL/MariaDB development libraries and `pkg-config` available.

## 4) Configure environment variables

Set environment variables in cPanel Python App configuration or in a local `.env` file.

This project auto-loads `.env` from the application root using `python-dotenv`, so you can keep production variables in `/home/jambasimaging26/human_resource_portal/.env`.

Minimum required values:

```env
DJANGO_SETTINGS_MODULE=hrms.settings.prod
DJANGO_SECRET_KEY=your-long-random-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=hr.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://hr.yourdomain.com
DJANGO_SECURE_PROXY_SSL_HEADER=True

DB_ENGINE=django.db.backends.postgresql
DB_NAME=hrms_db
DB_USER=hrms_user
DB_PASSWORD=strong-password
DB_HOST=localhost
DB_PORT=5432

DJANGO_SECURE_SSL_REDIRECT=True
```

For MySQL, set:
- `DB_ENGINE=django.db.backends.mysql`
- `DB_PORT=3306`

## 5) Database setup

- Create database and DB user in cPanel (MySQL/PostgreSQL Databases).
- Grant all privileges for the app database user.
- Run migrations:

```bash
python manage.py migrate
```

## 6) Static and media

Collect static files:

```bash
python manage.py collectstatic --noinput
```

Notes:
- Static files are collected into `staticfiles/`.
- User uploads go to `media/`.
- Ensure `media/` is writable by the app user.

## 7) Create admin account

```bash
python manage.py createsuperuser
```

## 8) Restart and verify

- Restart app from cPanel Python App panel.
- Open your subdomain and verify:
  - Home page loads
  - `/admin/` opens
  - Static assets load (CSS/images)
  - Login works

## 9) Production hardening checklist

- `DJANGO_DEBUG=False`
- Strong `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS` set correctly
- HTTPS enabled on subdomain (SSL/TLS)
- DB credentials are not committed to Git
- `.env`, `db.sqlite3`, and `media/` remain untracked
- Regular database backups enabled in cPanel

## 10) Common troubleshooting

### 500 error after deploy
- Check cPanel app error logs.
- Confirm `DJANGO_SETTINGS_MODULE=hrms.settings.prod`.
- Confirm all env vars exist.
- Confirm migrations ran successfully.

### Static files not loading
- Re-run `python manage.py collectstatic --noinput`.
- Restart app.

### DB connection fails
- Verify engine/host/port/user/password.
- Confirm DB user has privileges.
- For MySQL, install `mysqlclient` only if your host provides required system packages (`pkg-config` + MySQL/MariaDB dev libs).

### App imports fail
- Confirm app root contains `manage.py` and `passenger_wsgi.py`.
- Reinstall dependencies in the same virtualenv used by cPanel Python App.
