from django import forms

from .models import Notice, NoticeComment


class NoticeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            can_manage = user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER'}
            if not can_manage and 'is_public' in self.fields:
                self.fields.pop('is_public')

    class Meta:
        model = Notice
        fields = ['title', 'content', 'is_public', 'expiry_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class NoticeCommentForm(forms.ModelForm):

    class Meta:
        model = NoticeComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write a comment...'}),
        }
