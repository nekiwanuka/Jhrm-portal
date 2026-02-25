from django import forms
from django.contrib.auth.hashers import make_password

from .models import BrandingSettings


class BrandingSettingsForm(forms.ModelForm):
    class Meta:
        model = BrandingSettings
        fields = [
            'app_name',
            'tagline',
            'logo',
            'company_address',
            'company_phone',
            'company_email',
            'hr_name',
            'hr_title',
            'hr_signature',
            'primary_color',
			'primary_hover_color',
            'secondary_color',
            'accent_color',
            'sidebar_color',
            'body_bg_color',
			'footer_enabled',
			'footer_left_text',
			'footer_right_text',
			'footer_link_text',
			'footer_link_url',
			'footer_bg_color',
			'footer_text_color',
        ]
        widgets = {
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'company_address': forms.TextInput(attrs={'class': 'form-control'}),
            'company_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'hr_name': forms.TextInput(attrs={'class': 'form-control'}),
            'hr_title': forms.TextInput(attrs={'class': 'form-control'}),
            'hr_signature': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
			'primary_hover_color': forms.TextInput(attrs={'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
            'sidebar_color': forms.TextInput(attrs={'type': 'color'}),
            'body_bg_color': forms.TextInput(attrs={'type': 'color'}),
			'footer_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
			'footer_left_text': forms.TextInput(attrs={'class': 'form-control'}),
			'footer_right_text': forms.TextInput(attrs={'class': 'form-control'}),
			'footer_link_text': forms.TextInput(attrs={'class': 'form-control'}),
			'footer_link_url': forms.URLInput(attrs={'class': 'form-control'}),
			'footer_bg_color': forms.TextInput(attrs={'type': 'color'}),
			'footer_text_color': forms.TextInput(attrs={'type': 'color'}),
        }


class PublicAccessCodeForm(forms.Form):
    code = forms.CharField(
        label='Access code',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter access code'}),
        max_length=100,
    )


class PublicAccessCodeSettingsForm(forms.ModelForm):
    new_code = forms.CharField(
        label='New access code',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep current code'}),
        max_length=100,
    )

    class Meta:
        model = BrandingSettings
        fields = ['public_access_code_enabled']
        widgets = {
            'public_access_code_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        new_code = (self.cleaned_data.get('new_code') or '').strip()
        if new_code:
            obj.public_access_code_hash = make_password(new_code)
            obj.public_access_code_version = (obj.public_access_code_version or 0) + 1
        if commit:
            obj.save()
        return obj
