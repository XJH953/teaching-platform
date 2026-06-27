from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.db import IntegrityError
from .models import Task, Submission
from .forms import TaskForm


def teacher_required(view_func):
    """装饰器：只有老师可以访问"""
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.is_teacher:
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


# ============================================================
# Student views
# ============================================================

@login_required
def student_task_list_view(request):
    """学生查看自己班级的作业列表"""
    student_class = request.user.profile.class_group

    if not student_class:
        return render(request, 'assignments/student_list.html', {
            'tasks': [],
            'submissions': {},
            'no_class': True,
        })

    tasks = Task.objects.filter(class_group=student_class).order_by('-created_at')

    # Build a dict of task_id -> submission for the current student
    submission_map = {
        sub.task_id: sub
        for sub in Submission.objects.filter(
            task__in=tasks, student=request.user
        )
    }

    # Attach submission to each task for easy template access
    for task in tasks:
        task.student_submission = submission_map.get(task.pk)

    return render(request, 'assignments/student_list.html', {
        'tasks': tasks,
        'class_group': student_class,
    })


@login_required
def student_task_detail_view(request, pk):
    """学生查看作业详情并提交"""
    student = request.user
    student_class = student.profile.class_group

    task = get_object_or_404(
        Task.objects.select_related('class_group', 'teacher__user'),
        pk=pk, class_group=student_class,
    )

    submission = Submission.objects.filter(
        task=task, student=student
    ).first()

    if request.method == 'POST':
        if submission:
            messages.warning(request, '您已经提交过该作业，不能重复提交。')
            return redirect('assignments:student_submit', pk=task.pk)

        content = request.POST.get('content', '').strip()
        uploaded_file = request.FILES.get('file')

        if not content and not uploaded_file:
            messages.error(request, '请填写文字内容或上传文件。')
            return render(request, 'assignments/student_detail.html', {
                'task': task,
                'submission': None,
            })

        try:
            submission = Submission.objects.create(
                task=task,
                student=student,
                content=content,
                file=uploaded_file,
            )
            messages.success(request, '作业提交成功！')
        except IntegrityError:
            messages.warning(request, '您已经提交过该作业，不能重复提交。')

        return redirect('assignments:student_submit', pk=task.pk)

    return render(request, 'assignments/student_detail.html', {
        'task': task,
        'submission': submission,
    })


@login_required
def student_submission_view(request, pk):
    """学生查看自己某个作业的提交详情（只读）"""
    student = request.user
    student_class = student.profile.class_group

    task = get_object_or_404(
        Task.objects.select_related('class_group', 'teacher__user'),
        pk=pk, class_group=student_class,
    )

    submission = get_object_or_404(
        Submission.objects.select_related('task', 'student'),
        task=task, student=student,
    )

    return render(request, 'assignments/student_detail.html', {
        'task': task,
        'submission': submission,
    })


@teacher_required
def task_create_view(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, teacher=request.user.profile)
        if form.is_valid():
            task = form.save(commit=False)
            task.teacher = request.user.profile
            task.save()
            messages.success(request, f'作业"{task.title}"已布置')
            return redirect('assignments:list')
    else:
        form = TaskForm(teacher=request.user.profile)

    return render(request, 'assignments/create.html', {'form': form})


@teacher_required
def task_list_view(request):
    """老师查看自己布置的作业，按班级分组"""
    profile = request.user.profile
    classes = profile.taught_classes.all().order_by('-created_at')

    # Build a list of classes with their tasks and submission stats
    class_data = []
    for cls in classes:
        tasks = cls.tasks.annotate(
            submission_count_annotated=Count('submissions'),
        ).order_by('-created_at')

        for task in tasks:
            task.total_students = cls.student_count

        class_data.append({
            'class_group': cls,
            'tasks': tasks,
        })

    return render(request, 'assignments/list.html', {'class_data': class_data})


