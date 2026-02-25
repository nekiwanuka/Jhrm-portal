# cPanel Subdomain Deployment (Passenger/WSGI)

## 1) Prepare subdomain
- Create a subdomain in cPanel (for example `hr.yourdomain.com`).
- Point document root to project directory.

## 2) Upload project
- Upload project files to cPanel via File Manager or Git.
- Create and activate virtual environment.

## 3) Install dependencies
- `pip install -r requirements.txt`

## 4) Configure environment
- Copy `.env.example` to `.env` and fill production values.
- Ensure `DJANGO_SETTINGS_MODULE=hrms.settings.prod`.

## 5) Configure Passenger/WSGI
- Use `passenger_wsgi.py` as startup file for Python app.
- Confirm app root and startup script path in cPanel Python App config.

## 6) Database
- Create PostgreSQL or MySQL database from cPanel.
- Apply credentials in environment variables.
- Run migrations:
  - `python manage.py migrate`

## 7) Static/media
- Collect static files:
  - `python manage.py collectstatic --noinput`
- Ensure `media/` is writable.

## 8) Security checklist
- `DEBUG=False`
- Set secure secret key
- Restrict `ALLOWED_HOSTS`
- Enable HTTPS at subdomain

## 9) Create admin user
- `python manage.py createsuperuser`

## 10) Restart app
- Restart Python app from cPanel panel.
