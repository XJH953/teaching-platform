from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from apps.assignments.models import Task, Submission
from apps.classes.models import ClassGroup


def _make_aware(dt_str):
    dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M')
    return timezone.make_aware(dt)


def _create_task(**kwargs):
    """Helper: create a task with M2M class_groups"""
    class_groups = kwargs.pop('class_groups', None)
    task = Task.objects.create(**kwargs)
    if class_groups:
        task.class_groups.add(*class_groups)
    return task


class TaskCreateTest(TestCase):

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

        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.save()

        self.client.login(username='teacher', password='test123')

    def test_teacher_can_create_task(self):
        response = self.client.post(reverse('assignments:create'), {
            'title': '古诗背诵',
            'description': '背诵《静夜思》',
            'class_groups': [self.class_group.pk],
            'due_date': '2026-07-01T23:59',
        })
        self.assertRedirects(response, reverse('assignments:list'))

        task = Task.objects.get(title='古诗背诵')
        self.assertEqual(task.teacher, self.teacher_user.profile)
        self.assertIn(self.class_group, task.class_groups.all())

    def test_task_appears_in_list(self):
        _create_task(
            title='古诗背诵',
            description='背诵《静夜思》',
            class_groups=[self.class_group],
            teacher=self.teacher_user.profile,
        )
        response = self.client.get(reverse('assignments:list'))
        self.assertContains(response, '古诗背诵')
        self.assertContains(response, '语文一班')

    def test_task_list_shows_submission_stats(self):
        task = _create_task(
            title='古诗背诵',
            class_groups=[self.class_group],
            teacher=self.teacher_user.profile,
        )
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
        self.assertContains(response, '1')

    def test_non_teacher_cannot_create(self):
        self.client.login(username='student', password='test123')
        response = self.client.post(reverse('assignments:create'), {
            'title': '学生偷布置作业',
            'class_groups': [self.class_group.pk],
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_only_teacher_classes_in_dropdown(self):
        other_teacher = User.objects.create_user(username='other', password='test123')
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
        self.client.logout()
        response = self.client.get(reverse('assignments:create'))
        self.assertEqual(response.status_code, 302)

    def test_create_get_shows_form(self):
        response = self.client.get(reverse('assignments:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '布置作业')


class TaskDetailTest(TestCase):

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

        self.task = _create_task(
            title='古诗背诵',
            description='背诵《静夜思》并默写',
            class_groups=[self.class_group],
            teacher=self.teacher_user.profile,
            due_date=_make_aware('2026-07-01T23:59'),
        )

        self.student1 = User.objects.create_user(username='张三', password='')
        self.student1.profile.role = 'student'
        self.student1.profile.class_group = self.class_group
        self.student1.profile.save()

        self.student2 = User.objects.create_user(username='李四', password='')
        self.student2.profile.role = 'student'
        self.student2.profile.class_group = self.class_group
        self.student2.profile.save()

        self.sub1 = Submission.objects.create(
            task=self.task, student=self.student1,
            content='床前明月光，疑是地上霜。',
            status='pending',
        )
        self.sub2 = Submission.objects.create(
            task=self.task, student=self.student2,
            content='举头望明月，低头思故乡。',
            status='graded', score=95, comment='很好',
        )

        self.client.login(username='teacher', password='test123')

    def test_detail_shows_task_info(self):
        response = self.client.get(reverse('assignments:detail', args=[self.task.pk]))
        self.assertContains(response, '古诗背诵')
        self.assertContains(response, '背诵《静夜思》')
        self.assertContains(response, '语文一班')

    def test_detail_shows_submissions(self):
        response = self.client.get(reverse('assignments:detail', args=[self.task.pk]))
        self.assertContains(response, '张三')
        self.assertContains(response, '李四')
        self.assertContains(response, '待批改')
        self.assertContains(response, '已批改')

    def test_detail_shows_score_when_graded(self):
        response = self.client.get(reverse('assignments:detail', args=[self.task.pk]))
        self.assertContains(response, '95')

    def test_submission_list_shows_correct_data(self):
        response = self.client.get(reverse('assignments:submissions', args=[self.task.pk]))
        self.assertContains(response, '张三')
        self.assertContains(response, '95 分')

    def test_submission_list_shows_content(self):
        response = self.client.get(reverse('assignments:submissions', args=[self.task.pk]))
        self.assertContains(response, '床前明月光')

    def test_teacher_cannot_view_other_teachers_task(self):
        other_teacher = User.objects.create_user(username='other', password='test123')
        other_teacher.profile.role = 'teacher'
        other_teacher.profile.save()

        other_class = ClassGroup.objects.create(
            name='其他班级', subject='politics',
            teacher=other_teacher.profile,
        )
        other_task = _create_task(
            title='其他老师的作业',
            class_groups=[other_class],
            teacher=other_teacher.profile,
        )
        response = self.client.get(reverse('assignments:detail', args=[other_task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_detail_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('assignments:detail', args=[self.task.pk]))
        self.assertEqual(response.status_code, 302)

    def test_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('assignments:list'))
        self.assertEqual(response.status_code, 302)

    def test_empty_task_list_shows_no_classes_message(self):
        empty_teacher = User.objects.create_user(username='empty', password='test123')
        empty_teacher.profile.role = 'teacher'
        empty_teacher.profile.save()
        self.client.login(username='empty', password='test123')
        response = self.client.get(reverse('assignments:list'))
        self.assertContains(response, '还没有布置过作业')


class StudentTaskListTest(TestCase):

    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()

        self.class_a = ClassGroup.objects.create(
            name='语文一班', subject='chinese',
            teacher=self.teacher_user.profile,
        )
        self.class_b = ClassGroup.objects.create(
            name='语文二班', subject='chinese',
            teacher=self.teacher_user.profile,
        )

        self.task_a = _create_task(
            title='古诗背诵', class_groups=[self.class_a],
            teacher=self.teacher_user.profile,
            due_date=_make_aware('2026-07-01T23:59'),
        )
        self.task_b = _create_task(
            title='作文', class_groups=[self.class_b],
            teacher=self.teacher_user.profile,
        )

        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_a
        self.student_user.profile.save()

        self.client.login(username='student', password='test123')

    def test_student_sees_tasks_for_own_class(self):
        response = self.client.get(reverse('assignments:student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '古诗背诵')

    def test_student_does_not_see_tasks_for_other_classes(self):
        response = self.client.get(reverse('assignments:student_list'))
        self.assertNotContains(response, '作文')

    def test_student_list_shows_status_badge_pending(self):
        response = self.client.get(reverse('assignments:student_list'))
        self.assertContains(response, '待提交')

    def test_student_list_shows_status_badge_submitted(self):
        Submission.objects.create(
            task=self.task_a, student=self.student_user,
            content='床前明月光', status='pending',
        )
        response = self.client.get(reverse('assignments:student_list'))
        self.assertContains(response, '已提交')

    def test_student_list_shows_status_badge_graded(self):
        Submission.objects.create(
            task=self.task_a, student=self.student_user,
            content='床前明月光', status='graded', score=90,
        )
        response = self.client.get(reverse('assignments:student_list'))
        self.assertContains(response, '已批改')

    def test_student_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('assignments:student_list'))
        self.assertEqual(response.status_code, 302)

    def test_student_without_class_sees_message(self):
        no_class = User.objects.create_user(username='no_class', password='test123')
        no_class.profile.role = 'student'
        no_class.profile.save()
        self.client.login(username='no_class', password='test123')
        response = self.client.get(reverse('assignments:student_list'))
        self.assertContains(response, '尚未分配班级')


class StudentSubmitTest(TestCase):

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

        self.task = _create_task(
            title='古诗背诵',
            description='背诵《静夜思》并默写',
            class_groups=[self.class_group],
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
        response = self.client.get(
            reverse('assignments:student_submit', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '古诗背诵')
        self.assertContains(response, '提交作业')

    def test_student_can_submit_homework(self):
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
        Submission.objects.create(
            task=self.task, student=self.student_user,
            content='举头望明月', status='pending',
        )
        response = self.client.get(
            reverse('assignments:student_submit', args=[self.task.pk]))
        self.assertContains(response, '举头望明月')
        self.assertContains(response, '我的提交')

    def test_student_cannot_submit_twice(self):
        Submission.objects.create(
            task=self.task, student=self.student_user,
            content='第一次提交', status='pending',
        )
        response = self.client.post(
            reverse('assignments:student_submit', args=[self.task.pk]),
            {'content': '第二次提交'},
        )
        self.assertRedirects(response,
            reverse('assignments:student_submit', args=[self.task.pk]))
        sub = Submission.objects.get(task=self.task, student=self.student_user)
        self.assertEqual(sub.content, '第一次提交')

    def test_graded_submission_shows_score_and_comment(self):
        Submission.objects.create(
            task=self.task, student=self.student_user,
            content='床前明月光', status='graded',
            score=95, comment='很好！',
        )
        response = self.client.get(
            reverse('assignments:student_submit', args=[self.task.pk]))
        self.assertContains(response, '95')
        self.assertContains(response, '很好！')
        self.assertContains(response, '批改结果')

    def test_cannot_submit_empty_content(self):
        response = self.client.post(
            reverse('assignments:student_submit', args=[self.task.pk]),
            {'content': ''},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '请填写文字内容或上传文件')

    def test_submit_page_requires_login(self):
        self.client.logout()
        response = self.client.get(
            reverse('assignments:student_submit', args=[self.task.pk]))
        self.assertEqual(response.status_code, 302)

    def test_student_cannot_submit_to_other_class_task(self):
        other_class = ClassGroup.objects.create(
            name='语文二班', subject='chinese',
            teacher=self.teacher_user.profile,
        )
        other_task = _create_task(
            title='其他班级作业', class_groups=[other_class],
            teacher=self.teacher_user.profile,
        )
        response = self.client.get(
            reverse('assignments:student_submit', args=[other_task.pk]))
        self.assertEqual(response.status_code, 404)


class GradeSubmissionTest(TestCase):

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

        self.task = _create_task(
            title='古诗背诵', class_groups=[self.class_group],
            teacher=self.teacher_user.profile,
        )

        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_group
        self.student_user.profile.save()

        self.submission = Submission.objects.create(
            task=self.task, student=self.student_user,
            content='床前明月光', status='pending',
        )

        self.client.login(username='teacher', password='test123')

    def test_teacher_can_grade_submission(self):
        response = self.client.post(
            reverse('assignments:grade', args=[self.task.pk, self.submission.pk]),
            {'score': '95', 'comment': '很好！'},
        )
        self.assertRedirects(response,
            reverse('assignments:detail', args=[self.task.pk]))
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'graded')
        self.assertEqual(self.submission.score, 95)
        self.assertEqual(self.submission.comment, '很好！')

    def test_score_and_comment_are_saved(self):
        self.client.post(
            reverse('assignments:grade', args=[self.task.pk, self.submission.pk]),
            {'score': '88', 'comment': '有进步空间'},
        )
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.score, 88)
        self.assertEqual(self.submission.status, 'graded')

    def test_non_teacher_cannot_grade(self):
        self.client.login(username='student', password='test123')
        self.client.post(
            reverse('assignments:grade', args=[self.task.pk, self.submission.pk]),
            {'score': '100', 'comment': '篡改'},
        )
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'pending')

    def test_grade_page_shows_submission_content(self):
        response = self.client.get(
            reverse('assignments:grade', args=[self.task.pk, self.submission.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '床前明月光')
        self.assertContains(response, '提交评分')

    def test_teacher_cannot_grade_other_teachers_submission(self):
        other_teacher = User.objects.create_user(
            username='other', password='test123')
        other_teacher.profile.role = 'teacher'
        other_teacher.profile.save()

        other_class = ClassGroup.objects.create(
            name='其他班级', subject='politics',
            teacher=other_teacher.profile,
        )
        other_task = _create_task(
            title='其他老师的作业', class_groups=[other_class],
            teacher=other_teacher.profile,
        )
        other_student = User.objects.create_user(username='other_stu', password='')
        other_student.profile.role = 'student'
        other_student.profile.class_group = other_class
        other_student.profile.save()
        other_sub = Submission.objects.create(
            task=other_task, student=other_student,
            content='其他内容', status='pending',
        )
        self.client.post(
            reverse('assignments:grade', args=[other_task.pk, other_sub.pk]),
            {'score': '50', 'comment': '不应成功'},
        )
        other_sub.refresh_from_db()
        self.assertEqual(other_sub.status, 'pending')


class DashboardCountsTest(TestCase):

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

        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_group
        self.student_user.profile.save()

    def test_teacher_dashboard_shows_pending_count(self):
        task = _create_task(
            title='古诗背诵', class_groups=[self.class_group],
            teacher=self.teacher_user.profile,
        )
        for i, (status, score) in enumerate([
            ('pending', None), ('pending', None), ('graded', 90)
        ]):
            stu = User.objects.create_user(username=f'stu{i}', password='')
            stu.profile.role = 'student'
            stu.profile.class_group = self.class_group
            stu.profile.save()
            Submission.objects.create(
                task=task, student=stu, content=f'内容{i}',
                status=status, score=score,
            )
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '2')

    def test_student_dashboard_shows_pending_count(self):
        for i in range(3):
            _create_task(
                title=f'作业{i}', class_groups=[self.class_group],
                teacher=self.teacher_user.profile,
            )
        task = Task.objects.filter(class_groups=self.class_group).first()
        Submission.objects.create(
            task=task, student=self.student_user,
            content='已完成', status='pending',
        )
        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '2')

    def test_teacher_dashboard_zero_when_no_pending(self):
        task = _create_task(
            title='古诗背诵', class_groups=[self.class_group],
            teacher=self.teacher_user.profile,
        )
        stu = User.objects.create_user(username='stu1', password='')
        stu.profile.role = 'student'
        stu.profile.class_group = self.class_group
        stu.profile.save()
        Submission.objects.create(
            task=task, student=stu, content='内容',
            status='graded', score=95,
        )
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '0')

    def test_student_dashboard_zero_when_all_submitted(self):
        task = _create_task(
            title='古诗背诵', class_groups=[self.class_group],
            teacher=self.teacher_user.profile,
        )
        Submission.objects.create(
            task=task, student=self.student_user,
            content='已完成', status='pending',
        )
        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '0')
