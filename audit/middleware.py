from audit.models import AuditLog


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response
        if getattr(request, 'skip_audit_log', False):
            return response
        if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            action = f'{request.method} {request.path}'
            AuditLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action=action,
                path=request.path,
                method=request.method,
                status_code=response.status_code,
            )
        return response
