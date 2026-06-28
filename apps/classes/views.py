from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
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


@require_POST
@teacher_required
def delete_student_view(request, class_id, student_id):
    """老师删除班级中的一名学生"""
    class_group = get_object_or_404(
        ClassGroup, id=class_id, teacher=request.user.profile
    )
    student = get_object_or_404(User, id=student_id)

    # 确认该学生属于此班级
    if student.profile.class_group != class_group:
        return JsonResponse({'success': False, 'error': '该学生不在此班级中'}, status=403)

    name = student.username
    student.delete()  # 级联删除 profile 和相关提交

    return JsonResponse({
        'success': True,
        'name': name,
    })


@require_POST
@teacher_required
def delete_class_view(request, class_id):
    """老师删除自己的班级"""
    class_group = get_object_or_404(
        ClassGroup, id=class_id, teacher=request.user.profile
    )
    name = class_group.name
    class_group.delete()  # 级联删除学生、作业、提交记录

    return JsonResponse({
        'success': True,
        'name': name,
    })


@teacher_required
def add_students_view(request, class_id):
    """老师向已有班级添加学生"""
    class_group = get_object_or_404(
        ClassGroup, id=class_id, teacher=request.user.profile
    )

    if request.method == 'POST':
        names_text = request.POST.get('student_names', '').strip()
        if not names_text:
            messages.error(request, '请输入至少一个学生姓名。')
            return render(request, 'classes/add_students.html', {
                'class_group': class_group,
            })

        name_list = [n.strip() for n in names_text.split('\n') if n.strip()]

        # 去重
        seen = set()
        unique_names = []
        for n in name_list:
            if n not in seen:
                seen.add(n)
                unique_names.append(n)

        created = 0
        skipped = 0
        for name in unique_names:
            if User.objects.filter(username=name).exists():
                skipped += 1
                continue
            user = User.objects.create_user(username=name, password='')
            user.is_active = False
            user.profile.class_group = class_group
            user.profile.save()
            user.save()
            created += 1

        if created:
            messages.success(request,
                f'成功导入 {created} 名学生到「{class_group.name}」。')
        if skipped:
            messages.warning(request,
                f'跳过 {skipped} 个已存在的姓名。')

        return redirect('classes:detail', class_id=class_id)

    return render(request, 'classes/add_students.html', {
        'class_group': class_group,
    })
