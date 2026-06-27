from django.contrib.auth.models import User
from apps.classes.models import ClassGroup

t = User.objects.create_superuser('admin', 'a@b.com', 'admin123')
t.profile.role = 'teacher'
t.profile.save()

cg = ClassGroup.objects.create(name='chinese1', subject='chinese', teacher=t.profile)
for name in ['zhangsan', 'lisi', 'wangwu']:
    u = User.objects.create_user(username=name, password='')
    u.is_active = False
    u.profile.class_group = cg
    u.profile.save()
    u.save()

print(f'Teacher: admin / admin123')
print(f'Class: {cg.name} with {cg.student_count} students')
print('OK')
