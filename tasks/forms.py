from django import forms

from .models import Task


class TaskForm(forms.ModelForm):

    def clean(self):
        cleaned = super().clean()
        visibility = cleaned.get('visibility')
        visible_to = cleaned.get('visible_to')
        if visibility == Task.VISIBILITY_USER and not visible_to:
            assigned_to = cleaned.get('assigned_to')
            if assigned_to:
                cleaned['visible_to'] = assigned_to
            else:
                self.add_error('visible_to', 'Select a user for a personal task.')
        return cleaned

    class Meta:
        model = Task
        fields = ['title', 'description', 'visibility', 'visible_to', 'assigned_to', 'status', 'progress', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
            'visible_to': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'progress': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
