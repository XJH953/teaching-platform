from django.contrib import admin
from .models import ClassGroup


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'teacher', 'student_count', 'created_at']
    list_filter = ['subject']
    search_fields = ['name']
