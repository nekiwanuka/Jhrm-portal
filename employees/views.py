from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.permissions import HRAdminRequiredMixin, SupervisorPlusRequiredMixin

from .forms import DepartmentForm, EmployeeDocumentForm, EmployeeOnboardingForm, EmployeeProfileForm, PositionForm
from .role_forms import EmployeeDepartmentRoleForm
from .models import Department, EmployeeDepartmentRole, EmployeeDocument, EmployeeProfile, Position
from accounts.models import User


def _can_suspend_target(actor, target: User) -> bool:
	"""HR_MANAGER can suspend most users; SUPER_ADMIN/superuser can suspend anyone except superuser."""
	if not actor.is_authenticated:
		return False
	if target.is_superuser:
		return False
	if actor.is_superuser or actor.role == User.ROLE_SUPER_ADMIN:
		return True
	if actor.role == User.ROLE_HR_MANAGER:
		return target.role != User.ROLE_SUPER_ADMIN
	return False


@login_required
@require_POST
def toggle_user_access(request, user_pk):
	"""Suspend/unsuspend a user by toggling is_active."""
	if not (request.user.is_authenticated and (request.user.is_superuser or request.user.role in {User.ROLE_SUPER_ADMIN, User.ROLE_HR_MANAGER})):
		messages.error(request, 'You do not have permission to manage user access.')
		return redirect('employees:list')

	target = get_object_or_404(User, pk=user_pk)
	if not _can_suspend_target(request.user, target):
		messages.error(request, 'You do not have permission to suspend this account.')
		return redirect('employees:list')

	target.is_active = not target.is_active
	target.save(update_fields=['is_active'])

	if target.is_active:
		messages.success(request, f'Access restored for {target.get_full_name() or target.username}.')
	else:
		messages.success(request, f'Account suspended for {target.get_full_name() or target.username}.')

	return redirect('employees:list')


def _can_manage_documents(user):
	if not user.is_authenticated:
		return False
	if user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'}:
		return True
	if user.groups.filter(name__in={'Super Admin', 'HR Manager', 'Supervisor'}).exists():
		return True
	return EmployeeDepartmentRole.objects.filter(
		employee=user,
		is_active=True,
		role__code__in={'super-admin', 'hr-manager', 'supervisor'},
	).exists()


class EmployeeListView(LoginRequiredMixin, SupervisorPlusRequiredMixin, ListView):
	model = EmployeeProfile
	template_name = 'employees/employee_list.html'
	context_object_name = 'employees'

	def get_queryset(self):
		qs = EmployeeProfile.objects.select_related('user', 'department', 'position').order_by('employee_id')
		user = self.request.user
		if user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER'}:
			return qs
		try:
			profile = user.employee_profile
		except EmployeeProfile.DoesNotExist:
			profile = None
		if profile and profile.department_id:
			return qs.filter(department_id=profile.department_id)
		return qs


class EmployeeCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = EmployeeProfile
	form_class = EmployeeOnboardingForm
	template_name = 'employees/employee_onboard_form.html'
	success_url = reverse_lazy('employees:list')

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['request_user'] = self.request.user
		return kwargs

	@transaction.atomic
	def form_valid(self, form):
		# Extra safety: block HR managers from creating SUPER_ADMIN even if posted manually.
		requested_role = form.cleaned_data.get('role', User.ROLE_STAFF)
		if requested_role == User.ROLE_SUPER_ADMIN and not (
			self.request.user.is_superuser or self.request.user.role == User.ROLE_SUPER_ADMIN
		):
			messages.error(self.request, 'Only the System Admin can create a Super Admin user.')
			return self.form_invalid(form)

		user = User.objects.create_user(
			username=form.cleaned_data['username'],
			password=form.cleaned_data['password1'],
			first_name=form.cleaned_data.get('first_name', ''),
			last_name=form.cleaned_data.get('last_name', ''),
			email=form.cleaned_data.get('email', ''),
			phone_number=form.cleaned_data.get('phone_number', ''),
			role=form.cleaned_data.get('role', User.ROLE_STAFF),
		)
		form.instance.user = user
		response = super().form_valid(form)
		primary_role = form.cleaned_data.get('primary_role')
		department = self.object.department
		if primary_role and department:
			EmployeeDepartmentRole.objects.get_or_create(
				employee=self.object.user,
				department=department,
				role=primary_role,
				defaults={'is_active': True},
			)
		return response


class EmployeeUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = EmployeeProfile
	form_class = EmployeeProfileForm
	template_name = 'employees/employee_form.html'
	success_url = reverse_lazy('employees:list')


class EmployeePreviewView(LoginRequiredMixin, SupervisorPlusRequiredMixin, DetailView):
	model = EmployeeProfile
	template_name = 'employees/employee_preview.html'
	context_object_name = 'employee'

	def get_queryset(self):
		qs = EmployeeProfile.objects.select_related('user', 'department', 'position').order_by('employee_id')
		user = self.request.user
		if user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER'}:
			return qs
		try:
			profile = user.employee_profile
		except EmployeeProfile.DoesNotExist:
			profile = None
		if profile and profile.department_id:
			return qs.filter(department_id=profile.department_id)
		return qs.filter(user=user)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['documents'] = EmployeeDocument.objects.filter(user=self.object.user).order_by('-uploaded_at')[:8]
		return context


class EmployeeDocumentListView(LoginRequiredMixin, HRAdminRequiredMixin, ListView):
	model = EmployeeDocument
	template_name = 'employees/employee_document_list.html'
	context_object_name = 'documents'

	def dispatch(self, request, *args, **kwargs):
		self.employee_profile = get_object_or_404(EmployeeProfile.objects.select_related('user'), pk=kwargs.get('employee_pk'))
		self.target_user = self.employee_profile.user
		return super().dispatch(request, *args, **kwargs)

	def get_queryset(self):
		return EmployeeDocument.objects.filter(user=self.target_user).select_related('uploaded_by', 'user').order_by('-uploaded_at')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['document_owner'] = self.target_user
		context['employee_profile'] = self.employee_profile
		context['can_manage_docs'] = _can_manage_documents(self.request.user)
		return context


class EmployeeDocumentCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = EmployeeDocument
	form_class = EmployeeDocumentForm
	template_name = 'common/form.html'

	def dispatch(self, request, *args, **kwargs):
		self.employee_profile = get_object_or_404(EmployeeProfile.objects.select_related('user'), pk=kwargs.get('employee_pk'))
		self.target_user = self.employee_profile.user
		return super().dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		form.instance.user = self.target_user
		form.instance.uploaded_by = self.request.user
		return super().form_valid(form)

	def get_success_url(self):
		return reverse_lazy('employees:documents', kwargs={'employee_pk': self.employee_profile.pk})


class EmployeeDocumentDeleteView(LoginRequiredMixin, HRAdminRequiredMixin, DeleteView):
	model = EmployeeDocument
	template_name = 'employees/employee_document_confirm_delete.html'

	def dispatch(self, request, *args, **kwargs):
		self.employee_profile = get_object_or_404(EmployeeProfile.objects.select_related('user'), pk=kwargs.get('employee_pk'))
		self.target_user = self.employee_profile.user
		return super().dispatch(request, *args, **kwargs)

	def get_queryset(self):
		return EmployeeDocument.objects.filter(user=self.target_user)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['cancel_url'] = reverse('employees:documents', kwargs={'employee_pk': self.employee_profile.pk})
		return context

	def get_success_url(self):
		return reverse_lazy('employees:documents', kwargs={'employee_pk': self.employee_profile.pk})


class MyEmployeeDocumentListView(LoginRequiredMixin, ListView):
	model = EmployeeDocument
	template_name = 'employees/employee_document_list.html'
	context_object_name = 'documents'

	def get_queryset(self):
		return EmployeeDocument.objects.filter(user=self.request.user).select_related('uploaded_by', 'user').order_by('-uploaded_at')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['document_owner'] = self.request.user
		context['employee_profile'] = EmployeeProfile.objects.select_related('user').filter(user=self.request.user).first()
		context['can_manage_docs'] = True
		context['is_my_docs'] = True
		context['back_url'] = reverse('core:dashboard')
		context['upload_url'] = reverse('employees:my_document_upload')
		return context


