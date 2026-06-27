from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Task, Submission
from apps.classes.models import ClassGroup


class TaskCreateTest(TestCase):
    """作业创建测试"""

    def setUp(self):
        # 创建老师用户
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()

        # 创建班级
        self.class_group = ClassGroup.objects.create(
            name='语文一班', subject='chinese',
            teacher=self.teacher_user.profile,
        )

        # 创建学生用户
        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.save()

        # 老师登录
        self.client.login(username='teacher', password='test123')

    def test_teacher_can_create_task(self):
        """老师可以布置作业"""
        response = self.client.post(reverse('assignments:create'), {
            'title': '古诗背诵',
            'description': '背诵《静夜思》',
            'class_group': self.class_group.pk,
            'due_date': '2026-07-01T23:59',
        })
        self.assertRedirects(response, reverse('assignments:list'))

        task = Task.objects.get(title='古诗背诵')
        self.assertEqual(task.teacher, self.teacher_user.profile)
        self.assertEqual(task.class_group, self.class_group)
        self.assertEqual(task.description, '背诵《静夜思》')

    def test_task_appears_in_list(self):
        """布置的作业出现在列表中"""
        task = Task.objects.create(
            title='古诗背诵',
            description='背诵《静夜思》',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )
        response = self.client.get(reverse('assignments:list'))
        self.assertContains(response, '古诗背诵')
        self.assertContains(response, '语文一班')

    def test_non_teacher_cannot_create(self):
        """学生不能布置作业"""
        self.client.login(username='student', password='test123')

        response = self.client.post(reverse('assignments:create'), {
            'title': '学生偷布置作业',
            'description': '不应成功',
            'class_group': self.class_group.pk,
            'due_date': '2026-07-01T23:59',
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertFalse(Task.objects.filter(title='学生偷布置作业').exists())

    def test_only_teacher_classes_in_dropdown(self):
        """表单中只显示本老师的班级"""
        other_teacher = User.objects.create_user(username='other_teacher', password='test123')
        other_teacher.profile.role = 'teacher'
        other_teacher.profile.save()

        ClassGroup.objects.create(
            name='其他班级', subject='politics',
            teacher=other_teacher.profile,
        )

        response = self.client.get(reverse('assignments:create'))
        self.assertContains(response, '语文一班')
        self.assertNotContains(response, '其他班级')

    def test_create_requires_login(self):
        """未登录不能访问创建页面"""
        self.client.logout()
        response = self.client.get(reverse('assignments:create'))
        self.assertEqual(response.status_code, 302)


class TaskDetailTest(TestCase):
    """作业详情与提交列表测试"""

    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()

        self.class_group = ClassGroup.objects.create(
            name='语文一班', subject='chinese',
            teacher=self.teacher_user.profile,
        )

        self.task = Task.objects.create(
            title='古诗背诵',
            description='背诵《静夜思》',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )

        self.student1 = User.objects.create_user(username='张三', password='')
        self.student1.profile.role = 'student'
        self.student1.profile.class_group = self.class_group
        self.student1.profile.save()

        self.sub1 = Submission.objects.create(
            task=self.task, student=self.student1,
            content='床前明月光',
            status='pending',
        )

        self.client.login(username='teacher', password='test123')

    def test_detail_shows_submissions(self):
        """详情页显示提交"""
        response = self.client.get(
            reverse('assignments:detail', args=[self.task.pk])
        )
        self.assertContains(response, '张三')
        self.assertContains(response, '古诗背诵')

    def test_submission_list_shows_correct_data(self):
        """提交列表显示正确的数据"""
        response = self.client.get(
            reverse('assignments:submissions', args=[self.task.pk])
        )
        self.assertContains(response, '张三')
        self.assertContains(response, '床前明月光')

    def test_teacher_cannot_view_other_teachers_task(self):
        """老师不能查看其他老师的作业详情"""
        other_teacher = User.objects.create_user(username='other', password='test123')
        other_teacher.profile.role = 'teacher'
        other_teacher.profile.save()

        other_class = ClassGroup.objects.create(
            name='其他班级', subject='politics',
            teacher=other_teacher.profile,
        )
        other_task = Task.objects.create(
            title='其他老师的作业',
            class_group=other_class,
            teacher=other_teacher.profile,
        )

        response = self.client.get(
            reverse('assignments:detail', args=[other_task.pk])
        )
        self.assertEqual(response.status_code, 404)


class GradeAnalyticsTest(TestCase):
    """成绩分析测试"""

    def setUp(self):
        # Create teacher
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()

        # Create two classes
        self.class_a = ClassGroup.objects.create(
            name='语文一班', subject='chinese',
            teacher=self.teacher_user.profile,
        )
        self.class_b = ClassGroup.objects.create(
            name='语文二班', subject='chinese',
            teacher=self.teacher_user.profile,
        )

        # Create students
        self.student1 = User.objects.create_user(username='student1', password='test123')
        self.student1.profile.role = 'student'
        self.student1.profile.class_group = self.class_a
        self.student1.profile.save()

        self.student2 = User.objects.create_user(username='student2', password='test123')
        self.student2.profile.role = 'student'
        self.student2.profile.class_group = self.class_a
        self.student2.profile.save()

        # Create tasks
        self.task1 = Task.objects.create(
            title='古诗背诵', class_group=self.class_a,
            teacher=self.teacher_user.profile,
        )
        self.task2 = Task.objects.create(
            title='作文写作', class_group=self.class_a,
            teacher=self.teacher_user.profile,
        )

        # Create graded submissions
        Submission.objects.create(
            task=self.task1, student=self.student1,
            content='答案1', score=80, status='graded',
        )
        Submission.objects.create(
            task=self.task1, student=self.student2,
            content='答案2', score=90, status='graded',
        )
        Submission.objects.create(
            task=self.task2, student=self.student1,
            content='作文1', score=85, status='graded',
        )
        # Pending submission (should not affect averages)
        Submission.objects.create(
            task=self.task2, student=self.student2,
            content='作文2', score=None, status='pending',
        )

    def test_teacher_can_access_analytics(self):
        """老师可以访问成绩分析页面"""
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('assignments:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '成绩分析')

    def test_student_cannot_access_analytics(self):
        """学生不能访问成绩分析页面"""
        self.client.login(username='student1', password='test123')
        response = self.client.get(reverse('assignments:analytics'))
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_correct_averages_computed(self):
        """正确的平均分计算"""
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('assignments:analytics'))

        # Overall average: (80+90+85) / 3 = 85.0
        self.assertContains(response, '85.0')

        # Task1 avg: (80+90) / 2 = 85.0
        # Task2 avg: (85) / 1 = 85.0
        # Both show as 85.0

        # Student1 avg: (80+85) / 2 = 82.5
        self.assertContains(response, '82.5')
        # Student2 avg: (90) / 1 = 90.0
        self.assertContains(response, '90.0')

    def test_empty_state_no_assignments(self):
        """没有作业时的空状态"""
        # Create a new teacher with no assignments
        new_teacher = User.objects.create_user(
            username='newteacher', password='test123'
        )
        new_teacher.profile.role = 'teacher'
        new_teacher.profile.save()

        self.client.login(username='newteacher', password='test123')
        response = self.client.get(reverse('assignments:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '暂无作业数据')

    def test_analytics_shows_assignment_titles(self):
        """分析页显示作业标题"""
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('assignments:analytics'))
        self.assertContains(response, '古诗背诵')
        self.assertContains(response, '作文写作')

    def test_analytics_shows_class_info(self):
        """分析页显示班级信息"""
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('assignments:analytics'))
        self.assertContains(response, '语文一班')
        self.assertContains(response, '语文二班')

    def test_analytics_requires_login(self):
        """成绩分析页需要登录"""
        self.client.logout()
        response = self.client.get(reverse('assignments:analytics'))
        self.assertEqual(response.status_code, 302)
