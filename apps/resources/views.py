from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Resource
from .forms import ResourceForm


# ---- Browsing & Search (Task 3) ----

SUBJECT_LABELS = {
    'chinese': '语文',
    'politics': '政治',
}


@login_required
def resource_list_view(request):
    """公开资源浏览 — 支持按学科筛选和关键词搜索"""
    resources = Resource.objects.select_related('author__user').all()

    subject = request.GET.get('subject', '').strip()
    q = request.GET.get('q', '').strip()

    if subject in dict(Resource.SUBJECT_CHOICES):
        resources = resources.filter(subject=subject)

    if q:
        resources = resources.filter(
            Q(title__icontains=q) | Q(content__icontains=q)
        )

    resources = resources.order_by('-created_at')

    context = {
        'resources': resources,
        'current_subject': subject,
        'search_query': q,
        'subject_labels': SUBJECT_LABELS,
    }
    return render(request, 'resources/list.html', context)


@login_required
def resource_detail_view(request, pk):
    """资源详情页"""
    resource = get_object_or_404(
        Resource.objects.select_related('author__user'), pk=pk
    )
    is_author = resource.author == request.user.profile
    return render(request, 'resources/detail.html', {
        'resource': resource,
        'is_author': is_author,
    })


def teacher_required(view_func):
    """装饰器：只有老师可以访问"""
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.is_teacher:
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


@teacher_required
def resource_create_view(request):
    """老师发布新资源"""
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.author = request.user.profile
            resource.save()
            messages.success(request, f'资源"{resource.title}"发布成功')
            return redirect('resources:my_list')
    else:
        form = ResourceForm()

    return render(request, 'resources/create.html', {'form': form})


@teacher_required
def resource_edit_view(request, pk):
    """老师编辑自己的资源"""
    resource = get_object_or_404(Resource, pk=pk, author=request.user.profile)
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f'资源"{resource.title}"已更新')
            return redirect('resources:my_list')
    else:
        form = ResourceForm(instance=resource)

    return render(request, 'resources/edit.html', {'form': form, 'resource': resource})


@teacher_required
def resource_delete_view(request, pk):
    """老师删除自己的资源"""
    resource = get_object_or_404(Resource, pk=pk, author=request.user.profile)
    if request.method == 'POST':
        title = resource.title
        resource.delete()
        messages.success(request, f'资源"{title}"已删除')
        return redirect('resources:my_list')

    return render(request, 'resources/delete.html', {'resource': resource})


@teacher_required
def my_resource_list_view(request):
    """老师查看自己发布的资源列表"""
    resources = Resource.objects.filter(
        author=request.user.profile
    ).order_by('-created_at')
    return render(request, 'resources/my_list.html', {'resources': resources})
