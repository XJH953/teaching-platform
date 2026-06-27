from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from apps.accounts.models import Profile
from apps.classes.models import ClassGroup


class ProfileModelTest(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher1', password='test123'
        )
        self.student_user = User.objects.create_user(
            username='张三', password='test123'
        )
        self.class_group = ClassGroup.objects.create(
            name='语文一班',
            subject='chinese',
            teacher=self.teacher_user.profile
        )

    def test_profile_created_automatically(self):
        """创建 User 时自动创建 Profile"""
        user = User.objects.create_user(username='testuser', password='pass')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.role, 'student')  # 默认学生

    def test_teacher_role(self):
        """老师角色判断"""
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()
        self.assertTrue(self.teacher_user.profile.is_teacher)

    def test_student_role(self):
        """学生角色判断"""
        self.assertTrue(self.student_user.profile.is_student)

    def test_display_name_student_with_class(self):
        """学生显示名包含班级信息"""
        self.student_user.profile.class_group = self.class_group
        self.student_user.profile.save()
        name = self.student_user.profile.get_display_name()
        self.assertIn('语文一班', name)
        self.assertIn('张三', name)

    def test_display_name_teacher(self):
        """老师显示名"""
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()
        name = self.teacher_user.profile.get_display_name()
        self.assertEqual(name, 'teacher1')

    def test_student_cannot_be_teacher(self):
        """学生不是老师"""
        self.assertFalse(self.student_user.profile.is_teacher)


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher1', password='testpass123'
        )
        self.user.profile.role = 'teacher'
        self.user.profile.save()

    def test_login_page_returns_200(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_redirects_to_dashboard(self):
        response = self.client.post('/', {
            'username': 'teacher1',
            'password': 'testpass123',
        })
        self.assertRedirects(response, '/dashboard/')

    def test_login_invalid_credentials(self):
        response = self.client.post('/', {
            'username': 'teacher1',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)  # 返回登录页
        self.assertContains(response, '用户名或密码错误')
