import secrets
import string

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/dashboard/')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def dashboard_view(request):
    context = {}
    if request.user.profile.is_teacher:
        from apps.assignments.models import Submission

        classes = request.user.profile.taught_classes.all()
        context['class_count'] = classes.count()
        context['student_count'] = sum(c.student_count for c in classes)
        context['active_student_count'] = sum(
            c.students.filter(user__is_active=True).count() for c in classes
        )
        context['pending_count'] = Submission.objects.filter(
            task__teacher=request.user.profile,
            status='pending',
        ).count()
    else:
        from apps.assignments.models import Task

        student = request.user
        if student.profile.class_group:
            context['pending_count'] = Task.objects.filter(
                class_group=student.profile.class_group,
            ).exclude(
                submissions__student=student,
            ).count()
        else:
            context['pending_count'] = 0
    return render(request, 'dashboard.html', context)


@login_required
def welcome_view(request):
    return render(request, 'accounts/welcome.html')


@require_POST
def first_login_view(request):
    """首次登录：用姓名领取密码"""
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': '请输入姓名'})

    try:
        user = User.objects.get(username=name)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': '该姓名不在系统中，请联系老师'})

    if user.is_active:
        return JsonResponse({'success': False, 'error': '该账号已激活，请直接用密码登录'})

    # 生成 8 位随机密码（字母+数字）
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(8))

    user.set_password(password)
    user.is_active = True
    user.save()

    return JsonResponse({
        'success': True,
        'password': password,
        'name': name,
    })


@require_POST
@login_required
def reset_password_view(request, student_id):
    """老师重置学生密码"""
    if not request.user.profile.is_teacher:
        return JsonResponse({'success': False, 'error': '仅老师可操作'}, status=403)

    student = get_object_or_404(User, id=student_id)

    # 验证该学生确实属于老师的班级
    if student.profile.class_group is None or \
       student.profile.class_group.teacher != request.user.profile:
        return JsonResponse({'success': False, 'error': '该学生不在你的班级中'}, status=403)

    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for _ in range(8))
    student.set_password(new_password)
    student.save()

    return JsonResponse({
        'success': True,
        'password': new_password,
        'name': student.username,
    })


def logout_view(request):
    """支持 GET 和 POST 的退出视图"""
    logout(request)
    return redirect('/')


@login_required
def change_password_view(request):
    """学生/老师自行修改密码"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        new_password2 = request.POST.get('new_password2', '')

        user = request.user

        if not user.check_password(old_password):
            return render(request, 'accounts/change_password.html', {
                'error': '当前密码不正确'
            })

        if len(new_password) < 4:
            return render(request, 'accounts/change_password.html', {
                'error': '新密码至少需要 4 位'
            })

        if new_password != new_password2:
            return render(request, 'accounts/change_password.html', {
                'error': '两次输入的新密码不一致'
            })

        user.set_password(new_password)
        user.save()
        # 重新登录以保持会话
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

        return render(request, 'accounts/change_password.html', {
            'success': True
        })

    return render(request, 'accounts/change_password.html')
