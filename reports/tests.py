from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import ReportRequestForm
from .models import ReportRequest, WeeklyReport


class WeeklyReportSubmitTests(TestCase):
	def test_duplicate_weekly_submit_creates_second_report(self):
		User = get_user_model()
		user = User.objects.create_user(username='alice', password='password123', role='STAFF')
		self.client.login(username='alice', password='password123')

		url = reverse('reports:weekly_submit')
		week_start = date(2026, 2, 23)

		resp1 = self.client.post(url, {
			'week_start': week_start,
			'achievements': 'A1',
			'challenges': 'C1',
			'next_week_plan': 'P1',
			'general_notes': 'N1',
		})
		self.assertEqual(resp1.status_code, 302)
		self.assertEqual(WeeklyReport.objects.count(), 1)

		resp2 = self.client.post(url, {
			'week_start': week_start,
			'achievements': 'A2',
			'challenges': 'C2',
			'next_week_plan': 'P2',
			'general_notes': 'N2',
		})
		self.assertEqual(resp2.status_code, 302)
		self.assertEqual(WeeklyReport.objects.count(), 2)

		reports = list(WeeklyReport.objects.filter(employee=user, week_start=week_start).order_by('submission_number'))
		self.assertEqual(reports[0].submission_number, 1)
		self.assertEqual(reports[0].achievements, 'A1')
		self.assertEqual(reports[1].submission_number, 2)
		self.assertEqual(reports[1].achievements, 'A2')


class ReportRequestFormTests(TestCase):
	def test_request_selected_requires_at_least_one_employee(self):
		User = get_user_model()
		requester = User.objects.create_user(username='req', password='password123', role='SUPERVISOR')
		form = ReportRequestForm(
			data={
				'report_type': 'attendance',
				'start_date': '2026-02-01',
				'end_date': '2026-02-07',
				'department_name': '',
				'request_all_employees': False,
				'requested_employees': [],
			},
			user=requester,
			instance=ReportRequest(requested_by=requester),
		)
		self.assertFalse(form.is_valid())
		self.assertIn('Select at least one employee', str(form.errors))

	def test_request_all_is_valid_without_selection(self):
		User = get_user_model()
		requester = User.objects.create_user(username='req2', password='password123', role='HR_MANAGER')
		form = ReportRequestForm(
			data={
				'report_type': 'attendance',
				'start_date': '2026-02-01',
				'end_date': '2026-02-07',
				'department_name': '',
				'request_all_employees': True,
			},
			user=requester,
			instance=ReportRequest(requested_by=requester),
		)
		self.assertTrue(form.is_valid())
