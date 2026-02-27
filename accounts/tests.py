import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LoginNextRedirectTests(TestCase):
	def test_login_preserves_next_for_my_profile(self):
		User = get_user_model()
		User.objects.create_user(username='alice', password='pass12345', role='STAFF')

		target = '/employees/me/profile/'
		login_url = reverse('accounts:login')

		# Unauthenticated access redirects to login with next.
		resp = self.client.get(target)
		self.assertEqual(resp.status_code, 302)
		self.assertIn(login_url, resp['Location'])
		self.assertIn('next=', resp['Location'])

		# Login page should render a hidden next field containing the target.
		resp = self.client.get(f'{login_url}?next={target}')
		self.assertEqual(resp.status_code, 200)
		html = resp.content.decode('utf-8', errors='replace')
		m = re.search(r'name="next"\s+value="([^"]*)"', html)
		self.assertIsNotNone(m)
		next_value = m.group(1)
		self.assertEqual(next_value, target)

		# Posting the login form with that next should redirect to the target.
		resp = self.client.post(login_url, data={'username': 'alice', 'password': 'pass12345', 'next': next_value})
		self.assertEqual(resp.status_code, 302)
		self.assertEqual(resp['Location'], target)
