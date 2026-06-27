from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from apps.quizzes.models import Quiz, Question, QuizAttempt
from apps.classes.models import ClassGroup


class QuizCreateTest(TestCase):
    """测验创建测试"""

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

    def test_teacher_can_create_quiz(self):
        """老师可以创建测验"""
        response = self.client.post(reverse('quizzes:create'), {
            'title': '期中测验',
            'class_group': self.class_group.pk,
        })
        quiz = Quiz.objects.get(title='期中测验')
        self.assertRedirects(
            response,
            reverse('quizzes:add_questions', args=[quiz.pk])
        )
        self.assertEqual(quiz.teacher, self.teacher_user.profile)
        self.assertEqual(quiz.class_group, self.class_group)

    def test_create_requires_login(self):
        """未登录不能创建测验"""
        self.client.logout()
        response = self.client.get(reverse('quizzes:create'))
        self.assertEqual(response.status_code, 302)

    def test_non_teacher_cannot_create(self):
        """学生不能创建测验"""
        self.client.login(username='student', password='test123')
        response = self.client.post(reverse('quizzes:create'), {
            'title': '学生偷建测验',
            'class_group': self.class_group.pk,
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertFalse(Quiz.objects.filter(title='学生偷建测验').exists())

    def test_create_get_shows_form(self):
        """GET 请求显示创建表单"""
        response = self.client.get(reverse('quizzes:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '创建新测验')


class AddQuestionsTest(TestCase):
    """添加题目测试"""

    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher', password='test123'
        )
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()

        # 创建学生用户（用于测试权限拦截）
        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.save()

        self.class_group = ClassGroup.objects.create(
            name='语文一班', subject='chinese',
            teacher=self.teacher_user.profile,
        )

        self.quiz = Quiz.objects.create(
            title='期中测验',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )

        self.client.login(username='teacher', password='test123')

    def test_teacher_can_add_question(self):
        """老师可以向测验添加题目"""
        response = self.client.post(
            reverse('quizzes:add_questions', args=[self.quiz.pk]),
            {
                'text': '静夜思的作者是谁？',
                'option_a': '李白',
                'option_b': '杜甫',
                'option_c': '白居易',
                'option_d': '王维',
                'correct': 'a',
            }
        )
        self.assertRedirects(
            response,
            reverse('quizzes:add_questions', args=[self.quiz.pk])
        )
        self.assertEqual(self.quiz.questions.count(), 1)

        q = self.quiz.questions.first()
        self.assertEqual(q.text, '静夜思的作者是谁？')
        self.assertEqual(q.option_a, '李白')
        self.assertEqual(q.correct, 'a')

    def test_add_question_page_shows_existing_questions(self):
        """题目页面显示已添加的题目"""
        Question.objects.create(
            quiz=self.quiz,
            text='静夜思的作者是谁？',
            option_a='李白', option_b='杜甫',
            option_c='白居易', option_d='王维',
            correct='a',
        )
        response = self.client.get(
            reverse('quizzes:add_questions', args=[self.quiz.pk])
        )
        self.assertContains(response, '静夜思的作者是谁？')
        self.assertContains(response, '李白')

    def test_non_teacher_cannot_add_question(self):
        """学生不能添加题目"""
        self.client.logout()
        self.client.login(username='student', password='test123')
        response = self.client.post(
            reverse('quizzes:add_questions', args=[self.quiz.pk]),
            {
                'text': '恶意题目',
                'option_a': 'A', 'option_b': 'B',
                'option_c': 'C', 'option_d': 'D',
                'correct': 'a',
            }
        )
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertEqual(self.quiz.questions.count(), 0)

    def test_add_questions_requires_login(self):
        """添加题目需要登录"""
        self.client.logout()
        response = self.client.get(
            reverse('quizzes:add_questions', args=[self.quiz.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_teacher_cannot_add_to_other_teachers_quiz(self):
        """老师不能向其他老师的测验添加题目"""
        other_teacher = User.objects.create_user(
            username='other', password='test123'
        )
        other_teacher.profile.role = 'teacher'
        other_teacher.profile.save()

        self.client.login(username='other', password='test123')
        response = self.client.post(
            reverse('quizzes:add_questions', args=[self.quiz.pk]),
            {
                'text': '偷加的题目',
                'option_a': 'A', 'option_b': 'B',
                'option_c': 'C', 'option_d': 'D',
                'correct': 'a',
            }
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.quiz.questions.count(), 0)


class QuizListTest(TestCase):
    """测验列表测试"""

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

        self.quiz_a = Quiz.objects.create(
            title='一班测验',
            class_group=self.class_a,
            teacher=self.teacher_user.profile,
        )
        self.quiz_b = Quiz.objects.create(
            title='二班测验',
            class_group=self.class_b,
            teacher=self.teacher_user.profile,
        )

        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_a
        self.student_user.profile.save()

    def test_teacher_sees_all_own_quizzes(self):
        """老师看到自己所有的测验"""
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('quizzes:list'))
        self.assertContains(response, '一班测验')
        self.assertContains(response, '二班测验')

    def test_student_sees_class_quizzes(self):
        """学生看到自己班级的测验"""
        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('quizzes:list'))
        self.assertContains(response, '一班测验')
        self.assertNotContains(response, '二班测验')

    def test_student_without_class_sees_message(self):
        """未分配班级的学生看到提示"""
        no_class_student = User.objects.create_user(
            username='no_class', password='test123'
        )
        no_class_student.profile.role = 'student'
        no_class_student.profile.save()
        self.client.login(username='no_class', password='test123')
        response = self.client.get(reverse('quizzes:list'))
        self.assertContains(response, '尚未分配班级')

    def test_list_requires_login(self):
        """列表页需要登录"""
        self.client.logout()
        response = self.client.get(reverse('quizzes:list'))
        self.assertEqual(response.status_code, 302)

    def test_student_sees_attempt_status(self):
        """学生看到已完成的测验状态"""
        Question.objects.create(
            quiz=self.quiz_a,
            text='题目1', option_a='A', option_b='B',
            option_c='C', option_d='D', correct='a',
        )
        QuizAttempt.objects.create(
            quiz=self.quiz_a,
            student=self.student_user,
            score=1, total=1,
        )
        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('quizzes:list'))
        self.assertContains(response, '已完成')
        self.assertContains(response, '1/1')


class TakeQuizTest(TestCase):
    """学生参加测验测试"""

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

        self.quiz = Quiz.objects.create(
            title='期中测验',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )

        # Add 3 questions
        Question.objects.create(
            quiz=self.quiz,
            text='题目1？', option_a='对', option_b='错',
            option_c='C', option_d='D', correct='a',
        )
        Question.objects.create(
            quiz=self.quiz,
            text='题目2？', option_a='A', option_b='对',
            option_c='C', option_d='D', correct='b',
        )
        Question.objects.create(
            quiz=self.quiz,
            text='题目3？', option_a='A', option_b='B',
            option_c='对', option_d='D', correct='c',
        )

        self.student_user = User.objects.create_user(
            username='student', password='test123'
        )
        self.student_user.profile.role = 'student'
        self.student_user.profile.class_group = self.class_group
        self.student_user.profile.save()

        self.client.login(username='student', password='test123')

    def test_take_page_shows_questions(self):
        """测验页面显示所有题目"""
        response = self.client.get(
            reverse('quizzes:take', args=[self.quiz.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '题目1？')
        self.assertContains(response, '题目2？')
        self.assertContains(response, '题目3？')

    def test_student_can_submit_and_get_scored(self):
        """学生提交后自动评分"""
        response = self.client.post(
            reverse('quizzes:take', args=[self.quiz.pk]),
            {
                'question_%d' % self.quiz.questions.all()[0].pk: 'a',
                'question_%d' % self.quiz.questions.all()[1].pk: 'b',
                'question_%d' % self.quiz.questions.all()[2].pk: 'c',
            }
        )
        self.assertEqual(response.status_code, 200)
        attempt = QuizAttempt.objects.get(
            quiz=self.quiz, student=self.student_user
        )
        self.assertEqual(attempt.score, 3)
        self.assertEqual(attempt.total, 3)

    def test_partial_score(self):
        """部分正确时得部分分"""
        questions = list(self.quiz.questions.all())
        response = self.client.post(
            reverse('quizzes:take', args=[self.quiz.pk]),
            {
                'question_%d' % questions[0].pk: 'a',  # correct
                'question_%d' % questions[1].pk: 'a',  # wrong
                'question_%d' % questions[2].pk: 'a',  # wrong
            }
        )
        attempt = QuizAttempt.objects.get(
            quiz=self.quiz, student=self.student_user
        )
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.total, 3)

    def test_result_page_shows_score(self):
        """结果页显示得分"""
        questions = list(self.quiz.questions.all())
        self.client.post(
            reverse('quizzes:take', args=[self.quiz.pk]),
            {
                'question_%d' % questions[0].pk: 'a',
                'question_%d' % questions[1].pk: 'b',
                'question_%d' % questions[2].pk: 'c',
            }
        )
        response = self.client.get(
            reverse('quizzes:take', args=[self.quiz.pk])
        )
        self.assertContains(response, '3 / 3')

    def test_student_cannot_take_quiz_twice(self):
        """学生不能重复参加同一测验"""
        questions = list(self.quiz.questions.all())
        self.client.post(
            reverse('quizzes:take', args=[self.quiz.pk]),
            {
                'question_%d' % questions[0].pk: 'a',
                'question_%d' % questions[1].pk: 'b',
                'question_%d' % questions[2].pk: 'c',
            }
        )
        # Try again
        response = self.client.post(
            reverse('quizzes:take', args=[self.quiz.pk]),
            {
                'question_%d' % questions[0].pk: 'a',
                'question_%d' % questions[1].pk: 'a',
                'question_%d' % questions[2].pk: 'a',
            }
        )
        # Should still redirect and have original score
        attempt = QuizAttempt.objects.get(
            quiz=self.quiz, student=self.student_user
        )
        self.assertEqual(attempt.score, 3)

    def test_cannot_take_other_class_quiz(self):
        """学生不能参加其他班级的测验"""
        other_class = ClassGroup.objects.create(
            name='语文二班', subject='chinese',
            teacher=self.teacher_user.profile,
        )
        other_quiz = Quiz.objects.create(
            title='二班测验',
            class_group=other_class,
            teacher=self.teacher_user.profile,
        )
        response = self.client.get(
            reverse('quizzes:take', args=[other_quiz.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_take_requires_login(self):
        """参加测验需要登录"""
        self.client.logout()
        response = self.client.get(
            reverse('quizzes:take', args=[self.quiz.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_empty_quiz_shows_error(self):
        """没有题目的测验显示错误"""
        empty_quiz = Quiz.objects.create(
            title='空测验',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )
        response = self.client.post(
            reverse('quizzes:take', args=[empty_quiz.pk]),
            {}
        )
        self.assertRedirects(response, reverse('quizzes:list'))


class QuizResultsTest(TestCase):
    """老师查看测验成绩测试"""

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

        self.quiz = Quiz.objects.create(
            title='期中测验',
            class_group=self.class_group,
            teacher=self.teacher_user.profile,
        )

        Question.objects.create(
            quiz=self.quiz,
            text='题目1？', option_a='A', option_b='B',
            option_c='C', option_d='D', correct='a',
        )

        # Create students with attempts
        for i, score in enumerate([1, 0]):
            stu = User.objects.create_user(
                username=f'stu{i}', password=''
            )
            stu.profile.role = 'student'
            stu.profile.class_group = self.class_group
            stu.profile.save()
            QuizAttempt.objects.create(
                quiz=self.quiz, student=stu,
                score=score, total=1,
            )

        self.client.login(username='teacher', password='test123')

    def test_results_page_shows_attempts(self):
        """成绩页显示所有学生的作答记录"""
        response = self.client.get(
            reverse('quizzes:results', args=[self.quiz.pk])
        )
        self.assertContains(response, 'stu0')
        self.assertContains(response, 'stu1')
        self.assertContains(response, '1 / 1')
        self.assertContains(response, '0 / 1')

    def test_results_shows_percentage(self):
        """成绩页显示百分比"""
        response = self.client.get(
            reverse('quizzes:results', args=[self.quiz.pk])
        )
        self.assertContains(response, '100%')

    def test_non_teacher_cannot_view_results(self):
        """学生不能查看成绩列表"""
        stu = User.objects.create_user(
            username='student_viewer', password='test123'
        )
        stu.profile.role = 'student'
        stu.profile.save()
        self.client.login(username='student_viewer', password='test123')
        response = self.client.get(
            reverse('quizzes:results', args=[self.quiz.pk])
        )
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_results_requires_login(self):
        """成绩页需要登录"""
        self.client.logout()
        response = self.client.get(
            reverse('quizzes:results', args=[self.quiz.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_teacher_cannot_view_other_teachers_results(self):
        """老师不能查看其他老师的测验成绩"""
        other_teacher = User.objects.create_user(
            username='other', password='test123'
        )
        other_teacher.profile.role = 'teacher'
        other_teacher.profile.save()
        self.client.login(username='other', password='test123')
        response = self.client.get(
            reverse('quizzes:results', args=[self.quiz.pk])
        )
        self.assertEqual(response.status_code, 404)


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

    def test_navbar_has_quiz_link_teacher(self):
        """老师导航栏有测验链接"""
        self.client.login(username='teacher', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '测验')

    def test_navbar_has_quiz_link_student(self):
        """学生导航栏有测验链接"""
        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, '测验')
