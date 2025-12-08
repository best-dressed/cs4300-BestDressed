"""
Custom forms for the Best Dressed 'users' application.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class SignUpForm(UserCreationForm):  # pylint: disable=too-many-ancestors
    """
    Custom user registration form that extends Django's UserCreationForm.

    This form adds an email field to the standard user creation form,
    making email required during registration. It handles user signup
    with username, email, and password validation.

    Attributes:
        email: EmailField that requires a valid email address during signup.

    Meta:
        model: The User model to create instances of.
        fields: Fields to include in the form (username, email, password1, password2).

    Note:
        The too-many-ancestors warning is disabled because this inherits from
        Django's UserCreationForm, which has a deep inheritance hierarchy that
        we cannot control.
    """
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        """
        Save the user instance with the provided email.

        Args:
            commit: If True, save the user to the database immediately.
                   If False, return an unsaved user instance.

        Returns:
            User: The created user instance.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
