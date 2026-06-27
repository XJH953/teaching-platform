from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from apps.classes.models import ClassGroup


class ClassManagementTest(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()
        self.client.login(username='teacher', password='test123')

    def test_create_class(self):
        response = self.client.post(reverse('classes:create'), {
            'name': '语文一班',
            'subject': 'chinese',
            'student_names': '张三\n李四\n王五',
        })
        self.assertRedirects(response, reverse('classes:list'))

        cg = ClassGroup.objects.get(name='语文一班')
        self.assertEqual(cg.student_count, 3)

        # 验证学生账号已创建且未激活
        zhang = User.objects.get(username='张三')
        self.assertFalse(zhang.is_active)

    def test_class_list(self):
        ClassGroup.objects.create(
            name='语文一班', subject='chinese',
            teacher=self.teacher_user.profile
        )
        response = self.client.get(reverse('classes:list'))
        self.assertContains(response, '语文一班')

    def test_class_detail(self):
        cg = ClassGroup.objects.create(
            name='语文一班', subject='chinese',
            teacher=self.teacher_user.profile
        )
        # 添加学生
        stu = User.objects.create_user(username='张三', password='')
        stu.is_active = False
        stu.profile.class_group = cg
        stu.profile.save()
        stu.save()

        response = self.client.get(reverse('classes:detail', args=[cg.id]))
        self.assertContains(response, '张三')

    def test_create_class_no_student_names(self):
        """不填学生也可以创建班级"""
        response = self.client.post(reverse('classes:create'), {
            'name': '空班',
            'subject': 'politics',
            'student_names': '',
        })
        self.assertEqual(ClassGroup.objects.count(), 1)

    def test_duplicate_student_name_in_same_class(self):
        """同班重名应提示错误"""
        response = self.client.post(reverse('classes:create'), {
            'name': '语文一班',
            'subject': 'chinese',
            'student_names': '张三\n张三',
        })
        self.assertContains(response, '重复')  # 应包含错误提示

    def test_non_teacher_cannot_create_class(self):
        """学生不能创建班级"""
        student = User.objects.create_user(username='stu', password='pass')
        student.profile.role = 'student'
        student.profile.save()
        self.client.login(username='stu', password='pass')

        response = self.client.post(reverse('classes:create'), {
            'name': '黑班级', 'subject': 'chinese', 'student_names': ''
        })
        self.assertEqual(response.status_code, 302)  # 重定向或403
