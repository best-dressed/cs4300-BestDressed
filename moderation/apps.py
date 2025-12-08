"""
Moderation App
"""
from django.apps import AppConfig


class ModerationConfig(AppConfig):
    """Setup for moderation"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moderation'
