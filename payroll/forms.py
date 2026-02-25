from django import forms

from employees.models import Department

from .models import EmployeePayItem, PayItemType, PayrollRun, Penalty, SalaryStructure


class PayrollRunForm(forms.ModelForm):
    class Meta:
        model = PayrollRun
        fields = ['month']
        widgets = {
            'month': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class SalaryStructureForm(forms.ModelForm):
    class Meta:
        model = SalaryStructure
        fields = ['employee', 'basic_salary', 'allowances', 'deductions', 'currency', 'effective_from', 'is_active']
        widgets = {
            'effective_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class PayItemTypeForm(forms.ModelForm):
    class Meta:
        model = PayItemType
        fields = ['code', 'name', 'kind', 'taxable', 'is_active']


class EmployeePayItemForm(forms.ModelForm):
    class Meta:
        model = EmployeePayItem
        fields = ['employee', 'item_type', 'amount', 'start_date', 'end_date', 'is_recurring', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class PenaltyForm(forms.ModelForm):
    department = forms.ModelChoiceField(queryset=Department.objects.filter(is_active=True), required=False)

    class Meta:
        model = Penalty
        fields = ['employee', 'department', 'incident_date', 'applies_to_month', 'amount', 'reason', 'status', 'clearance_notes']
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'applies_to_month': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
