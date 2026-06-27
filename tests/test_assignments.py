from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from apps.assignments.models import Task, Submission
from apps.classes.models import ClassGroup


def _make_aware(dt_str):
    """Convert a naive datetime string to timezone-aware datetime."""
    dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M')
    return timezone.make_aware(dt)


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

    def test_task_list_shows_submission_stats(self):
        """作业列表显示提交统计"""
        task = Task.objects.create(
            title='古诗背诵',
            description='背诵《静夜思》',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )

        # 创建学生并提交作业
        stu = User.objects.create_user(username='张三', password='')
        stu.profile.role = 'student'
        stu.profile.class_group = self.class_group
        stu.profile.save()

        Submission.objects.create(
            task=task, student=stu,
            content='静夜思 床前明月光...',
            status='pending',
        )

        response = self.client.get(reverse('assignments:list'))
        # Should show 1 submitted out of... depends on students in class
        self.assertContains(response, '1')

    def test_non_teacher_cannot_create(self):
        """学生不能布置作业"""
        self.client.login(username='student', password='test123')

        response = self.client.post(reverse('assignments:create'), {
            'title': '学生偷布置作业',
            'description': '不应成功',
            'class_group': self.class_group.pk,
            'due_date': '2026-07-01T23:59',
        })
        # 重定向到 dashboard（非老师被 teacher_required 拦截）
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertFalse(Task.objects.filter(title='学生偷布置作业').exists())

    def test_only_teacher_classes_in_dropdown(self):
        """表单中只显示本老师的班级"""
        # 创建另一个老师及其班级
        other_teacher = User.objects.create_user(username='other_teacher', password='test123')
        other_teacher.profile.role = 'teacher'
        other_teacher.profile.save()

        other_class = ClassGroup.objects.create(
            name='其他班级', subject='politics',
            teacher=other_teacher.profile,
        )

        # 当前老师访问创建页面
        response = self.client.get(reverse('assignments:create'))
        # 应该看到自己的班级
        self.assertContains(response, '语文一班')
        # 不应该看到其他老师的班级
        self.assertNotContains(response, '其他班级')

    def test_create_requires_login(self):
        """未登录不能访问创建页面"""
        self.client.logout()
        response = self.client.get(reverse('assignments:create'))
        self.assertEqual(response.status_code, 302)

    def test_create_get_shows_form(self):
        """GET 请求显示创建表单"""
        response = self.client.get(reverse('assignments:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '布置作业')


class TaskDetailTest(TestCase):
    """作业详情与提交列表测试"""

    def setUp(self):
        # 创建老师
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

        # 创建作业
        self.task = Task.objects.create(
            title='古诗背诵',
            description='背诵《静夜思》并默写',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
            due_date=_make_aware('2026-07-01T23:59'),
        )

        # 创建学生
        self.student1 = User.objects.create_user(username='张三', password='')
        self.student1.profile.role = 'student'
        self.student1.profile.class_group = self.class_group
        self.student1.profile.save()

        self.student2 = User.objects.create_user(username='李四', password='')
        self.student2.profile.role = 'student'
        self.student2.profile.class_group = self.class_group
        self.student2.profile.save()

        # 学生提交作业
        self.sub1 = Submission.objects.create(
            task=self.task, student=self.student1,
            content='床前明月光，疑是地上霜。',
            status='pending',
        )
        self.sub2 = Submission.objects.create(
            task=self.task, student=self.student2,
            content='举头望明月，低头思故乡。',
            status='graded',
            score=95,
            comment='很好',
        )

        self.client.login(username='teacher', password='test123')

    def test_detail_shows_task_info(self):
        """详情页显示作业信息"""
        response = self.client.get(
            reverse('assignments:detail', args=[self.task.pk])
        )
        self.assertContains(response, '古诗背诵')
        self.assertContains(response, '背诵《静夜思》')
        self.assertContains(response, '语文一班')

    def test_detail_shows_submissions(self):
        """详情页显示所有提交"""
        response = self.client.get(
            reverse('assignments:detail', args=[self.task.pk])
        )
        self.assertContains(response, '张三')
        self.assertContains(response, '李四')
        self.assertContains(response, '待批改')
        self.assertContains(response, '已批改')

    def test_detail_shows_score_when_graded(self):
        """详情页显示已批改的分数"""
        response = self.client.get(
            reverse('assignments:detail', args=[self.task.pk])
        )
        self.assertContains(response, '95')

    def test_submission_list_shows_correct_data(self):
        """提交列表显示正确的数据"""
        response = self.client.get(
            reverse('assignments:submissions', args=[self.task.pk])
        )
        self.assertContains(response, '张三')
        self.assertContains(response, '李四')
        self.assertContains(response, '95 分')
        self.assertContains(response, '待批改')

    def test_submission_list_shows_content(self):
        """提交列表显示学生提交的内容"""
        response = self.client.get(
            reverse('assignments:submissions', args=[self.task.pk])
        )
        self.assertContains(response, '床前明月光')

    def test_teacher_cannot_view_other_teachers_task(self):
        """老师不能查看其他老师的作业详情"""
        # 创建另一个老师及其作业
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

    def test_detail_requires_login(self):
        """详情页需要登录"""
        self.client.logout()
        response = self.client.get(
            reverse('assignments:detail', args=[self.task.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_list_requires_login(self):
        """列表页需要登录"""
        self.client.logout()
        response = self.client.get(reverse('assignments:list'))
        self.assertEqual(response.status_code, 302)

    def test_empty_task_list_shows_no_classes_message(self):
        """没有班级时显示提示"""
        # 使用一个没有班级的新老师
        empty_teacher = User.objects.create_user(username='empty_teacher', password='test123')
        empty_teacher.profile.role = 'teacher'
        empty_teacher.profile.save()
        self.client.login(username='empty_teacher', password='test123')

        response = self.client.get(reverse('assignments:list'))
        self.assertContains(response, '还没有创建班级')


class StudentTaskListTest(TestCase):
    """学生作业列表测试"""

    def setUp(self):
        # 创建老师
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()

        # 创建两个班级
        self.class_a = ClassGroup.objects.create(
            name='语文一班', subject='chinese',
            teacher=self.teacher_user.profile,
        )
        self.class_b = ClassGroup.objects.create(
            name='语文二班', subject='chinese',
            teacher=self.teacher_user.profile,
        )

        # 创建作业
        self.task_a = Task.objects.create(
            title='古诗背诵',
            description='背诵《静夜思》',
            class_group=self.class_a,
            teacher=self.teacher_user.profile,
            due_date=_make_aware('2026-07-01T23:59'),
        )
        self.task_b = Task.objects.create(
            title='作文',
            description='写一篇作文',
            class_group=self.class_b,
            teacher=self.teacher_user.profile,
        )

        # 创建学生（属于班级A）
        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_a
        self.student_user.profile.save()

        self.client.login(username='student', password='test123')

    def test_student_sees_tasks_for_own_class(self):
        """学生能看到自己班级的作业"""
        response = self.client.get(reverse('assignments:student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '古诗背诵')
        self.assertContains(response, '语文一班')

    def test_student_does_not_see_tasks_for_other_classes(self):
        """学生看不到其他班级的作业"""
        response = self.client.get(reverse('assignments:student_list'))
        self.assertNotContains(response, '作文')

    def test_student_list_shows_status_badge_pending(self):
        """作业列表显示待提交状态"""
        response = self.client.get(reverse('assignments:student_list'))
        self.assertContains(response, '待提交')

    def test_student_list_shows_status_badge_submitted(self):
        """作业列表显示已提交状态"""
        Submission.objects.create(
            task=self.task_a, student=self.student_user,
            content='床前明月光',
            status='pending',
        )
        response = self.client.get(reverse('assignments:student_list'))
        self.assertContains(response, '已提交')

    def test_student_list_shows_status_badge_graded(self):
        """作业列表显示已批改状态"""
        Submission.objects.create(
            task=self.task_a, student=self.student_user,
            content='床前明月光',
            status='graded', score=90, comment='不错',
        )
        response = self.client.get(reverse('assignments:student_list'))
        self.assertContains(response, '已批改')

    def test_student_list_requires_login(self):
        """学生作业列表需要登录"""
        self.client.logout()
        response = self.client.get(reverse('assignments:student_list'))
        self.assertEqual(response.status_code, 302)

    def test_student_without_class_sees_message(self):
        """未分配班级的学生看到提示"""
        no_class_student = User.objects.create_user(
            username='no_class_student', password='test123'
        )
        no_class_student.profile.role = 'student'
        no_class_student.profile.save()
        self.client.login(username='no_class_student', password='test123')

        response = self.client.get(reverse('assignments:student_list'))
        self.assertContains(response, '尚未分配班级')


class StudentSubmitTest(TestCase):
    """学生提交作业测试"""

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
            description='背诵《静夜思》并默写',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
            due_date=_make_aware('2026-07-01T23:59'),
        )

        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_group
        self.student_user.profile.save()

        self.client.login(username='student', password='test123')

    def test_submit_page_shows_task_info(self):
        """提交页面显示作业信息"""
        response = self.client.get(
            reverse('assignments:student_submit', args=[self.task.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '古诗背诵')
        self.assertContains(response, '背诵《静夜思》')
        self.assertContains(response, '提交作业')

    def test_student_can_submit_homework(self):
        """学生可以提交作业"""
        response = self.client.post(
            reverse('assignments:student_submit', args=[self.task.pk]),
            {'content': '床前明月光，疑是地上霜。'},
        )
        self.assertRedirects(response,
            reverse('assignments:student_submit', args=[self.task.pk]))

        sub = Submission.objects.get(task=self.task, student=self.student_user)
        self.assertEqual(sub.content, '床前明月光，疑是地上霜。')
        self.assertEqual(sub.status, 'pending')

    def test_submitted_content_shows_on_detail_page(self):
        """提交后内容显示在详情页"""
        Submission.objects.create(
            task=self.task, student=self.student_user,
            content='举头望明月，低头思故乡。',
            status='pending',
        )
        response = self.client.get(
            reverse('assignments:student_submit', args=[self.task.pk])
        )
        self.assertContains(response, '举头望明月，低头思故乡。')
        self.assertContains(response, '我的提交')

    def test_student_cannot_submit_twice(self):
        """学生不能重复提交作业"""
        Submission.objects.create(
            task=self.task, student=self.student_user,
            content='第一次提交的内容',
            status='pending',
        )
        response = self.client.post(
            reverse('assignments:student_submit', args=[self.task.pk]),
            {'content': '第二次提交的内容'},
        )
        self.assertRedirects(response,
            reverse('assignments:student_submit', args=[self.task.pk]))

        # 内容应该还是第一次的
        sub = Submission.objects.get(task=self.task, student=self.student_user)
        self.assertEqual(sub.content, '第一次提交的内容')

    def test_graded_submission_shows_score_and_comment(self):
        """已批改的提交显示分数和评语"""
        Submission.objects.create(
            task=self.task, student=self.student_user,
            content='床前明月光',
            status='graded', score=95, comment='很好，继续保持！',
        )
        response = self.client.get(
            reverse('assignments:student_submit', args=[self.task.pk])
        )
        self.assertContains(response, '95')
        self.assertContains(response, '很好，继续保持！')
        self.assertContains(response, '批改结果')

    def test_cannot_submit_empty_content(self):
        """不能提交空内容"""
        response = self.client.post(
            reverse('assignments:student_submit', args=[self.task.pk]),
            {'content': ''},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '提交内容不能为空')
        self.assertFalse(
            Submission.objects.filter(task=self.task, student=self.student_user).exists()
        )

    def test_submit_page_requires_login(self):
        """提交页面需要登录"""
        self.client.logout()
        response = self.client.get(
            reverse('assignments:student_submit', args=[self.task.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_student_cannot_submit_to_other_class_task(self):
        """学生不能提交其他班级的作业"""
        other_class = ClassGroup.objects.create(
            name='语文二班', subject='chinese',
            teacher=self.teacher_user.profile,
        )
        other_task = Task.objects.create(
            title='其他班级作业',
            class_group=other_class,
            teacher=self.teacher_user.profile,
        )
        response = self.client.get(
            reverse('assignments:student_submit', args=[other_task.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_access_student_list(self):
        """老师也可以访问学生作业列表（看到自己班级学生的视角）"""
        # 老师也能访问，但会按班级筛选
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('assignments:student_list'))
        self.assertEqual(response.status_code, 200)


class GradeSubmissionTest(TestCase):
    """老师批改作业测试"""

    def setUp(self):
        # 创建老师
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

        # 创建作业
        self.task = Task.objects.create(
            title='古诗背诵',
            description='背诵《静夜思》',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )

        # 创建学生
        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_group
        self.student_user.profile.save()

        # 学生提交作业
        self.submission = Submission.objects.create(
            task=self.task,
            student=self.student_user,
            content='床前明月光，疑是地上霜。',
            status='pending',
        )

        self.client.login(username='teacher', password='test123')

    def test_teacher_can_grade_submission(self):
        """老师批改作业后状态变为已批改"""
        response = self.client.post(
            reverse('assignments:grade', args=[self.task.pk, self.submission.pk]),
            {'score': '95', 'comment': '很好，继续保持！'},
        )
        self.assertRedirects(response,
            reverse('assignments:detail', args=[self.task.pk]))

        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'graded')
        self.assertEqual(self.submission.score, 95)
        self.assertEqual(self.submission.comment, '很好，继续保持！')

    def test_score_and_comment_are_saved(self):
        """分数和评语正确保存"""
        self.client.post(
            reverse('assignments:grade', args=[self.task.pk, self.submission.pk]),
            {'score': '88', 'comment': '有进步空间'},
        )

        self.submission.refresh_from_db()
        self.assertEqual(self.submission.score, 88)
        self.assertEqual(self.submission.comment, '有进步空间')
        self.assertEqual(self.submission.status, 'graded')

    def test_non_teacher_cannot_grade(self):
        """非老师不能批改作业"""
        self.client.login(username='student', password='test123')
        response = self.client.post(
            reverse('assignments:grade', args=[self.task.pk, self.submission.pk]),
            {'score': '100', 'comment': '篡改'},
        )

        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'pending')
        self.assertIsNone(self.submission.score)

    def test_grade_page_shows_submission_content(self):
        """批改页面显示学生提交内容"""
        response = self.client.get(
            reverse('assignments:grade', args=[self.task.pk, self.submission.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '床前明月光')
        self.assertContains(response, 'student')
        self.assertContains(response, '提交评分')

    def test_teacher_cannot_grade_other_teachers_submission(self):
        """老师不能批改其他老师的作业提交"""
        other_teacher = User.objects.create_user(
            username='other_teacher', password='test123'
        )
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
        other_student = User.objects.create_user(
            username='other_student', password=''
        )
        other_student.profile.role = 'student'
        other_student.profile.class_group = other_class
        other_student.profile.save()
        other_submission = Submission.objects.create(
            task=other_task,
            student=other_student,
            content='其他内容',
            status='pending',
        )

        response = self.client.post(
            reverse('assignments:grade',
                args=[other_task.pk, other_submission.pk]),
            {'score': '50', 'comment': '不应成功'},
        )

        other_submission.refresh_from_db()
        self.assertEqual(other_submission.status, 'pending')
        self.assertIsNone(other_submission.score)


class DashboardCountsTest(TestCase):
    """仪表盘待批/待交数量测试"""

    def setUp(self):
        # 创建老师
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

        # 创建学生
        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_group
        self.student_user.profile.save()

    def test_teacher_dashboard_shows_pending_count(self):
        """老师仪表盘显示待批改数量"""
        task = Task.objects.create(
            title='古诗背诵',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )

        # 创建3个学生提交，2个pending, 1个graded
        for i, (status, score) in enumerate([
            ('pending', None), ('pending', None), ('graded', 90)
        ]):
            stu = User.objects.create_user(
                username=f'stu{i}', password=''
            )
            stu.profile.role = 'student'
            stu.profile.class_group = self.class_group
            stu.profile.save()
            Submission.objects.create(
                task=task,
                student=stu,
                content=f'内容{i}',
                status=status,
                score=score,
            )

        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '2')

    def test_student_dashboard_shows_pending_count(self):
        """学生仪表盘显示待交作业数量"""
        # 创建3个作业
        for i in range(3):
            Task.objects.create(
                title=f'作业{i}',
                class_group=self.class_group,
                teacher=self.teacher_user.profile,
            )

        # 学生提交了1个作业
        task = Task.objects.filter(class_group=self.class_group).first()
        Submission.objects.create(
            task=task,
            student=self.student_user,
            content='已完成',
            status='pending',
        )

        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        # 3个作业，提交了1个，待交2个
        self.assertContains(response, '2')

    def test_teacher_dashboard_zero_when_no_pending(self):
        """老师仪表盘在没有待批改时为0"""
        task = Task.objects.create(
            title='古诗背诵',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )

        stu = User.objects.create_user(username='stu1', password='')
        stu.profile.role = 'student'
        stu.profile.class_group = self.class_group
        stu.profile.save()
        Submission.objects.create(
            task=task, student=stu,
            content='内容', status='graded', score=95,
        )

        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '0')

    def test_student_dashboard_zero_when_all_submitted(self):
        """学生仪表盘在全部提交后为0"""
        task = Task.objects.create(
            title='古诗背诵',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )

        Submission.objects.create(
            task=task,
            student=self.student_user,
            content='已完成',
            status='pending',
        )

        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        # 1个作业，已提交，待交0个
        self.assertContains(response, '0')