class MyEmployeeDocumentCreateView(LoginRequiredMixin, CreateView):
	model = EmployeeDocument
	form_class = EmployeeDocumentForm
	template_name = 'common/form.html'

	def form_valid(self, form):
		form.instance.user = self.request.user
		form.instance.uploaded_by = self.request.user
		return super().form_valid(form)

	def get_success_url(self):
		return reverse_lazy('employees:my_documents')


class MyEmployeeDocumentDeleteView(LoginRequiredMixin, DeleteView):
	model = EmployeeDocument
	template_name = 'employees/employee_document_confirm_delete.html'

	def get_queryset(self):
		return EmployeeDocument.objects.filter(user=self.request.user)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['cancel_url'] = reverse('employees:my_documents')
		return context

	def get_success_url(self):
		return reverse_lazy('employees:my_documents')


class DepartmentListView(LoginRequiredMixin, SupervisorPlusRequiredMixin, ListView):
	model = Department
	template_name = 'employees/department_list.html'
	context_object_name = 'departments'


class PositionListView(LoginRequiredMixin, SupervisorPlusRequiredMixin, ListView):
	model = Position
	template_name = 'employees/position_list.html'
	context_object_name = 'positions'

	def get_queryset(self):
		return Position.objects.select_related('department').order_by('department__name', 'title')


class EmployeeDepartmentRoleListView(LoginRequiredMixin, SupervisorPlusRequiredMixin, ListView):
	model = EmployeeDepartmentRole
	template_name = 'employees/employee_department_role_list.html'
	context_object_name = 'assignments'
	paginate_by = 50

	def get_queryset(self):
		qs = EmployeeDepartmentRole.objects.select_related('employee', 'department', 'role', 'reporting_manager').order_by('-is_active', 'department__name')
		user = self.request.user
		if user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER'}:
			return qs
		try:
			profile = user.employee_profile
		except EmployeeProfile.DoesNotExist:
			profile = None
		if profile and profile.department_id:
			return qs.filter(department_id=profile.department_id)
		return qs


class DepartmentCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = Department
	form_class = DepartmentForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('employees:departments')


class DepartmentUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = Department
	form_class = DepartmentForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('employees:departments')


class DepartmentDeleteView(LoginRequiredMixin, HRAdminRequiredMixin, DeleteView):
	model = Department
	template_name = 'employees/department_confirm_delete.html'
	success_url = reverse_lazy('employees:departments')

	def form_valid(self, form):
		try:
			return super().form_valid(form)
		except ProtectedError:
			messages.error(self.request, 'This department is referenced by assignments and cannot be deleted. Deactivate it instead.')
			return super().render_to_response(self.get_context_data(form=form))


class PositionCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = Position
	form_class = PositionForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('employees:positions')


class PositionUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = Position
	form_class = PositionForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('employees:positions')


class PositionDeleteView(LoginRequiredMixin, HRAdminRequiredMixin, DeleteView):
	model = Position
	template_name = 'employees/position_confirm_delete.html'
	success_url = reverse_lazy('employees:positions')


class EmployeeDepartmentRoleCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = EmployeeDepartmentRole
	form_class = EmployeeDepartmentRoleForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('employees:assignments')


class EmployeeDepartmentRoleUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = EmployeeDepartmentRole
	form_class = EmployeeDepartmentRoleForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('employees:assignments')


class EmployeeDepartmentRoleDeleteView(LoginRequiredMixin, HRAdminRequiredMixin, DeleteView):
	model = EmployeeDepartmentRole
	template_name = 'employees/employee_department_role_confirm_delete.html'
	success_url = reverse_lazy('employees:assignments')
