from audit.models import AuditLog
from audit.models import Notification
from django.contrib.auth import get_user_model
from django.db.models import Q


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

            # Notify admins (true notifications center)
            try:
                User = get_user_model()
                admins = list(User.objects.filter(Q(is_superuser=True) | Q(role__in={'SUPER_ADMIN', 'HR_MANAGER'})).only('id'))
                actor = request.user if request.user.is_authenticated else None
                if admins:
                    Notification.objects.bulk_create(
                        [
                            Notification(
                                recipient=a,
                                actor=actor,
                                message=action,
                                path=request.path,
                                level=Notification.LEVEL_INFO,
                            )
                            for a in admins
                            if not actor or a.id != actor.id
                        ]
                    )
            except Exception:
                pass
        return response
