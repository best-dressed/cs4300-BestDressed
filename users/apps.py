"""
Django app configuration for the users application.

This module defines the configuration for the users app, which handles
user authentication, registration, and user-related functionality.
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuration class for the users application.

    This class configures the users app with Django's application registry,
    setting the default auto field type and the app name.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
