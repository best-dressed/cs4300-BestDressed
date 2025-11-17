"""
Comprehensive test suite for Dashboard, Wardrobe, Account Settings, and Outfit features.

This test file covers:
- Dashboard view and functionality (with enhanced stats)
- Account Settings/User Profile management
- Wardrobe management (add, edit, delete, save from catalog, search, sort)
- Outfit creation and management (create, edit, delete, detail)
- Quick Actions (toggle favorite, duplicate, quick add to outfit)
- Smart Collections (favorites, seasons, occasions, recent, incomplete)
- Search and Filtering (outfit search, sort, combined filters)
- Model constraints and behavior
- Integration workflows
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from best_dressed_app.models import Item, UserProfile, WardrobeItem, Outfit
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
import json


# ==================== DASHBOARD TESTS ====================

class DashboardTests(TestCase):
    """Tests for the user dashboard view"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
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
        User = get_user_model()
        other_user = User.objects.create_user(
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
        
        outfit = Outfit.objects.create(user=self.user, name="Outfit 1")
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
        
        outfit = Outfit.objects.create(user=self.user, name="Test Outfit")
        
        response = self.client.get(reverse('dashboard'))
        
        self.assertIsNotNone(response.context['random_outfit'])
        self.assertEqual(response.context['random_outfit'], outfit)
    
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
        User = get_user_model()
        self.user = User.objects.create_user(
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
        User = get_user_model()
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('account_settings'), {
            'bio': 'User 1 bio',
            'style_preferences': 'user1 style'
        })
        
        self.client.logout()
        self.client.login(username='testuser2', password='testpass123')
        response = self.client.post(reverse('account_settings'), {
            'bio': 'User 2 bio',
            'style_preferences': 'user2 style'
        })
        
        profile1 = UserProfile.objects.get(user=self.user)
        profile2 = UserProfile.objects.get(user=user2)
        
        self.assertEqual(profile1.bio, 'User 1 bio')
        self.assertEqual(profile2.bio, 'User 2 bio')
        self.assertNotEqual(profile1.bio, profile2.bio)


# ==================== WARDROBE TESTS ====================

class SaveToWardrobeTests(TestCase):
    """Tests for saving catalog items to user's wardrobe"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.catalog_item = Item.objects.create(
            title="Cool Jacket",
            description="A very cool jacket",
            image_url="https://example.com/jacket.jpg"
        )
    
    def test_save_to_wardrobe_requires_authentication(self):
        """Test that unauthenticated users cannot save items"""
        response = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_save_to_wardrobe_creates_wardrobe_item(self):
        """Test that POST request creates a wardrobe item"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk})
        )
        
        self.assertRedirects(response, reverse('item_detail', kwargs={'pk': self.catalog_item.pk}))
        
        wardrobe_item = WardrobeItem.objects.get(user=self.user, catalog_item=self.catalog_item)
        self.assertEqual(wardrobe_item.title, "Cool Jacket")
        self.assertEqual(wardrobe_item.description, "A very cool jacket")
    
    def test_save_to_wardrobe_prevents_duplicates(self):
        """Test that saving the same item twice doesn't create duplicates"""
        self.client.login(username='testuser', password='testpass123')
        
        response1 = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk})
        )
        
        self.assertEqual(WardrobeItem.objects.filter(user=self.user, catalog_item=self.catalog_item).count(), 1)
        
        with transaction.atomic():
            response2 = self.client.post(
                reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk})
            )
        
        self.assertEqual(response2.status_code, 302)
        
        self.assertEqual(WardrobeItem.objects.filter(user=self.user, catalog_item=self.catalog_item).count(), 1)
    
    def test_save_to_wardrobe_shows_success_message(self):
        """Test that success message is displayed when item is saved"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk}),
            follow=True
        )
        
        messages_list = list(response.context['messages'])
        self.assertTrue(any('added to your wardrobe' in str(msg) for msg in messages_list))
    
    def test_save_to_wardrobe_only_accepts_post(self):
        """Test that GET requests are not allowed"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk}),
            follow=True
        )
        
        self.assertEqual(WardrobeItem.objects.filter(user=self.user).count(), 0)
        messages_list = list(response.context['messages'])
        self.assertTrue(any('Invalid request method' in str(msg) for msg in messages_list))
    
    def test_save_to_wardrobe_handles_nonexistent_item(self):
        """Test that 404 is returned for non-existent catalog items"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': 99999})
        )
        
        self.assertEqual(response.status_code, 404)


class MyWardrobeTests(TestCase):
    """Tests for viewing and managing the user's wardrobe"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Blue Shirt",
            description="A nice blue shirt",
            category="top",
            brand="Nike",
            color="blue"
        )
        self.item2 = WardrobeItem.objects.create(
            user=self.user,
            title="Black Pants",
            description="Comfortable black pants",
            category="bottom",
            brand="Adidas",
            color="black"
        )
    
    def test_my_wardrobe_requires_authentication(self):
        """Test that unauthenticated users cannot access wardrobe"""
        response = self.client.get(reverse('my_wardrobe'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_my_wardrobe_displays_user_items(self):
        """Test that wardrobe displays all user's items"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_wardrobe'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_wardrobe.html')
        
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 2)
        self.assertIn(self.item1, wardrobe_items)
        self.assertIn(self.item2, wardrobe_items)
    
    def test_my_wardrobe_only_shows_user_items(self):
        """Test that users only see their own items, not other users' items"""
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        other_item = WardrobeItem.objects.create(
            user=other_user,
            title="Other User's Shirt",
            category="top"
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_wardrobe'))
        
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 2)
        self.assertNotIn(other_item, wardrobe_items)
    
    def test_my_wardrobe_category_filter(self):
        """Test filtering wardrobe items by category"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_wardrobe'), {'category': 'top'})
        
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 1)
        self.assertEqual(wardrobe_items[0].title, "Blue Shirt")
    
    def test_my_wardrobe_search_functionality(self):
        """Test searching wardrobe items"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_wardrobe'), {'search': 'blue'})
        
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 1)
        self.assertEqual(wardrobe_items[0].title, "Blue Shirt")
    
    def test_my_wardrobe_search_multiple_fields(self):
        """Test that search works across multiple fields"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_wardrobe'), {'search': 'Nike'})
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 1)
        
        response = self.client.get(reverse('my_wardrobe'), {'search': 'black'})
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 1)
        self.assertEqual(wardrobe_items[0].title, "Black Pants")
    
    def test_my_wardrobe_sorting(self):
        """Test sorting wardrobe items"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_wardrobe'), {'sort': 'title'})
        wardrobe_items = list(response.context['wardrobe_items'])
        self.assertEqual(wardrobe_items[0].title, "Black Pants")
        self.assertEqual(wardrobe_items[1].title, "Blue Shirt")
        
        response = self.client.get(reverse('my_wardrobe'), {'sort': '-title'})
        wardrobe_items = list(response.context['wardrobe_items'])
        self.assertEqual(wardrobe_items[0].title, "Blue Shirt")
        self.assertEqual(wardrobe_items[1].title, "Black Pants")
    
    def test_my_wardrobe_combined_filters(self):
        """Test using multiple filters together"""
        self.client.login(username='testuser', password='testpass123')
        
        WardrobeItem.objects.create(
            user=self.user,
            title="Blue Jeans",
            category="bottom",
            color="blue"
        )
        
        response = self.client.get(reverse('my_wardrobe'), {
            'category': 'bottom',
            'search': 'blue'
        })
        
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 1)
        self.assertEqual(wardrobe_items[0].title, "Blue Jeans")


