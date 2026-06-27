from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Topic, Reply
from apps.classes.models import ClassGroup


class TopicCreateTest(TestCase):
    """讨论创建测试"""

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

    def test_teacher_can_create_topic(self):
        """老师可以创建讨论"""
        self.client.login(username='teacher', password='test123')
        response = self.client.post(reverse('discussions:create'), {
            'title': '讨论主题',
            'content': '讨论内容',
            'class_group': self.class_group.pk,
        })
        topic = Topic.objects.get(title='讨论主题')
        self.assertRedirects(response, reverse('discussions:detail', args=[topic.pk]))
        self.assertEqual(topic.author, self.teacher_user)
        self.assertEqual(topic.class_group, self.class_group)

    def test_teacher_can_create_global_topic(self):
        """老师可以创建全校讨论"""
        self.client.login(username='teacher', password='test123')
        response = self.client.post(reverse('discussions:create'), {
            'title': '全校通知',
            'content': '重要通知内容',
            'class_group': '',
        })
        topic = Topic.objects.get(title='全校通知')
        self.assertIsNone(topic.class_group)

    def test_student_can_create_topic(self):
        """学生可以创建讨论（自动关联班级）"""
        self.client.login(username='student', password='test123')
        response = self.client.post(reverse('discussions:create'), {
            'title': '学生讨论',
            'content': '学生讨论内容',
        })
        topic = Topic.objects.get(title='学生讨论')
        self.assertEqual(topic.author, self.student_user)
        self.assertEqual(topic.class_group, self.class_group)

    def test_create_requires_login(self):
        """未登录不能创建讨论"""
        self.client.logout()
        response = self.client.get(reverse('discussions:create'))
        self.assertEqual(response.status_code, 302)

    def test_create_get_shows_form(self):
        """GET 请求显示创建表单"""
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('discussions:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '发起讨论')

    def test_create_requires_title(self):
        """标题不能为空"""
        self.client.login(username='teacher', password='test123')
        response = self.client.post(reverse('discussions:create'), {
            'title': '',
            'content': '内容',
        })
        self.assertEqual(Topic.objects.count(), 0)
        self.assertContains(response, '标题和内容不能为空')

    def test_create_requires_content(self):
        """内容不能为空"""
        self.client.login(username='teacher', password='test123')
        response = self.client.post(reverse('discussions:create'), {
            'title': '标题',
            'content': '',
        })
        self.assertEqual(Topic.objects.count(), 0)
        self.assertContains(response, '标题和内容不能为空')


class TopicListTest(TestCase):
    """讨论列表测试"""

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

        self.student_a = User.objects.create_user(
            username='student_a', password='test123'
        )
        self.student_a.profile.role = 'student'
        self.student_a.profile.class_group = self.class_a
        self.student_a.profile.save()

        self.student_b = User.objects.create_user(
            username='student_b', password='test123'
        )
        self.student_b.profile.role = 'student'
        self.student_b.profile.class_group = self.class_b
        self.student_b.profile.save()

        # Create topics
        self.topic_a = Topic.objects.create(
            title='一班讨论', content='一班的内容',
            author=self.teacher_user, class_group=self.class_a,
        )
        self.topic_b = Topic.objects.create(
            title='二班讨论', content='二班的内容',
            author=self.teacher_user, class_group=self.class_b,
        )
        self.topic_global = Topic.objects.create(
            title='全校讨论', content='全校内容',
            author=self.teacher_user, class_group=None,
        )

    def test_teacher_sees_all_topics(self):
        """老师可以看到所有讨论"""
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('discussions:list'))
        self.assertContains(response, '一班讨论')
        self.assertContains(response, '二班讨论')
        self.assertContains(response, '全校讨论')

    def test_student_sees_class_and_global_topics(self):
        """学生只能看到自己班级和全校的讨论"""
        self.client.login(username='student_a', password='test123')
        response = self.client.get(reverse('discussions:list'))
        self.assertContains(response, '一班讨论')
        self.assertContains(response, '全校讨论')
        self.assertNotContains(response, '二班讨论')

    def test_list_shows_reply_count(self):
        """列表显示回复数"""
        Reply.objects.create(
            topic=self.topic_a, content='回复1',
            author=self.teacher_user,
        )
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('discussions:list'))
        self.assertContains(response, '1 条回复')

    def test_list_requires_login(self):
        """列表页需要登录"""
        self.client.logout()
        response = self.client.get(reverse('discussions:list'))
        self.assertEqual(response.status_code, 302)


