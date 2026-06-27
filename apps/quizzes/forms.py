from django import forms
from .models import Quiz, Question


class QuizCreateForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'class_group']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '测验标题'
            }),
            'class_group': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'title': '标题',
            'class_group': '班级',
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if self.teacher:
            self.fields['class_group'].queryset = (
                self.teacher.taught_classes.all()
            )


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 3, 'placeholder': '输入题目内容'
            }),
            'option_a': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '选项A'
            }),
            'option_b': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '选项B'
            }),
            'option_c': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '选项C'
            }),
            'option_d': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '选项D'
            }),
            'correct': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'text': '题目',
            'option_a': '选项A',
            'option_b': '选项B',
            'option_c': '选项C',
            'option_d': '选项D',
            'correct': '正确答案',
        }