class AddWardrobeItemTests(TestCase):
    """Tests for manually adding items to wardrobe"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
    
    def test_add_wardrobe_item_requires_authentication(self):
        """Test that unauthenticated users cannot add items"""
        response = self.client.get(reverse('add_wardrobe_item'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_add_wardrobe_item_get_displays_form(self):
        """Test that GET request displays the add item form"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_wardrobe_item'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wardrobe_item_form.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['mode'], 'add')
    
    def test_add_wardrobe_item_post_creates_item(self):
        """Test that POST request creates a new wardrobe item"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('add_wardrobe_item'), {
            'title': 'My New Shirt',
            'description': 'A shirt I own',
            'category': 'top',
            'color': 'red',
            'brand': 'Generic',
            'image_url': 'https://example.com/shirt.jpg'
        })
        
        self.assertRedirects(response, reverse('my_wardrobe'))
        
        item = WardrobeItem.objects.get(title='My New Shirt')
        self.assertEqual(item.user, self.user)
        self.assertEqual(item.category, 'top')
        self.assertIsNone(item.catalog_item)
    
    def test_add_wardrobe_item_sets_correct_user(self):
        """Test that the item is assigned to the logged-in user"""
        self.client.login(username='testuser', password='testpass123')
        
        self.client.post(reverse('add_wardrobe_item'), {
            'title': 'Test Item',
            'category': 'other',
            'description': 'Test description'
        })
        
        item = WardrobeItem.objects.get(title='Test Item')
        self.assertEqual(item.user, self.user)


class EditWardrobeItemTests(TestCase):
    """Tests for editing wardrobe items"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item = WardrobeItem.objects.create(
            user=self.user,
            title="Original Title",
            description="Original description",
            category="top"
        )
    
    def test_edit_wardrobe_item_requires_authentication(self):
        """Test that unauthenticated users cannot edit items"""
        response = self.client.get(
            reverse('edit_wardrobe_item', kwargs={'item_pk': self.item.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_edit_wardrobe_item_get_displays_form(self):
        """Test that GET request displays the edit form with existing data"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('edit_wardrobe_item', kwargs={'item_pk': self.item.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wardrobe_item_form.html')
        self.assertEqual(response.context['mode'], 'edit')
        self.assertEqual(response.context['item'], self.item)
    
    def test_edit_wardrobe_item_post_updates_item(self):
        """Test that POST request updates the wardrobe item"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('edit_wardrobe_item', kwargs={'item_pk': self.item.pk}),
            {
                'title': 'Updated Title',
                'description': 'Updated description',
                'category': 'bottom',
                'color': 'blue',
                'brand': 'NewBrand'
            }
        )
        
        self.assertRedirects(response, reverse('my_wardrobe'))
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Updated Title')
        self.assertEqual(self.item.description, 'Updated description')
        self.assertEqual(self.item.category, 'bottom')
    
    def test_edit_wardrobe_item_user_can_only_edit_own_items(self):
        """Test that users can only edit their own items"""
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        other_item = WardrobeItem.objects.create(
            user=other_user,
            title="Other User's Item",
            category="top"
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('edit_wardrobe_item', kwargs={'item_pk': other_item.pk})
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_edit_wardrobe_item_shows_success_message(self):
        """Test that success message is displayed after update"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('edit_wardrobe_item', kwargs={'item_pk': self.item.pk}),
            {
                'title': 'Updated Title',
                'category': 'top',
                'description': 'Updated'
            },
            follow=True
        )
        
        messages_list = list(response.context['messages'])
        self.assertTrue(any('updated' in str(msg).lower() for msg in messages_list))


class DeleteWardrobeItemTests(TestCase):
    """Tests for deleting wardrobe items"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item = WardrobeItem.objects.create(
            user=self.user,
            title="Item to Delete",
            category="top"
        )
    
    def test_delete_wardrobe_item_requires_authentication(self):
        """Test that unauthenticated users cannot delete items"""
        response = self.client.post(
            reverse('delete_wardrobe_item', kwargs={'item_pk': self.item.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_delete_wardrobe_item_get_shows_confirmation(self):
        """Test that GET request shows confirmation page"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('delete_wardrobe_item', kwargs={'item_pk': self.item.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'confirm_delete_wardrobe_item.html')
        self.assertEqual(response.context['item'], self.item)
    
    def test_delete_wardrobe_item_post_deletes_item(self):
        """Test that POST request deletes the item"""
        self.client.login(username='testuser', password='testpass123')
        
        self.assertTrue(WardrobeItem.objects.filter(pk=self.item.pk).exists())
        
        response = self.client.post(
            reverse('delete_wardrobe_item', kwargs={'item_pk': self.item.pk})
        )
        
        self.assertRedirects(response, reverse('my_wardrobe'))
        
        self.assertFalse(WardrobeItem.objects.filter(pk=self.item.pk).exists())
    
    def test_delete_wardrobe_item_user_can_only_delete_own_items(self):
        """Test that users can only delete their own items"""
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        other_item = WardrobeItem.objects.create(
            user=other_user,
            title="Other User's Item",
            category="top"
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('delete_wardrobe_item', kwargs={'item_pk': other_item.pk})
        )
        
        self.assertEqual(response.status_code, 404)
        
        self.assertTrue(WardrobeItem.objects.filter(pk=other_item.pk).exists())
    
    def test_delete_wardrobe_item_shows_success_message(self):
        """Test that success message is displayed after deletion"""
        self.client.login(username='testuser', password='testpass123')
        
        item_title = self.item.title
        response = self.client.post(
            reverse('delete_wardrobe_item', kwargs={'item_pk': self.item.pk}),
            follow=True
        )
        
        messages_list = list(response.context['messages'])
        self.assertTrue(any('removed from your wardrobe' in str(msg) for msg in messages_list))
        self.assertTrue(any(item_title in str(msg) for msg in messages_list))


# ==================== OUTFIT TESTS ====================

class CreateOutfitTests(TestCase):
    """Tests for creating outfits"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        self.item2 = WardrobeItem.objects.create(
            user=self.user,
            title="Pants",
            category="bottom"
        )
    
    def test_create_outfit_requires_authentication(self):
        """Test that unauthenticated users cannot create outfits"""
        response = self.client.get(reverse('create_outfit'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_create_outfit_get_displays_form(self):
        """Test that GET request displays the create outfit form"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_outfit'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_outfit.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['mode'], 'create')
    
    def test_create_outfit_displays_user_wardrobe_items(self):
        """Test that form shows user's wardrobe items for selection"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_outfit'))
        
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 2)
        self.assertIn(self.item1, wardrobe_items)
        self.assertIn(self.item2, wardrobe_items)
    
    def test_create_outfit_post_creates_outfit(self):
        """Test that POST request creates a new outfit"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('create_outfit'), {
            'name': 'Casual Friday',
            'description': 'Perfect for casual work day',
            'items': [self.item1.pk, self.item2.pk],
            'occasion': 'casual',
            'season': 'all'
        })
        
        self.assertRedirects(response, reverse('my_outfits'))
        
        outfit = Outfit.objects.get(name='Casual Friday')
        self.assertEqual(outfit.user, self.user)
        self.assertEqual(outfit.items.count(), 2)
        self.assertIn(self.item1, outfit.items.all())
        self.assertIn(self.item2, outfit.items.all())
    
    def test_create_outfit_assigns_to_correct_user(self):
        """Test that outfit is assigned to the logged-in user"""
        self.client.login(username='testuser', password='testpass123')
        
        self.client.post(reverse('create_outfit'), {
            'name': 'Test Outfit',
            'description': 'Test',
            'items': [self.item1.pk]
        })
        
        outfit = Outfit.objects.get(name='Test Outfit')
        self.assertEqual(outfit.user, self.user)
    
    def test_create_outfit_shows_success_message(self):
        """Test that success message is displayed after creation"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('create_outfit'), {
            'name': 'New Outfit',
            'description': 'Description',
            'items': [self.item1.pk]
        }, follow=True)
        
        messages_list = list(response.context['messages'])
        self.assertTrue(any('created successfully' in str(msg) for msg in messages_list))


class MyOutfitsTests(TestCase):
    """Tests for viewing user's outfits with search and filtering"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        
        self.outfit1 = Outfit.objects.create(
            user=self.user,
            name="Casual Look",
            description="For everyday wear",
            occasion="casual",
            season="summer"
        )
        self.outfit1.items.add(self.item1)
        
        self.outfit2 = Outfit.objects.create(
            user=self.user,
            name="Formal Look",
            description="For special occasions",
            occasion="formal",
            season="winter",
            is_favorite=True
        )
    
    def test_my_outfits_requires_authentication(self):
        """Test that unauthenticated users cannot view outfits"""
        response = self.client.get(reverse('my_outfits'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_my_outfits_displays_user_outfits(self):
        """Test that page displays all user's outfits"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_outfits'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_outfits.html')
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 2)
        self.assertIn(self.outfit1, outfits)
        self.assertIn(self.outfit2, outfits)
    
    def test_my_outfits_only_shows_user_outfits(self):
        """Test that users only see their own outfits"""
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        other_outfit = Outfit.objects.create(
            user=other_user,
            name="Other User's Outfit"
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_outfits'))
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 2)
        self.assertNotIn(other_outfit, outfits)
    
    def test_my_outfits_search_functionality(self):
        """Test searching outfits by name or description"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'search': 'Casual'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Casual Look")
    
    def test_my_outfits_search_in_description(self):
        """Test that search works in description field"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'search': 'everyday'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Casual Look")
    
    def test_my_outfits_sort_by_name(self):
        """Test sorting outfits by name"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'sort': 'name'})
        outfits = list(response.context['outfits'])
        self.assertEqual(outfits[0].name, "Casual Look")
        self.assertEqual(outfits[1].name, "Formal Look")
        
        response = self.client.get(reverse('my_outfits'), {'sort': '-name'})
        outfits = list(response.context['outfits'])
        self.assertEqual(outfits[0].name, "Formal Look")
        self.assertEqual(outfits[1].name, "Casual Look")
    
    def test_my_outfits_favorites_filter(self):
        """Test filtering to show only favorites"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'favorites': 'true'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertTrue(outfits[0].is_favorite)


