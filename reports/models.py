from django.conf import settings
from django.db import models
from datetime import timedelta


class WeeklyReport(models.Model):
	employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weekly_reports')
	week_start = models.DateField(help_text='Start date for the reporting week')
	week_end = models.DateField(blank=True, null=True)
	submission_number = models.PositiveSmallIntegerField(default=1)

	achievements = models.TextField(blank=True)
	challenges = models.TextField(blank=True)
	next_week_plan = models.TextField(blank=True)
	general_notes = models.TextField(blank=True)

	submitted_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-week_start', '-submitted_at']
		indexes = [
			models.Index(fields=['week_start']),
			models.Index(fields=['employee', 'week_start']),
		]
		constraints = [
			models.UniqueConstraint(fields=['employee', 'week_start', 'submission_number'], name='unique_weekly_report_per_employee_week_submission'),
		]

	def __str__(self):
		return f'Weekly Report {self.employee} ({self.week_start}) #{self.submission_number}'

	def save(self, *args, **kwargs):
		if self.week_start and not self.week_end:
			self.week_end = self.week_start + timedelta(days=6)
		return super().save(*args, **kwargs)


class ReportRequest(models.Model):
	REPORT_CHOICES = [
		('attendance', 'Attendance'),
		('leave', 'Leave'),
		('payroll', 'Payroll'),
		('performance', 'Performance'),
	]

	requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	report_type = models.CharField(max_length=20, choices=REPORT_CHOICES)
	start_date = models.DateField()
	end_date = models.DateField()
	department_name = models.CharField(max_length=120, blank=True)
	request_all_employees = models.BooleanField(default=True)
	requested_employees = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		blank=True,
		related_name='report_requests_received',
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		indexes = [
			models.Index(fields=['report_type']),
			models.Index(fields=['start_date', 'end_date']),
		]

	def __str__(self):
		return f'{self.report_type} report by {self.requested_by}'

	def targets_label(self):
		if self.request_all_employees:
			return 'All employees'
		count = self.requested_employees.count()
		if count == 0:
			return 'No employees selected'
		if count == 1:
			return '1 employee'
		return f'{count} employees'
