from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    ROLE_CHOICES = [
        ('teacher', '老师'),
        ('student', '学生'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    class_group = models.ForeignKey(
        'classes.ClassGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    @property
    def is_student(self):
        return self.role == 'student'

    def get_display_name(self):
        if self.is_teacher:
            return self.user.username
        if self.class_group:
            return f'{self.class_group.name} {self.user.username}'
        return self.user.username

    def __str__(self):
        return f'{self.get_role_display()}: {self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
