from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import Topic, Reply
from apps.classes.models import ClassGroup


@login_required
def topic_list_view(request):
    """讨论列表：学生看本班或全校话题，老师看所有话题"""
    profile = request.user.profile

    if profile.is_teacher:
        topics = Topic.objects.select_related(
            'author__profile', 'class_group'
        ).order_by('-created_at')
    else:
        student_class = profile.class_group
        topics = Topic.objects.select_related(
            'author__profile', 'class_group'
        ).filter(
            models.Q(class_group=student_class) | models.Q(class_group__isnull=True)
        ).order_by('-created_at')

    return render(request, 'discussions/list.html', {
        'topics': topics,
    })


@login_required
def topic_create_view(request):
    """创建新讨论主题"""
    profile = request.user.profile

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        class_group_id = request.POST.get('class_group', '')

        if not title or not content:
            messages.error(request, '标题和内容不能为空。')
            return render(request, 'discussions/create.html', {
                'classes': _get_available_classes(profile),
            })

        topic = Topic(title=title, content=content, author=request.user)

        if profile.is_teacher:
            if class_group_id:
                cls = get_object_or_404(
                    ClassGroup, pk=class_group_id, teacher=profile
                )
                topic.class_group = cls
        else:
            topic.class_group = profile.class_group

        topic.save()
        messages.success(request, f'讨论"{topic.title}"已发起。')
        return redirect('discussions:detail', pk=topic.pk)

    return render(request, 'discussions/create.html', {
        'classes': _get_available_classes(profile),
    })


@login_required
def topic_detail_view(request, pk):
    """查看讨论详情和回复"""
    profile = request.user.profile
    topic = get_object_or_404(
        Topic.objects.select_related('author__profile', 'class_group'),
        pk=pk,
    )

    # 权限检查：学生只能看本班或全校的话题
    if profile.is_student and topic.class_group is not None:
        if topic.class_group != profile.class_group:
            messages.error(request, '您无权查看该讨论。')
            return redirect('discussions:list')

    replies = topic.replies.select_related('author__profile').order_by('created_at')

    return render(request, 'discussions/detail.html', {
        'topic': topic,
        'replies': replies,
    })


@login_required
def reply_create_view(request, pk):
    """发表回复"""
    if request.method != 'POST':
        return redirect('discussions:detail', pk=pk)

    topic = get_object_or_404(Topic, pk=pk)
    profile = request.user.profile

    # 权限检查
    if profile.is_student and topic.class_group is not None:
        if topic.class_group != profile.class_group:
            messages.error(request, '您无权回复该讨论。')
            return redirect('discussions:list')

    content = request.POST.get('content', '').strip()
    if not content:
        messages.error(request, '回复内容不能为空。')
        return redirect('discussions:detail', pk=pk)

    Reply.objects.create(
        topic=topic,
        content=content,
        author=request.user,
    )
    messages.success(request, '回复已发表。')
    return redirect('discussions:detail', pk=pk)


def _get_available_classes(profile):
    """获取用户可选的班级列表"""
    if profile.is_teacher:
        return profile.taught_classes.all().order_by('-created_at')
    return []