class SmartCollectionsTests(TestCase):
    """Tests for smart collection filtering"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        Outfit.objects.create(user=self.user, name="Summer Casual", season="summer", occasion="casual")
        Outfit.objects.create(user=self.user, name="Winter Formal", season="winter", occasion="formal")
        Outfit.objects.create(user=self.user, name="Work Outfit", occasion="business")
        Outfit.objects.create(user=self.user, name="Date Night", occasion="date", is_favorite=True)
        
        self.recent_outfit = Outfit.objects.create(user=self.user, name="Recent Outfit")
        
        old_outfit = Outfit.objects.create(user=self.user, name="Old Outfit")
        old_outfit.created_at = timezone.now() - timedelta(days=31)
        old_outfit.save()
        
        item = WardrobeItem.objects.create(user=self.user, title="Shirt", category="top")
        incomplete = Outfit.objects.create(user=self.user, name="Incomplete")
        incomplete.items.add(item)
    
    def test_favorites_collection(self):
        """Test favorites collection filter"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'collection': 'favorites'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Date Night")
    
    def test_summer_collection(self):
        """Test summer season collection filter"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'collection': 'summer'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Summer Casual")
    
    def test_winter_collection(self):
        """Test winter season collection filter"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'collection': 'winter'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Winter Formal")
    
    def test_casual_collection(self):
        """Test casual occasion collection filter"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'collection': 'casual'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Summer Casual")
    
    def test_work_collection(self):
        """Test work/business occasion collection filter"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'collection': 'work'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Work Outfit")
    
    def test_date_collection(self):
        """Test date night occasion collection filter"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'collection': 'date'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Date Night")
    
    def test_formal_collection(self):
        """Test formal occasion collection filter"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'collection': 'formal'})
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 1)
        self.assertEqual(outfits[0].name, "Winter Formal")
    
    def test_recent_collection(self):
        """Test recent collection (last 30 days)"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'collection': 'recent'})
        
        outfits = response.context['outfits']
        self.assertGreaterEqual(len(outfits), 6)
        self.assertIn(self.recent_outfit, outfits)
    
    def test_incomplete_collection(self):
        """Test incomplete collection (less than 3 items)"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'), {'collection': 'incomplete'})
        
        outfits = response.context['outfits']
        self.assertGreaterEqual(len(outfits), 1)
        self.assertTrue(any(o.name == "Incomplete" for o in outfits))
    
    def test_collection_counts_in_context(self):
        """Test that collection counts are provided in context"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('my_outfits'))
        
        collection_counts = response.context['collection_counts']
        
        self.assertIn('favorites', collection_counts)
        self.assertIn('summer', collection_counts)
        self.assertIn('winter', collection_counts)
        self.assertIn('casual', collection_counts)
        self.assertIn('work', collection_counts)
        self.assertIn('date', collection_counts)
        self.assertIn('formal', collection_counts)
        self.assertIn('recent', collection_counts)
        self.assertIn('incomplete', collection_counts)
        
        self.assertEqual(collection_counts['favorites'], 1)
        self.assertEqual(collection_counts['summer'], 1)
        self.assertEqual(collection_counts['winter'], 1)


class OutfitDetailTests(TestCase):
    """Tests for outfit detail view"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        
        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit",
            description="Test description",
            occasion="casual",
            season="summer"
        )
        self.outfit.items.add(self.item1)
    
    def test_outfit_detail_requires_authentication(self):
        """Test that unauthenticated users cannot view outfit details"""
        response = self.client.get(
            reverse('outfit_detail', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_outfit_detail_displays_outfit(self):
        """Test that outfit detail page displays correct information"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('outfit_detail', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'outfit_detail.html')
        self.assertEqual(response.context['outfit'], self.outfit)
        self.assertContains(response, "Test Outfit")
        self.assertContains(response, "Test description")
    
    def test_outfit_detail_user_can_only_view_own_outfits(self):
        """Test that users can only view their own outfits"""
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        other_outfit = Outfit.objects.create(
            user=other_user,
            name="Other User's Outfit"
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('outfit_detail', kwargs={'outfit_pk': other_outfit.pk})
        )
        
        self.assertEqual(response.status_code, 404)


class EditOutfitTests(TestCase):
    """Tests for editing outfits"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        self.item2 = WardrobeItem.objects.create(
            user=self.user,
            title="Pants",
            category="bottom"
        )
        
        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Original Name",
            description="Original description"
        )
        self.outfit.items.add(self.item1)
    
    def test_edit_outfit_requires_authentication(self):
        """Test that unauthenticated users cannot edit outfits"""
        response = self.client.get(
            reverse('edit_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_edit_outfit_get_displays_form(self):
        """Test that GET request displays edit form with existing data"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('edit_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_outfit.html')
        self.assertEqual(response.context['outfit'], self.outfit)
        self.assertEqual(response.context['mode'], 'edit')
    
    def test_edit_outfit_post_updates_outfit(self):
        """Test that POST request updates the outfit"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('edit_outfit', kwargs={'outfit_pk': self.outfit.pk}),
            {
                'name': 'Updated Name',
                'description': 'Updated description',
                'items': [self.item1.pk, self.item2.pk],
                'occasion': 'formal',
                'season': 'winter'
            }
        )
        
        self.assertRedirects(
            response,
            reverse('outfit_detail', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.outfit.refresh_from_db()
        self.assertEqual(self.outfit.name, 'Updated Name')
        self.assertEqual(self.outfit.description, 'Updated description')
        self.assertEqual(self.outfit.items.count(), 2)


class DeleteOutfitTests(TestCase):
    """Tests for deleting outfits"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Outfit to Delete"
        )
    
    def test_delete_outfit_requires_authentication(self):
        """Test that unauthenticated users cannot delete outfits"""
        response = self.client.post(
            reverse('delete_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_delete_outfit_get_shows_confirmation(self):
        """Test that GET request shows confirmation page"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('delete_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'confirm_delete_outfit.html')
        self.assertEqual(response.context['outfit'], self.outfit)
    
    def test_delete_outfit_post_deletes_outfit(self):
        """Test that POST request deletes the outfit"""
        self.client.login(username='testuser', password='testpass123')
        
        self.assertTrue(Outfit.objects.filter(pk=self.outfit.pk).exists())
        
        response = self.client.post(
            reverse('delete_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertRedirects(response, reverse('my_outfits'))
        self.assertFalse(Outfit.objects.filter(pk=self.outfit.pk).exists())


# ==================== QUICK ACTIONS TESTS ====================

class ToggleFavoriteTests(TestCase):
    """Tests for toggling outfit favorite status (AJAX)"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit",
            is_favorite=False
        )
    
    def test_toggle_favorite_requires_authentication(self):
        """Test that unauthenticated users cannot toggle favorites"""
        response = self.client.post(
            reverse('toggle_outfit_favorite', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_toggle_favorite_only_accepts_post(self):
        """Test that only POST requests are accepted"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('toggle_outfit_favorite', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(response.status_code, 405)
    
    def test_toggle_favorite_makes_favorite(self):
        """Test toggling from not favorite to favorite"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('toggle_outfit_favorite', kwargs={'outfit_pk': self.outfit.pk}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['is_favorite'])
        
        self.outfit.refresh_from_db()
        self.assertTrue(self.outfit.is_favorite)
    
    def test_toggle_favorite_removes_favorite(self):
        """Test toggling from favorite to not favorite"""
        self.client.login(username='testuser', password='testpass123')
        
        self.outfit.is_favorite = True
        self.outfit.save()
        
        response = self.client.post(
            reverse('toggle_outfit_favorite', kwargs={'outfit_pk': self.outfit.pk}),
            content_type='application/json'
        )
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(data['is_favorite'])
        
        self.outfit.refresh_from_db()
        self.assertFalse(self.outfit.is_favorite)


class DuplicateOutfitTests(TestCase):
    """Tests for duplicating outfits"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        
        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Original Outfit",
            description="Original description",
            is_favorite=True
        )
        self.outfit.items.add(self.item1)
    
    def test_duplicate_outfit_requires_authentication(self):
        """Test that unauthenticated users cannot duplicate outfits"""
        response = self.client.post(
            reverse('duplicate_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_duplicate_outfit_creates_copy(self):
        """Test that duplicating creates a new outfit with (Copy) suffix"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('duplicate_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        self.assertEqual(Outfit.objects.filter(user=self.user).count(), 2)
        
        duplicate = Outfit.objects.get(name="Original Outfit (Copy)")
        self.assertEqual(duplicate.description, "Original description")
        self.assertEqual(duplicate.items.count(), 1)
        self.assertIn(self.item1, duplicate.items.all())
        
        self.assertFalse(duplicate.is_favorite)
    
    def test_duplicate_outfit_redirects_to_detail(self):
        """Test that after duplication, user is redirected to new outfit detail"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('duplicate_outfit', kwargs={'outfit_pk': self.outfit.pk})
        )
        
        duplicate = Outfit.objects.get(name="Original Outfit (Copy)")
        self.assertRedirects(
            response,
            reverse('outfit_detail', kwargs={'outfit_pk': duplicate.pk})
        )


class QuickAddToOutfitTests(TestCase):
    """Tests for quick add wardrobe item to outfit"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        
        self.outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit"
        )
    
    def test_quick_add_requires_authentication(self):
        """Test that unauthenticated users cannot quick add"""
        response = self.client.get(
            reverse('quick_add_to_outfit', kwargs={'item_pk': self.item.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_quick_add_get_displays_outfit_list(self):
        """Test that GET request displays list of outfits"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('quick_add_to_outfit', kwargs={'item_pk': self.item.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'quick_add_to_outfit.html')
        self.assertEqual(response.context['wardrobe_item'], self.item)
        self.assertIn(self.outfit, response.context['outfits'])
    
    def test_quick_add_post_adds_item_to_outfit(self):
        """Test that POST request adds item to selected outfit"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('quick_add_to_outfit', kwargs={'item_pk': self.item.pk}),
            {'outfit_id': self.outfit.pk}
        )
        
        self.assertRedirects(response, reverse('my_wardrobe'))
        
        self.outfit.refresh_from_db()
        self.assertIn(self.item, self.outfit.items.all())
    
    def test_quick_add_prevents_duplicate_additions(self):
        """Test that adding same item twice shows info message"""
        self.client.login(username='testuser', password='testpass123')
        
        self.outfit.items.add(self.item)
        
        response = self.client.post(
            reverse('quick_add_to_outfit', kwargs={'item_pk': self.item.pk}),
            {'outfit_id': self.outfit.pk},
            follow=True
        )
        
        messages_list = list(response.context['messages'])
        self.assertTrue(any('already in' in str(msg) for msg in messages_list))


# ==================== MODEL TESTS ====================

class WardrobeModelTests(TestCase):
    """Tests for WardrobeItem model constraints and behavior"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.catalog_item = Item.objects.create(
            title="Test Item",
            description="Test description"
        )
    
    def test_wardrobe_item_string_representation(self):
        """Test the __str__ method returns correct format"""
        item = WardrobeItem.objects.create(
            user=self.user,
            title="Test Shirt",
            category="top"
        )
        
        self.assertEqual(str(item), "testuser - Test Shirt")
    
    def test_wardrobe_item_unique_together_constraint(self):
        """Test that unique_together constraint prevents duplicate saves"""
        WardrobeItem.objects.create(
            user=self.user,
            title="First Save",
            catalog_item=self.catalog_item,
            category="top"
        )
        
        with self.assertRaises(IntegrityError):
            WardrobeItem.objects.create(
                user=self.user,
                title="Second Save",
                catalog_item=self.catalog_item,
                category="top"
            )
    
    def test_wardrobe_item_allows_different_users_same_catalog_item(self):
        """Test that different users can save the same catalog item"""
        User = get_user_model()
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        item1 = WardrobeItem.objects.create(
            user=self.user,
            title="User 1 Save",
            catalog_item=self.catalog_item,
            category="top"
        )
        
        item2 = WardrobeItem.objects.create(
            user=user2,
            title="User 2 Save",
            catalog_item=self.catalog_item,
            category="top"
        )
        
        self.assertIsNotNone(item1.pk)
        self.assertIsNotNone(item2.pk)
    
    def test_wardrobe_item_catalog_item_nullable(self):
        """Test that catalog_item can be None for manually added items"""
        item = WardrobeItem.objects.create(
            user=self.user,
            title="Manual Item",
            category="top",
            catalog_item=None
        )
        
        self.assertIsNone(item.catalog_item)
        self.assertIsNotNone(item.pk)


class OutfitModelTests(TestCase):
    """Tests for Outfit model constraints and behavior"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
    
    def test_outfit_string_representation(self):
        """Test the __str__ method returns correct format"""
        outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit"
        )
        
        self.assertEqual(str(outfit), "testuser - Test Outfit")
    
    def test_outfit_item_count_method(self):
        """Test the item_count helper method"""
        outfit = Outfit.objects.create(
            user=self.user,
            name="Test Outfit"
        )
        outfit.items.add(self.item1)
        
        self.assertEqual(outfit.item_count(), 1)
    
    def test_outfit_unique_name_per_user(self):
        """Test that outfit names must be unique per user"""
        Outfit.objects.create(
            user=self.user,
            name="Casual Look"
        )
        
        with self.assertRaises(IntegrityError):
            Outfit.objects.create(
                user=self.user,
                name="Casual Look"
            )
    
    def test_outfit_allows_same_name_different_users(self):
        """Test that different users can have outfits with the same name"""
        User = get_user_model()
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        outfit1 = Outfit.objects.create(
            user=self.user,
            name="Casual Look"
        )
        
        outfit2 = Outfit.objects.create(
            user=user2,
            name="Casual Look"
        )
        
        self.assertIsNotNone(outfit1.pk)
        self.assertIsNotNone(outfit2.pk)
    
    def test_outfit_many_to_many_items(self):
        """Test that outfits can contain multiple items"""
        item2 = WardrobeItem.objects.create(
            user=self.user,
            title="Pants",
            category="bottom"
        )
        
        outfit = Outfit.objects.create(
            user=self.user,
            name="Complete Look"
        )
        outfit.items.add(self.item1, item2)
        
        self.assertEqual(outfit.items.count(), 2)
        self.assertIn(self.item1, outfit.items.all())
        self.assertIn(item2, outfit.items.all())


# ==================== INTEGRATION TESTS ====================

class ItemDetailWithWardrobeTests(TestCase):
    """Tests for item detail view with wardrobe integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.item = Item.objects.create(
            title="Test Item",
            description="Test description",
            image_url="https://example.com/item.jpg"
        )
    
    def test_item_detail_shows_already_saved_status(self):
        """Test that item detail shows if item is already in wardrobe"""
        self.client.login(username='testuser', password='testpass123')
        
        WardrobeItem.objects.create(
            user=self.user,
            title=self.item.title,
            catalog_item=self.item,
            category='other'
        )
        
        response = self.client.get(reverse('item_detail', kwargs={'pk': self.item.pk}))
        
        self.assertTrue(response.context['already_saved'])
    
    def test_item_detail_shows_not_saved_status(self):
        """Test that item detail shows if item is not yet in wardrobe"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('item_detail', kwargs={'pk': self.item.pk}))
        
        self.assertFalse(response.context['already_saved'])
    
    def test_item_detail_unauthenticated_no_save_status(self):
        """Test that unauthenticated users see appropriate state"""
        response = self.client.get(reverse('item_detail', kwargs={'pk': self.item.pk}))
        
        self.assertFalse(response.context['already_saved'])


class WardrobeIntegrationTests(TestCase):
    """Integration tests for wardrobe workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.catalog_item = Item.objects.create(
            title="Catalog Shirt",
            description="A nice shirt from the catalog",
            image_url="https://example.com/shirt.jpg"
        )
    
    def test_complete_wardrobe_workflow(self):
        """Test complete workflow: browse catalog, save item, view in wardrobe, edit, delete"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Browse catalog and view item
        response = self.client.get(reverse('item_detail', kwargs={'pk': self.catalog_item.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['already_saved'])
        
        # 2. Save to wardrobe
        response = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk}),
            follow=True
        )
        self.assertEqual(WardrobeItem.objects.filter(user=self.user).count(), 1)
        
        # 3. View in wardrobe
        response = self.client.get(reverse('my_wardrobe'))
        self.assertEqual(len(response.context['wardrobe_items']), 1)
        
        # 4. Edit the item
        wardrobe_item = WardrobeItem.objects.get(user=self.user)
        response = self.client.post(
            reverse('edit_wardrobe_item', kwargs={'item_pk': wardrobe_item.pk}),
            {
                'title': 'Updated Title',
                'category': 'top',
                'description': 'Updated description'
            }
        )
        wardrobe_item.refresh_from_db()
        self.assertEqual(wardrobe_item.title, 'Updated Title')
        
        # 5. Delete the item
        response = self.client.post(
            reverse('delete_wardrobe_item', kwargs={'item_pk': wardrobe_item.pk})
        )
        self.assertEqual(WardrobeItem.objects.filter(user=self.user).count(), 0)


class OutfitIntegrationTests(TestCase):
    """Integration tests for outfit creation workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
    
    def test_complete_outfit_workflow(self):
        """Test complete workflow: add items to wardrobe, create outfit, view outfit"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Add items to wardrobe
        response = self.client.post(reverse('add_wardrobe_item'), {
            'title': 'Blue Shirt',
            'category': 'top',
            'description': 'A blue shirt'
        })
        
        response = self.client.post(reverse('add_wardrobe_item'), {
            'title': 'Black Pants',
            'category': 'bottom',
            'description': 'Black pants'
        })
        
        self.assertEqual(WardrobeItem.objects.filter(user=self.user).count(), 2)
        
        # 2. Create outfit from wardrobe items
        items = WardrobeItem.objects.filter(user=self.user)
        response = self.client.post(reverse('create_outfit'), {
            'name': 'Work Outfit',
            'description': 'Professional look for work',
            'items': [item.pk for item in items],
            'occasion': 'business',
            'season': 'all'
        })
        
        self.assertEqual(Outfit.objects.filter(user=self.user).count(), 1)
        
        # 3. View outfit in my_outfits
        response = self.client.get(reverse('my_outfits'))
        self.assertEqual(len(response.context['outfits']), 1)
        
        outfit = response.context['outfits'][0]
        self.assertEqual(outfit.name, 'Work Outfit')
        self.assertEqual(outfit.items.count(), 2)


class CompleteWorkflowTests(TestCase):
    """Integration tests for complete user workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        self.catalog_item = Item.objects.create(
            title="Catalog Shirt",
            description="A nice shirt",
            image_url="https://example.com/shirt.jpg"
        )
    
    def test_complete_outfit_creation_workflow(self):
        """Test complete workflow from browsing catalog to creating outfit"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Save catalog item to wardrobe
        self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk})
        )
        
        # 2. Verify item in wardrobe
        response = self.client.get(reverse('my_wardrobe'))
        self.assertEqual(len(response.context['wardrobe_items']), 1)
        
        # 3. Create outfit with wardrobe item
        item = WardrobeItem.objects.get(user=self.user)
        response = self.client.post(reverse('create_outfit'), {
            'name': 'New Outfit',
            'description': 'Test outfit',
            'items': [item.pk],
            'occasion': 'casual'
        })
        
        # 4. Verify outfit was created
        outfit = Outfit.objects.get(user=self.user)
        self.assertEqual(outfit.name, 'New Outfit')
        self.assertIn(item, outfit.items.all())
        
        # 5. View outfit detail
        response = self.client.get(
            reverse('outfit_detail', kwargs={'outfit_pk': outfit.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Outfit')