from django import forms
from .models import ClassGroup


class ClassCreateForm(forms.ModelForm):
    student_names = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 8,
            'placeholder': '每行一个学生姓名，例如：\n张三\n李四\n王五\n\n如有重名，请手动加后缀区分（张三1、张三2）',
        }),
        required=False,
        label='学生名单'
    )

    class Meta:
        model = ClassGroup
        fields = ['name', 'subject']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '例如：语文一班',
            }),
            'subject': forms.Select(attrs={
                'class': 'form-input',
            }),
        }
        labels = {
            'name': '班级名称',
            'subject': '学科',
        }

    def clean_student_names(self):
        names = self.cleaned_data['student_names'].strip()
        if not names:
            return []

        name_list = [n.strip() for n in names.split('\n') if n.strip()]

        # 检查重名
        seen = set()
        for n in name_list:
            if n in seen:
                raise forms.ValidationError(f'名单中有重复的姓名：{n}')
            seen.add(n)

        # 检查是否与现有学生冲突
        from django.contrib.auth.models import User
        existing = User.objects.filter(
            username__in=name_list, is_active=True
        ).values_list('username', flat=True)
        if existing:
            raise forms.ValidationError(
                f'以下学生已激活账号：{", ".join(existing)}'
            )

        return name_list
