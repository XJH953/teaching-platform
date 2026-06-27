from django.db import models


class ClassGroup(models.Model):
    SUBJECT_CHOICES = [
        ('chinese', '语文'),
        ('politics', '政治'),
    ]

    name = models.CharField('班级名称', max_length=100)
    subject = models.CharField('学科', max_length=20, choices=SUBJECT_CHOICES)
    teacher = models.ForeignKey(
        'accounts.Profile',
        on_delete=models.CASCADE,
        related_name='taught_classes'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '班级'
        verbose_name_plural = '班级'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name}（{self.get_subject_display()}）'

    @property
    def student_count(self):
        return self.students.count()
