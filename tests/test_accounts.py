import json

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


class FirstLoginTest(TestCase):
    def setUp(self):
        # 创建被老师导入但未激活的学生
        self.student = User.objects.create_user(
            username='李四',
            password=''  # 无密码
        )
        self.student.is_active = False
        self.student.save()

    def test_first_login_returns_password(self):
        """首次登录返回生成的密码"""
        response = self.client.post('/first-login/', {
            'name': '李四',
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('password', data)
        self.assertEqual(len(data['password']), 8)

    def test_first_login_activates_user(self):
        """首次登录激活账号"""
        self.client.post('/first-login/', {'name': '李四'})
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_active)
        self.assertTrue(self.student.has_usable_password())

    def test_first_login_name_not_found(self):
        """不存在的姓名返回错误"""
        response = self.client.post('/first-login/', {'name': '不存在'})
        data = response.json()
        self.assertFalse(data['success'])

    def test_first_login_already_active(self):
        """已激活的账号不能再次首次登录"""
        self.student.is_active = True
        self.student.set_password('existing')
        self.student.save()
        response = self.client.post('/first-login/', {'name': '李四'})
        data = response.json()
        self.assertFalse(data['success'])


class PasswordResetTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher.profile.role = 'teacher'
        self.teacher.profile.save()

        self.student = User.objects.create_user(
            username='张三', password='oldpass'
        )
        self.student.profile.save()

        # 创建班级并将学生关联到老师的班级
        self.class_group = ClassGroup.objects.create(
            name='语文一班',
            subject='chinese',
            teacher=self.teacher.profile
        )
        self.student.profile.class_group = self.class_group
        self.student.profile.save()

        self.client.login(username='teacher', password='test123')

    def test_reset_password_as_teacher(self):
        old_hash = self.student.password
        response = self.client.post(
            reverse('accounts:reset_password', args=[self.student.id])
        )
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('password', data)

        self.student.refresh_from_db()
        self.assertNotEqual(self.student.password, old_hash)

    def test_non_teacher_cannot_reset(self):
        student_user = User.objects.create_user(
            username='stu', password='pass'
        )
        self.client.login(username='stu', password='pass')
        response = self.client.post(
            reverse('accounts:reset_password', args=[self.student.id])
        )
        self.assertNotEqual(response.status_code, 200)
