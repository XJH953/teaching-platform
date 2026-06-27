from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_view(request):
    context = {}
    if request.user.profile.is_teacher:
        context['class_count'] = request.user.taught_classes.count()
    return render(request, 'dashboard.html', context)
