"""
Admin pannel for moderation tools
"""
from django.contrib import admin
from .models import BannedIP
# Register your models here.
admin.site.register(BannedIP)
