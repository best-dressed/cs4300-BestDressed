"""
Comprehensive test suite for Dashboard and Account Settings features.

This test file covers:
- Dashboard view and functionality (with enhanced stats)
- Account Settings/User Profile management
- Integration workflows
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from best_dressed_app.models import UserProfile, WardrobeItem, Outfit


# ==================== DASHBOARD TESTS ====================

class DashboardTests(TestCase):
    """Tests for the user dashboard view"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()

    def test_dashboard_requires_authentication(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_dashboard_loads_for_authenticated_user(self):
        """Test that authenticated users can access dashboard"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_dashboard_creates_user_profile_if_not_exists(self):
        """Test that dashboard creates UserProfile if it doesn't exist"""
        self.client.login(username='testuser', password='testpass123')

        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())

        response = self.client.get(reverse('dashboard'))

        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.assertEqual(response.status_code, 200)

    def test_dashboard_uses_existing_profile(self):
        """Test that dashboard uses existing profile instead of creating duplicate"""
        self.client.login(username='testuser', password='testpass123')

        profile = UserProfile.objects.create(
            user=self.user,
            bio="Test bio",
            style_preferences="casual"
        )

        self.client.get(reverse('dashboard'))

        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 1)

        profile.refresh_from_db()
        self.assertEqual(profile.bio, "Test bio")

    def test_dashboard_displays_correct_wardrobe_count(self):
        """Test that dashboard shows accurate count of wardrobe items"""
        self.client.login(username='testuser', password='testpass123')

        WardrobeItem.objects.create(
            user=self.user,
            title="Test Shirt",
            category="top"
        )
        WardrobeItem.objects.create(
            user=self.user,
            title="Test Pants",
            category="bottom"
        )

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.context['wardrobe_count'], 2)
        self.assertContains(response, '2')

    def test_dashboard_only_counts_user_items(self):
        """Test that dashboard only counts items belonging to the logged-in user"""
        user_model = get_user_model()
        other_user = user_model.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        WardrobeItem.objects.create(
            user=other_user,
            title="Other User's Item",
            category="top"
        )

        self.client.login(username='testuser', password='testpass123')
        WardrobeItem.objects.create(
            user=self.user,
            title="My Item",
            category="bottom"
        )

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.context['wardrobe_count'], 1)

    def test_dashboard_displays_username(self):
        """Test that dashboard displays the user's username"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'testuser')
        self.assertContains(response, 'Welcome back')

    def test_dashboard_has_navigation_links(self):
        """Test that dashboard includes links to major features"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, '/account/')
        self.assertContains(response, '/wardrobe/')
        self.assertContains(response, '/outfits/')
        self.assertContains(response, '/item_listing/')

    def test_dashboard_displays_correct_counts(self):
        """Test that dashboard shows accurate counts for all metrics"""
        self.client.login(username='testuser', password='testpass123')

        WardrobeItem.objects.create(user=self.user, title="Shirt", category="top")
        WardrobeItem.objects.create(user=self.user, title="Pants", category="bottom")

        Outfit.objects.create(user=self.user, name="Outfit 1")
        Outfit.objects.create(user=self.user, name="Outfit 2", is_favorite=True)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.context['wardrobe_count'], 2)
        self.assertEqual(response.context['outfit_count'], 2)
        self.assertEqual(response.context['favorites_count'], 1)

    def test_dashboard_season_stats(self):
        """Test that dashboard displays outfit breakdown by season"""
        self.client.login(username='testuser', password='testpass123')

        Outfit.objects.create(user=self.user, name="Summer 1", season="summer")
        Outfit.objects.create(user=self.user, name="Summer 2", season="summer")
        Outfit.objects.create(user=self.user, name="Winter 1", season="winter")

        response = self.client.get(reverse('dashboard'))

        season_stats = list(response.context['season_stats'])

        summer_stat = next((s for s in season_stats if s['season'] == 'summer'), None)
        winter_stat = next((s for s in season_stats if s['season'] == 'winter'), None)

        self.assertIsNotNone(summer_stat)
        self.assertIsNotNone(winter_stat)
        self.assertEqual(summer_stat['count'], 2)
        self.assertEqual(winter_stat['count'], 1)

    def test_dashboard_occasion_stats(self):
        """Test that dashboard displays outfit breakdown by occasion"""
        self.client.login(username='testuser', password='testpass123')

        Outfit.objects.create(user=self.user, name="Casual 1", occasion="casual")
        Outfit.objects.create(user=self.user, name="Casual 2", occasion="casual")
        Outfit.objects.create(user=self.user, name="Formal 1", occasion="formal")

        response = self.client.get(reverse('dashboard'))

        occasion_stats = list(response.context['occasion_stats'])

        casual_stat = next((s for s in occasion_stats if s['occasion'] == 'casual'), None)
        formal_stat = next((s for s in occasion_stats if s['occasion'] == 'formal'), None)

        self.assertIsNotNone(casual_stat)
        self.assertIsNotNone(formal_stat)
        self.assertEqual(casual_stat['count'], 2)
        self.assertEqual(formal_stat['count'], 1)

    def test_dashboard_recent_outfits(self):
        """Test that dashboard shows recent outfits (last 4)"""
        self.client.login(username='testuser', password='testpass123')

        for i in range(5):
            Outfit.objects.create(user=self.user, name=f"Outfit {i}")

        response = self.client.get(reverse('dashboard'))

        recent_outfits = response.context['recent_outfits']
        self.assertEqual(len(recent_outfits), 4)

    def test_dashboard_random_outfit(self):
        """Test that dashboard shows a random outfit suggestion"""
        self.client.login(username='testuser', password='testpass123')

        Outfit.objects.create(user=self.user, name="Test Outfit")

        response = self.client.get(reverse('dashboard'))

        self.assertIsNotNone(response.context['random_outfit'])

    def test_dashboard_no_random_outfit_when_none_exist(self):
        """Test dashboard handles case with no outfits"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('dashboard'))

        self.assertIsNone(response.context['random_outfit'])


# ==================== ACCOUNT SETTINGS TESTS ====================

class AccountSettingsTests(TestCase):
    """Tests for account settings and user profile management"""

    def setUp(self):
        """Set up test fixtures"""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()

    def test_account_settings_requires_authentication(self):
        """Test that unauthenticated users cannot access account settings"""
        response = self.client.get(reverse('account_settings'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_account_settings_loads_for_authenticated_user(self):
        """Test that authenticated users can access account settings"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('account_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account_settings.html')

    def test_account_settings_creates_profile_if_not_exists(self):
        """Test that accessing settings creates profile if it doesn't exist"""
        self.client.login(username='testuser', password='testpass123')

        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())

        response = self.client.get(reverse('account_settings'))

        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.assertEqual(response.status_code, 200)

    def test_account_settings_displays_existing_profile_data(self):
        """Test that form is pre-filled with existing profile data"""
        self.client.login(username='testuser', password='testpass123')

        profile = UserProfile.objects.create(
            user=self.user,
            bio="I love fashion",
            style_preferences="casual, streetwear",
            favorite_colors="blue, black"
        )

        response = self.client.get(reverse('account_settings'))

        self.assertEqual(response.context['profile'], profile)

        self.assertContains(response, "I love fashion")
        self.assertContains(response, "casual, streetwear")

    def test_account_settings_update_profile_via_post(self):
        """Test that POST request updates profile successfully"""
        self.client.login(username='testuser', password='testpass123')

        profile = UserProfile.objects.create(
            user=self.user,
            bio="Old bio",
            style_preferences="old style"
        )

        response = self.client.post(reverse('account_settings'), {
            'bio': 'Updated bio',
            'style_preferences': 'new style, modern',
            'favorite_colors': 'red, green'
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account_settings'))

        profile.refresh_from_db()
        self.assertEqual(profile.bio, 'Updated bio')
        self.assertEqual(profile.style_preferences, 'new style, modern')
        self.assertEqual(profile.favorite_colors, 'red, green')

    def test_account_settings_shows_success_message(self):
        """Test that success message is displayed after profile update"""
        self.client.login(username='testuser', password='testpass123')

        UserProfile.objects.create(user=self.user)

        response = self.client.post(reverse('account_settings'), {
            'bio': 'New bio',
            'style_preferences': 'casual',
            'favorite_colors': 'blue'
        }, follow=True)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertIn('updated successfully', str(messages_list[0]))

    def test_account_settings_profile_unique_to_user(self):
        """Test that each user has their own profile"""
        user_model = get_user_model()
        user2 = user_model.objects.create_user(
            username='testuser2',
            password='testpass123'
        )

        self.client.login(username='testuser', password='testpass123')
        self.client.post(reverse('account_settings'), {
            'bio': 'User 1 bio',
            'style_preferences': 'user1 style'
        })

        self.client.logout()
        self.client.login(username='testuser2', password='testpass123')
        self.client.post(reverse('account_settings'), {
            'bio': 'User 2 bio',
            'style_preferences': 'user2 style'
        })

        profile1 = UserProfile.objects.get(user=self.user)
        profile2 = UserProfile.objects.get(user=user2)

        self.assertEqual(profile1.bio, 'User 1 bio')
        self.assertEqual(profile2.bio, 'User 2 bio')
        self.assertNotEqual(profile1.bio, profile2.bio)
