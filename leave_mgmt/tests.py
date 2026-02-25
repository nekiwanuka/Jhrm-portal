from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class LeaveTemplateRenderingTests(TestCase):
	def setUp(self):
		self.supervisor = User.objects.create_user(
			username='supervisor1',
			password='Pass12345',
			role=User.ROLE_SUPERVISOR,
			is_staff=True,
		)

	def test_leave_list_renders_for_authenticated_user(self):
		self.client.force_login(self.supervisor)
		response = self.client.get(reverse('leave_mgmt:list'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Leave')
