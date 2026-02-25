from .base import *
import os

DEBUG = False

env_allowed_hosts = [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]
if env_allowed_hosts:
	ALLOWED_HOSTS = env_allowed_hosts
elif not ALLOWED_HOSTS:
	ALLOWED_HOSTS = ['jhrmp.jambasimaging.com', 'localhost', '127.0.0.1']

if not CSRF_TRUSTED_ORIGINS:
	CSRF_TRUSTED_ORIGINS = ['https://jhrmp.jambasimaging.com']

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() in ('1', 'true', 'yes', 'on')
SECURE_HSTS_PRELOAD = os.getenv('DJANGO_SECURE_HSTS_PRELOAD', 'True').lower() in ('1', 'true', 'yes', 'on')
SECURE_SSL_REDIRECT = os.getenv('DJANGO_SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
