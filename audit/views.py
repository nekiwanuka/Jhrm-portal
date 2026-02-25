from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from .models import AuditLog
from .models import Notification


class AdminOnlyMixin(UserPassesTestMixin):
	def test_func(self):
		user = self.request.user
		return user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER'}


class AuditLogListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
	model = AuditLog
	template_name = 'audit/log_list.html'
	context_object_name = 'logs'
	paginate_by = 25


class NotificationListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
	model = Notification
	template_name = 'audit/notifications.html'
	context_object_name = 'notifications'
	paginate_by = 30

	def get_queryset(self):
		return Notification.objects.filter(recipient=self.request.user)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['unread_count'] = Notification.objects.filter(recipient=self.request.user, is_read=False).count()
		return context


@login_required
@require_POST
def mark_notification_read(request, pk):
	user = request.user
	if not (user.is_superuser or getattr(user, 'role', None) in {'SUPER_ADMIN', 'HR_MANAGER'}):
		return HttpResponseForbidden('Forbidden')

	n = get_object_or_404(Notification, pk=pk, recipient=user)
	if not n.is_read:
		n.is_read = True
		n.save(update_fields=['is_read'])
	return redirect('audit:notifications')


@login_required
@require_POST
def mark_all_notifications_read(request):
	user = request.user
	if not (user.is_superuser or getattr(user, 'role', None) in {'SUPER_ADMIN', 'HR_MANAGER'}):
		return HttpResponseForbidden('Forbidden')

	Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
	return redirect('audit:notifications')
