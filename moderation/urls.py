"""
Urls for error messages related to moderation
"""

from django.urls import path
from . import views

urlpatterns = [
    # IP ban page
    path("ip_ban/", views.ip_ban_page, name="ip_ban"),

    # Filtered content page (generic moderation)
    path("filtered_content/", views.filtered_content_message, name="filtered_content"),

    path("invalid_post/", views.invalid_post, name="invalid_post"),
]
