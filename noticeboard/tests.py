from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from audit.models import Notification
from noticeboard.models import Notice


class NoticeboardNotificationTests(TestCase):
	def test_creating_notice_creates_notification_for_admins(self):
		User = get_user_model()
		admin = User.objects.create_user(username='hr1', password='pass12345', role='HR_MANAGER')
		staff = User.objects.create_user(username='staff1', password='pass12345', role='STAFF')

		self.client.force_login(staff)
		url = reverse('noticeboard:create')
		response = self.client.post(url, data={'title': 'Hello', 'content': 'World', 'expiry_date': ''})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(Notice.objects.count(), 1)

		self.assertEqual(Notification.objects.filter(recipient=admin).count(), 1)
