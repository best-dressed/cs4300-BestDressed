"""App configuration for the forum app."""
from django.apps import AppConfig


class ForumConfig(AppConfig):
    """Configuration class for the forum application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forum'
