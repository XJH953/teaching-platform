from django.contrib import admin
from .models import Topic, Reply


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'class_group', 'reply_count', 'created_at']
    list_filter = ['class_group']
    search_fields = ['title', 'content']


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content']
