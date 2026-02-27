from .base import *
import os
import sys

DEBUG = False

RUNNING_TESTS = 'test' in sys.argv


def env_bool(name, default=False):
	return os.getenv(name, str(default)).lower() in ('1', 'true', 'yes', 'on')

env_allowed_hosts = [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]
if env_allowed_hosts:
	ALLOWED_HOSTS = env_allowed_hosts
elif not ALLOWED_HOSTS:
	ALLOWED_HOSTS = ['jhrmp.jambasimaging.com', 'localhost', '127.0.0.1']

if not CSRF_TRUSTED_ORIGINS:
	CSRF_TRUSTED_ORIGINS = ['https://jhrmp.jambasimaging.com']

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 0 if RUNNING_TESTS else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False if RUNNING_TESTS else env_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', True)
SECURE_HSTS_PRELOAD = False if RUNNING_TESTS else env_bool('DJANGO_SECURE_HSTS_PRELOAD', True)
SECURE_SSL_REDIRECT = False if RUNNING_TESTS else env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
SESSION_COOKIE_SECURE = False if RUNNING_TESTS else True
CSRF_COOKIE_SECURE = False if RUNNING_TESTS else True
