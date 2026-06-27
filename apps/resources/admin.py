from django.contrib import admin
from .models import Resource

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'author', 'created_at']
    list_filter = ['subject']
    search_fields = ['title', 'content']
