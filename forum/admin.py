from django.contrib import admin
from .models import Thread, Post

# Register your models here.
@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('thread', 'user', 'created_at')

