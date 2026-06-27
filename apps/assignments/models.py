from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    """作业"""
    title = models.CharField('作业标题', max_length=200)
    description = models.TextField('作业要求', blank=True, default='')
    class_group = models.ForeignKey(
        'classes.ClassGroup',
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    teacher = models.ForeignKey(
        'accounts.Profile',
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    due_date = models.DateTimeField('截止时间', null=True, blank=True)
    created_at = models.DateTimeField('发布时间', auto_now_add=True)

    class Meta:
        verbose_name = '作业'
        verbose_name_plural = '作业'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def submission_count(self):
        return self.submissions.count()

    @property
    def graded_count(self):
        return self.submissions.filter(status='graded').count()


class Submission(models.Model):
    """学生提交"""
    STATUS_CHOICES = [
        ('pending', '待批改'),
        ('graded', '已批改'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField('答案/作文', blank=True, default='')
    file = models.FileField('附件', upload_to='submissions/', blank=True, null=True)
    submitted_at = models.DateTimeField('提交时间', auto_now_add=True)
    score = models.IntegerField('分数', null=True, blank=True)
    comment = models.TextField('评语', blank=True, default='')
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name = '提交'
        verbose_name_plural = '提交'
        ordering = ['-submitted_at']
        unique_together = ['task', 'student']

    def __str__(self):
        return f'{self.student.username} - {self.task.title}'
