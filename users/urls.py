"""
URL configuration for users app.

"""

from django.urls import include, path
from .views import (
    SignUpView,
    UserLoginView,
    UserLogoutView,
    UserPasswordChangeView,
    UserPasswordChangeDoneView,
    UserPasswordResetView,
    UserPasswordResetDoneView,
    UserPasswordResetConfirmView,
    UserPasswordResetCompleteView,
    AboutView
)

urlpatterns = [
    path("creation/", include('django_registration.backends.activation.urls')),
    path("creation/", include('django.contrib.auth.urls')),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("about/", AboutView.as_view(), name="about"),

    # Password change
    path("password_change/", UserPasswordChangeView.as_view(), name="password_change"),
    path("password_change/done/", UserPasswordChangeDoneView.as_view(), name="password_change_done"),

    # Password reset (forgot password)
    path("password_reset/", UserPasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", UserPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", UserPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", UserPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
