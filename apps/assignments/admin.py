from django.contrib import admin
from .models import Task, Submission

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'due_date', 'created_at']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['task', 'student', 'status', 'score', 'submitted_at']
    list_filter = ['status']
