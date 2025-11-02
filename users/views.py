"""
Django views for the Best Dressed 'users' application.
"""

from django.contrib.auth.views import ( LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView)
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

# sign-up page
class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")


# log in page
class UserLoginView(LoginView):
    template_name = "registration/login.html"


# logout
class UserLogoutView(LogoutView):
    template_name = "registration/logout.html"


# change password
class UserPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "registration/password_change_done.html"


# forgot password / reset flow
class UserPasswordResetView(PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"

class AboutView(TemplateView):
    template_name = "about.html"