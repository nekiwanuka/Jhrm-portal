from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditLog, Notification


class AuditMiddlewareNotificationScopeTests(TestCase):
	def test_generic_post_creates_audit_log_but_no_notification(self):
		User = get_user_model()
		User.objects.create_user(username='hr1', password='pass12345', role='HR_MANAGER')

		url = reverse('core:public_access')
		response = self.client.post(url, data={'code': 'bad-code', 'next': '/'})
		self.assertIn(response.status_code, {200, 302})

		self.assertEqual(Notification.objects.count(), 0)
		self.assertEqual(AuditLog.objects.filter(method='POST', path=url).count(), 1)
