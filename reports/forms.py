from django import forms
from django.contrib.auth import get_user_model

from employees.models import EmployeeProfile

from .models import ReportRequest, WeeklyReport


class ReportRequestForm(forms.ModelForm):
    request_all_employees = forms.BooleanField(
        required=False,
        label='Request for all employees',
        help_text='If unchecked, choose one or more employees below.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = ReportRequest
        fields = ['report_type', 'start_date', 'end_date', 'department_name', 'request_all_employees', 'requested_employees']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'department_name': forms.TextInput(attrs={'class': 'form-control'}),
            'requested_employees': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        User = get_user_model()
        qs = User.objects.all().order_by('username')
        user = self.request_user
        if user and user.is_authenticated:
            if not (user.is_superuser or getattr(user, 'role', None) in {'SUPER_ADMIN', 'HR_MANAGER'}):
                try:
                    profile = user.employee_profile
                except EmployeeProfile.DoesNotExist:
                    profile = None
                if profile and profile.department_id:
                    department_user_ids = EmployeeProfile.objects.filter(
                        department_id=profile.department_id
                    ).values_list('user_id', flat=True)
                    qs = qs.filter(id__in=department_user_ids)
                else:
                    qs = qs.filter(id=user.id)
        self.fields['requested_employees'].queryset = qs

        # Render checkbox with proper Bootstrap wrapper when using {{ form.as_p }}
        self.fields['request_all_employees'].widget.attrs.setdefault('class', 'form-check-input')

    def clean(self):
        cleaned = super().clean()
        request_all = cleaned.get('request_all_employees')
        employees = cleaned.get('requested_employees')
        if request_all:
            # Ignore any selections if "all" is chosen.
            cleaned['requested_employees'] = self.fields['requested_employees'].queryset.none()
            return cleaned
        if not employees or len(employees) == 0:
            raise forms.ValidationError('Select at least one employee, or choose "Request for all employees".')
        return cleaned


class WeeklyReportForm(forms.ModelForm):
    class Meta:
        model = WeeklyReport
        fields = ['week_start', 'achievements', 'challenges', 'next_week_plan', 'general_notes']
        widgets = {
            'week_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
