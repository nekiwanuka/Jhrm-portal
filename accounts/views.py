from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.permissions import HRAdminRequiredMixin

from .models import BusinessRole


class BusinessRoleListView(LoginRequiredMixin, HRAdminRequiredMixin, ListView):
	model = BusinessRole
	template_name = 'accounts/role_list.html'
	context_object_name = 'roles'
	paginate_by = 30

	def get_queryset(self):
		return BusinessRole.objects.select_related('department_scope').order_by('department_scope__name', 'name')


class BusinessRoleCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = BusinessRole
	template_name = 'common/form.html'
	success_url = reverse_lazy('accounts:roles')
	fields = [
		'code',
		'name',
		'description',
		'department_scope',
		'approval_authority_level',
		'financial_authorization_limit',
		'is_active',
	]


class BusinessRoleUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = BusinessRole
	template_name = 'common/form.html'
	success_url = reverse_lazy('accounts:roles')
	fields = [
		'code',
		'name',
		'description',
		'department_scope',
		'approval_authority_level',
		'financial_authorization_limit',
		'is_active',
	]


class BusinessRoleDeleteView(LoginRequiredMixin, HRAdminRequiredMixin, DeleteView):
	model = BusinessRole
	template_name = 'accounts/role_confirm_delete.html'
	success_url = reverse_lazy('accounts:roles')

	def form_valid(self, form):
		try:
			return super().form_valid(form)
		except ProtectedError:
			messages.error(self.request, 'This role is in use and cannot be deleted. Deactivate it instead.')
			return super().render_to_response(self.get_context_data(form=form))
