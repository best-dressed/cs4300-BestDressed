"""
Unit tests for the Django authentication backend in the users app.
"""

from django.test import TestCase, Client
from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse
from django.core import mail
from users.forms import SignUpForm

User = get_user_model()

class AuthenticationBackendTests(TestCase):
    """Tests for Django's authentication backend."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )

    def test_authenticate_with_valid_credentials(self):
        """Test that authentication succeeds with valid credentials."""
        user = authenticate(username='testuser', password='testpass123')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.is_authenticated)

    def test_authenticate_with_invalid_username(self):
        """Test that authentication fails with invalid username."""
        user = authenticate(username='wronguser', password='testpass123')
        self.assertIsNone(user)

    def test_authenticate_with_invalid_password(self):
        """Test that authentication fails with invalid password."""
        user = authenticate(username='testuser', password='wrongpass')
        self.assertIsNone(user)

    def test_authenticate_with_empty_credentials(self):
        """Test that authentication fails with empty credentials."""
        user = authenticate(username='', password='')
        self.assertIsNone(user)

    def test_authenticate_with_none_credentials(self):
        """Test that authentication fails with None credentials."""
        user = authenticate(username=None, password=None)
        self.assertIsNone(user)

    def test_user_password_is_hashed(self):
        """Test that user passwords are hashed, not stored in plaintext."""
        self.assertNotEqual(self.test_user.password, 'testpass123')
        self.assertTrue(self.test_user.password.startswith('pbkdf2_sha256$'))

    def test_check_password_method(self):
        """Test the check_password method."""
        self.assertTrue(self.test_user.check_password('testpass123'))
        self.assertFalse(self.test_user.check_password('wrongpass'))

    def test_set_password_method(self):
        """Test the set_password method."""
        self.test_user.set_password('newpass456')
        self.test_user.save()

        # Old password should not work
        user = authenticate(username='testuser', password='testpass123')
        self.assertIsNone(user)

        # New password should work
        user = authenticate(username='testuser', password='newpass456')
        self.assertIsNotNone(user)


class UserLoginTests(TestCase):
    """Tests for user login functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.login_url = reverse('login')
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )

    def test_login_page_loads(self):
        """Test that the login page loads successfully."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_login_with_valid_credentials(self):
        """Test login with valid credentials."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })

        # Should redirect to dashboard after successful login
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

        # User should be authenticated
        dummy = get_user_model().objects.get(username='testuser')
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpass'
        })

        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

        # Should show error message
        self.assertContains(response, 'Please enter a correct username and password')

    def test_login_with_inactive_user(self):
        """Test login with inactive user account."""
        self.test_user.is_active = False
        self.test_user.save()

        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })

        # Should not authenticate inactive user
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)


