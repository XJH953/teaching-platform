from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'class_group', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '作业标题'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 8, 'placeholder': '作业要求和说明'}),
            'class_group': forms.Select(attrs={'class': 'form-input'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }
        labels = {
            'title': '标题',
            'description': '要求',
            'class_group': '班级',
            'due_date': '截止时间',
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if self.teacher:
            # Only show classes belonging to this teacher
            self.fields['class_group'].queryset = self.teacher.taught_classes.all()
