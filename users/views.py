"""
Django views for the Best Dressed 'users' application.
"""

from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from .forms import SignUpForm


# sign-up page
class SignUpView(CreateView):
    """View for page sign up"""
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")


# log in page
class UserLoginView(LoginView):
    """Page for user login"""
    template_name = "registration/login.html"


# logout
class UserLogoutView(LogoutView):
    """Page for user logout"""
    template_name = "registration/logout.html"


# change password
class UserPasswordChangeView(PasswordChangeView):
    """Page to change password"""
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    """View to confirm password is done"""
    template_name = "registration/password_change_done.html"


# forgot password / reset flow
class UserPasswordResetView(PasswordResetView):
    """View to reset password"""
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    """View to confirm user password reset"""
    template_name = "registration/password_reset_done.html"


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    """View to ask for cofirmation on password reset"""
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    """View to confirm user password reset"""
    template_name = "registration/password_reset_complete.html"

class AboutView(TemplateView):
    """View to display about page"""
    template_name = "registration/about.html"