class UserLogoutTests(TestCase):
    """Tests for user logout functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.logout_url = reverse('logout')
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )

    def test_logout_authenticated_user(self):
        """Test logout for authenticated user."""
        # First login
        self.client.login(username='testuser', password='testpass123')
        self.assertTrue('_auth_user_id' in self.client.session)

        # Then logout
        response = self.client.post(self.logout_url)

        # Should redirect to index
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'))

        # User should no longer be authenticated
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_logout_unauthenticated_user(self):
        """Test logout for unauthenticated user."""
        response = self.client.post(self.logout_url)

        # Should still redirect
        self.assertEqual(response.status_code, 302)


class PasswordChangeTests(TestCase):
    """Tests for password change functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.password_change_url = reverse('password_change')
        self.password_change_done_url = reverse('password_change_done')
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='oldpass123'
        )
        self.client.login(username='testuser', password='oldpass123')

    def test_password_change_page_requires_login(self):
        """Test that password change page requires authentication."""
        self.client.logout()
        response = self.client.get(self.password_change_url)

        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_password_change_page_loads_for_authenticated_user(self):
        """Test that password change page loads for authenticated user."""
        response = self.client.get(self.password_change_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_change_form.html')

    def test_password_change_with_valid_data(self):
        """Test password change with valid data."""
        response = self.client.post(self.password_change_url, {
            'old_password': 'oldpass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        })

        # Should redirect to password change done page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.password_change_done_url)

        # Verify password was actually changed
        self.client.logout()
        login_success = self.client.login(username='testuser', password='newpass456')
        self.assertTrue(login_success)

    def test_password_change_with_wrong_old_password(self):
        """Test password change with incorrect old password."""
        response = self.client.post(self.password_change_url, {
            'old_password': 'wrongpass',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        })

        # Should stay on password change page with error
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('old_password', form.errors)

    def test_password_change_with_mismatched_passwords(self):
        """Test password change with mismatched new passwords."""
        response = self.client.post(self.password_change_url, {
            'old_password': 'oldpass123',
            'new_password1': 'newpass456',
            'new_password2': 'differentpass789'
        })

        # Should stay on password change page with error
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('new_password2', form.errors)


class PasswordResetTests(TestCase):
    """Tests for password reset functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.password_reset_url = reverse('password_reset')
        self.password_reset_done_url = reverse('password_reset_done')
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )

    def test_password_reset_page_loads(self):
        """Test that password reset page loads."""
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_form.html')

    def test_password_reset_sends_email(self):
        """Test that password reset sends an email."""
        response = self.client.post(self.password_reset_url, {
            'email': 'testuser@example.com'
        })

        # Should redirect to password reset done page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.password_reset_done_url)

        # Should send one email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('testuser@example.com', mail.outbox[0].to)

    def test_password_reset_with_invalid_email(self):
        """Test password reset with non-existent email."""
        response = self.client.post(self.password_reset_url, {
            'email': 'nonexistent@example.com'
        })

        # Still redirects to done page (security best practice)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.password_reset_done_url)

        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_with_invalid_email_format(self):
        """Test password reset with invalid email format."""
        response = self.client.post(self.password_reset_url, {
            'email': 'not-an-email'
        })

        # Should stay on password reset page with error
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class SignUpFormTests(TestCase):
    """Tests for the custom SignUpForm."""

    def test_signup_form_valid_data(self):
        """Test SignUpForm with valid data."""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_signup_form_saves_email(self):
        """Test that SignUpForm saves the email field."""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.username, 'newuser')
        self.assertTrue(user.check_password('securepass123'))

    def test_signup_form_missing_email(self):
        """Test SignUpForm with missing email."""
        form_data = {
            'username': 'newuser',
            'email': '',
            'password1': 'securepass123',
            'password2': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_signup_form_invalid_email(self):
        """Test SignUpForm with invalid email format."""
        form_data = {
            'username': 'newuser',
            'email': 'not-an-email',
            'password1': 'securepass123',
            'password2': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_signup_form_password_mismatch(self):
        """Test SignUpForm with mismatched passwords."""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'securepass123',
            'password2': 'differentpass456'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_signup_form_duplicate_username(self):
        """Test SignUpForm with duplicate username."""
        # Create existing user
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='pass123'
        )

        form_data = {
            'username': 'existinguser',
            'email': 'newuser@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)


class UserModelTests(TestCase):
    """Tests for User model authentication behavior."""

    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        self.assertEqual(user.username, 'admin')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_string_representation(self):
        """Test User model string representation."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'testuser')

    def test_get_user_by_username(self):
        """Test retrieving user by username."""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        user = User.objects.get(username='testuser')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')

    def test_get_user_by_email(self):
        """Test retrieving user by email."""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        user = User.objects.get(email='test@example.com')
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')


class SessionManagementTests(TestCase):
    """Tests for session management with authentication backend."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )

    def test_session_created_on_login(self):
        """Test that a session is created when user logs in."""
        self.client.login(username='testuser', password='testpass123')

        # Session should exist
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            self.test_user.pk
        )

    def test_session_cleared_on_logout(self):
        """Test that session is cleared when user logs out."""
        self.client.login(username='testuser', password='testpass123')
        self.assertTrue('_auth_user_id' in self.client.session)

        self.client.logout()
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_session_persists_across_requests(self):
        """Test that authentication persists across requests."""
        self.client.login(username='testuser', password='testpass123')

        # Make a request that requires authentication
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)

        # Make another request
        response = self.client.get(reverse('password_change_done'))
        self.assertEqual(response.status_code, 200)
