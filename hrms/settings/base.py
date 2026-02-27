from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / '.env', override=True)


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ('1', 'true', 'yes', 'on')


def env_bool_optional(name: str):
    """Return True/False if env var is set, else None."""
    if name not in os.environ:
        return None
    return os.getenv(name, '').lower() in ('1', 'true', 'yes', 'on')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = env_bool('DJANGO_DEBUG', True)
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

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.getenv('DJANGO_MEDIA_ROOT', str(BASE_DIR / 'media')))

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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:public_home'

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

if env_bool('DJANGO_SECURE_PROXY_SSL_HEADER', True):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
