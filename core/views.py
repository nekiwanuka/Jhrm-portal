from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, TemplateView, UpdateView
from django.views.generic import DetailView, ListView
from django.db.models import Q

import mimetypes

from .pdf import render_user_manual_pdf

from attendance.models import AttendanceRecord
from core.permissions import HRAdminRequiredMixin, SupervisorPlusRequiredMixin, user_is_hr_admin, user_is_supervisor_plus
from employees.models import Department, EmployeeDocument, EmployeeProfile
from leave_mgmt.models import LeaveRequest
from noticeboard.models import Notice
from reports.models import WeeklyReport
from tasks.models import Task

from .forms import BrandingSettingsForm, ExecutiveEmailForm, PublicAccessCodeForm, PublicAccessCodeSettingsForm
from .models import BrandingSettings
from .models import InboundEmail
from .models import InboundEmailAttachment

import logging


logger = logging.getLogger(__name__)


class PublicHomeView(TemplateView):
	template_name = 'core/public_home.html'


class PublicAccessCodeView(TemplateView):
	template_name = 'core/access_code.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = PublicAccessCodeForm()
		context['next'] = self.request.GET.get('next', '/')
		return context

	def post(self, request, *args, **kwargs):
		form = PublicAccessCodeForm(request.POST)
		next_url = request.POST.get('next') or request.GET.get('next') or '/'

		branding = BrandingSettings.get_solo()
		if not branding.public_access_code_enabled or not branding.public_access_code_hash:
			return redirect(next_url)

		if form.is_valid():
			code = form.cleaned_data['code']
			if check_password(code, branding.public_access_code_hash):
				request.session['public_access_granted'] = True
				request.session['public_access_granted_version'] = getattr(branding, 'public_access_code_version', 1)
				return redirect(next_url)
			messages.error(request, 'Invalid access code.')

		return self.render_to_response({'form': form, 'next': next_url})


