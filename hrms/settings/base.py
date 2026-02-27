from pathlib import Path
import os
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
import secrets
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / '.env', override=True)


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ('1', 'true', 'yes', 'on')


def env_bool_optional(name: str):
    """Return True/False if env var is set, else None."""
    if name not in os.environ:
        return None
    return os.getenv(name, '').lower() in ('1', 'true', 'yes', 'on')

DEBUG = env_bool('DJANGO_DEBUG', False)
RUNNING_TESTS = 'test' in sys.argv

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '').strip()
ALLOW_INSECURE_SECRET_KEY = env_bool('DJANGO_ALLOW_INSECURE_SECRET_KEY', False)
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-dev-key'
    else:
        # In production, prefer an environment-provided secret key, but fall back to a
        # stable, file-backed key to avoid accidental outages.
        secret_key_path = BASE_DIR / '.django_secret_key'
        try:
            if secret_key_path.exists():
                SECRET_KEY = secret_key_path.read_text(encoding='utf-8').strip()
            else:
                SECRET_KEY = secrets.token_urlsafe(64)
                secret_key_path.write_text(SECRET_KEY, encoding='utf-8')
        except OSError:
            if not ALLOW_INSECURE_SECRET_KEY:
                raise ImproperlyConfigured('DJANGO_SECRET_KEY is required when DJANGO_DEBUG is False')

if not DEBUG and not ALLOW_INSECURE_SECRET_KEY:
    if SECRET_KEY.startswith('django-insecure-') or len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be a long, random value (>=50 chars) in production')

ALLOWED_HOSTS = [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'accounts',
    'employees',
    'leave_mgmt',
    'payroll',
    'attendance',
    'performance',
    'reports',
    'audit',
    'noticeboard',
    'tasks',
    'calendar_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'core.middleware.ActiveUserRequiredMiddleware',
    'core.middleware.PublicAccessCodeMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'hrms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.org_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'hrms.wsgi.application'
ASGI_APPLICATION = 'hrms.asgi.application'

DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.getenv('DB_NAME', 'hrms_db'),
            'USER': os.getenv('DB_USER', 'hrms_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('DJANGO_TIME_ZONE', 'Africa/Kampala')
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = Path(os.getenv('DJANGO_STATIC_ROOT', str(BASE_DIR / 'staticfiles')))
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = os.getenv('DJANGO_STATICFILES_STORAGE', 'whitenoise.storage.CompressedManifestStaticFilesStorage')

if RUNNING_TESTS:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.getenv('DJANGO_MEDIA_ROOT', str(BASE_DIR / 'media')))

# Upload guardrails (DoS protection + consistent form validation).
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE', str(25 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('DJANGO_FILE_UPLOAD_MAX_MEMORY_SIZE', str(5 * 1024 * 1024)))

MAX_DOCUMENT_UPLOAD_SIZE_BYTES = int(os.getenv('DJANGO_MAX_DOCUMENT_UPLOAD_SIZE_BYTES', str(10 * 1024 * 1024)))
MAX_PHOTO_UPLOAD_SIZE_BYTES = int(os.getenv('DJANGO_MAX_PHOTO_UPLOAD_SIZE_BYTES', str(5 * 1024 * 1024)))
MAX_BRANDING_UPLOAD_SIZE_BYTES = int(os.getenv('DJANGO_MAX_BRANDING_UPLOAD_SIZE_BYTES', str(2 * 1024 * 1024)))

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', os.getenv('MAIL_MAILER', 'django.core.mail.backends.smtp.EmailBackend'))
EMAIL_HOST = os.getenv('EMAIL_HOST', os.getenv('MAIL_HOST', 'localhost'))
EMAIL_PORT = int(os.getenv('EMAIL_PORT', os.getenv('MAIL_PORT', '25')))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', os.getenv('MAIL_USERNAME', ''))
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', os.getenv('MAIL_PASSWORD', ''))

# Encryption selection precedence:
# 1) explicit EMAIL_USE_TLS / EMAIL_USE_SSL if present
# 2) MAIL_ENCRYPTION only if explicit flags are not provided
_tls = env_bool_optional('EMAIL_USE_TLS')
_ssl = env_bool_optional('EMAIL_USE_SSL')
if _tls is None and _ssl is None:
    _mail_encryption = os.getenv('MAIL_ENCRYPTION', '').lower().strip()
    EMAIL_USE_TLS = _mail_encryption == 'tls'
    EMAIL_USE_SSL = _mail_encryption == 'ssl'
else:
    EMAIL_USE_TLS = bool(_tls)
    EMAIL_USE_SSL = bool(_ssl)

# Guard against misconfiguration (some environments set both unexpectedly).
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    # Prefer SSL on 465, otherwise prefer TLS.
    if EMAIL_PORT == 465:
        EMAIL_USE_TLS = False
    else:
        EMAIL_USE_SSL = False

EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '30'))

# Inbound email (IMAP) settings for portal inbox polling.
IMAP_HOST = os.getenv('IMAP_HOST', EMAIL_HOST)
IMAP_PORT = int(os.getenv('IMAP_PORT', '993'))
IMAP_USER = os.getenv('IMAP_USER', EMAIL_HOST_USER)
IMAP_PASSWORD = os.getenv('IMAP_PASSWORD', EMAIL_HOST_PASSWORD)
IMAP_USE_SSL = env_bool('IMAP_USE_SSL', True)
IMAP_MAILBOX = os.getenv('IMAP_MAILBOX', 'INBOX')
IMAP_MAX_FETCH = int(os.getenv('IMAP_MAX_FETCH', '50'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:public_home'

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv('DJANGO_SESSION_COOKIE_SAMESITE', 'Lax')
CSRF_COOKIE_SAMESITE = os.getenv('DJANGO_CSRF_COOKIE_SAMESITE', 'Lax')
X_FRAME_OPTIONS = 'DENY'

SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', (not DEBUG) and (not RUNNING_TESTS))
SESSION_COOKIE_SECURE = env_bool('DJANGO_SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = env_bool('DJANGO_CSRF_COOKIE_SECURE', not DEBUG)

SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '0' if (DEBUG or RUNNING_TESTS) else '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', (not DEBUG) and (not RUNNING_TESTS))
SECURE_HSTS_PRELOAD = env_bool('DJANGO_SECURE_HSTS_PRELOAD', False)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = os.getenv('DJANGO_SECURE_REFERRER_POLICY', 'same-origin')
SECURE_CROSS_ORIGIN_OPENER_POLICY = os.getenv('DJANGO_SECURE_COOP', 'same-origin')

if RUNNING_TESTS:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False

if env_bool('DJANGO_SECURE_PROXY_SSL_HEADER', True):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
