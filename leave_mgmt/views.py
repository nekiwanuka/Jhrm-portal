from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.permissions import HRAdminRequiredMixin, SupervisorPlusRequiredMixin

from .forms import LeaveApprovalForm, LeaveRequestForm, LeaveTypeForm
from .models import LeaveRequest, LeaveType


class LeaveRequestListView(LoginRequiredMixin, ListView):
	model = LeaveRequest
	template_name = 'leave_mgmt/leave_list.html'
	context_object_name = 'leave_requests'

	def get_queryset(self):
		user = self.request.user
		if user.role in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'} or user.is_superuser:
			return LeaveRequest.objects.select_related('employee', 'leave_type').order_by('-created_at')
		return LeaveRequest.objects.filter(employee=user).select_related('leave_type').order_by('-created_at')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		is_privileged = user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'}
		if not is_privileged:
			year = timezone.localdate().year
			approved = LeaveRequest.objects.filter(
				employee=user,
				status=LeaveRequest.STATUS_APPROVED,
				start_date__year=year,
			).select_related('leave_type')
			used_by_type = {}
			for req in approved:
				used_by_type[req.leave_type_id] = used_by_type.get(req.leave_type_id, 0) + req.total_days

			entitlements = []
			for leave_type in LeaveType.objects.filter(is_active=True).order_by('name'):
				used = used_by_type.get(leave_type.id, 0)
				entitlements.append(
					{
						'leave_type': leave_type,
						'max_days': leave_type.max_days_per_year,
						'used_days': used,
						'remaining_days': max(leave_type.max_days_per_year - used, 0),
					}
				)
			context['entitlements'] = entitlements
			context['entitlement_year'] = year
		return context


class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
	model = LeaveRequest
	form_class = LeaveRequestForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('leave_mgmt:list')

	def form_valid(self, form):
		form.instance.employee = self.request.user
		try:
			form.instance.full_clean()
		except ValidationError as exc:
			form.add_error(None, exc)
			return self.form_invalid(form)
		return super().form_valid(form)


class LeaveRequestApprovalView(LoginRequiredMixin, SupervisorPlusRequiredMixin, UpdateView):
	model = LeaveRequest
	form_class = LeaveApprovalForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('leave_mgmt:list')

	def form_valid(self, form):
		old_status = self.get_object().status
		new_status = form.instance.status
		if new_status == LeaveRequest.STATUS_PENDING:
			form.instance.approved_by = None
			form.instance.decided_at = None
		elif new_status in {LeaveRequest.STATUS_APPROVED, LeaveRequest.STATUS_REJECTED}:
			form.instance.approved_by = self.request.user
			if new_status != old_status:
				form.instance.decided_at = timezone.now()
		return super().form_valid(form)


class LeaveTypeListView(LoginRequiredMixin, HRAdminRequiredMixin, ListView):
	model = LeaveType
	template_name = 'leave_mgmt/leave_type_list.html'
	context_object_name = 'leave_types'

	def get_queryset(self):
		return LeaveType.objects.all().order_by('name')


class LeaveTypeCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = LeaveType
	form_class = LeaveTypeForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('leave_mgmt:type_list')


class LeaveTypeUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = LeaveType
	form_class = LeaveTypeForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('leave_mgmt:type_list')


class LeaveOfferLetterView(LoginRequiredMixin, DetailView):
	model = LeaveRequest
	template_name = 'leave_mgmt/leave_letter.html'
	context_object_name = 'leave'

	def dispatch(self, request, *args, **kwargs):
		obj = self.get_object()
		user = request.user
		is_privileged = user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'}
		if not is_privileged and obj.employee_id != user.id:
			raise PermissionDenied
		return super().dispatch(request, *args, **kwargs)