class DashboardView(LoginRequiredMixin, TemplateView):
	template_name = 'core/dashboard.html'

	def dispatch(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return super().dispatch(request, *args, **kwargs)
		if not user_is_supervisor_plus(request.user):
			return redirect('core:staff_dashboard')
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		is_hr_admin = user_is_hr_admin(user)

		employees_qs = EmployeeProfile.objects.select_related('department')
		departments_qs = Department.objects.filter(is_active=True)
		if not is_hr_admin:
			try:
				profile = user.employee_profile
			except EmployeeProfile.DoesNotExist:
				profile = None
			if profile and profile.department_id:
				employees_qs = employees_qs.filter(department_id=profile.department_id)
				departments_qs = departments_qs.filter(id=profile.department_id)

		context['employees_count'] = employees_qs.count()
		context['active_employees_count'] = employees_qs.filter(status=EmployeeProfile.STATUS_ACTIVE).count()
		context['departments_count'] = departments_qs.count()

		leave_qs = LeaveRequest.objects.all()
		if not is_hr_admin:
			leave_qs = leave_qs.filter(employee=user)
		context['pending_leave_count'] = leave_qs.filter(status=LeaveRequest.STATUS_PENDING).count()

		attendance_qs = AttendanceRecord.objects.all()
		if not is_hr_admin:
			attendance_qs = attendance_qs.filter(employee=user)
		today = timezone.localdate()
		context['attendance_today_count'] = attendance_qs.filter(date=today).count()

		context['notices_count'] = Notice.objects.filter(is_public=True).count()
		context['tasks_count'] = Task.objects.count()
		context['tasks_done'] = Task.objects.filter(status=Task.STATUS_DONE).count()
		return context


class StaffDashboardView(LoginRequiredMixin, TemplateView):
	template_name = 'core/staff_dashboard.html'

	def dispatch(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return super().dispatch(request, *args, **kwargs)
		if user_is_supervisor_plus(request.user):
			return redirect('core:dashboard')
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user

		context['my_documents_count'] = EmployeeDocument.objects.filter(user=user).count()
		context['my_pending_leave_count'] = LeaveRequest.objects.filter(
			employee=user,
			status=LeaveRequest.STATUS_PENDING,
		).count()
		context['my_weekly_reports_count'] = WeeklyReport.objects.filter(employee=user).count()

		today = timezone.localdate()
		context['my_attendance_today_count'] = AttendanceRecord.objects.filter(employee=user, date=today).count()

		my_tasks = Task.objects.filter(assigned_to=user)
		context['my_tasks_open_count'] = my_tasks.exclude(status=Task.STATUS_DONE).count()
		context['my_tasks_done_count'] = my_tasks.filter(status=Task.STATUS_DONE).count()

		try:
			profile = user.employee_profile
		except EmployeeProfile.DoesNotExist:
			profile = None

		context['employee_profile'] = profile
		context['notices_count'] = Notice.objects.filter(is_public=True).count()
		return context


class GlobalSearchView(LoginRequiredMixin, TemplateView):
	template_name = 'core/search.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		q = (self.request.GET.get('q') or '').strip()
		context['q'] = q
		if not q:
			context.update({
				'employees': [],
				'documents': [],
				'notices': [],
				'leave_requests': [],
				'weekly_reports': [],
				'tasks': [],
			})
			return context

		is_hr = user_is_hr_admin(user)
		is_sup = user_is_supervisor_plus(user)
		dept_id = None
		try:
			profile = user.employee_profile
			dept_id = profile.department_id
		except EmployeeProfile.DoesNotExist:
			profile = None

		employees_qs = EmployeeProfile.objects.select_related('user', 'department', 'position')
		if not is_hr:
			if is_sup and dept_id:
				employees_qs = employees_qs.filter(department_id=dept_id)
			else:
				employees_qs = employees_qs.filter(user=user)
		employees_qs = employees_qs.filter(
			Q(employee_id__icontains=q)
			| Q(user__username__icontains=q)
			| Q(user__first_name__icontains=q)
			| Q(user__last_name__icontains=q)
			| Q(user__email__icontains=q)
			| Q(department__name__icontains=q)
			| Q(position__title__icontains=q)
		).order_by('employee_id')
		context['employees'] = list(employees_qs[:10])

		docs_qs = EmployeeDocument.objects.select_related('user', 'uploaded_by').order_by('-uploaded_at')
		if not is_hr:
			if is_sup and dept_id:
				docs_qs = docs_qs.filter(user__employee_profile__department_id=dept_id)
			else:
				docs_qs = docs_qs.filter(user=user)
		docs_qs = docs_qs.filter(
			Q(description__icontains=q)
			| Q(document_type__icontains=q)
			| Q(user__username__icontains=q)
			| Q(user__first_name__icontains=q)
			| Q(user__last_name__icontains=q)
		)
		context['documents'] = list(docs_qs[:10])

		notices_qs = Notice.objects.filter(is_public=True).filter(Q(title__icontains=q) | Q(content__icontains=q)).order_by('-created_at')
		context['notices'] = list(notices_qs[:10])

		leave_qs = LeaveRequest.objects.all().order_by('-created_at')
		if not is_hr:
			leave_qs = leave_qs.filter(employee=user)
		leave_qs = leave_qs.filter(Q(reason__icontains=q) | Q(status__icontains=q))
		context['leave_requests'] = list(leave_qs[:10])

		reports_qs = WeeklyReport.objects.all().order_by('-submitted_at')
		if not is_hr:
			reports_qs = reports_qs.filter(employee=user)
		reports_qs = reports_qs.filter(
			Q(achievements__icontains=q)
			| Q(challenges__icontains=q)
			| Q(next_week_plan__icontains=q)
			| Q(general_notes__icontains=q)
		)
		context['weekly_reports'] = list(reports_qs[:10])

		tasks_qs = Task.objects.all().order_by('-created_at')
		if not is_hr:
			tasks_qs = tasks_qs.filter(
				Q(visibility=Task.VISIBILITY_ALL)
				| Q(visible_to=user)
				| Q(assigned_to=user)
				| Q(created_by=user)
			)
		tasks_qs = tasks_qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
		context['tasks'] = list(tasks_qs[:10])

		return context


class ThemeSettingsUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = BrandingSettings
	form_class = BrandingSettingsForm
	template_name = 'core/theme_settings.html'
	success_url = reverse_lazy('core:theme_settings')

	def get_object(self, queryset=None):
		return BrandingSettings.get_solo()

	def post(self, request, *args, **kwargs):
		self.object = self.get_object()
		if 'reset_theme' in request.POST:
			self.object.reset_to_defaults()
			self.object.save()
			messages.success(request, 'Theme settings reset to defaults.')
			return redirect(self.success_url)
		return super().post(request, *args, **kwargs)

	def form_valid(self, form):
		messages.success(self.request, 'Theme settings updated successfully.')
		return super().form_valid(form)


class PublicAccessCodeSettingsUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = BrandingSettings
	form_class = PublicAccessCodeSettingsForm
	template_name = 'core/access_code_settings.html'
	success_url = reverse_lazy('core:access_code_settings')

	def get_object(self, queryset=None):
		return BrandingSettings.get_solo()

	def form_valid(self, form):
		messages.success(self.request, 'Access code settings updated.')
		return super().form_valid(form)


class ExecutiveEmailView(LoginRequiredMixin, SupervisorPlusRequiredMixin, FormView):
	template_name = 'core/send_email.html'
	form_class = ExecutiveEmailForm
	success_url = reverse_lazy('core:send_email')

	def form_valid(self, form):
		recipients = form.cleaned_data['to']
		subject = form.cleaned_data['subject']
		message = form.cleaned_data['message']
		attachments = form.cleaned_data.get('attachments') or []

		try:
			email = EmailMessage(
				subject=subject,
				body=message,
				from_email=None,
				to=recipients,
			)
			for f in attachments:
				content_type = getattr(f, 'content_type', None) or 'application/octet-stream'
				email.attach(f.name, f.read(), content_type)
			email.send(fail_silently=False)
		except Exception:
			logger.exception('SMTP send failed in ExecutiveEmailView')
			form.add_error(None, 'Email could not be sent. Please confirm SMTP settings and try again.')
			return self.form_invalid(form)

		if attachments:
			messages.success(
				self.request,
				f'Email sent to {len(recipients)} recipient(s) with {len(attachments)} attachment(s).',
			)
		else:
			messages.success(self.request, f'Email sent to {len(recipients)} recipient(s).')
		return super().form_valid(form)


class UserManualPdfView(LoginRequiredMixin, TemplateView):
	"""Role-aware user manual PDF download."""
	def get(self, request, *args, **kwargs):
		branding = BrandingSettings.get_solo()
		user = request.user

		role = getattr(user, 'role', None) or ('SUPER_ADMIN' if getattr(user, 'is_superuser', False) else 'STAFF')
		is_superuser = bool(getattr(user, 'is_superuser', False))
		is_hr_admin = is_superuser or role in {'SUPER_ADMIN', 'HR_MANAGER'}
		is_supervisor_plus = is_hr_admin or role in {'SUPERVISOR'}

		return render_user_manual_pdf(
			user=user,
			branding=branding,
			is_hr_admin=is_hr_admin,
			is_supervisor_plus=is_supervisor_plus,
		)


class UserManualStaffPdfView(LoginRequiredMixin, SupervisorPlusRequiredMixin, TemplateView):
	"""Download the Staff user manual (for distribution by Supervisor+/HR/Admin)."""
	def get(self, request, *args, **kwargs):
		branding = BrandingSettings.get_solo()
		return render_user_manual_pdf(
			user=request.user,
			branding=branding,
			is_hr_admin=False,
			is_supervisor_plus=False,
			manual_role_label='Staff',
			generated_for_name='All Staff',
		)


class InboxListView(LoginRequiredMixin, SupervisorPlusRequiredMixin, ListView):
	template_name = 'core/inbox_list.html'
	context_object_name = 'emails'

	def get_queryset(self):
		return InboundEmail.objects.order_by('-uid')[:50]


class InboxDetailView(LoginRequiredMixin, SupervisorPlusRequiredMixin, DetailView):
	template_name = 'core/inbox_detail.html'
	model = InboundEmail
	context_object_name = 'email'


def inbox_attachment_download(request, pk: int):
	if not (request.user.is_authenticated and user_is_supervisor_plus(request.user)):
		raise Http404
	att = InboundEmailAttachment.objects.select_related('email').filter(pk=pk).first()
	if not att or not att.file:
		raise Http404
	content_type, _ = mimetypes.guess_type(att.file.name)
	response = FileResponse(att.file.open('rb'), content_type=content_type or 'application/octet-stream')
	filename = att.filename or att.file.name.split('/')[-1]
	response['Content-Disposition'] = f'inline; filename="{filename}"'
	return response
