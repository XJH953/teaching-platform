from django import forms
from .models import Resource


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'content', 'file', 'subject']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '课件标题'}),
            'content': forms.Textarea(attrs={'class': 'form-input', 'rows': 12, 'placeholder': '正文内容（可选）'}),
            'file': forms.FileInput(attrs={'class': 'form-input'}),
            'subject': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'title': '标题',
            'content': '内容',
            'file': '附件',
            'subject': '学科',
        }
