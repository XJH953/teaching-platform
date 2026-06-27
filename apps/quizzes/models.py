from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    title = models.CharField('测验标题', max_length=200)
    class_group = models.ForeignKey(
        'classes.ClassGroup',
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    teacher = models.ForeignKey(
        'accounts.Profile',
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '测验'
        verbose_name_plural = '测验'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField('题目')
    option_a = models.CharField('选项A', max_length=200)
    option_b = models.CharField('选项B', max_length=200)
    option_c = models.CharField('选项C', max_length=200)
    option_d = models.CharField('选项D', max_length=200)
    correct = models.CharField('正确答案', max_length=1, choices=[
        ('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')
    ])

    class Meta:
        verbose_name = '题目'
        verbose_name_plural = '题目'

    def __str__(self):
        return self.text[:50]


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='quiz_attempts'
    )
    score = models.IntegerField('得分', default=0)
    total = models.IntegerField('总分', default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['quiz', 'student']
        verbose_name = '测验记录'
        verbose_name_plural = '测验记录'

    def __str__(self):
        return f'{self.student.username} - {self.quiz.title} ({self.score}/{self.total})'
