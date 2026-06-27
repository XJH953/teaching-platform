from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from apps.resources.models import Resource


class ResourceBrowseTest(TestCase):
    """资源浏览和搜索测试"""

    def setUp(self):
        # 创建老师用户
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()

        # 创建学生用户
        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.save()

        # 创建多个资源供浏览
        Resource.objects.create(
            title='语文课件：古诗鉴赏',
            subject='chinese',
            content='这是一份关于古诗鉴赏的课件内容。',
            author=self.teacher_user.profile,
        )
        Resource.objects.create(
            title='政治课件：社会主义核心价值观',
            subject='politics',
            content='核心价值观包括富强、民主、文明、和谐等。',
            author=self.teacher_user.profile,
        )
        Resource.objects.create(
            title='语文练习题：阅读理解',
            subject='chinese',
            content='这份练习题包含多篇阅读理解文章。',
            author=self.teacher_user.profile,
        )

    def _login_as_student(self):
        """学生登录"""
        self.client.login(username='student', password='test123')

    def _login_as_teacher(self):
        """老师登录"""
        self.client.login(username='teacher', password='test123')

    # ---- List view tests ----

    def test_list_shows_all_resources(self):
        """资源列表显示所有资源"""
        self._login_as_student()
        response = self.client.get(reverse('resources:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '语文课件：古诗鉴赏')
        self.assertContains(response, '政治课件：社会主义核心价值观')
        self.assertContains(response, '语文练习题：阅读理解')

    def test_list_requires_login(self):
        """资源列表需要登录"""
        response = self.client.get(reverse('resources:list'))
        self.assertEqual(response.status_code, 302)

    def test_filter_by_subject_chinese(self):
        """按学科筛选 - 语文"""
        self._login_as_student()
        response = self.client.get(reverse('resources:list') + '?subject=chinese')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '古诗鉴赏')
        self.assertContains(response, '阅读理解')
        self.assertNotContains(response, '社会主义核心价值观')

    def test_filter_by_subject_politics(self):
        """按学科筛选 - 政治"""
        self._login_as_student()
        response = self.client.get(reverse('resources:list') + '?subject=politics')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '社会主义核心价值观')
        self.assertNotContains(response, '古诗鉴赏')

    def test_invalid_subject_ignored(self):
        """无效的学科参数被忽略，显示全部资源"""
        self._login_as_student()
        response = self.client.get(reverse('resources:list') + '?subject=math')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '古诗鉴赏')
        self.assertContains(response, '社会主义核心价值观')

    def test_search_by_title(self):
        """按标题搜索"""
        self._login_as_student()
        response = self.client.get(reverse('resources:list') + '?q=古诗')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '古诗鉴赏')
        self.assertNotContains(response, '社会主义核心价值观')

    def test_search_by_content(self):
        """按内容搜索"""
        self._login_as_student()
        response = self.client.get(reverse('resources:list') + '?q=富强')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '社会主义核心价值观')
        self.assertNotContains(response, '古诗鉴赏')

    def test_search_no_results(self):
        """搜索无结果"""
        self._login_as_student()
        response = self.client.get(reverse('resources:list') + '?q=不存在的关键词xyz')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '没有找到匹配的资源')

    def test_combined_filter_and_search(self):
        """同时使用学科筛选和关键词搜索"""
        self._login_as_student()
        # 只在语文里搜索"古诗"
        response = self.client.get(
            reverse('resources:list') + '?subject=chinese&q=古诗'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '古诗鉴赏')
        self.assertNotContains(response, '阅读理解')

    def test_empty_list_shows_message(self):
        """空列表显示提示信息"""
        Resource.objects.all().delete()
        self._login_as_student()
        response = self.client.get(reverse('resources:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '还没有任何资源')

    # ---- Detail view tests ----

    def test_detail_shows_full_resource(self):
        """详情页显示完整资源信息"""
        self._login_as_student()
        resource = Resource.objects.get(title='语文课件：古诗鉴赏')
        response = self.client.get(reverse('resources:detail', args=[resource.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '语文课件：古诗鉴赏')
        self.assertContains(response, '古诗鉴赏的课件内容')
        self.assertContains(response, '语文')

    def test_detail_requires_login(self):
        """详情页需要登录"""
        resource = Resource.objects.first()
        response = self.client.get(reverse('resources:detail', args=[resource.pk]))
        self.assertEqual(response.status_code, 302)

    def test_detail_404_for_nonexistent(self):
        """不存在的资源返回404"""
        self._login_as_student()
        response = self.client.get(reverse('resources:detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_author_sees_edit_delete_buttons(self):
        """资源作者可以看到编辑和删除按钮"""
        self._login_as_teacher()
        resource = Resource.objects.get(title='语文课件：古诗鉴赏')
        response = self.client.get(reverse('resources:detail', args=[resource.pk]))
        self.assertContains(response, '编辑')
        self.assertContains(response, '删除')

    def test_non_author_sees_no_edit_delete_buttons(self):
        """非作者看不到编辑和删除按钮"""
        self._login_as_student()
        resource = Resource.objects.get(title='语文课件：古诗鉴赏')
        response = self.client.get(reverse('resources:detail', args=[resource.pk]))
        self.assertNotContains(response, '>编辑<')
        self.assertNotContains(response, '>删除<')

    def test_detail_shows_file_download_when_file_exists(self):
        """有附件时显示下载链接"""
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake_file = SimpleUploadedFile(
            'test_handout.pdf',
            b'fake pdf content',
            content_type='application/pdf'
        )
        resource = Resource.objects.create(
            title='带附件的资源',
            subject='chinese',
            content='有附件的内容',
            file=fake_file,
            author=self.teacher_user.profile,
        )

        self._login_as_student()
        response = self.client.get(reverse('resources:detail', args=[resource.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '下载附件')

    def test_detail_content_with_linebreaks(self):
        """详情页内容保留换行"""
        resource = Resource.objects.create(
            title='多行内容',
            subject='chinese',
            content='第一行\n第二行\n第三行',
            author=self.teacher_user.profile,
        )

        self._login_as_student()
        response = self.client.get(reverse('resources:detail', args=[resource.pk]))
        self.assertEqual(response.status_code, 200)
        # white-space:pre-wrap style preserves line breaks


class ResourceCRUDTest(TestCase):
    def setUp(self):
        # 创建老师用户
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()

        # 创建另一个老师用户（用于测试跨用户编辑）
        self.other_teacher = User.objects.create_user(
            username='other_teacher', password='test123'
        )
        self.other_teacher.profile.role = 'teacher'
        self.other_teacher.profile.save()

        # 创建学生用户
        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.save()

        # 老师登录
        self.client.login(username='teacher', password='test123')

    def test_teacher_can_create_resource(self):
        """老师可以发布新资源"""
        response = self.client.post(reverse('resources:create'), {
            'title': '语文课件第一课',
            'subject': 'chinese',
            'content': '这是课件内容。',
        })
        self.assertRedirects(response, reverse('resources:my_list'))

        resource = Resource.objects.get(title='语文课件第一课')
        self.assertEqual(resource.author, self.teacher_user.profile)
        self.assertEqual(resource.subject, 'chinese')
        self.assertEqual(resource.content, '这是课件内容。')

    def test_teacher_can_edit_own_resource(self):
        """老师可以编辑自己发布的资源"""
        resource = Resource.objects.create(
            title='原始标题',
            subject='chinese',
            content='原始内容',
            author=self.teacher_user.profile,
        )

        response = self.client.post(reverse('resources:edit', args=[resource.pk]), {
            'title': '修改后的标题',
            'subject': 'politics',
            'content': '修改后的内容',
        })
        self.assertRedirects(response, reverse('resources:my_list'))

        resource.refresh_from_db()
        self.assertEqual(resource.title, '修改后的标题')
        self.assertEqual(resource.subject, 'politics')
        self.assertEqual(resource.content, '修改后的内容')

    def test_teacher_can_delete_own_resource(self):
        """老师可以删除自己发布的资源"""
        resource = Resource.objects.create(
            title='待删除资源',
            subject='chinese',
            content='将被删除',
            author=self.teacher_user.profile,
        )

        response = self.client.post(reverse('resources:delete', args=[resource.pk]))
        self.assertRedirects(response, reverse('resources:my_list'))
        self.assertFalse(Resource.objects.filter(pk=resource.pk).exists())

    def test_non_teacher_cannot_create(self):
        """学生不能发布资源"""
        self.client.login(username='student', password='test123')

        response = self.client.post(reverse('resources:create'), {
            'title': '学生尝试发布',
            'subject': 'chinese',
            'content': '不应该成功',
        })
        # 重定向到 dashboard（非老师被 teacher_required 拦截）
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertFalse(Resource.objects.filter(title='学生尝试发布').exists())

    def test_teacher_cannot_edit_others_resource(self):
        """老师不能编辑其他老师的资源"""
        # 其他老师创建资源
        resource = Resource.objects.create(
            title='其他老师的资源',
            subject='chinese',
            content='别人的内容',
            author=self.other_teacher.profile,
        )

        # 当前老师尝试编辑
        response = self.client.post(reverse('resources:edit', args=[resource.pk]), {
            'title': '恶意修改',
            'subject': 'politics',
            'content': '被篡改',
        })
        # 应返回 404（get_object_or_404 按 author 过滤）
        self.assertEqual(response.status_code, 404)

        resource.refresh_from_db()
        self.assertEqual(resource.title, '其他老师的资源')

    def test_teacher_cannot_delete_others_resource(self):
        """老师不能删除其他老师的资源"""
        resource = Resource.objects.create(
            title='别人的资源',
            subject='chinese',
            content='不应被删除',
            author=self.other_teacher.profile,
        )

        response = self.client.post(reverse('resources:delete', args=[resource.pk]))
        # 应返回 404（get_object_or_404 按 author 过滤）
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Resource.objects.filter(pk=resource.pk).exists())

    def test_my_list_shows_only_own_resources(self):
        """我的资源列表只显示当前老师的资源"""
        # 当前老师的资源
        Resource.objects.create(
            title='我的资源1', subject='chinese',
            author=self.teacher_user.profile,
        )
        Resource.objects.create(
            title='我的资源2', subject='politics',
            author=self.teacher_user.profile,
        )
        # 其他老师的资源
        Resource.objects.create(
            title='别人的资源', subject='chinese',
            author=self.other_teacher.profile,
        )

        response = self.client.get(reverse('resources:my_list'))
        self.assertContains(response, '我的资源1')
        self.assertContains(response, '我的资源2')
        self.assertNotContains(response, '别人的资源')
