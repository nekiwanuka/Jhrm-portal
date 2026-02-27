from decimal import Decimal

from django import forms

from .models import BusinessRole


class BusinessRoleForm(forms.ModelForm):
	financial_authorization_limit = forms.DecimalField(required=False)

	class Meta:
		model = BusinessRole
		fields = [
			'code',
			'name',
			'description',
			'department_scope',
			'approval_authority_level',
			'financial_authorization_limit',
			'is_active',
		]

	def clean_financial_authorization_limit(self):
		value = self.cleaned_data.get('financial_authorization_limit', None)
		if value in (None, ''):
			return Decimal('0')
		return value
from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Email',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Email address',
                'autocomplete': 'username',
                'autofocus': 'autofocus',
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Password',
                'autocomplete': 'current-password',
            }
        )
    )
