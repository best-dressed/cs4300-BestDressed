"""
Comprehensive test suite for Wardrobe features.

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
from django.db import transaction
import json


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
