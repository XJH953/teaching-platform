from django.contrib import admin
from .models import Quiz, Question, QuizAttempt


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'class_group', 'teacher', 'question_count', 'created_at']
    list_filter = ['class_group__subject']
    search_fields = ['title']
    inlines = [QuestionInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'student', 'score', 'total', 'completed_at']
    list_filter = ['quiz']
    search_fields = ['student__username']