class TopicDetailTest(TestCase):
    """讨论详情测试"""

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

        self.other_class = ClassGroup.objects.create(
            name='语文二班', subject='chinese',
            teacher=self.teacher_user.profile,
        )

        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_group
        self.student_user.profile.save()

        self.topic = Topic.objects.create(
            title='测试讨论', content='测试内容',
            author=self.teacher_user, class_group=self.class_group,
        )

    def test_detail_shows_topic_and_replies(self):
        """详情页显示主题和回复"""
        Reply.objects.create(
            topic=self.topic, content='回复内容',
            author=self.teacher_user,
        )
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('discussions:detail', args=[self.topic.pk]))
        self.assertContains(response, '测试讨论')
        self.assertContains(response, '测试内容')
        self.assertContains(response, '回复内容')

    def test_student_cannot_view_other_class_topic(self):
        """学生不能看其他班级的讨论"""
        other_topic = Topic.objects.create(
            title='其他班讨论', content='其他内容',
            author=self.teacher_user, class_group=self.other_class,
        )
        self.client.login(username='student', password='test123')
        response = self.client.get(
            reverse('discussions:detail', args=[other_topic.pk])
        )
        self.assertRedirects(response, reverse('discussions:list'))

    def test_student_can_view_global_topic(self):
        """学生可以看全校讨论"""
        global_topic = Topic.objects.create(
            title='全校讨论', content='全校内容',
            author=self.teacher_user, class_group=None,
        )
        self.client.login(username='student', password='test123')
        response = self.client.get(
            reverse('discussions:detail', args=[global_topic.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '全校讨论')

    def test_detail_requires_login(self):
        """详情页需要登录"""
        self.client.logout()
        response = self.client.get(
            reverse('discussions:detail', args=[self.topic.pk])
        )
        self.assertEqual(response.status_code, 302)


class ReplyCreateTest(TestCase):
    """回复创建测试"""

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

        self.topic = Topic.objects.create(
            title='测试讨论', content='测试内容',
            author=self.teacher_user, class_group=self.class_group,
        )

    def test_user_can_reply(self):
        """用户可以回复讨论"""
        self.client.login(username='teacher', password='test123')
        response = self.client.post(
            reverse('discussions:reply', args=[self.topic.pk]),
            {'content': '我的回复'},
        )
        self.assertRedirects(
            response,
            reverse('discussions:detail', args=[self.topic.pk])
        )
        self.assertEqual(self.topic.replies.count(), 1)
        reply = self.topic.replies.first()
        self.assertEqual(reply.content, '我的回复')
        self.assertEqual(reply.author, self.teacher_user)

    def test_empty_reply_rejected(self):
        """空回复被拒绝"""
        self.client.login(username='teacher', password='test123')
        response = self.client.post(
            reverse('discussions:reply', args=[self.topic.pk]),
            {'content': ''},
        )
        self.assertEqual(self.topic.replies.count(), 0)

    def test_reply_requires_login(self):
        """回复需要登录"""
        self.client.logout()
        response = self.client.post(
            reverse('discussions:reply', args=[self.topic.pk]),
            {'content': '回复'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.topic.replies.count(), 0)

    def test_student_cannot_reply_other_class_topic(self):
        """学生不能回复其他班级的讨论"""
        other_class = ClassGroup.objects.create(
            name='语文二班', subject='chinese',
            teacher=self.teacher_user.profile,
        )
        other_topic = Topic.objects.create(
            title='其他班讨论', content='内容',
            author=self.teacher_user, class_group=other_class,
        )
        self.client.login(username='student', password='test123')
        response = self.client.post(
            reverse('discussions:reply', args=[other_topic.pk]),
            {'content': '越权回复'},
        )
        self.assertRedirects(response, reverse('discussions:list'))
        self.assertEqual(other_topic.replies.count(), 0)

    def test_teacher_can_reply_any_topic(self):
        """老师可以回复任何讨论"""
        other_class = ClassGroup.objects.create(
            name='语文二班', subject='chinese',
            teacher=self.teacher_user.profile,
        )
        other_topic = Topic.objects.create(
            title='其他班讨论', content='内容',
            author=self.teacher_user, class_group=other_class,
        )
        self.client.login(username='teacher', password='test123')
        response = self.client.post(
            reverse('discussions:reply', args=[other_topic.pk]),
            {'content': '老师回复'},
        )
        self.assertRedirects(
            response,
            reverse('discussions:detail', args=[other_topic.pk])
        )
        self.assertEqual(other_topic.replies.count(), 1)


class NavbarTest(TestCase):
    """导航栏测试"""

    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()

        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.save()

    def test_navbar_has_discussions_link_teacher(self):
        """老师导航栏有讨论链接"""
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '讨论')

    def test_navbar_has_discussions_link_student(self):
        """学生导航栏有讨论链接"""
        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '讨论')
