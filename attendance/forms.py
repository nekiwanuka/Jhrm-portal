from django import forms

from .models import AttendanceRecord


class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['employee', 'date', 'check_in', 'check_out', 'is_late']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_in': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'check_out': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
