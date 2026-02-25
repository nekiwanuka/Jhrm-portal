import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.views.generic import CreateView, DetailView, ListView, View

from core.permissions import SupervisorPlusRequiredMixin

from employees.models import EmployeeProfile
from employees.models import EmployeeDepartmentRole

from .forms import ReportRequestForm, WeeklyReportForm
from .models import ReportRequest, WeeklyReport


def _is_hr_admin(user):
	if not user.is_authenticated:
		return False
	if user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER'}:
		return True
	if user.groups.filter(name__in={'Super Admin', 'HR Manager'}).exists():
		return True
	return EmployeeDepartmentRole.objects.filter(employee=user, is_active=True, role__code__in={'super-admin', 'hr-manager'}).exists()


def _is_supervisor_plus(user):
	if not user.is_authenticated:
		return False
	if user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'}:
		return True
	if user.groups.filter(name__in={'Super Admin', 'HR Manager', 'Supervisor'}).exists():
		return True
	return EmployeeDepartmentRole.objects.filter(employee=user, is_active=True, role__code__in={'super-admin', 'hr-manager', 'supervisor'}).exists()


class WeeklyReportListView(ListView):
	model = WeeklyReport
	template_name = 'reports/weekly_report_list.html'
	context_object_name = 'weekly_reports'
	paginate_by = 30

	def get_queryset(self):
		qs = WeeklyReport.objects.select_related('employee').order_by('-week_start', '-submitted_at')
		user = self.request.user
		if not user.is_authenticated:
			return qs
		if _is_hr_admin(user):
			return qs
		if _is_supervisor_plus(user) and not (user.role == 'STAFF'):
			try:
				profile = user.employee_profile
			except EmployeeProfile.DoesNotExist:
				profile = None
			if profile and profile.department_id:
				department_user_ids = EmployeeProfile.objects.filter(department_id=profile.department_id).values_list('user_id', flat=True)
				return qs.filter(employee_id__in=department_user_ids)
			return qs.filter(employee=user)
		return qs.filter(employee=user)


class WeeklyReportDetailView(DetailView):
	model = WeeklyReport
	template_name = 'reports/weekly_report_detail.html'
	context_object_name = 'report'

	def get_queryset(self):
		# Reuse the same visibility rules as the list view.
		qs = WeeklyReport.objects.select_related('employee').order_by('-week_start', '-submitted_at')
		user = self.request.user
		if not user.is_authenticated:
			return qs
		if _is_hr_admin(user):
			return qs
		if _is_supervisor_plus(user) and not (user.role == 'STAFF'):
			try:
				profile = user.employee_profile
			except EmployeeProfile.DoesNotExist:
				profile = None
			if profile and profile.department_id:
				department_user_ids = EmployeeProfile.objects.filter(department_id=profile.department_id).values_list('user_id', flat=True)
				return qs.filter(employee_id__in=department_user_ids)
			return qs.filter(employee=user)
		return qs.filter(employee=user)


class WeeklyReportCreateView(LoginRequiredMixin, CreateView):
	model = WeeklyReport
	form_class = WeeklyReportForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('reports:weekly_list')

	def form_valid(self, form):
		user = self.request.user
		week_start = form.cleaned_data.get('week_start')

		for attempt in range(3):
			try:
				with transaction.atomic():
					max_submission = WeeklyReport.objects.filter(employee=user, week_start=week_start).aggregate(
						Max('submission_number')
					)['submission_number__max'] or 0
					self.object = form.save(commit=False)
					self.object.employee = user
					self.object.submission_number = max_submission + 1
					self.object.save()
				preview_url = reverse('reports:weekly_detail', args=[self.object.pk])
				messages.success(
					self.request,
					format_html(
						'Weekly report submitted (#{}) — <a class="alert-link" href="{}">Preview</a>',
						self.object.submission_number,
						preview_url,
					),
				)
				return redirect(self.get_success_url())
			except IntegrityError:
				# Defensive fallback for race conditions / double-submit.
				if attempt >= 2:
					raise
				continue

		return super().form_invalid(form)


class ReportRequestListView(LoginRequiredMixin, SupervisorPlusRequiredMixin, ListView):
	model = ReportRequest
	template_name = 'reports/report_list.html'
	context_object_name = 'report_requests'

	def get_queryset(self):
		return ReportRequest.objects.select_related('requested_by').prefetch_related('requested_employees').order_by('-created_at')


class ReportRequestDetailView(LoginRequiredMixin, SupervisorPlusRequiredMixin, DetailView):
	model = ReportRequest
	template_name = 'reports/report_request_detail.html'
	context_object_name = 'report_request'

	def get_queryset(self):
		return ReportRequest.objects.select_related('requested_by').prefetch_related('requested_employees')


class ReportRequestCreateView(LoginRequiredMixin, SupervisorPlusRequiredMixin, CreateView):
	model = ReportRequest
	form_class = ReportRequestForm
	template_name = 'reports/report_request_form.html'
	success_url = reverse_lazy('reports:list')

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def form_valid(self, form):
		form.instance.requested_by = self.request.user
		return super().form_valid(form)


class ReportCSVExportView(LoginRequiredMixin, SupervisorPlusRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="reports.csv"'
		writer = csv.writer(response)
		writer.writerow(['Requested By', 'Type', 'Start', 'End', 'Department', 'Targets', 'Created'])
		for report in ReportRequest.objects.all().prefetch_related('requested_employees').order_by('-created_at'):
			if report.request_all_employees:
				targets = 'All employees'
			else:
				targets = '; '.join(
					[(u.get_full_name() or u.username) for u in report.requested_employees.all()]
				) or 'No employees selected'
			writer.writerow([
				report.requested_by.username,
				report.report_type,
				report.start_date,
				report.end_date,
				report.department_name,
				targets,
				report.created_at,
			])
		return response
