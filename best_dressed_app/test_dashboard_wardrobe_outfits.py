"""
Comprehensive test suite for Dashboard, Wardrobe, Account Settings, and Outfit features.

This test file covers:
- Dashboard view and functionality
- Account Settings/User Profile management
- Wardrobe management (add, edit, delete, save from catalog)
- Outfit creation and management
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from best_dressed_app.models import Item, UserProfile, WardrobeItem, Outfit
from django.contrib import messages
from django.db import IntegrityError, transaction


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
        # Should redirect to login page
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
        
        # Verify no profile exists yet
        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())
        
        # Access dashboard
        response = self.client.get(reverse('dashboard'))
        
        # Profile should now exist
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_uses_existing_profile(self):
        """Test that dashboard uses existing profile instead of creating duplicate"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create a profile manually
        profile = UserProfile.objects.create(
            user=self.user,
            bio="Test bio",
            style_preferences="casual"
        )
        
        # Access dashboard
        self.client.get(reverse('dashboard'))
        
        # Should still be only one profile
        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 1)
        
        # Profile should be unchanged
        profile.refresh_from_db()
        self.assertEqual(profile.bio, "Test bio")
    
    def test_dashboard_displays_correct_wardrobe_count(self):
        """Test that dashboard shows accurate count of wardrobe items"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create some wardrobe items
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
        
        # Check that context has correct count
        self.assertEqual(response.context['wardrobe_count'], 2)
        self.assertContains(response, '2')  # Should display the count
    
    def test_dashboard_only_counts_user_items(self):
        """Test that dashboard only counts items belonging to the logged-in user"""
        # Create another user with items
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
        
        # Login as test user and create one item
        self.client.login(username='testuser', password='testpass123')
        WardrobeItem.objects.create(
            user=self.user,
            title="My Item",
            category="bottom"
        )
        
        response = self.client.get(reverse('dashboard'))
        
        # Should only count the logged-in user's items
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
        
        # Check for important links using actual URLs from template
        self.assertContains(response, '/account/')  # Account Settings
        self.assertContains(response, '/wardrobe/')  # My Wardrobe
        self.assertContains(response, '/outfits/')  # My Outfits
        self.assertContains(response, '/item_listing/')  # Browse Catalog


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
        
        # Should redirect to login
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
        
        # Verify no profile exists
        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())
        
        # Access account settings
        response = self.client.get(reverse('account_settings'))
        
        # Profile should now exist
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.assertEqual(response.status_code, 200)
    
    def test_account_settings_displays_existing_profile_data(self):
        """Test that form is pre-filled with existing profile data"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create profile with specific data
        profile = UserProfile.objects.create(
            user=self.user,
            bio="I love fashion",
            style_preferences="casual, streetwear",
            favorite_colors="blue, black"
        )
        
        response = self.client.get(reverse('account_settings'))
        
        # Check context has the profile
        self.assertEqual(response.context['profile'], profile)
        
        # Check that the page contains the profile data
        self.assertContains(response, "I love fashion")
        self.assertContains(response, "casual, streetwear")
    
    def test_account_settings_update_profile_via_post(self):
        """Test that POST request updates profile successfully"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create initial profile
        profile = UserProfile.objects.create(
            user=self.user,
            bio="Old bio",
            style_preferences="old style"
        )
        
        # Update profile via POST
        response = self.client.post(reverse('account_settings'), {
            'bio': 'Updated bio',
            'style_preferences': 'new style, modern',
            'favorite_colors': 'red, green'
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account_settings'))
        
        # Verify database was updated
        profile.refresh_from_db()
        self.assertEqual(profile.bio, 'Updated bio')
        self.assertEqual(profile.style_preferences, 'new style, modern')
        self.assertEqual(profile.favorite_colors, 'red, green')
    
    def test_account_settings_shows_success_message(self):
        """Test that success message is displayed after profile update"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create profile
        UserProfile.objects.create(user=self.user)
        
        # Update profile
        response = self.client.post(reverse('account_settings'), {
            'bio': 'New bio',
            'style_preferences': 'casual',
            'favorite_colors': 'blue'
        }, follow=True)  # follow=True to see messages after redirect
        
        # Check for success message
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertIn('updated successfully', str(messages_list[0]))
    
    def test_account_settings_profile_unique_to_user(self):
        """Test that each user has their own profile"""
        # Create two users
        User = get_user_model()
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        # Login as first user and create profile
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('account_settings'), {
            'bio': 'User 1 bio',
            'style_preferences': 'user1 style'
        })
        
        # Login as second user
        self.client.logout()
        self.client.login(username='testuser2', password='testpass123')
        response = self.client.post(reverse('account_settings'), {
            'bio': 'User 2 bio',
            'style_preferences': 'user2 style'
        })
        
        # Verify both profiles exist with correct data
        profile1 = UserProfile.objects.get(user=self.user)
        profile2 = UserProfile.objects.get(user=user2)
        
        self.assertEqual(profile1.bio, 'User 1 bio')
        self.assertEqual(profile2.bio, 'User 2 bio')
        self.assertNotEqual(profile1.bio, profile2.bio)


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
        
        # Create a catalog item
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
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_save_to_wardrobe_creates_wardrobe_item(self):
        """Test that POST request creates a wardrobe item"""
        self.client.login(username='testuser', password='testpass123')
        
        # Save item to wardrobe
        response = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk})
        )
        
        # Should redirect back to item detail
        self.assertRedirects(response, reverse('item_detail', kwargs={'pk': self.catalog_item.pk}))
        
        # Verify wardrobe item was created
        wardrobe_item = WardrobeItem.objects.get(user=self.user, catalog_item=self.catalog_item)
        self.assertEqual(wardrobe_item.title, "Cool Jacket")
        self.assertEqual(wardrobe_item.description, "A very cool jacket")
    
    def test_save_to_wardrobe_prevents_duplicates(self):
        """Test that saving the same item twice doesn't create duplicates"""
        from django.db import transaction
        
        self.client.login(username='testuser', password='testpass123')
        
        # Save item first time
        response1 = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk})
        )
        
        # Verify it was created
        self.assertEqual(WardrobeItem.objects.filter(user=self.user, catalog_item=self.catalog_item).count(), 1)
        
        # Try to save again - wrap in atomic to handle the IntegrityError gracefully
        with transaction.atomic():
            response2 = self.client.post(
                reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk})
            )
        
        # Should redirect
        self.assertEqual(response2.status_code, 302)
        
        # Should still be only one
        self.assertEqual(WardrobeItem.objects.filter(user=self.user, catalog_item=self.catalog_item).count(), 1)

    
    def test_save_to_wardrobe_shows_success_message(self):
        """Test that success message is displayed when item is saved"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk}),
            follow=True
        )
        
        # Check for success message
        messages_list = list(response.context['messages'])
        self.assertTrue(any('added to your wardrobe' in str(msg) for msg in messages_list))
    
    def test_save_to_wardrobe_only_accepts_post(self):
        """Test that GET requests are not allowed"""
        self.client.login(username='testuser', password='testpass123')
        
        # Try GET request
        response = self.client.get(
            reverse('save_to_wardrobe', kwargs={'item_pk': self.catalog_item.pk}),
            follow=True
        )
        
        # Should show error message and not create item
        self.assertEqual(WardrobeItem.objects.filter(user=self.user).count(), 0)
        messages_list = list(response.context['messages'])
        self.assertTrue(any('Invalid request method' in str(msg) for msg in messages_list))
    
    def test_save_to_wardrobe_handles_nonexistent_item(self):
        """Test that 404 is returned for non-existent catalog items"""
        self.client.login(username='testuser', password='testpass123')
        
        # Try to save item that doesn't exist
        response = self.client.post(
            reverse('save_to_wardrobe', kwargs={'item_pk': 99999})
        )
        
        # Should return 404
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
        
        # Create some wardrobe items
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
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_my_wardrobe_displays_user_items(self):
        """Test that wardrobe displays all user's items"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_wardrobe'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_wardrobe.html')
        
        # Check that both items are in the context
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 2)
        self.assertIn(self.item1, wardrobe_items)
        self.assertIn(self.item2, wardrobe_items)
    
    def test_my_wardrobe_only_shows_user_items(self):
        """Test that users only see their own items, not other users' items"""
        # Create another user with items
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
        
        # Login as test user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_wardrobe'))
        
        # Should only see own items
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 2)
        self.assertNotIn(other_item, wardrobe_items)
    
    def test_my_wardrobe_category_filter(self):
        """Test filtering wardrobe items by category"""
        self.client.login(username='testuser', password='testpass123')
        
        # Filter by 'top' category
        response = self.client.get(reverse('my_wardrobe'), {'category': 'top'})
        
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 1)
        self.assertEqual(wardrobe_items[0].title, "Blue Shirt")
    
    def test_my_wardrobe_search_functionality(self):
        """Test searching wardrobe items"""
        self.client.login(username='testuser', password='testpass123')
        
        # Search for "blue"
        response = self.client.get(reverse('my_wardrobe'), {'search': 'blue'})
        
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 1)
        self.assertEqual(wardrobe_items[0].title, "Blue Shirt")
    
    def test_my_wardrobe_search_multiple_fields(self):
        """Test that search works across multiple fields"""
        self.client.login(username='testuser', password='testpass123')
        
        # Search by brand
        response = self.client.get(reverse('my_wardrobe'), {'search': 'Nike'})
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 1)
        
        # Search by color
        response = self.client.get(reverse('my_wardrobe'), {'search': 'black'})
        wardrobe_items = response.context['wardrobe_items']
        self.assertEqual(len(wardrobe_items), 1)
        self.assertEqual(wardrobe_items[0].title, "Black Pants")
    
    def test_my_wardrobe_sorting(self):
        """Test sorting wardrobe items"""
        self.client.login(username='testuser', password='testpass123')
        
        # Sort A-Z by title
        response = self.client.get(reverse('my_wardrobe'), {'sort': 'title'})
        wardrobe_items = list(response.context['wardrobe_items'])
        self.assertEqual(wardrobe_items[0].title, "Black Pants")  # B comes before Bl
        self.assertEqual(wardrobe_items[1].title, "Blue Shirt")
        
        # Sort Z-A by title
        response = self.client.get(reverse('my_wardrobe'), {'sort': '-title'})
        wardrobe_items = list(response.context['wardrobe_items'])
        self.assertEqual(wardrobe_items[0].title, "Blue Shirt")
        self.assertEqual(wardrobe_items[1].title, "Black Pants")
    
    def test_my_wardrobe_combined_filters(self):
        """Test using multiple filters together"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add more items for testing
        WardrobeItem.objects.create(
            user=self.user,
            title="Blue Jeans",
            category="bottom",
            color="blue"
        )
        
        # Filter by category and search
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
        
        # Should redirect to login
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
        
        # Should redirect to my_wardrobe
        self.assertRedirects(response, reverse('my_wardrobe'))
        
        # Verify item was created
        item = WardrobeItem.objects.get(title='My New Shirt')
        self.assertEqual(item.user, self.user)
        self.assertEqual(item.category, 'top')
        self.assertIsNone(item.catalog_item)  # Manual items have no catalog_item
    
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
        
        # Create a wardrobe item
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
        
        # Should redirect to login
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
        
        # Should redirect to my_wardrobe
        self.assertRedirects(response, reverse('my_wardrobe'))
        
        # Verify item was updated
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Updated Title')
        self.assertEqual(self.item.description, 'Updated description')
        self.assertEqual(self.item.category, 'bottom')
    
    def test_edit_wardrobe_item_user_can_only_edit_own_items(self):
        """Test that users can only edit their own items"""
        # Create another user
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        # Create item for other user
        other_item = WardrobeItem.objects.create(
            user=other_user,
            title="Other User's Item",
            category="top"
        )
        
        # Login as test user and try to edit other user's item
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('edit_wardrobe_item', kwargs={'item_pk': other_item.pk})
        )
        
        # Should return 404 (item not found for this user)
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
        
        # Check for success message
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
        
        # Create a wardrobe item
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
        
        # Should redirect to login
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
        
        # Verify item exists
        self.assertTrue(WardrobeItem.objects.filter(pk=self.item.pk).exists())
        
        # Delete the item
        response = self.client.post(
            reverse('delete_wardrobe_item', kwargs={'item_pk': self.item.pk})
        )
        
        # Should redirect to my_wardrobe
        self.assertRedirects(response, reverse('my_wardrobe'))
        
        # Verify item was deleted
        self.assertFalse(WardrobeItem.objects.filter(pk=self.item.pk).exists())
    
    def test_delete_wardrobe_item_user_can_only_delete_own_items(self):
        """Test that users can only delete their own items"""
        # Create another user with an item
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
        
        # Login as test user and try to delete other user's item
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('delete_wardrobe_item', kwargs={'item_pk': other_item.pk})
        )
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
        
        # Verify item was NOT deleted
        self.assertTrue(WardrobeItem.objects.filter(pk=other_item.pk).exists())
    
    def test_delete_wardrobe_item_shows_success_message(self):
        """Test that success message is displayed after deletion"""
        self.client.login(username='testuser', password='testpass123')
        
        item_title = self.item.title
        response = self.client.post(
            reverse('delete_wardrobe_item', kwargs={'item_pk': self.item.pk}),
            follow=True
        )
        
        # Check for success message
        messages_list = list(response.context['messages'])
        self.assertTrue(any('removed from your wardrobe' in str(msg) for msg in messages_list))
        self.assertTrue(any(item_title in str(msg) for msg in messages_list))


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
        
        # Create some wardrobe items to use in outfits
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
        
        # Should redirect to login
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
        
        # Should redirect to my_outfits
        self.assertRedirects(response, reverse('my_outfits'))
        
        # Verify outfit was created
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
        
        # Check for success message
        messages_list = list(response.context['messages'])
        self.assertTrue(any('created successfully' in str(msg) for msg in messages_list))


class MyOutfitsTests(TestCase):
    """Tests for viewing user's outfits"""
    
    def setUp(self):
        """Set up test fixtures"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        # Create wardrobe items
        self.item1 = WardrobeItem.objects.create(
            user=self.user,
            title="Shirt",
            category="top"
        )
        
        # Create outfits
        self.outfit1 = Outfit.objects.create(
            user=self.user,
            name="Casual Look",
            description="For everyday wear"
        )
        self.outfit1.items.add(self.item1)
        
        self.outfit2 = Outfit.objects.create(
            user=self.user,
            name="Formal Look",
            description="For special occasions",
            is_favorite=True
        )
    
    def test_my_outfits_requires_authentication(self):
        """Test that unauthenticated users cannot view outfits"""
        response = self.client.get(reverse('my_outfits'))
        
        # Should redirect to login
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
        # Create another user with an outfit
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        other_outfit = Outfit.objects.create(
            user=other_user,
            name="Other User's Outfit"
        )
        
        # Login as test user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_outfits'))
        
        outfits = response.context['outfits']
        self.assertEqual(len(outfits), 2)
        self.assertNotIn(other_outfit, outfits)
    
    def test_my_outfits_ordering(self):
        """Test that outfits are ordered correctly (favorites first, then newest)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('my_outfits'))
        
        outfits = list(response.context['outfits'])
        
        # Favorite outfit should come first
        self.assertEqual(outfits[0], self.outfit2)
        self.assertTrue(outfits[0].is_favorite)


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
        
        # Create catalog items
        self.item = Item.objects.create(
            title="Test Item",
            description="Test description",
            image_url="https://example.com/item.jpg"
        )
    
    def test_item_detail_shows_already_saved_status(self):
        """Test that item detail shows if item is already in wardrobe"""
        self.client.login(username='testuser', password='testpass123')
        
        # Save item to wardrobe
        WardrobeItem.objects.create(
            user=self.user,
            title=self.item.title,
            catalog_item=self.item,
            category='other'
        )
        
        # View item detail
        response = self.client.get(reverse('item_detail', kwargs={'pk': self.item.pk}))
        
        # Should indicate item is already saved
        self.assertTrue(response.context['already_saved'])
    
    def test_item_detail_shows_not_saved_status(self):
        """Test that item detail shows if item is not yet in wardrobe"""
        self.client.login(username='testuser', password='testpass123')
        
        # View item detail without saving
        response = self.client.get(reverse('item_detail', kwargs={'pk': self.item.pk}))
        
        # Should indicate item is not saved
        self.assertFalse(response.context['already_saved'])
    
    def test_item_detail_unauthenticated_no_save_status(self):
        """Test that unauthenticated users see appropriate state"""
        # Don't login
        response = self.client.get(reverse('item_detail', kwargs={'pk': self.item.pk}))
        
        # Should not show as saved for anonymous users
        self.assertFalse(response.context['already_saved'])


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
        # Create first wardrobe item
        WardrobeItem.objects.create(
            user=self.user,
            title="First Save",
            catalog_item=self.catalog_item,
            category="top"
        )
        
        # Try to create duplicate
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
        
        # Both users save the same catalog item
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
        
        # Both should exist
        self.assertIsNotNone(item1.pk)
        self.assertIsNotNone(item2.pk)
    
    def test_wardrobe_item_catalog_item_nullable(self):
        """Test that catalog_item can be None for manually added items"""
        item = WardrobeItem.objects.create(
            user=self.user,
            title="Manual Item",
            category="top",
            catalog_item=None  # No associated catalog item
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
        
        # Try to create another outfit with same name
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
        
        # Both should exist
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


# Integration tests that test multiple components working together
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
        
        # Create catalog item
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