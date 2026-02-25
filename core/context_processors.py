from __future__ import annotations

from typing import Any

from .models import BrandingSettings


def org_context(request) -> dict[str, Any]:
	branding = BrandingSettings.get_solo()
	user = getattr(request, 'user', None)
	if not user or not getattr(user, 'is_authenticated', False):
		return {'my_department': None, 'branding': branding, 'unread_notifications_count': 0}

	# Notifications: admin-only badge count
	unread_notifications_count = 0
	try:
		if user.is_superuser or getattr(user, 'role', None) in {'SUPER_ADMIN', 'HR_MANAGER'}:
			from audit.models import Notification
			unread_notifications_count = Notification.objects.filter(recipient=user, is_read=False).count()
	except Exception:
		unread_notifications_count = 0

	try:
		profile = user.employee_profile
	except Exception:
		# Covers EmployeeProfile.DoesNotExist and other edge cases.
		return {'my_department': None, 'branding': branding, 'unread_notifications_count': unread_notifications_count}

	return {
		'my_department': getattr(profile, 'department', None),
		'branding': branding,
		'unread_notifications_count': unread_notifications_count,
	}
