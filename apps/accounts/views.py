import secrets
import string

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.shortcuts import render, redirect
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
        context['class_count'] = request.user.profile.taught_classes.count()
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
