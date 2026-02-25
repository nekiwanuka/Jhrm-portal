from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from accounts.models import BusinessRole

from .models import EmployeeDepartmentRole


class EmployeeDepartmentRoleForm(forms.ModelForm):
	class Meta:
		model = EmployeeDepartmentRole
		fields = [
			'employee',
			'department',
			'role',
			'reporting_manager',
			'effective_start_date',
			'effective_end_date',
			'is_active',
		]
		widgets = {
			'effective_start_date': forms.DateInput(attrs={'type': 'date'}),
			'effective_end_date': forms.DateInput(attrs={'type': 'date'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		dept_id = None
		if self.data.get('department'):
			dept_id = self.data.get('department')
		elif self.instance and self.instance.department_id:
			dept_id = self.instance.department_id

		roles = BusinessRole.objects.filter(is_active=True)
		if dept_id:
			roles = roles.filter(Q(department_scope__isnull=True) | Q(department_scope_id=dept_id))
		self.fields['role'].queryset = roles.order_by('name')

	def clean(self):
		cleaned = super().clean()
		department = cleaned.get('department')
		role = cleaned.get('role')
		if role and role.department_scope and department and role.department_scope_id != department.id:
			raise ValidationError('Selected role is scoped to a different department.')
		return cleaned
