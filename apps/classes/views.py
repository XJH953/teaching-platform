from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def class_list_view(request):
    """班级列表 —— 占位，Task 8 实现完整逻辑"""
    return render(request, 'classes/list.html', {})