@teacher_required
def task_detail_view(request, pk):
    """查看作业详情 + 提交列表"""
    task = get_object_or_404(
        Task.objects.select_related('class_group', 'teacher__user'), pk=pk,
        teacher=request.user.profile,
    )
    submissions = task.submissions.select_related(
        'student__profile'
    ).order_by('-submitted_at')

    return render(request, 'assignments/detail.html', {
        'task': task,
        'submissions': submissions,
    })


@teacher_required
def submission_list_view(request, pk):
    """查看某个作业的所有提交"""
    task = get_object_or_404(Task, pk=pk, teacher=request.user.profile)
    submissions = task.submissions.select_related(
        'student__profile__class_group'
    ).order_by('-submitted_at')

    return render(request, 'assignments/submission_list.html', {
        'task': task,
        'submissions': submissions,
    })


@teacher_required
def grade_submission_view(request, task_pk, submission_pk):
    """老师批改作业"""
    submission = get_object_or_404(
        Submission.objects.select_related('task', 'student__profile'),
        pk=submission_pk,
        task__pk=task_pk,
    )

    # Verify the teacher owns this task
    if submission.task.teacher != request.user.profile:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        score = request.POST.get('score', '').strip()
        comment = request.POST.get('comment', '').strip()

        if score:
            try:
                submission.score = int(score)
            except ValueError:
                messages.error(request, '分数必须是整数。')
                return render(request, 'assignments/grade.html', {
                    'submission': submission,
                })

        submission.comment = comment
        submission.status = 'graded'
        submission.save()

        messages.success(request,
            f'{submission.student.username} 的作业已批改完成。')
        return redirect('assignments:detail', pk=task_pk)

    return render(request, 'assignments/grade.html', {
        'submission': submission,
    })


@teacher_required
def grade_analytics_view(request):
    """成绩分析页 — 老师查看所有班级的成绩统计"""
    profile = request.user.profile

    # All tasks by this teacher
    tasks = Task.objects.filter(teacher=profile)
    submissions = Submission.objects.filter(task__in=tasks, status='graded')

    # Overall stats
    total_assignments = tasks.count()
    total_submissions = Submission.objects.filter(task__in=tasks).count()
    graded_submissions = submissions.count()
    overall_avg = submissions.aggregate(avg=Avg('score'))['avg'] or 0

    # Per-assignment stats
    task_stats = tasks.annotate(
        sub_count=Count('submissions'),
        graded_count_annotated=Count('submissions', filter=Q(submissions__status='graded')),
        avg_score=Avg('submissions__score', filter=Q(submissions__status='graded')),
    ).order_by('-created_at')

    # Per-class stats
    classes = profile.taught_classes.all().order_by('-created_at')
    class_stats = []
    for c in classes:
        class_subs = Submission.objects.filter(
            task__class_group=c, status='graded'
        )
        class_stats.append({
            'class': c,
            'avg': class_subs.aggregate(avg=Avg('score'))['avg'] or 0,
            'count': class_subs.count(),
            'student_count': c.student_count,
        })

    # Per-student stats within this teacher's classes
    student_class_map = {}
    for c in classes:
        for student_profile in c.students.select_related('user').all():
            student_class_map[student_profile.user_id] = c

    student_subs = Submission.objects.filter(
        task__in=tasks, status='graded'
    ).select_related('student')

    student_scores = {}
    for sub in student_subs:
        uid = sub.student_id
        if uid not in student_scores:
            student_scores[uid] = []
        student_scores[uid].append(sub.score)

    student_stats = []
    for uid, scores in student_scores.items():
        from django.contrib.auth.models import User
        user = User.objects.get(pk=uid)
        cls = student_class_map.get(uid)
        student_stats.append({
            'student': user,
            'class': cls,
            'avg': sum(scores) / len(scores),
            'count': len(scores),
        })
    student_stats.sort(key=lambda x: x['avg'], reverse=True)

    context = {
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'overall_avg': overall_avg,
        'task_stats': task_stats,
        'class_stats': class_stats,
        'student_stats': student_stats,
    }
    return render(request, 'assignments/analytics.html', context)
