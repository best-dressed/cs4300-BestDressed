"""App configuration for the API Django application."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuration class for the API Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
