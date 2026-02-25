from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import EmployeeDocument, EmployeeProfile


class EmployeeOnboardingTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username='hradmin',
			password='Pass12345',
			role=User.ROLE_HR_MANAGER,
			is_staff=True,
		)

	def test_employee_create_page_renders_onboarding_pages(self):
		self.client.force_login(self.admin)
		response = self.client.get(reverse('employees:create'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Account Setup')
		self.assertContains(response, 'Save & Next Page')
		self.assertContains(response, 'Create User & Employee Profile')

	def test_employee_create_creates_user_and_profile(self):
		self.client.force_login(self.admin)
		payload = {
			'username': 'newstaff',
			'password1': 'Pass12345',
			'password2': 'Pass12345',
			'first_name': 'New',
			'last_name': 'Staff',
			'email': 'newstaff@example.com',
			'phone_number': '0700000002',
			'role': User.ROLE_STAFF,
			'employee_id': 'EMP-T-001',
			'employment_type': 'FULL_TIME',
			'date_hired': '2026-02-23',
			'status': 'ACTIVE',
		}
		response = self.client.post(reverse('employees:create'), payload)
		self.assertEqual(response.status_code, 302)
		self.assertTrue(User.objects.filter(username='newstaff').exists())
		self.assertTrue(EmployeeProfile.objects.filter(user__username='newstaff').exists())


class EmployeeDocumentOwnershipTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='staff1',
			password='Pass12345',
			role=User.ROLE_STAFF,
		)

	def test_my_documents_lists_documents_owned_by_logged_user(self):
		EmployeeDocument.objects.create(
			user=self.user,
			document_type=EmployeeDocument.DOC_OTHER,
			file=SimpleUploadedFile('doc.txt', b'hello'),
			description='My file',
			uploaded_by=self.user,
		)
		self.client.force_login(self.user)
		response = self.client.get(reverse('employees:my_documents'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'My file')
