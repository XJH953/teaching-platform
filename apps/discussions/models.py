from django.db import models
from django.contrib.auth.models import User


class Topic(models.Model):
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
    class_group = models.ForeignKey(
        'classes.ClassGroup',
        on_delete=models.CASCADE,
        related_name='topics',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '讨论主题'
        verbose_name_plural = '讨论主题'

    def __str__(self):
        return self.title

    @property
    def reply_count(self):
        return self.replies.count()


class Reply(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField('回复')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '回复'
        verbose_name_plural = '回复'

    def __str__(self):
        return f'{self.author.username} 回复 {self.topic.title}'
