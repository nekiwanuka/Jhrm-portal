from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


class ActiveUserRequiredMiddleware:
    """Logs out suspended (is_active=False) users and blocks access."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and not user.is_active:
            logout(request)
            messages.error(request, 'Your account has been suspended. Contact HR for help.')
            return redirect(reverse('accounts:login'))
        return self.get_response(request)


class PublicAccessCodeMiddleware:
    """Requires an access code (stored in session) to view selected public pages."""

    SESSION_KEY = 'public_access_granted'
    SESSION_VERSION_KEY = 'public_access_granted_version'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Authenticated users bypass the public access code.
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return self.get_response(request)

        # Avoid interfering with static/media/admin endpoints.
        path = request.path or ''
        if path.startswith('/static/') or path.startswith('/media/') or path.startswith('/admin/'):
            return self.get_response(request)

        # Allow the access code entry page itself.
        try:
            access_url = reverse('core:public_access')
        except Exception:
            access_url = '/access/'
        if path.startswith(access_url):
            return self.get_response(request)

        # Lazy import to avoid app-loading issues.
        from core.models import BrandingSettings
        branding = BrandingSettings.get_solo()
        if not getattr(branding, 'public_access_code_enabled', False):
            return self.get_response(request)

        code_hash = getattr(branding, 'public_access_code_hash', '')
        if not code_hash:
            return self.get_response(request)

        if request.session.get(self.SESSION_KEY) and request.session.get(self.SESSION_VERSION_KEY) == getattr(branding, 'public_access_code_version', 1):
            return self.get_response(request)

        # Redirect to access code entry.
        return redirect(f"{access_url}?next={request.get_full_path()}")
