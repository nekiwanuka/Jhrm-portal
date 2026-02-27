from __future__ import annotations

from typing import Any

from .models import BrandingSettings
from .permissions import user_is_hr_admin, user_is_super_admin, user_is_supervisor_plus


def org_context(request) -> dict[str, Any]:
	branding = BrandingSettings.get_solo()
	user = getattr(request, 'user', None)
	if not user or not getattr(user, 'is_authenticated', False):
		return {'my_department': None, 'branding': branding, 'unread_notifications_count': 0}

	is_super_admin = False
	is_hr_admin = False
	is_supervisor_plus = False
	try:
		is_super_admin = user_is_super_admin(user)
		is_hr_admin = user_is_hr_admin(user)
		is_supervisor_plus = user_is_supervisor_plus(user)
	except Exception:
		is_super_admin = bool(getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'SUPER_ADMIN')
		is_hr_admin = bool(getattr(user, 'is_superuser', False) or getattr(user, 'role', None) in {'SUPER_ADMIN', 'HR_MANAGER'})
		is_supervisor_plus = bool(getattr(user, 'is_superuser', False) or getattr(user, 'role', None) in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'})

	# Notifications: admin-only badge count
	unread_notifications_count = 0
	try:
		if is_hr_admin:
			from audit.models import Notification
			unread_notifications_count = Notification.objects.filter(recipient=user, is_read=False).count()
	except Exception:
		unread_notifications_count = 0

	try:
		profile = user.employee_profile
	except Exception:
		# Covers EmployeeProfile.DoesNotExist and other edge cases.
		return {
			'my_department': None,
			'branding': branding,
			'unread_notifications_count': unread_notifications_count,
			'is_super_admin': is_super_admin,
			'is_hr_admin': is_hr_admin,
			'is_supervisor_plus': is_supervisor_plus,
		}

	return {
		'my_department': getattr(profile, 'department', None),
		'branding': branding,
		'unread_notifications_count': unread_notifications_count,
		'is_super_admin': is_super_admin,
		'is_hr_admin': is_hr_admin,
		'is_supervisor_plus': is_supervisor_plus,
	}
