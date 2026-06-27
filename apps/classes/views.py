from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import ClassGroup
from .forms import ClassCreateForm


def teacher_required(view_func):
    """装饰器：只有老师可以访问"""
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.is_teacher:
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


@teacher_required
def class_list_view(request):
    classes = ClassGroup.objects.filter(
        teacher=request.user.profile
    ).order_by('-created_at')
    return render(request, 'classes/list.html', {'classes': classes})


@teacher_required
def class_create_view(request):
    if request.method == 'POST':
        form = ClassCreateForm(request.POST)
        if form.is_valid():
            class_group = form.save(commit=False)
            class_group.teacher = request.user.profile
            class_group.save()

            # 批量创建学生
            student_names = form.cleaned_data.get('student_names', [])
            for name in student_names:
                user = User.objects.create_user(username=name, password='')
                user.is_active = False
                user.profile.class_group = class_group
                user.profile.save()
                user.save()

            messages.success(request, f'班级"{class_group.name}"创建成功，已导入 {len(student_names)} 名学生')
            return redirect('classes:list')
    else:
        form = ClassCreateForm()

    return render(request, 'classes/create.html', {'form': form})


@teacher_required
def class_detail_view(request, class_id):
    class_group = get_object_or_404(
        ClassGroup, id=class_id, teacher=request.user.profile
    )
    students = class_group.students.all().order_by('user__username')
    return render(request, 'classes/detail.html', {
        'class_group': class_group,
        'students': students,
    })
