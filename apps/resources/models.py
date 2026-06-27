from django.db import models

class Resource(models.Model):
    SUBJECT_CHOICES = [
        ('chinese', '语文'),
        ('politics', '政治'),
    ]

    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容', blank=True, default='')
    file = models.FileField('附件', upload_to='resources/', blank=True, null=True)
    subject = models.CharField('学科', max_length=20, choices=SUBJECT_CHOICES)
    author = models.ForeignKey(
        'accounts.Profile',
        on_delete=models.CASCADE,
        related_name='resources'
    )
    created_at = models.DateTimeField('发布时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '资源'
        verbose_name_plural = '资源'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
