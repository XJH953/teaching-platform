from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count
from .models import Quiz, Question, QuizAttempt
from .forms import QuizCreateForm, QuestionForm


def teacher_required(view_func):
    """装饰器：只有老师可以访问"""
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.is_teacher:
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


# ============================================================
# Shared: list view (teacher sees own quizzes, student sees
#          quizzes for their class)
# ============================================================

@login_required
def quiz_list_view(request):
    """测验列表：老师看自己创建的，学生看自己班级的"""
    if request.user.profile.is_teacher:
        profile = request.user.profile
        classes = profile.taught_classes.all().order_by('-created_at')
        class_data = []
        for cls in classes:
            quizzes = cls.quizzes.annotate(
                question_count_annotated=Count('questions'),
            ).order_by('-created_at')
            class_data.append({
                'class_group': cls,
                'quizzes': quizzes,
            })
        return render(request, 'quizzes/teacher/list.html', {
            'class_data': class_data,
        })
    else:
        student_class = request.user.profile.class_group
        if not student_class:
            return render(request, 'quizzes/student/list.html', {
                'quizzes': [],
                'attempts': {},
                'no_class': True,
            })

        quizzes = Quiz.objects.filter(
            class_group=student_class
        ).order_by('-created_at')

        # Build attempt map
        attempt_map = {
            a.quiz_id: a
            for a in QuizAttempt.objects.filter(
                quiz__in=quizzes, student=request.user
            )
        }

        # Attach attempt to each quiz for easy template access
        for quiz in quizzes:
            quiz.student_attempt = attempt_map.get(quiz.pk)

        return render(request, 'quizzes/student/list.html', {
            'quizzes': quizzes,
            'class_group': student_class,
        })


# ============================================================
# Teacher views
# ============================================================

@teacher_required
def quiz_create_view(request):
    """老师创建测验"""
    if request.method == 'POST':
        form = QuizCreateForm(request.POST, teacher=request.user.profile)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.teacher = request.user.profile
            quiz.save()
            messages.success(request, f'测验"{quiz.title}"创建成功，请添加题目。')
            return redirect('quizzes:add_questions', pk=quiz.pk)
    else:
        form = QuizCreateForm(teacher=request.user.profile)

    return render(request, 'quizzes/teacher/create.html', {'form': form})


@teacher_required
def add_questions_view(request, pk):
    """老师向测验中添加题目"""
    quiz = get_object_or_404(Quiz, pk=pk, teacher=request.user.profile)
    questions = quiz.questions.all().order_by('id')

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, '题目添加成功。')
            return redirect('quizzes:add_questions', pk=quiz.pk)
        else:
            messages.error(request, '请检查表单内容。')
    else:
        form = QuestionForm()

    return render(request, 'quizzes/teacher/add_questions.html', {
        'quiz': quiz,
        'questions': questions,
        'form': form,
    })


@teacher_required
def quiz_results_view(request, pk):
    """老师查看测验成绩"""
    quiz = get_object_or_404(Quiz, pk=pk, teacher=request.user.profile)
    attempts = quiz.attempts.select_related(
        'student__profile__class_group'
    ).order_by('-completed_at')

    return render(request, 'quizzes/teacher/results.html', {
        'quiz': quiz,
        'attempts': attempts,
    })


# ============================================================
# Student views
# ============================================================

@login_required
def take_quiz_view(request, pk):
    """学生参加测验"""
    student = request.user
    student_class = student.profile.class_group

    quiz = get_object_or_404(
        Quiz.objects.select_related('class_group', 'teacher__user'),
        pk=pk, class_group=student_class,
    )

    # Check if already attempted
    attempt = QuizAttempt.objects.filter(
        quiz=quiz, student=student
    ).first()

    if request.method == 'POST':
        if attempt:
            messages.warning(request, '您已经完成过该测验。')
            return redirect('quizzes:take', pk=quiz.pk)

        # Auto-score
        questions = quiz.questions.all()
        score = 0
        total = len(questions)

        if total == 0:
            messages.error(request, '该测验没有题目。')
            return redirect('quizzes:list')

        # Collect student answers for result display
        student_answers = {}
        for question in questions:
            answer = request.POST.get(f'question_{question.pk}', '').strip().lower()
            student_answers[question.pk] = {
                'question': question,
                'student_answer': answer,
                'is_correct': answer == question.correct,
            }
            if answer == question.correct:
                score += 1

        # Create attempt (unique_together prevents duplicate)
        try:
            attempt = QuizAttempt.objects.create(
                quiz=quiz,
                student=student,
                score=score,
                total=total,
            )
        except IntegrityError:
            messages.warning(request, '您已经完成过该测验。')
            return redirect('quizzes:take', pk=quiz.pk)

        return render(request, 'quizzes/student/result.html', {
            'quiz': quiz,
            'attempt': attempt,
            'student_answers': student_answers.values(),
        })

    questions = quiz.questions.all().order_by('id')
    OPTIONS = [
        ('a', 'option_a'),
        ('b', 'option_b'),
        ('c', 'option_c'),
        ('d', 'option_d'),
    ]

    return render(request, 'quizzes/student/take.html', {
        'quiz': quiz,
        'questions': questions,
        'attempt': attempt,
        'options': OPTIONS,
    })
