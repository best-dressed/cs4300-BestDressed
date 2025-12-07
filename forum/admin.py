"""Admin configuration for the forum app."""
from django.contrib import admin
from .models import Thread, Post

class ThreadAdmin(admin.ModelAdmin):
    """Admin interface for Thread model."""
    list_display = ('title', 'user', 'created_at')
    search_fields = ('title', 'content')

class PostAdmin(admin.ModelAdmin):
    """Admin interface for Post model."""
    list_display = ('thread', 'user', 'created_at')
    search_fields = ('content',)

admin.site.register(Thread, ThreadAdmin)
admin.site.register(Post, PostAdmin)
