from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from accounts.models import User
from accounts.models import BusinessRole

from .models import Department, EmployeeDocument, EmployeeProfile, Position


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = [
            'name',
            'department_type',
            'description',
            'parent',
            'cost_center_code',
            'budget_allocation',
            'head',
            'is_active',
        ]


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['title', 'department']


class EmployeeProfileForm(forms.ModelForm):
    primary_role = forms.ModelChoiceField(
        queryset=BusinessRole.objects.filter(is_active=True),
        required=False,
        help_text='Optional. Creates/updates the employee’s primary department role assignment.',
    )

    class Meta:
        model = EmployeeProfile
        fields = [
            'user',
            'employee_id',
            'photo',
            'department',
            'position',
            'national_id',
            'passport_number',
            'tin',
            'nssf_number',
            'date_of_birth',
            'gender',
            'marital_status',
            'emergency_contact_name',
            'emergency_contact_phone',
            'employment_type',
            'date_hired',
            'probation_end_date',
            'status',
            'bank_name',
            'bank_account_number',
            'bank_branch',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_hired': forms.DateInput(attrs={'type': 'date'}),
            'probation_end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dept_id = None
        if self.data.get('department'):
            dept_id = self.data.get('department')
        elif self.instance and self.instance.department_id:
            dept_id = self.instance.department_id

        if dept_id:
            self.fields['position'].queryset = Position.objects.filter(department_id=dept_id).order_by('title')
            self.fields['primary_role'].queryset = BusinessRole.objects.filter(is_active=True).filter(
                Q(department_scope__isnull=True) | Q(department_scope_id=dept_id)
            ).order_by('name')
        else:
            self.fields['position'].queryset = Position.objects.all().order_by('department__name', 'title')
            self.fields['primary_role'].queryset = BusinessRole.objects.filter(is_active=True).order_by('name')

    def clean(self):
        cleaned = super().clean()
        department = cleaned.get('department')
        position = cleaned.get('position')
        if position and department and position.department_id != department.id:
            raise ValidationError('Selected position must belong to the selected department.')
        return cleaned


class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'file', 'description']


class EmployeeOnboardingForm(EmployeeProfileForm):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=30, required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial=User.ROLE_STAFF)
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta(EmployeeProfileForm.Meta):
        fields = [
            'employee_id',
            'photo',
            'department',
            'position',
            'national_id',
            'passport_number',
            'tin',
            'nssf_number',
            'date_of_birth',
            'gender',
            'marital_status',
            'emergency_contact_name',
            'emergency_contact_phone',
            'employment_type',
            'date_hired',
            'probation_end_date',
            'status',
            'bank_name',
            'bank_account_number',
            'bank_branch',
        ]

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            self.add_error('password2', 'Passwords do not match.')

        request_user = getattr(self, 'request_user', None)
        requested_role = cleaned.get('role')
        if requested_role == User.ROLE_SUPER_ADMIN:
            if not request_user or not (getattr(request_user, 'is_superuser', False) or getattr(request_user, 'role', None) == User.ROLE_SUPER_ADMIN):
                self.add_error('role', 'Only the System Admin can create a Super Admin user.')
        return cleaned

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)

        # Prevent HR managers/supervisors/staff from even seeing SUPER_ADMIN in the dropdown.
        if self.request_user and not (self.request_user.is_superuser or self.request_user.role == User.ROLE_SUPER_ADMIN):
            self.fields['role'].choices = [
                c for c in self.fields['role'].choices if c[0] != User.ROLE_SUPER_ADMIN
            ]
